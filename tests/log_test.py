from app.core.enums import UserRole
from app.trainer.service import create_trainer_profile
from tests.conftest import auth_headers, create_test_user


async def _create_test_trainer_profile(db, email: str):
    trainer_user = await create_test_user(db, UserRole.trainer, email)
    trainer_profile = await create_trainer_profile(
        db, trainer_user.id, "experienced", "fertility"
    )
    return trainer_user, trainer_profile


async def _create_test_client(client, trainer_profile_id, email, db):
    client_user = await create_test_user(db, UserRole.client, email)
    headers = auth_headers(client_user)
    await client.post(
        "/client/create",
        json={"trainer_id": str(trainer_profile_id)},
        headers=headers,
    )
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
    data = response.json()
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
