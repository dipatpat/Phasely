from sqlalchemy import select

from app.core.enums import UserRole
from app.recipe.models import Ingredient
from tests.conftest import auth_headers, create_test_user


def _recipe_payload(**overrides):
    payload = {
        "name": "Ceasar Salad",
        "meal_type": "lunch",
        "protein": "30.00",
        "carbs": "10.00",
        "fat": "8.00",
        "calories": 350,
        "serving_size": "1 bowl",
        "ingredients": [
            {"name": "chicken", "quantity": "100.00", "unit": "g"},
            {"name": "lettuce", "quantity": "50.00", "unit": "g"},
        ],
        "dietary_tag_names": ["high-protein", "gluten-free"],
    }
    payload.update(overrides)
    return payload


async def test_create_recipe_as_trainer_succeeds(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)

    response = await client.post(
        "/recipe/create", json=_recipe_payload(), headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Ceasar Salad"
    ingredient_names = {i["name"] for i in data["ingredients"]}
    assert ingredient_names == {"chicken", "lettuce"}
    tag_names = {t["name"] for t in data["dietary_tags"]}
    assert tag_names == {"high-protein", "gluten-free"}


async def test_create_recipe_as_client_forbidden(client, db):
    user = await create_test_user(db, UserRole.client, "client1@client.com")
    headers = auth_headers(user)

    response = await client.post(
        "/recipe/create", json=_recipe_payload(), headers=headers
    )
    assert response.status_code == 403


async def test_create_recipe_reuses_existing_ingredient(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)

    await client.post(
        "/recipe/create",
        json=_recipe_payload(name="Ceasar Salad"),
        headers=headers,
    )
    await client.post(
        "/recipe/create",
        json=_recipe_payload(
            name="Chicken Soup",
            ingredients=[{"name": "chicken", "quantity": "150.00", "unit": "g"}],
        ),
        headers=headers,
    )

    result = await db.execute(select(Ingredient).where(Ingredient.name == "chicken"))
    matches = result.scalars().all()
    assert len(matches) == 1


async def test_create_recipe_reuses_existing_dietary_tag(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)

    first_recipe = await client.post(
        "/recipe/create", json=_recipe_payload(name="Ceasar Salad"), headers=headers
    )
    second_recipe = await client.post(
        "/recipe/create",
        json=_recipe_payload(
            name="Seitan Salad",
            ingredients=[{"name": "seitan", "quantity": "100.00", "unit": "g"}],
        ),
        headers=headers,
    )
    first_tag_id = next(
        t["id"]
        for t in first_recipe.json()["dietary_tags"]
        if t["name"] == "high-protein"
    )
    second_tag_id = next(
        t["id"]
        for t in second_recipe.json()["dietary_tags"]
        if t["name"] == "high-protein"
    )
    assert first_tag_id == second_tag_id


async def test_list_recipes_visible_to_client(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    await client.post(
        "/recipe/create", json=_recipe_payload(), headers=auth_headers(trainer)
    )

    client_user = await create_test_user(db, UserRole.client, "client1@client.com")
    response = await client.get("/recipe/", headers=auth_headers(client_user))
    assert response.status_code == 200
    names = [recipe["name"] for recipe in response.json()]
    assert "Ceasar Salad" in names


async def test_get_recipe_by_id_success(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    created = await client.post(
        "/recipe/create", json=_recipe_payload(), headers=headers
    )
    recipe_id = created.json()["id"]

    response = await client.get(
        "/recipe/by_id", params={"recipe_id": recipe_id}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Ceasar Salad"


async def test_get_recipe_by_id_not_found(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)

    response = await client.get(
        "/recipe/by_id",
        params={"recipe_id": "00000000-0000-0000-0000-000000000000"},
        headers=headers,
    )
    assert response.status_code == 404


async def test_update_recipe_scalar_fields(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    created = await client.post(
        "/recipe/create", json=_recipe_payload(), headers=headers
    )
    recipe_id = created.json()["id"]

    response = await client.patch(
        "/recipe/update",
        params={"recipe_id": recipe_id},
        json={"calories": 400},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["calories"] == 400
    assert data["name"] == "Ceasar Salad"


async def test_update_recipe_replaces_ingredients(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    created = await client.post(
        "/recipe/create", json=_recipe_payload(), headers=headers
    )
    recipe_id = created.json()["id"]

    response = await client.patch(
        "/recipe/update",
        params={"recipe_id": recipe_id},
        json={"ingredients": [{"name": "seitan", "quantity": "100.00", "unit": "g"}]},
        headers=headers,
    )
    assert response.status_code == 200
    ingredient_names = {i["name"] for i in response.json()["ingredients"]}
    assert ingredient_names == {"seitan"}


async def test_update_recipe_not_found(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)

    response = await client.patch(
        "/recipe/update",
        params={"recipe_id": "00000000-0000-0000-0000-000000000000"},
        json={"calories": 400},
        headers=headers,
    )
    assert response.status_code == 404


async def test_delete_recipe_success(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    created = await client.post(
        "/recipe/create", json=_recipe_payload(), headers=headers
    )
    recipe_id = created.json()["id"]

    response = await client.delete(
        "/recipe/delete", params={"recipe_id": recipe_id}, headers=headers
    )
    assert response.status_code == 204

    follow_up = await client.get(
        "/recipe/by_id", params={"recipe_id": recipe_id}, headers=headers
    )
    assert follow_up.status_code == 404


async def test_delete_recipe_not_found(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)

    response = await client.delete(
        "/recipe/delete",
        params={"recipe_id": "00000000-0000-0000-0000-000000000000"},
        headers=headers,
    )
    assert response.status_code == 404


async def test_delete_recipe_as_client_forbidden(client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    created = await client.post(
        "/recipe/create", json=_recipe_payload(), headers=auth_headers(trainer)
    )
    recipe_id = created.json()["id"]

    client_user = await create_test_user(db, UserRole.client, "client1@client.com")
    response = await client.delete(
        "/recipe/delete",
        params={"recipe_id": recipe_id},
        headers=auth_headers(client_user),
    )
    assert response.status_code == 403
