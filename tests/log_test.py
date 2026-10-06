from app.core.enums import UserRole
from app.trainer.service import create_trainer_profile
from tests.conftest import auth_headers, create_test_user


async def _create_test_trainer_profile(db, email: str):
    trainer_user = await create_test_user(db, UserRole.trainer, email)
    trainer_profile = await create_trainer_profile(
        db, trainer_user.id, "experienced", "fertility"
    )
    return trainer_user, trainer_profile


async def _create_test_client(client, trainer_profile_id, email, db, **profile_kwargs):
    client_user = await create_test_user(db, UserRole.client, email)
    headers = auth_headers(client_user)
    payload = {"trainer_id": str(trainer_profile_id), **profile_kwargs}
    await client.post("/client/create", json=payload, headers=headers)
    return client_user


async def _create_test_recipe(client, trainer_headers, name="Chicken Salad"):
    response = await client.post(
        "/recipe/create",
        json={
            "name": name,
            "meal_type": "lunch",
            "protein": "30.00",
            "carbs": "10.00",
            "fat": "8.00",
            "calories": 350,
            "serving_size": "1 bowl",
            "ingredients": [{"name": "chicken", "quantity": "200.00", "unit": "g"}],
            "dietary_tag_names": [],
        },
        headers=trainer_headers,
    )
    return response.json()


async def _create_test_exercise(client, trainer_headers, name="Squat"):
    response = await client.post(
        "/exercise/create", json={"name": name}, headers=trainer_headers
    )
    return response.json()


