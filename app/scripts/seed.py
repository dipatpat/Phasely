"""Fill the development database with realistic demo data.

Run inside the API container:
    docker compose --profile demo exec api uv run python -m app.scripts.seed --reset

Every account's password is DEMO_PASSWORD. Never run this against production:
--reset deletes every row in every table.
"""

import argparse
import asyncio
import json
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

import redis.asyncio as aioredis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.models  # noqa: F401
from app.auth.security import hash_password
from app.auth.service import create_user
from app.client.service import create_client_profile
from app.core.base import Base
from app.core.config import APP_TZ, settings
from app.core.database import AsyncSessionLocal
from app.core.enums import CyclePhase, DifficultyLevel, MealType, UserRole
from app.exercise.service import create_exercise
from app.log.models import DailyLog, ExerciseLog, MealLog, PeriodLog
from app.plan.models import NutritionPlan, TrainingPlan
from app.plan.schemas import NutritionPlanRecipeCreate, TrainingPlanExerciseCreate
from app.plan.service import create_nutrition_plan, create_training_plan
from app.recipe.schemas import IngredientCreate
from app.recipe.service import create_recipe
from app.recommendation.service import CycleParameters
from app.report.service import generate_weekly_report_data
from app.report.tasks import previous_week_start
from app.session.service import (
    book_session,
    cancel_session,
    complete_session,
    confirm_session,
)
from app.trainer.service import create_availability_slot, create_trainer_profile
from app.user.models import User

DEMO_PASSWORD = "phasely123"
DATA = json.loads(Path(__file__).with_name("seed_data.json").read_text())
# Typical energy (0-10) per phase, so the history looks like a real cycle
ENERGY_BY_PHASE = {
    CyclePhase.menstrual: (3, 5),
    CyclePhase.follicular: (6, 8),
    CyclePhase.ovulatory: (8, 9),
    CyclePhase.luteal: (4, 6),
}
# Fixed seed: the "random" sleep/energy values are the same on every run
rng = random.Random(42)


def today() -> date:
    return datetime.now(APP_TZ).date()


def next_weekdays(count: int) -> list[date]:
    days, day = [], today()
    while len(days) < count:
        day += timedelta(days=1)
        if day.isoweekday() <= 5:
            days.append(day)
    return days


async def reset_database(db: AsyncSession) -> None:
    for table in reversed(Base.metadata.sorted_tables):
        await db.execute(table.delete())
    await db.commit()


async def create_account(
    db: AsyncSession, first: str, last: str, email: str, role: UserRole
) -> User:
    hashed = hash_password(DEMO_PASSWORD)
    return await create_user(db, first, last, email, hashed, role)


async def create_library(db: AsyncSession) -> tuple[list, dict]:
    recipes = []
    for item in DATA["recipes"]:
        protein, carbs, fat, calories = item["macros"]
        recipe = await create_recipe(
            db,
            name=item["name"],
            meal_type=MealType(item["meal"]),
            protein=Decimal(protein),
            carbs=Decimal(carbs),
            fat=Decimal(fat),
            calories=calories,
            serving_size="1 serving",
            preparation_notes=item.get("notes"),
            ingredients=[
                IngredientCreate(name=name, quantity=Decimal(str(qty)), unit=unit)
                for name, qty, unit in item["ingredients"]
            ],
            dietary_tag_names=item["tags"],
        )
        recipes.append((recipe, CyclePhase(item["phase"])))

    exercises = {}
    for name, description in DATA["exercises"]:
        exercises[name] = await create_exercise(db, name, description)
    return recipes, exercises


