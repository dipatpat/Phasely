import asyncio
import json
import uuid
from datetime import date

from app.core.enums import UserRole
from app.report.service import generate_weekly_report_data
from app.report.tasks import generate_weekly_report
from app.trainer.service import create_trainer_profile
from tests.conftest import FakeRedis, TestSessionLocal, auth_headers, create_test_user


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


async def _create_test_recipe(
    client, trainer_headers, name="Chicken Salad", calories=350
):
    response = await client.post(
        "/recipe/create",
        json={
            "name": name,
            "meal_type": "lunch",
            "protein": "30.00",
            "carbs": "10.00",
            "fat": "8.00",
            "calories": calories,
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


async def _get_own_client_profile_id(client, headers) -> str:
    response = await client.get("/client/", headers=headers)
    return response.json()["id"]


async def test_generate_weekly_report_data_builds_per_day_breakdown(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)
    client_profile_id = await _get_own_client_profile_id(client, headers)

    recipe = await _create_test_recipe(client, trainer_headers, calories=400)
    exercise = await _create_test_exercise(client, trainer_headers)

    await client.post(
        "/log/daily/create",
        json={
            "log_date": "2026-09-07",
            "cycle_phase": "luteal",
            "hours_of_sleep": "7.5",
            "energy_level": 6,
        },
        headers=headers,
    )
    await client.post(
        "/log/meal/create",
        json={
            "recipe_id": recipe["id"],
            "meal_type": "lunch",
            "consumed_at": "2026-09-07T12:30:00",
            "portion_quantity": "1",
            "portion_unit": "bowl",
        },
        headers=headers,
    )
    await client.post(
        "/log/exercise/create",
        json={"exercise_id": exercise["id"], "completed_at": "2026-09-07T18:00:00"},
        headers=headers,
    )

    report = await generate_weekly_report_data(
        db, uuid.UUID(client_profile_id), date(2026, 9, 7)
    )

    assert report["week_start"] == "2026-09-07"
    assert report["week_end"] == "2026-09-13"
    assert len(report["daily_breakdown"]) == 7

    monday = report["daily_breakdown"][0]
    assert monday["date"] == "2026-09-07"
    assert monday["cycle_phase"] == "luteal"
    assert monday["energy_level"] == 6
    assert monday["hours_of_sleep"] == 7.5
    assert monday["calories_consumed"] == 400
    assert monday["exercises_completed"] == 1

    tuesday = report["daily_breakdown"][1]
    assert tuesday["date"] == "2026-09-08"
    assert tuesday["cycle_phase"] is None
    assert tuesday["energy_level"] is None
    assert tuesday["calories_consumed"] == 0
    assert tuesday["exercises_completed"] == 0


async def test_generate_weekly_report_task_caches_result(mocker, client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)
    client_profile_id = await _get_own_client_profile_id(client, headers)

    await client.post(
        "/log/daily/create",
        json={"log_date": "2026-09-07", "cycle_phase": "luteal", "energy_level": 5},
        headers=headers,
    )

    fake_redis = FakeRedis()
    mocker.patch("app.report.tasks.AsyncSessionLocal", TestSessionLocal)
    mocker.patch("app.report.tasks.get_redis", return_value=fake_redis)

    result = await asyncio.to_thread(
        generate_weekly_report, client_profile_id, "2026-09-07"
    )

    assert result["daily_breakdown"][0]["cycle_phase"] == "luteal"

    cache_key = f"weekly_report:{client_profile_id}:2026-09-07"
    cached = await fake_redis.get(cache_key)
    assert cached is not None
    assert json.loads(cached)["week_start"] == "2026-09-07"


async def test_trigger_weekly_report_as_client_uses_own_profile(mocker, client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)
    client_profile_id = await _get_own_client_profile_id(client, headers)

    mock_delay = mocker.patch("app.report.router.generate_weekly_report.delay")

    response = await client.post(
        "/report/weekly", json={"week_start": "2026-09-07"}, headers=headers
    )

    assert response.status_code == 200
    mock_delay.assert_called_once_with(client_profile_id, "2026-09-07")


async def test_trigger_weekly_report_rejects_non_monday(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)

    response = await client.post(
        "/report/weekly", json={"week_start": "2026-09-08"}, headers=headers
    )

    assert response.status_code == 422


async def test_trigger_weekly_report_as_trainer_for_own_client(mocker, client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    client_headers = auth_headers(client_user)
    client_profile_id = await _get_own_client_profile_id(client, client_headers)

    mock_delay = mocker.patch("app.report.router.generate_weekly_report.delay")

    response = await client.post(
        "/report/weekly",
        json={"week_start": "2026-09-07", "client_id": client_profile_id},
        headers=trainer_headers,
    )

    assert response.status_code == 200
    mock_delay.assert_called_once_with(client_profile_id, "2026-09-07")


async def test_trigger_weekly_report_as_trainer_without_client_id_fails(client, db):
    trainer_user, _ = await _create_test_trainer_profile(db, "trainer1@trainer.com")
    headers = auth_headers(trainer_user)

    response = await client.post(
        "/report/weekly", json={"week_start": "2026-09-07"}, headers=headers
    )

    assert response.status_code == 422


async def test_trigger_weekly_report_as_trainer_for_unowned_client_forbidden(
    client, db
):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    other_trainer_user, _ = await _create_test_trainer_profile(
        db, "trainer2@trainer.com"
    )
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    client_headers = auth_headers(client_user)
    client_profile_id = await _get_own_client_profile_id(client, client_headers)

    other_trainer_headers = auth_headers(other_trainer_user)
    response = await client.post(
        "/report/weekly",
        json={"week_start": "2026-09-07", "client_id": client_profile_id},
        headers=other_trainer_headers,
    )

    assert response.status_code == 404


async def test_get_weekly_report_cache_miss_returns_404(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)

    response = await client.get(
        "/report/weekly", params={"week_start": "2026-09-07"}, headers=headers
    )

    assert response.status_code == 404


async def test_get_weekly_report_cache_hit_returns_report(client, redis_client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)
    client_profile_id = await _get_own_client_profile_id(client, headers)

    cached_report = {
        "week_start": "2026-09-07",
        "week_end": "2026-09-13",
        "daily_breakdown": [],
    }
    cache_key = f"weekly_report:{client_profile_id}:2026-09-07"
    await redis_client.set(cache_key, json.dumps(cached_report))

    response = await client.get(
        "/report/weekly", params={"week_start": "2026-09-07"}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["week_end"] == "2026-09-13"


async def test_get_weekly_report_as_trainer_for_own_client(client, redis_client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    client_user = await _create_test_client(
        client, trainer_profile.id, "client1@client.com", db
    )
    client_headers = auth_headers(client_user)
    client_profile_id = await _get_own_client_profile_id(client, client_headers)

    cached_report = {
        "week_start": "2026-09-07",
        "week_end": "2026-09-13",
        "daily_breakdown": [],
    }
    cache_key = f"weekly_report:{client_profile_id}:2026-09-07"
    await redis_client.set(cache_key, json.dumps(cached_report))

    response = await client.get(
        "/report/weekly",
        params={"week_start": "2026-09-07", "client_id": client_profile_id},
        headers=trainer_headers,
    )

    assert response.status_code == 200
    assert response.json()["week_end"] == "2026-09-13"


async def test_get_weekly_report_as_trainer_without_client_id_fails(client, db):
    trainer_user, _ = await _create_test_trainer_profile(db, "trainer1@trainer.com")
    headers = auth_headers(trainer_user)

    response = await client.get(
        "/report/weekly", params={"week_start": "2026-09-07"}, headers=headers
    )

    assert response.status_code == 422
