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


async def test_create_nutrition_plan_as_trainer_succeeds(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    _, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    recipe = await _create_test_recipe(client, trainer_headers)

    response = await client.post(
        "/plan/nutrition/create",
        json={
            "client_id": client_profile["id"],
            "title": "Luteal Phase Plan",
            "recipes": [
                {
                    "recipe_id": recipe["id"],
                    "meal_type": "lunch",
                    "cycle_phase": "luteal",
                }
            ],
        },
        headers=trainer_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Luteal Phase Plan"
    assert len(data["recipes"]) == 1
    assert data["recipes"][0]["recipe"]["name"] == "Chicken Salad"


async def test_create_nutrition_plan_as_client_forbidden(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    _, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    other_client_user = await create_test_user(db, UserRole.client, "other@client.com")

    response = await client.post(
        "/plan/nutrition/create",
        json={"client_id": client_profile["id"], "title": "Plan", "recipes": []},
        headers=auth_headers(other_client_user),
    )
    assert response.status_code == 403


async def test_create_nutrition_plan_for_unrelated_client_not_found(client, db):
    trainer_a_user, trainer_a_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_b_user, _ = await _create_test_trainer_profile(db, "trainer2@trainer.com")
    _, client_profile = await _create_test_client_profile(
        client, trainer_a_profile.id, "client1@client.com", db
    )

    response = await client.post(
        "/plan/nutrition/create",
        json={"client_id": client_profile["id"], "title": "Plan", "recipes": []},
        headers=auth_headers(trainer_b_user),
    )
    assert response.status_code == 404


async def test_create_nutrition_plan_duplicate_active_conflicts(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    _, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    payload = {"client_id": client_profile["id"], "title": "Plan", "recipes": []}

    first = await client.post(
        "/plan/nutrition/create", json=payload, headers=trainer_headers
    )
    assert first.status_code == 201

    second = await client.post(
        "/plan/nutrition/create", json=payload, headers=trainer_headers
    )
    assert second.status_code == 409


async def test_create_nutrition_plan_invalid_recipe_not_found(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    _, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )

    response = await client.post(
        "/plan/nutrition/create",
        json={
            "client_id": client_profile["id"],
            "title": "Plan",
            "recipes": [
                {
                    "recipe_id": "00000000-0000-0000-0000-000000000000",
                    "meal_type": "lunch",
                    "cycle_phase": "luteal",
                }
            ],
        },
        headers=trainer_headers,
    )
    assert response.status_code == 404


async def test_get_nutrition_plan_by_id_as_client_success(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    client_user, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    created = await client.post(
        "/plan/nutrition/create",
        json={"client_id": client_profile["id"], "title": "Plan", "recipes": []},
        headers=trainer_headers,
    )
    plan_id = created.json()["id"]

    response = await client.get(
        f"/plan/nutrition/{plan_id}", headers=auth_headers(client_user)
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Plan"


async def test_get_nutrition_plan_by_id_forbidden_for_unrelated_trainer(client, db):
    trainer_a_user, trainer_a_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_b_user, _ = await _create_test_trainer_profile(db, "trainer2@trainer.com")
    _, client_profile = await _create_test_client_profile(
        client, trainer_a_profile.id, "client1@client.com", db
    )
    created = await client.post(
        "/plan/nutrition/create",
        json={"client_id": client_profile["id"], "title": "Plan", "recipes": []},
        headers=auth_headers(trainer_a_user),
    )
    plan_id = created.json()["id"]

    response = await client.get(
        f"/plan/nutrition/{plan_id}", headers=auth_headers(trainer_b_user)
    )
    assert response.status_code == 403


async def test_get_my_nutrition_plan_success(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    await client.post(
        "/plan/nutrition/create",
        json={"client_id": client_profile["id"], "title": "My Plan", "recipes": []},
        headers=auth_headers(trainer_user),
    )

    response = await client.get(
        "/plan/nutrition/mine", headers=auth_headers(client_user)
    )
    assert response.status_code == 200
    assert response.json()["title"] == "My Plan"


async def test_update_nutrition_plan_title(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    _, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    created = await client.post(
        "/plan/nutrition/create",
        json={"client_id": client_profile["id"], "title": "Old Title", "recipes": []},
        headers=trainer_headers,
    )
    plan_id = created.json()["id"]

    response = await client.patch(
        "/plan/nutrition/update",
        params={"plan_id": plan_id},
        json={"title": "New Title"},
        headers=trainer_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"


async def test_update_nutrition_plan_append_recipe(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    _, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    recipe = await _create_test_recipe(client, trainer_headers)
    created = await client.post(
        "/plan/nutrition/create",
        json={"client_id": client_profile["id"], "title": "Plan", "recipes": []},
        headers=trainer_headers,
    )
    plan_id = created.json()["id"]

    response = await client.patch(
        "/plan/nutrition/update",
        params={"plan_id": plan_id},
        json={
            "recipes": [
                {
                    "recipe_id": recipe["id"],
                    "meal_type": "breakfast",
                    "cycle_phase": "menstrual",
                }
            ]
        },
        headers=trainer_headers,
    )
    assert response.status_code == 200
    assert len(response.json()["recipes"]) == 1


async def test_update_nutrition_plan_duplicate_assignment_conflicts(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    _, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    recipe = await _create_test_recipe(client, trainer_headers)
    assignment = {
        "recipe_id": recipe["id"],
        "meal_type": "breakfast",
        "cycle_phase": "menstrual",
    }
    created = await client.post(
        "/plan/nutrition/create",
        json={
            "client_id": client_profile["id"],
            "title": "Plan",
            "recipes": [assignment],
        },
        headers=trainer_headers,
    )
    plan_id = created.json()["id"]

    response = await client.patch(
        "/plan/nutrition/update",
        params={"plan_id": plan_id},
        json={"recipes": [assignment]},
        headers=trainer_headers,
    )
    assert response.status_code == 409


async def test_remove_recipe_from_plan_success(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    _, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    recipe = await _create_test_recipe(client, trainer_headers)
    assignment = {
        "recipe_id": recipe["id"],
        "meal_type": "breakfast",
        "cycle_phase": "menstrual",
    }
    created = await client.post(
        "/plan/nutrition/create",
        json={
            "client_id": client_profile["id"],
            "title": "Plan",
            "recipes": [assignment],
        },
        headers=trainer_headers,
    )
    plan_id = created.json()["id"]

    response = await client.patch(
        "/plan/nutrition/remove_recipe",
        params={"plan_id": plan_id},
        json=[assignment],
        headers=trainer_headers,
    )
    assert response.status_code == 200
    assert len(response.json()["recipes"]) == 0


async def test_remove_recipe_from_plan_not_found(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    _, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    created = await client.post(
        "/plan/nutrition/create",
        json={"client_id": client_profile["id"], "title": "Plan", "recipes": []},
        headers=trainer_headers,
    )
    plan_id = created.json()["id"]

    response = await client.patch(
        "/plan/nutrition/remove_recipe",
        params={"plan_id": plan_id},
        json=[
            {
                "recipe_id": "00000000-0000-0000-0000-000000000000",
                "meal_type": "breakfast",
                "cycle_phase": "menstrual",
            }
        ],
        headers=trainer_headers,
    )
    assert response.status_code == 404


async def test_create_training_plan_as_trainer_succeeds(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    _, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    exercise = await _create_test_exercise(client, trainer_headers)

    response = await client.post(
        "/plan/training/create",
        json={
            "client_id": client_profile["id"],
            "title": "Strength Plan",
            "exercises": [
                {
                    "exercise_id": exercise["id"],
                    "cycle_phase": "follicular",
                    "day_of_week": 1,
                }
            ],
        },
        headers=trainer_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Strength Plan"
    assert len(data["exercises"]) == 1
    assert data["exercises"][0]["exercise"]["name"] == "Squat"


async def test_get_my_training_plan_success(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    client_user, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    await client.post(
        "/plan/training/create",
        json={
            "client_id": client_profile["id"],
            "title": "My Training Plan",
            "exercises": [],
        },
        headers=auth_headers(trainer_user),
    )

    response = await client.get(
        "/plan/training/mine", headers=auth_headers(client_user)
    )
    assert response.status_code == 200
    assert response.json()["title"] == "My Training Plan"


async def test_update_training_plan_append_exercise(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    _, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    exercise = await _create_test_exercise(client, trainer_headers)
    created = await client.post(
        "/plan/training/create",
        json={"client_id": client_profile["id"], "title": "Plan", "exercises": []},
        headers=trainer_headers,
    )
    plan_id = created.json()["id"]

    response = await client.patch(
        "/plan/training/update",
        params={"plan_id": plan_id},
        json={
            "exercises": [
                {
                    "exercise_id": exercise["id"],
                    "cycle_phase": "ovulatory",
                    "day_of_week": 3,
                }
            ]
        },
        headers=trainer_headers,
    )
    assert response.status_code == 200
    assert len(response.json()["exercises"]) == 1


async def test_remove_exercise_from_plan_success(client, db):
    trainer_user, trainer_profile = await _create_test_trainer_profile(
        db, "trainer1@trainer.com"
    )
    trainer_headers = auth_headers(trainer_user)
    _, client_profile = await _create_test_client_profile(
        client, trainer_profile.id, "client1@client.com", db
    )
    exercise = await _create_test_exercise(client, trainer_headers)
    assignment = {
        "exercise_id": exercise["id"],
        "cycle_phase": "ovulatory",
        "day_of_week": 3,
    }
    created = await client.post(
        "/plan/training/create",
        json={
            "client_id": client_profile["id"],
            "title": "Plan",
            "exercises": [assignment],
        },
        headers=trainer_headers,
    )
    plan_id = created.json()["id"]

    response = await client.patch(
        "/plan/training/remove_exercise",
        params={"plan_id": plan_id},
        json=[assignment],
        headers=trainer_headers,
    )
    assert response.status_code == 200
    assert len(response.json()["exercises"]) == 0