async def create_plans(
    db: AsyncSession, client_id, trainer_id, recipes: list, exercises: dict
) -> None:
    await create_nutrition_plan(
        db,
        client_id=client_id,
        trainer_id=trainer_id,
        title="Cycle-synced nutrition",
        recipes=[
            NutritionPlanRecipeCreate(
                recipe_id=recipe.id, meal_type=recipe.meal_type, cycle_phase=phase
            )
            for recipe, phase in recipes
        ],
    )

    assignments = []
    for phase, template in DATA["training"].items():
        for day_of_week in range(1, 8):
            # Three exercises per day, rotating through the phase's template
            for offset in range(3):
                name, difficulty, sets, reps, duration = template[
                    (day_of_week + offset) % len(template)
                ]
                assignments.append(
                    TrainingPlanExerciseCreate(
                        exercise_id=exercises[name].id,
                        cycle_phase=CyclePhase(phase),
                        day_of_week=day_of_week,
                        sets=sets,
                        reps=reps,
                        duration_seconds=duration,
                        difficulty_level=DifficultyLevel(difficulty),
                    )
                )
    await create_training_plan(
        db,
        client_id=client_id,
        trainer_id=trainer_id,
        title="Cycle-synced training",
        exercises=assignments,
    )


async def create_history(
    db: AsyncSession, client_id, cycle: CycleParameters, days: int
) -> None:
    """Daily, meal and exercise logs for the past days (today stays empty)."""
    nutrition = await db.scalar(
        select(NutritionPlan).where(NutritionPlan.client_id == client_id)
    )
    training = await db.scalar(
        select(TrainingPlan).where(TrainingPlan.client_id == client_id)
    )
    await db.refresh(nutrition, ["recipes"])
    await db.refresh(training, ["exercises"])

    for days_ago in range(days, 0, -1):
        day = today() - timedelta(days=days_ago)
        phase = cycle.phase_on(day)
        low, high = ENERGY_BY_PHASE[phase]
        db.add(
            DailyLog(
                client_id=client_id,
                log_date=day,
                cycle_phase=phase,
                hours_of_sleep=Decimal(str(rng.choice([6.5, 7, 7.5, 8, 8.5]))),
                energy_level=rng.randint(low, high),
            )
        )

        for meal_type, hour in [
            (MealType.breakfast, 8),
            (MealType.lunch, 13),
            (MealType.dinner, 19),
        ]:
            options = [
                item
                for item in nutrition.recipes
                if item.cycle_phase == phase and item.meal_type == meal_type
            ]
            if options:
                db.add(
                    MealLog(
                        client_id=client_id,
                        recipe_id=rng.choice(options).recipe_id,
                        meal_type=meal_type,
                        consumed_at=datetime.combine(day, time(hour), tzinfo=APP_TZ),
                        portion_quantity=Decimal("1"),
                        portion_unit="serving",
                    )
                )

        planned = [
            item
            for item in training.exercises
            if item.cycle_phase == phase and item.day_of_week == day.isoweekday()
        ]
        # On most days the client completes two of the planned exercises
        if planned and rng.random() < 0.75:
            for item in planned[:2]:
                db.add(
                    ExerciseLog(
                        client_id=client_id,
                        exercise_id=item.exercise_id,
                        completed_at=datetime.combine(day, time(18), tzinfo=APP_TZ),
                    )
                )
    await db.commit()


async def clear_cached_results() -> None:
    """Cached recommendations and reports belong to the wiped users."""
    redis = aioredis.from_url(settings.REDIS_URL)
    try:
        for pattern in ("recommendations:*", "weekly_report:*"):
            async for key in redis.scan_iter(match=pattern):
                await redis.delete(key)
    finally:
        await redis.aclose()


async def cache_last_weeks_reports(db: AsyncSession, client_ids: list) -> None:
    """What Celery Beat would have produced last Monday at 06:00."""
    week_start = previous_week_start(today())
    redis = aioredis.from_url(settings.REDIS_URL)
    try:
        for client_id in client_ids:
            report = await generate_weekly_report_data(db, client_id, week_start)
            key = f"weekly_report:{client_id}:{week_start.isoformat()}"
            await redis.set(key, json.dumps(report), ex=604800)
    finally:
        await redis.aclose()


