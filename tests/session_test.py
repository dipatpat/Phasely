from app.core.enums import UserRole
from app.trainer.service import create_trainer_profile
from tests.conftest import auth_headers, create_test_user


async def _create_test_trainer_profile(db, email: str):
    trainer_user = await create_test_user(db, UserRole.trainer, email)
    trainer_profile = await create_trainer_profile(
        db, trainer_user.id, "experienced", "fertility"
    )
    return trainer_user, trainer_profile


async def _create_test_client_profile(client, trainer_profile_id, email, db):
    client_user = await create_test_user(db, UserRole.client, email)
    headers = auth_headers(client_user)
    response = await client.post(
        "/client/create",
        json={"trainer_id": str(trainer_profile_id)},
        headers=headers,
    )
    return client_user, response.json()


async def _create_availability_slot(
    client, trainer_headers, slot_date, slot_start, slot_end
):
    response = await client.post(
        "/trainer/availability",
        json={
            "slot_date": slot_date,
            "slot_start": slot_start,
            "slot_end": slot_end,
        },
        headers=trainer_headers,
    )
    return response.json()


async def test_book_session_as_client_success(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    await _create_availability_slot(
        client, trainer_headers, "2026-10-01", "09:00:00", "10:00:00"
    )
    client_user, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)

    response = await client.post(
        "/session/book-client",
        json={"scheduled_at": "2026-10-01T09:00:00", "notes": "First session"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["notes"] == "First session"
    assert data["trainer"]["id"] == str(trainer_profile.id)
    assert data["client"]["id"] == client_profile["id"]


async def test_book_session_as_client_slot_unavailable_conflicts(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    await _create_availability_slot(
        client, trainer_headers, "2026-10-01", "09:00:00", "10:00:00"
    )
    client_user, _ = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)
    payload = {"scheduled_at": "2026-10-01T09:00:00"}

    first = await client.post("/session/book-client", json=payload, headers=headers)
    assert first.status_code == 201

    second = await client.post("/session/book-client", json=payload, headers=headers)
    assert second.status_code == 409


async def test_book_session_as_client_no_matching_availability_conflicts(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user, _ = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    headers = auth_headers(client_user)

    response = await client.post(
        "/session/book-client",
        json={"scheduled_at": "2026-10-01T09:00:00"},
        headers=headers,
    )
    assert response.status_code == 409


async def test_book_session_as_client_without_profile_forbidden(client, db):
    client_user = await create_test_user(db, UserRole.client, "client1@client.com")
    headers = auth_headers(client_user)

    response = await client.post(
        "/session/book-client",
        json={"scheduled_at": "2026-10-01T09:00:00"},
        headers=headers,
    )
    assert response.status_code == 403


async def test_book_session_as_trainer_success(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    await _create_availability_slot(
        client, trainer_headers, "2026-10-01", "09:00:00", "10:00:00"
    )
    _, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )

    response = await client.post(
        "/session/book-trainer",
        json={
            "client_id": client_profile["id"],
            "scheduled_at": "2026-10-01T09:00:00",
        },
        headers=trainer_headers,
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending"


async def test_book_session_as_trainer_for_unrelated_client_not_found(client, db):
    trainer_a_user, trainer_a_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_b_user, trainer_b_profile = await _create_test_trainer_profile(
        db, "trainer2@trainer.com"
    )
    trainer_b_headers = auth_headers(trainer_b_user)
    await _create_availability_slot(
        client, trainer_b_headers, "2026-10-01", "09:00:00", "10:00:00"
    )
    _, client_profile = await _create_test_client_profile(
        client, trainer_a_profile.id, "client1@client.com", db
    )

    response = await client.post(
        "/session/book-trainer",
        json={
            "client_id": client_profile["id"],
            "scheduled_at": "2026-10-01T09:00:00",
        },
        headers=trainer_b_headers,
    )
    assert response.status_code == 404


async def _book_session(client, client_headers, scheduled_at="2026-10-01T09:00:00"):
    response = await client.post(
        "/session/book-client",
        json={"scheduled_at": scheduled_at},
        headers=client_headers,
    )
    return response.json()


async def test_confirm_session_success(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    await _create_availability_slot(
        client, trainer_headers, "2026-10-01", "09:00:00", "10:00:00"
    )
    client_user, _ = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    session = await _book_session(client, auth_headers(client_user))

    response = await client.patch(
        "/session/confirm",
        params={"session_id": session["id"]},
        headers=trainer_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


async def test_confirm_session_by_another_trainer_forbidden(client, db):
    trainer_a_user, trainer_a_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_b_user, _ = await _create_test_trainer_profile(db, "trainer2@trainer.com")
    trainer_a_headers = auth_headers(trainer_a_user)
    await _create_availability_slot(
        client, trainer_a_headers, "2026-10-01", "09:00:00", "10:00:00"
    )
    client_user, _ = await _create_test_client_profile(
        client, trainer_a_profile.id, "client1@client.com", db
    )
    session = await _book_session(client, auth_headers(client_user))

    response = await client.patch(
        "/session/confirm",
        params={"session_id": session["id"]},
        headers=auth_headers(trainer_b_user),
    )
    assert response.status_code == 403


async def test_confirm_session_already_confirmed_conflicts(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    await _create_availability_slot(
        client, trainer_headers, "2026-10-01", "09:00:00", "10:00:00"
    )
    client_user, _ = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    session = await _book_session(client, auth_headers(client_user))

    await client.patch(
        "/session/confirm",
        params={"session_id": session["id"]},
        headers=trainer_headers,
    )
    second = await client.patch(
        "/session/confirm",
        params={"session_id": session["id"]},
        headers=trainer_headers,
    )
    assert second.status_code == 409


async def test_complete_session_success(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    await _create_availability_slot(
        client, trainer_headers, "2026-10-01", "09:00:00", "10:00:00"
    )
    client_user, _ = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    session = await _book_session(client, auth_headers(client_user))
    await client.patch(
        "/session/confirm",
        params={"session_id": session["id"]},
        headers=trainer_headers,
    )

    response = await client.patch(
        "/session/complete",
        params={"session_id": session["id"]},
        headers=trainer_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


async def test_complete_session_still_pending_conflicts(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    await _create_availability_slot(
        client, trainer_headers, "2026-10-01", "09:00:00", "10:00:00"
    )
    client_user, _ = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    session = await _book_session(client, auth_headers(client_user))

    response = await client.patch(
        "/session/complete",
        params={"session_id": session["id"]},
        headers=trainer_headers,
    )
    assert response.status_code == 409


async def test_cancel_session_by_client(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    await _create_availability_slot(
        client, trainer_headers, "2026-10-01", "09:00:00", "10:00:00"
    )
    client_user, _ = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    client_headers = auth_headers(client_user)
    session = await _book_session(client, client_headers)

    response = await client.patch(
        "/session/cancel",
        params={"session_id": session["id"]},
        json={"cancellation_reason": "Can't make it"},
        headers=client_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
    assert data["cancellation_reason"] == "Can't make it"


async def test_cancel_session_by_trainer(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    await _create_availability_slot(
        client, trainer_headers, "2026-10-01", "09:00:00", "10:00:00"
    )
    client_user, _ = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    session = await _book_session(client, auth_headers(client_user))

    response = await client.patch(
        "/session/cancel",
        params={"session_id": session["id"]},
        json={"cancellation_reason": "Trainer is sick"},
        headers=trainer_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


async def test_cancel_session_by_unrelated_client_forbidden(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    await _create_availability_slot(
        client, trainer_headers, "2026-10-01", "09:00:00", "10:00:00"
    )
    client_user, _ = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    session = await _book_session(client, auth_headers(client_user))

    other_trainer_user, other_trainer_profile = await _create_test_trainer_profile(
        db, "trainer2@trainer.com"
    )
    other_client_user, _ = await _create_test_client_profile(
        client, other_trainer_profile.id, "otherclient@client.com", db
    )

    response = await client.patch(
        "/session/cancel",
        params={"session_id": session["id"]},
        json={"cancellation_reason": "Not mine"},
        headers=auth_headers(other_client_user),
    )
    assert response.status_code == 403


async def test_my_sessions_returns_only_own_sessions(client, db):
    trainer_1_user, trainer_1_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_2_user, trainer_2_profile = await _create_test_trainer_profile(
        db, "trainer2@trainer.com"
    )
    trainer_1_headers = auth_headers(trainer_1_user)
    trainer_2_headers = auth_headers(trainer_2_user)
    await _create_availability_slot(
        client, trainer_1_headers, "2026-10-01", "09:00:00", "10:00:00"
    )
    await _create_availability_slot(
        client, trainer_2_headers, "2026-10-01", "09:00:00", "10:00:00"
    )
    client_1_user, _ = await _create_test_client_profile(
        client, trainer_1_profile.id, "client1@client.com", db
    )
    client_2_user, _ = await _create_test_client_profile(
        client, trainer_2_profile.id, "client2@client.com", db
    )
    await _book_session(client, auth_headers(client_1_user))
    await _book_session(client, auth_headers(client_2_user))

    response = await client.get("/session/my_sessions", headers=trainer_1_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["trainer"]["id"] == str(trainer_1_profile.id)


async def test_available_slots_excludes_booked_slot(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    await _create_availability_slot(
        client, trainer_headers, "2026-10-01", "09:00:00", "10:00:00"
    )
    await _create_availability_slot(
        client, trainer_headers, "2026-10-01", "11:00:00", "12:00:00"
    )
    client_user, _ = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    client_headers = auth_headers(client_user)
    await _book_session(client, client_headers, "2026-10-01T09:00:00")

    response = await client.get(
        "/session/available_slots",
        params={"date_target": "2026-10-01"},
        headers=client_headers,
    )
    assert response.status_code == 200
    slots = response.json()
    assert len(slots) == 1
    assert slots[0]["slot_start"] == "11:00:00"
