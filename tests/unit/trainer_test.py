from app.core.enums import UserRole
from tests.conftest import auth_headers, create_test_user


async def test_create_trainer_profile_as_trainer_succeeds(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)

    response = await client.post(
        "/trainer/create",
        json={"bio": "Strength coach", "specialization": "Powerlifting"},
        headers=headers,
    )
    assert response.status_code == 201