async def seed(reset: bool) -> None:
    async with AsyncSessionLocal() as db:
        if reset:
            await reset_database(db)
            await clear_cached_results()
        elif await db.scalar(select(func.count()).select_from(User)):
            print("The database already has data. Run with --reset to wipe it.")
            return

        # Trainers: Anna has the clients, Tomasz gives onboarding a second choice
        anna = await create_account(
            db, "Anna", "Kowalska", "anna@phasely.app", UserRole.trainer
        )
        trainer = await create_trainer_profile(
            db,
            anna.id,
            bio="Certified trainer focused on cycle-aware strength training.",
            specialization="Strength & Conditioning",
        )
        tomasz = await create_account(
            db, "Tomasz", "Wiśniewski", "tomasz@phasely.app", UserRole.trainer
        )
        await create_trainer_profile(
            db, tomasz.id, bio="Yoga and mobility coach.", specialization="Yoga"
        )

        # Clients: Maria (full history), Kasia (a few days), Ola (no plan yet)
        maria_cycle = CycleParameters(today() - timedelta(days=8), 28, 5)
        kasia_cycle = CycleParameters(today() - timedelta(days=20), 30, 4)
        clients = {}
        for first, last, goal, body_fat, cycle in [
            ("Maria", "Nowak", "Build strength", "24.5", maria_cycle),
            ("Kasia", "Zielińska", "Improve energy", "27.0", kasia_cycle),
            ("Ola", "Wójcik", "Lose weight", None, None),
        ]:
            email = f"{first.lower()}@phasely.app"
            user = await create_account(db, first, last, email, UserRole.client)
            clients[first] = await create_client_profile(
                db,
                user.id,
                trainer.id,
                body_fat_percentage=Decimal(body_fat) if body_fat else None,
                fitness_goal=goal,
                cycle_length_days=cycle.cycle_length_days if cycle else 28,
                period_length_days=cycle.period_length_days if cycle else 5,
                last_period_start=cycle.last_period_start if cycle else None,
            )

        # Tracked periods let the backend learn Maria's real cycle length
        for cycles_ago in range(3):
            start = maria_cycle.last_period_start - timedelta(days=28 * cycles_ago)
            db.add(PeriodLog(client_id=clients["Maria"].id, period_start_date=start))
        await db.commit()

        recipes, exercises = await create_library(db)
        for name in ("Maria", "Kasia"):
            await create_plans(db, clients[name].id, trainer.id, recipes, exercises)

        await create_history(db, clients["Maria"].id, maria_cycle, days=14)
        await create_history(db, clients["Kasia"].id, kasia_cycle, days=3)

        # Availability for the next 10 weekdays, plus one past slot
        for day in next_weekdays(10):
            for hour in (9, 11, 15, 17):
                await create_availability_slot(
                    db, trainer.id, day, time(hour), time(hour + 1)
                )
        past_day = today() - timedelta(days=3)
        await create_availability_slot(db, trainer.id, past_day, time(10), time(11))

        # Sessions: completed, confirmed, pending and cancelled
        upcoming = next_weekdays(3)
        past = await book_session(
            db, clients["Maria"].id, trainer.id, past_day, time(10), "Deadlift form"
        )
        await complete_session(db, await confirm_session(db, past))
        soon = await book_session(
            db, clients["Maria"].id, trainer.id, upcoming[0], time(9), "Plan review"
        )
        await confirm_session(db, soon)
        await book_session(
            db, clients["Kasia"].id, trainer.id, upcoming[1], time(11), "First session"
        )
        dropped = await book_session(
            db, clients["Maria"].id, trainer.id, upcoming[2], time(15), "Mobility"
        )
        await cancel_session(db, dropped, reason="Feeling unwell, need to rest")

        await cache_last_weeks_reports(db, [clients["Maria"].id, clients["Kasia"].id])

    print(f"Demo data created. Password for every account: {DEMO_PASSWORD}")
    print("  Trainer  anna@phasely.app    3 clients, 4 sessions, availability")
    print("  Trainer  tomasz@phasely.app  no clients")
    print("  Client   maria@phasely.app   14 days of history, today not logged yet,")
    print("                               last week's report ready in Progress")
    print("  Client   kasia@phasely.app   3 days of history")
    print("  Client   ola@phasely.app     no plan, no cycle data")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill the database with demo data")
    parser.add_argument(
        "--reset", action="store_true", help="delete ALL existing data first"
    )
    asyncio.run(seed(reset=parser.parse_args().reset))


if __name__ == "__main__":
    main()
