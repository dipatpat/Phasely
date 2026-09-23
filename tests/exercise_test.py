from app.core.enums import UserRole
from tests.conftest import auth_headers, create_test_user


async def test_create_exercise_as_trainer_succeeds(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)

    response = await client.post(
        "/exercise/create",
        json={"name": "Push-up", "description": "Bodyweight chest exercise"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Push-up"
    assert data["description"] == "Bodyweight chest exercise"


async def test_create_exercise_as_client_forbidden(client, db):
    user = await create_test_user(db, UserRole.client, "client1@client.com")
    headers = auth_headers(user)

    response = await client.post(
        "/exercise/create",
        json={"name": "Push-up"},
        headers=headers,
    )
    assert response.status_code == 403


async def test_create_exercise_duplicate_name_conflicts(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    payload = {"name": "Squat"}

    first = await client.post("/exercise/create", json=payload, headers=headers)
    assert first.status_code == 201

    second = await client.post("/exercise/create", json=payload, headers=headers)
    assert second.status_code == 409


async def test_list_exercises_visible_to_client(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    trainer_headers = auth_headers(trainer)
    await client.post(
        "/exercise/create", json={"name": "Lunge"}, headers=trainer_headers
    )

    client_user = await create_test_user(db, UserRole.client, "client1@client.com")
    response = await client.get("/exercise/", headers=auth_headers(client_user))
    assert response.status_code == 200
    names = [exercise["name"] for exercise in response.json()]
    assert "Lunge" in names


async def test_get_exercise_by_id_success(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    created = await client.post(
        "/exercise/create", json={"name": "Plank"}, headers=headers
    )
    exercise_id = created.json()["id"]

    response = await client.get(
        "/exercise/by_id", params={"exercise_id": exercise_id}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Plank"


async def test_get_exercise_by_id_not_found(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)

    response = await client.get(
        "/exercise/by_id",
        params={"exercise_id": "00000000-0000-0000-0000-000000000000"},
        headers=headers,
    )
    assert response.status_code == 404


async def test_update_exercise_success(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    created = await client.post(
        "/exercise/create", json={"name": "Burpee"}, headers=headers
    )
    exercise_id = created.json()["id"]

    response = await client.patch(
        "/exercise/update",
        params={"exercise_id": exercise_id},
        json={"description": "Full body cardio move"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Burpee"
    assert data["description"] == "Full body cardio move"


async def test_update_exercise_not_found(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)

    response = await client.patch(
        "/exercise/update",
        params={"exercise_id": "00000000-0000-0000-0000-000000000000"},
        json={"name": "Whatever"},
        headers=headers,
    )
    assert response.status_code == 404


async def test_update_exercise_duplicate_name_conflicts(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    await client.post("/exercise/create", json={"name": "Deadlift"}, headers=headers)
    created = await client.post(
        "/exercise/create", json={"name": "Row"}, headers=headers
    )
    exercise_id = created.json()["id"]

    response = await client.patch(
        "/exercise/update",
        params={"exercise_id": exercise_id},
        json={"name": "Deadlift"},
        headers=headers,
    )
    assert response.status_code == 409


async def test_delete_exercise_success(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    created = await client.post(
        "/exercise/create", json={"name": "Jumping Jack"}, headers=headers
    )
    exercise_id = created.json()["id"]

    response = await client.delete(
        "/exercise/remove", params={"exercise_id": exercise_id}, headers=headers
    )
    assert response.status_code == 204

    follow_up = await client.get(
        "/exercise/by_id", params={"exercise_id": exercise_id}, headers=headers
    )
    assert follow_up.status_code == 404


async def test_delete_exercise_not_found(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)

    response = await client.delete(
        "/exercise/remove",
        params={"exercise_id": "00000000-0000-0000-0000-000000000000"},
        headers=headers,
    )
    assert response.status_code == 404


async def test_delete_exercise_as_client_forbidden(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    created = await client.post(
        "/exercise/create", json={"name": "Sit-up"}, headers=auth_headers(trainer)
    )
    exercise_id = created.json()["id"]

    client_user = await create_test_user(db, UserRole.client, "client1@client.com")
    response = await client.delete(
        "/exercise/remove",
        params={"exercise_id": exercise_id},
        headers=auth_headers(client_user),
    )
    assert response.status_code == 403
