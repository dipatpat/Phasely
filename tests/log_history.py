from app.core.enums import UserRole
from app.trainer.service import create_trainer_profile
from tests.conftest import auth_headers, create_test_user


async def _create_test_trainer(db, email="trainer1@trainer.com"):
    trainer_user = await create_test_user(db, UserRole.trainer, email)
    trainer_profile = await create_trainer_profile(
        db, trainer_user.id, "experienced", "fertility"
    )
    return trainer_user, trainer_profile


async def _create_test_client(client, db, trainer_profile_id, email):
    client_user = await create_test_user(db, UserRole.client, email)
    response = await client.post(
        "/client/create",
        json={"trainer_id": str(trainer_profile_id)},
        headers=auth_headers(client_user),
    )
    return client_user, response.json()


async def _create_test_recipe(client, trainer_headers):
    response = await client.post(
        "/recipe/create",
        json={
            "name": "Oatmeal",
            "meal_type": "breakfast",
            "protein": "10.00",
            "carbs": "40.00",
            "fat": "5.00",
            "calories": 250,
            "serving_size": "1 bowl",
            "ingredients": [{"name": "oats", "quantity": "50.00", "unit": "g"}],
            "dietary_tag_names": [],
        },
        headers=trainer_headers,
    )
    return response.json()


async def _log_meal(client, headers, recipe_id, consumed_at):
    response = await client.post(
        "/log/meal/create",
        json={
            "recipe_id": recipe_id,
            "meal_type": "breakfast",
            "consumed_at": consumed_at,
            "portion_quantity": "1",
            "portion_unit": "bowl",
        },
        headers=headers,
    )
    assert response.status_code == 201


async def _setup_client_with_recipe(client, db):
    trainer_user, trainer_profile = await _create_test_trainer(db)
    client_user, client_profile = await _create_test_client(
        client, db, trainer_profile.id, "client1@client.com"
    )
    recipe = await _create_test_recipe(client, auth_headers(trainer_user))
    return trainer_user, client_user, client_profile, recipe


async def test_list_meal_logs_returns_one_day_in_time_order(client, db):
    _, client_user, _, recipe = await _setup_client_with_recipe(client, db)
    headers = auth_headers(client_user)
    await _log_meal(client, headers, recipe["id"], "2026-10-19T19:00:00+02:00")
    await _log_meal(client, headers, recipe["id"], "2026-10-19T08:00:00+02:00")
    await _log_meal(client, headers, recipe["id"], "2026-10-20T08:00:00+02:00")

    response = await client.get(
        "/log/meal", params={"start_date": "2026-10-19"}, headers=headers
    )

    assert response.status_code == 200
    times = [meal["consumed_at"] for meal in response.json()]
    assert len(times) == 2
    assert times == sorted(times)
    assert response.json()[0]["recipe"]["name"] == "Oatmeal"


async def test_list_meal_logs_uses_warsaw_days(client, db):
    _, client_user, _, recipe = await _setup_client_with_recipe(client, db)
    headers = auth_headers(client_user)
    await _log_meal(client, headers, recipe["id"], "2026-10-19T23:30:00+02:00")
    await _log_meal(client, headers, recipe["id"], "2026-10-19T22:30:00Z")

    on_19th = await client.get(
        "/log/meal", params={"start_date": "2026-10-19"}, headers=headers
    )
    on_20th = await client.get(
        "/log/meal", params={"start_date": "2026-10-20"}, headers=headers
    )

    assert len(on_19th.json()) == 1
    assert len(on_20th.json()) == 1


async def test_list_daily_logs_for_date_range(client, db):
    _, client_user, _, _ = await _setup_client_with_recipe(client, db)
    headers = auth_headers(client_user)
    for log_date in ["2026-10-22", "2026-10-19", "2026-10-20"]:
        await client.post(
            "/log/daily/create",
            json={"log_date": log_date, "cycle_phase": "luteal", "energy_level": 6},
            headers=headers,
        )

    response = await client.get(
        "/log/daily",
        params={"start_date": "2026-10-19", "end_date": "2026-10-21"},
        headers=headers,
    )

    assert response.status_code == 200
    assert [log["log_date"] for log in response.json()] == [
        "2026-10-19",
        "2026-10-20",
    ]


async def test_list_exercise_logs(client, db):
    trainer_user, client_user, _, _ = await _setup_client_with_recipe(client, db)
    exercise = (
        await client.post(
            "/exercise/create",
            json={"name": "Squat"},
            headers=auth_headers(trainer_user),
        )
    ).json()
    headers = auth_headers(client_user)
    await client.post(
        "/log/exercise/create",
        json={
            "exercise_id": exercise["id"],
            "completed_at": "2026-10-19T18:00:00+02:00",
        },
        headers=headers,
    )

    response = await client.get(
        "/log/exercise", params={"start_date": "2026-10-19"}, headers=headers
    )

    assert response.status_code == 200
    assert [log["exercise"]["name"] for log in response.json()] == ["Squat"]


async def test_trainer_reads_own_clients_logs(client, db):
    trainer_user, client_user, client_profile, recipe = await _setup_client_with_recipe(
        client, db
    )
    await _log_meal(
        client, auth_headers(client_user), recipe["id"], "2026-10-19T08:00:00+02:00"
    )

    response = await client.get(
        "/log/meal",
        params={"start_date": "2026-10-19", "client_id": client_profile["id"]},
        headers=auth_headers(trainer_user),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_trainer_cannot_read_unrelated_clients_logs(client, db):
    _, _, client_profile, _ = await _setup_client_with_recipe(client, db)
    other_trainer, _ = await _create_test_trainer(db, "trainer2@trainer.com")

    response = await client.get(
        "/log/meal",
        params={"start_date": "2026-10-19", "client_id": client_profile["id"]},
        headers=auth_headers(other_trainer),
    )

    assert response.status_code == 404


async def test_client_cannot_read_another_clients_logs(client, db):
    trainer_user, trainer_profile = await _create_test_trainer(db)
    owner, owner_profile = await _create_test_client(
        client, db, trainer_profile.id, "client1@client.com"
    )
    snooper, _ = await _create_test_client(
        client, db, trainer_profile.id, "client2@client.com"
    )
    recipe = await _create_test_recipe(client, auth_headers(trainer_user))
    await _log_meal(
        client, auth_headers(owner), recipe["id"], "2026-10-19T08:00:00+02:00"
    )

    response = await client.get(
        "/log/meal",
        params={"start_date": "2026-10-19", "client_id": owner_profile["id"]},
        headers=auth_headers(snooper),
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_list_logs_rejects_end_before_start(client, db):
    _, client_user, _, _ = await _setup_client_with_recipe(client, db)

    response = await client.get(
        "/log/daily",
        params={"start_date": "2026-10-19", "end_date": "2026-10-18"},
        headers=auth_headers(client_user),
    )

    assert response.status_code == 422


async def test_list_logs_rejects_range_over_31_days(client, db):
    _, client_user, _, _ = await _setup_client_with_recipe(client, db)
    headers = auth_headers(client_user)

    allowed = await client.get(
        "/log/daily",
        params={"start_date": "2026-10-01", "end_date": "2026-10-31"},
        headers=headers,
    )
    too_long = await client.get(
        "/log/daily",
        params={"start_date": "2026-10-01", "end_date": "2026-11-01"},
        headers=headers,
    )

    assert allowed.status_code == 200
    assert too_long.status_code == 422
