from app.core.enums import UserRole
from tests.conftest import auth_headers, create_test_user


async def test_create_trainer_profile_as_trainer_succeeds(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)

    response = await client.post(
        "/trainer/create",
        json={"bio": "Strength coach", "specialization": "Fertility"},
        headers=headers,
    )
    assert response.status_code == 201


async def test_create_trainer_profile_as_client_forbidden(client, db):
    user = await create_test_user(db, UserRole.client, "client1@client.com")
    headers = auth_headers(user)

    response = await client.post(
        "/trainer/create",
        json={"bio": "Strength coach", "specialization": "Fertility"},
        headers=headers,
    )
    assert response.status_code == 403


async def test_trainer_cannot_update_another_trainers_slot(client, db):
    trainer_a = await create_test_user(db, UserRole.trainer, "trainer1@trainer.com")
    trainer_b = await create_test_user(db, UserRole.trainer, "trainer2@trainer.com")
    headers_a = auth_headers(trainer_a)
    headers_b = auth_headers(trainer_b)

    await client.post(
        "/trainer/create",
        json={"bio": "1", "specialization": "Resistance"},
        headers=headers_a,
    )
    await client.post(
        "/trainer/create",
        json={"bio": "2", "specialization": "Resistance"},
        headers=headers_b,
    )

    slot = await client.post(
        "/trainer/availability",
        json={
            "slot_date": "2026-09-14",
            "slot_start": "09:00:00",
            "slot_end": "12:00:00",
        },
        headers=headers_a,
    )
    slot_id = slot.json()["id"]

    update = await client.patch(
        f"/trainer/availability/{slot_id}",
        json={"slot_start": "11:00:00"},
        headers=headers_b,
    )
    assert update.status_code == 404
