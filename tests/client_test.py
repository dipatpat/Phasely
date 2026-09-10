import uuid

from app.core.enums import UserRole
from app.trainer.service import create_trainer_profile
from tests.conftest import auth_headers, create_test_user


async def _create_test_trainer_profile(db, email: str):
    trainer_user = await create_test_user(db, UserRole.trainer, email)
    trainer_profile = await create_trainer_profile(
        db, trainer_user.id, "experienced", "fertility"
    )
    return trainer_user, trainer_profile


async def test_create_client_profile_success(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await create_test_user(db, UserRole.client, "client1@client.com")
    headers = auth_headers(client_user)

    response = await client.post(
        "/client/create",
        json={
            "trainer_id": str(trainer_profile.id),
            "fitness_goal": "Get stronger",
            "cycle_length_days": 28,
            "period_length_days": 5,
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["fitness_goal"] == "Get stronger"
    assert data["email"] == "client1@client.com"


async def test_create_client_profile_as_trainer_forbidden(client, db):
    trainer_user = await create_test_user(db, UserRole.trainer, "trainer2@trainer.com")
    headers = auth_headers(trainer_user)

    response = await client.post(
        "/client/create", json={"trainer_id": str(uuid.uuid4())}, headers=headers
    )
    assert response.status_code == 403


async def test_create_client_profile_bad_trainer_id_not_found(client, db):
    client_user = await create_test_user(db, UserRole.client, "client2@client.com")
    headers = auth_headers(client_user)

    response = await client.post(
        "/client/create", json={"trainer_id": str(uuid.uuid4())}, headers=headers
    )
    assert response.status_code == 404


async def test_create_client_profile_twice_conflicts(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer3@trainer.com"
    )
    client_user = await create_test_user(db, UserRole.client, "client3@client.com")
    headers = auth_headers(client_user)

    payload = {"trainer_id": str(trainer_profile.id)}
    first = await client.post("/client/create", json=payload, headers=headers)
    assert first.status_code == 201

    second = await client.post("/client/create", json=payload, headers=headers)
    assert second.status_code == 409


async def test_trainer_cannot_view_another_trainers_client(client, db):
    trainer1_user, trainer1_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer2_user, _ = await _create_test_trainer_profile(db, "trainer2@trainer.com")
    headers_1 = auth_headers(trainer1_user)
    headers_2 = auth_headers(trainer2_user)

    client_user = await create_test_user(db, UserRole.client, "client1@client.com")
    create_response = await client.post(
        "/client/create",
        json={"trainer_id": str(trainer1_profile.id)},
        headers=auth_headers(client_user),
    )
    client_profile_id = create_response.json()["id"]

    success_response = await client.get(
        f"/client/{client_profile_id}", headers=headers_1
    )
    assert success_response.status_code == 200

    failed_response = await client.get(
        f"/client/{client_profile_id}", headers=headers_2
    )
    assert failed_response.status_code == 404


async def test_get_my_clients_only_shows_own_clients(client, db):
    trainer_1_user, trainer_1_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_2_user, trainer_2_profile = await _create_test_trainer_profile(
        db, "trainer2@trainer.com"
    )
    headers_1 = auth_headers(trainer_1_user)

    client_1_user = await create_test_user(db, UserRole.client, "client1@example.com")
    client_2_user = await create_test_user(db, UserRole.client, "client2@example.com")
    await client.post(
        "/client/create",
        json={"trainer_id": str(trainer_1_profile.id)},
        headers=auth_headers(client_1_user),
    )
    await client.post(
        "/client/create",
        json={"trainer_id": str(trainer_2_profile.id)},
        headers=auth_headers(client_2_user),
    )

    response = await client.get("/trainer/my_clients", headers=headers_1)
    assert response.status_code == 200
    emails = [email["email"] for email in response.json()]
    assert "client1@example.com" in emails
    assert "client2@example.com" not in emails


async def test_get_my_trainer_returns_assigned_trainer(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user = await create_test_user(db, UserRole.client, "client1@client.com")
    headers = auth_headers(client_user)

    await client.post(
        "/client/create", json={"trainer_id": str(trainer_profile.id)}, headers=headers
    )

    response = await client.get("/client/my/trainer", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == str(trainer_profile.id)
