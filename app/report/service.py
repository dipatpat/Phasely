import uuid
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.log.models import DailyLog, ExerciseLog, MealLog
from app.recipe.models import Recipe


async def generate_weekly_report_data(
    db: AsyncSession, client_id: uuid.UUID, week_start: date
) -> dict:
    week_end = week_start + timedelta(days=6)
    week_end_datetime = datetime.combine(week_end, time.max)

    daily_log_result = await db.execute(
        select(DailyLog).where(
            DailyLog.client_id == client_id,
            DailyLog.log_date.between(week_start, week_end),
        )
    )
    daily_logs_by_date = {log.log_date: log for log in daily_log_result.scalars().all()}

    meal_result = await db.execute(
        select(
            func.date(MealLog.consumed_at),
            func.sum(Recipe.calories * MealLog.portion_quantity),
            func.sum(Recipe.protein * MealLog.portion_quantity),
            func.sum(Recipe.carbs * MealLog.portion_quantity),
            func.sum(Recipe.fat * MealLog.portion_quantity),
            func.count(MealLog.id),
        )
        .join(Recipe, MealLog.recipe_id == Recipe.id)
        .where(
            MealLog.client_id == client_id,
            MealLog.consumed_at.between(week_start, week_end_datetime),
        )
        .group_by(func.date(MealLog.consumed_at))
    )
    meals_by_date = {row[0]: row[1:] for row in meal_result.all()}

    exercise_result = await db.execute(
        select(func.date(ExerciseLog.completed_at), func.count(ExerciseLog.id))
        .where(
            ExerciseLog.client_id == client_id,
            ExerciseLog.completed_at.between(week_start, week_end_datetime),
        )
        .group_by(func.date(ExerciseLog.completed_at))
    )
    exercises_by_date = {row[0]: row[1] for row in exercise_result.all()}

    daily_breakdown = []
    current_day = week_start
    while current_day <= week_end:
        daily_log = daily_logs_by_date.get(current_day)
        calories, protein, carbs, fat, meals_logged = meals_by_date.get(
            current_day, (0, 0, 0, 0, 0)
        )
        daily_breakdown.append(
            {
                "date": current_day.isoformat(),
                "cycle_phase": daily_log.cycle_phase.value if daily_log else None,
                "energy_level": daily_log.energy_level if daily_log else None,
                "hours_of_sleep": (
                    float(daily_log.hours_of_sleep)
                    if daily_log and daily_log.hours_of_sleep is not None
                    else None
                ),
                "calories_consumed": round(calories),
                "protein": round(float(protein), 2),
                "carbs": round(float(carbs), 2),
                "fat": round(float(fat), 2),
                "meals_logged": meals_logged,
                "exercises_completed": exercises_by_date.get(current_day, 0),
            }
        )
        current_day += timedelta(days=1)

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "summary": _summarize(daily_breakdown),
        "daily_breakdown": daily_breakdown,
    }


def _average(values: list) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return round(sum(present) / len(present), 2)


def _summarize(daily_breakdown: list[dict]) -> dict:
    return {
        "days_logged": sum(1 for day in daily_breakdown if day["cycle_phase"]),
        "average_hours_of_sleep": _average(
            [day["hours_of_sleep"] for day in daily_breakdown]
        ),
        "average_energy_level": _average(
            [day["energy_level"] for day in daily_breakdown]
        ),
        "total_calories": sum(day["calories_consumed"] for day in daily_breakdown),
        "total_protein": round(sum(day["protein"] for day in daily_breakdown), 2),
        "total_carbs": round(sum(day["carbs"] for day in daily_breakdown), 2),
        "total_fat": round(sum(day["fat"] for day in daily_breakdown), 2),
        "total_meals_logged": sum(day["meals_logged"] for day in daily_breakdown),
        "total_exercises_completed": sum(
            day["exercises_completed"] for day in daily_breakdown
        ),
    }
