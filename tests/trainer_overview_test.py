from datetime import datetime

from app.core.config import APP_TZ
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
        json={"trainer_id": str(trainer_profile_id), "fitness_goal": "Build strength"},
        headers=auth_headers(client_user),
    )
    return client_user, response.json()


def _today() -> str:
    return datetime.now(APP_TZ).date().isoformat()


async def test_overview_shows_todays_log_and_plans(client, db):
    trainer_user, trainer_profile = await _create_test_trainer(db)
    trainer_headers = auth_headers(trainer_user)
    logged_user, logged = await _create_test_client(
        client, db, trainer_profile.id, "logged@client.com"
    )
    _, idle = await _create_test_client(
        client, db, trainer_profile.id, "idle@client.com"
    )
    await client.post(
        "/plan/nutrition/create",
        json={"client_id": logged["id"], "title": "Nutrition", "recipes": []},
        headers=trainer_headers,
    )
    await client.post(
        "/log/daily/create",
        json={
            "log_date": _today(),
            "cycle_phase": "luteal",
            "energy_level": 6,
            "hours_of_sleep": "7.5",
        },
        headers=auth_headers(logged_user),
    )

    response = await client.get("/trainer/my_clients/overview", headers=trainer_headers)

    assert response.status_code == 200
    by_id = {item["client"]["id"]: item for item in response.json()}
    assert set(by_id) == {logged["id"], idle["id"]}
    assert by_id[logged["id"]]["today_log"]["cycle_phase"] == "luteal"
    assert by_id[logged["id"]]["today_log"]["energy_level"] == 6
    assert by_id[logged["id"]]["last_log_date"] == _today()
    assert by_id[logged["id"]]["has_nutrition_plan"] is True
    assert by_id[logged["id"]]["has_training_plan"] is False
    assert by_id[idle["id"]]["today_log"] is None
    assert by_id[idle["id"]]["last_log_date"] is None


async def test_overview_last_log_date_is_most_recent_log(client, db):
    trainer_user, trainer_profile = await _create_test_trainer(db)
    client_user, _ = await _create_test_client(
        client, db, trainer_profile.id, "client1@client.com"
    )
    for log_date in ["2026-01-05", "2026-01-07"]:
        await client.post(
            "/log/daily/create",
            json={"log_date": log_date, "cycle_phase": "luteal"},
            headers=auth_headers(client_user),
        )

    response = await client.get(
        "/trainer/my_clients/overview", headers=auth_headers(trainer_user)
    )

    item = response.json()[0]
    assert item["today_log"] is None
    assert item["last_log_date"] == "2026-01-07"


async def test_overview_only_includes_own_clients(client, db):
    _, trainer_profile = await _create_test_trainer(db)
    other_trainer, _ = await _create_test_trainer(db, "trainer2@trainer.com")
    await _create_test_client(client, db, trainer_profile.id, "client1@client.com")

    response = await client.get(
        "/trainer/my_clients/overview", headers=auth_headers(other_trainer)
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_overview_forbidden_for_clients(client, db):
    _, trainer_profile = await _create_test_trainer(db)
    client_user, _ = await _create_test_client(
        client, db, trainer_profile.id, "client1@client.com"
    )

    response = await client.get(
        "/trainer/my_clients/overview", headers=auth_headers(client_user)
    )

    assert response.status_code == 403


async def test_trainer_gets_clients_active_training_plan(client, db):
    trainer_user, trainer_profile = await _create_test_trainer(db)
    trainer_headers = auth_headers(trainer_user)
    _, profile = await _create_test_client(
        client, db, trainer_profile.id, "client1@client.com"
    )
    await client.post(
        "/plan/training/create",
        json={"client_id": profile["id"], "title": "Strength", "exercises": []},
        headers=trainer_headers,
    )

    response = await client.get(
        f"/plan/training/client/{profile['id']}", headers=trainer_headers
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Strength"


async def test_client_without_active_plan_returns_404(client, db):
    trainer_user, trainer_profile = await _create_test_trainer(db)
    _, profile = await _create_test_client(
        client, db, trainer_profile.id, "client1@client.com"
    )

    response = await client.get(
        f"/plan/nutrition/client/{profile['id']}",
        headers=auth_headers(trainer_user),
    )

    assert response.status_code == 404


async def test_unrelated_trainer_cannot_read_clients_plan(client, db):
    trainer_user, trainer_profile = await _create_test_trainer(db)
    other_trainer, _ = await _create_test_trainer(db, "trainer2@trainer.com")
    _, profile = await _create_test_client(
        client, db, trainer_profile.id, "client1@client.com"
    )
    await client.post(
        "/plan/nutrition/create",
        json={"client_id": profile["id"], "title": "Nutrition", "recipes": []},
        headers=auth_headers(trainer_user),
    )

    response = await client.get(
        f"/plan/nutrition/client/{profile['id']}",
        headers=auth_headers(other_trainer),
    )

    assert response.status_code == 404