async def test_create_daily_log_as_client_succeeds(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)

    response = await client.post(
        "/log/daily/create",
        json={
            "log_date": "2026-10-01",
            "cycle_phase": "luteal",
            "hours_of_sleep": "7.5",
            "energy_level": 6,
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()["daily_log"]
    assert data["cycle_phase"] == "luteal"
    assert data["energy_level"] == 6


async def test_create_daily_log_as_trainer_forbidden(client, db):
    trainer_user, _ = await _create_test_trainer_profile(db, "trainer1@trainer.com")
    headers = auth_headers(trainer_user)

    response = await client.post(
        "/log/daily/create",
        json={"log_date": "2026-10-01", "cycle_phase": "luteal"},
        headers=headers,
    )
    assert response.status_code == 403


async def test_create_daily_log_without_profile_forbidden(client, db):
    client_user = await create_test_user(db, UserRole.client, "client1@client.com")
    headers = auth_headers(client_user)

    response = await client.post(
        "/log/daily/create",
        json={"log_date": "2026-10-01", "cycle_phase": "luteal"},
        headers=headers,
    )
    assert response.status_code == 403


async def test_create_daily_log_duplicate_date_conflicts(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)
    payload = {"log_date": "2026-10-01", "cycle_phase": "luteal"}

    first = await client.post("/log/daily/create", json=payload, headers=headers)
    assert first.status_code == 201

    second = await client.post("/log/daily/create", json=payload, headers=headers)
    assert second.status_code == 409


async def test_create_daily_log_different_dates_both_succeed(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)

    first = await client.post(
        "/log/daily/create",
        json={"log_date": "2026-10-01", "cycle_phase": "luteal"},
        headers=headers,
    )
    second = await client.post(
        "/log/daily/create",
        json={"log_date": "2026-10-02", "cycle_phase": "menstrual"},
        headers=headers,
    )
    assert first.status_code == 201
    assert second.status_code == 201


async def test_create_daily_log_falls_back_to_client_profile_data(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await _create_test_client(
        client,
        trainer_profile.id,
        "client1@client.com",
        db,
        last_period_start="2026-09-01",
        cycle_length_days=28,
        period_length_days=5,
    )
    headers = auth_headers(client_user)

    response = await client.post(
        "/log/daily/create",
        json={"log_date": "2026-09-08"},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["daily_log"]["cycle_phase"] == "follicular"


async def test_create_daily_log_insufficient_data_conflicts(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)

    response = await client.post(
        "/log/daily/create",
        json={"log_date": "2026-09-08"},
        headers=headers,
    )
    assert response.status_code == 400


async def test_create_daily_log_period_started_today_feeds_future_calculation(
    client, db
):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)

    first = await client.post(
        "/log/daily/create",
        json={"log_date": "2026-09-01", "period_started_today": True},
        headers=headers,
    )
    assert first.status_code == 201
    assert first.json()["daily_log"]["cycle_phase"] == "menstrual"

    second = await client.post(
        "/log/daily/create",
        json={"log_date": "2026-09-08"},
        headers=headers,
    )
    assert second.status_code == 201
    assert second.json()["daily_log"]["cycle_phase"] == "follicular"


async def test_create_meal_log_as_client_succeeds(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    recipe = await _create_test_recipe(client, trainer_headers)
    headers = auth_headers(client_user)

    response = await client.post(
        "/log/meal/create",
        json={
            "recipe_id": recipe["id"],
            "meal_type": "lunch",
            "consumed_at": "2026-10-01T12:30:00",
            "portion_quantity": "1.5",
            "portion_unit": "bowl",
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["recipe"]["name"] == "Chicken Salad"
    assert data["portion_unit"] == "bowl"


async def test_create_meal_log_as_trainer_forbidden(client, db):
    trainer_user, _ = await _create_test_trainer_profile(db, "trainer1@trainer.com")
    headers = auth_headers(trainer_user)

    response = await client.post(
        "/log/meal/create",
        json={
            "recipe_id": "00000000-0000-0000-0000-000000000000",
            "meal_type": "lunch",
            "consumed_at": "2026-10-01T12:30:00",
            "portion_quantity": "1.5",
            "portion_unit": "bowl",
        },
        headers=headers,
    )
    assert response.status_code == 403


async def test_create_meal_log_invalid_recipe_not_found(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)

    response = await client.post(
        "/log/meal/create",
        json={
            "recipe_id": "00000000-0000-0000-0000-000000000000",
            "meal_type": "lunch",
            "consumed_at": "2026-10-01T12:30:00",
            "portion_quantity": "1.5",
            "portion_unit": "bowl",
        },
        headers=headers,
    )
    assert response.status_code == 404


async def test_create_exercise_log_as_client_succeeds(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    exercise = await _create_test_exercise(client, trainer_headers)
    headers = auth_headers(client_user)

    response = await client.post(
        "/log/exercise/create",
        json={
            "exercise_id": exercise["id"],
            "completed_at": "2026-10-01T18:00:00",
            "notes": "Felt strong today",
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["exercise"]["name"] == "Squat"
    assert data["notes"] == "Felt strong today"


async def test_create_exercise_log_as_trainer_forbidden(client, db):
    trainer_user, _ = await _create_test_trainer_profile(db, "trainer1@trainer.com")
    headers = auth_headers(trainer_user)

    response = await client.post(
        "/log/exercise/create",
        json={
            "exercise_id": "00000000-0000-0000-0000-000000000000",
            "completed_at": "2026-10-01T18:00:00",
        },
        headers=headers,
    )
    assert response.status_code == 403


async def test_create_exercise_log_invalid_exercise_not_found(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)

    response = await client.post(
        "/log/exercise/create",
        json={
            "exercise_id": "00000000-0000-0000-0000-000000000000",
            "completed_at": "2026-10-01T18:00:00",
        },
        headers=headers,
    )
    assert response.status_code == 404


async def _get_own_client_profile_id(client, headers) -> str:
    response = await client.get("/client/", headers=headers)
    return response.json()["id"]


async def test_daily_log_recommendations_filtered_by_phase_and_day(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)
    client_profile_id = await _get_own_client_profile_id(client, headers)

    recipe_luteal = await _create_test_recipe(
        client, trainer_headers, name="Luteal Recipe"
    )
    recipe_follicular = await _create_test_recipe(
        client, trainer_headers, name="Follicular Recipe"
    )
    exercise_match = await _create_test_exercise(
        client, trainer_headers, name="Match Exercise"
    )
    exercise_wrong_day = await _create_test_exercise(
        client, trainer_headers, name="Wrong Day Exercise"
    )
    exercise_wrong_phase = await _create_test_exercise(
        client, trainer_headers, name="Wrong Phase Exercise"
    )

    await client.post(
        "/plan/nutrition/create",
        json={
            "client_id": client_profile_id,
            "title": "Nutrition Plan",
            "recipes": [
                {
                    "recipe_id": recipe_luteal["id"],
                    "meal_type": "lunch",
                    "cycle_phase": "luteal",
                },
                {
                    "recipe_id": recipe_follicular["id"],
                    "meal_type": "lunch",
                    "cycle_phase": "follicular",
                },
            ],
        },
        headers=trainer_headers,
    )
    await client.post(
        "/plan/training/create",
        json={
            "client_id": client_profile_id,
            "title": "Training Plan",
            "exercises": [
                {
                    "exercise_id": exercise_match["id"],
                    "cycle_phase": "luteal",
                    "day_of_week": 1,
                    "difficulty_level": "easy",
                },
                {
                    "exercise_id": exercise_wrong_day["id"],
                    "cycle_phase": "luteal",
                    "day_of_week": 2,
                    "difficulty_level": "easy",
                },
                {
                    "exercise_id": exercise_wrong_phase["id"],
                    "cycle_phase": "follicular",
                    "day_of_week": 1,
                    "difficulty_level": "easy",
                },
            ],
        },
        headers=trainer_headers,
    )

    response = await client.post(
        "/log/daily/create",
        json={
            "log_date": "2026-10-05",
            "cycle_phase": "luteal",
            "energy_level": 6,
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()

    recipe_names = {r["name"] for r in data["recommended_recipes"]}
    assert recipe_names == {"Luteal Recipe"}

    exercise_names = {e["name"] for e in data["recommended_exercises"]}
    assert exercise_names == {"Match Exercise"}


async def test_daily_log_recommendations_respect_energy_intensity(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)
    client_profile_id = await _get_own_client_profile_id(client, headers)

    easy_exercise = await _create_test_exercise(
        client, trainer_headers, name="Easy Exercise"
    )
    hard_exercise = await _create_test_exercise(
        client, trainer_headers, name="Hard Exercise"
    )

    await client.post(
        "/plan/training/create",
        json={
            "client_id": client_profile_id,
            "title": "Training Plan",
            "exercises": [
                {
                    "exercise_id": easy_exercise["id"],
                    "cycle_phase": "luteal",
                    "day_of_week": 1,
                    "difficulty_level": "easy",
                },
                {
                    "exercise_id": hard_exercise["id"],
                    "cycle_phase": "luteal",
                    "day_of_week": 1,
                    "difficulty_level": "hard",
                },
            ],
        },
        headers=trainer_headers,
    )

    response = await client.post(
        "/log/daily/create",
        json={"log_date": "2026-10-05", "cycle_phase": "luteal", "energy_level": 2},
        headers=headers,
    )
    assert response.status_code == 201
    exercise_names = {e["name"] for e in response.json()["recommended_exercises"]}
    assert exercise_names == {"Easy Exercise"}


async def test_get_today_recommendations_404_before_logging(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)

    response = await client.get("/log/daily/today", headers=headers)
    assert response.status_code == 404


async def test_recommendations_cache_invalidated_after_plan_change(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)
    client_profile_id = await _get_own_client_profile_id(client, headers)

    first_recipe = await _create_test_recipe(
        client, trainer_headers, name="First Recipe"
    )
    second_recipe = await _create_test_recipe(
        client, trainer_headers, name="Second Recipe"
    )

    created_plan = await client.post(
        "/plan/nutrition/create",
        json={
            "client_id": client_profile_id,
            "title": "Nutrition Plan",
            "recipes": [
                {
                    "recipe_id": first_recipe["id"],
                    "meal_type": "lunch",
                    "cycle_phase": "luteal",
                },
            ],
        },
        headers=trainer_headers,
    )
    plan_id = created_plan.json()["id"]

    first_response = await client.post(
        "/log/daily/create",
        json={"log_date": "2026-10-05", "cycle_phase": "luteal"},
        headers=headers,
    )
    assert {
        recipe["name"] for recipe in first_response.json()["recommended_recipes"]
    } == {"First Recipe"}

    await client.patch(
        "/plan/nutrition/update",
        params={"plan_id": plan_id},
        json={
            "recipes": [
                {
                    "recipe_id": second_recipe["id"],
                    "meal_type": "dinner",
                    "cycle_phase": "luteal",
                }
            ]
        },
        headers=trainer_headers,
    )

    # Updating the plan should have invalidated today's cached recommendations,
    # so this now reflects both recipes - not the stale first-only result.
    second_response = await client.get("/log/daily/today", headers=headers)
    assert {
        recipe["name"] for recipe in second_response.json()["recommended_recipes"]
    } == {
        "First Recipe",
        "Second Recipe",
    }
