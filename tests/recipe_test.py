import asyncio
import uuid

from sqlalchemy import func, select
from sqlalchemy.pool import NullPool

from app.core.enums import UserRole
from app.recipe.models import Ingredient, Recipe
from app.recipe.tasks import sync_recipe_to_postgres_full_text_search, task_engine
from tests.conftest import TestSessionLocal, auth_headers, create_test_user


def _recipe_payload(**overrides):
    payload = {
        "name": "Caesar Salad",
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
    assert data["name"] == "Caesar Salad"
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
        json=_recipe_payload(name="Caesar Salad"),
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
        "/recipe/create", json=_recipe_payload(name="Caesar Salad"), headers=headers
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
    assert "Caesar Salad" in names


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
    assert response.json()["name"] == "Caesar Salad"


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
    assert data["name"] == "Caesar Salad"


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


async def _matches_search(db, recipe_id: str, term: str) -> bool:
    result = await db.execute(
        select(Recipe.search_vector.op("@@")(func.to_tsquery("english", term))).where(
            Recipe.id == uuid.UUID(recipe_id)
        )
    )
    return bool(result.scalar_one())


async def test_sync_recipe_task_populates_search_vector(mocker, client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    created = await client.post(
        "/recipe/create",
        json=_recipe_payload(name="Caesar Salad", dietary_tag_names=["vegan"]),
        headers=headers,
    )
    recipe_id = created.json()["id"]

    mocker.patch("app.recipe.tasks.TaskSessionLocal", TestSessionLocal)

    await asyncio.to_thread(sync_recipe_to_postgres_full_text_search, recipe_id)

    assert await _matches_search(db, recipe_id, "salad")  # from name
    assert await _matches_search(db, recipe_id, "vegan")  # from dietary tag
    assert await _matches_search(db, recipe_id, "lunch")  # from meal_type
    assert not await _matches_search(db, recipe_id, "dinner")


def test_task_engine_does_not_pool_connections():
    assert isinstance(task_engine.pool, NullPool)


async def _sync_recipe(mocker, recipe_id: str) -> None:
    mocker.patch("app.recipe.tasks.TaskSessionLocal", TestSessionLocal)
    await asyncio.to_thread(sync_recipe_to_postgres_full_text_search, recipe_id)


async def test_search_recipes_matches_by_name(mocker, client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    created = await client.post(
        "/recipe/create",
        json=_recipe_payload(name="Caesar Salad", dietary_tag_names=["vegan"]),
        headers=headers,
    )
    await _sync_recipe(mocker, created.json()["id"])

    response = await client.get(
        "/recipe/search", params={"query": "salad"}, headers=headers
    )
    assert response.status_code == 200
    names = [recipe["name"] for recipe in response.json()]
    assert "Caesar Salad" in names


async def test_search_recipes_matches_by_dietary_tag(mocker, client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    created = await client.post(
        "/recipe/create",
        json=_recipe_payload(name="Caesar Salad", dietary_tag_names=["vegan"]),
        headers=headers,
    )
    await _sync_recipe(mocker, created.json()["id"])

    response = await client.get(
        "/recipe/search", params={"query": "vegan"}, headers=headers
    )
    assert response.status_code == 200
    names = [recipe["name"] for recipe in response.json()]
    assert "Caesar Salad" in names


async def test_search_recipes_no_match_returns_empty(mocker, client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    created = await client.post(
        "/recipe/create",
        json=_recipe_payload(name="Caesar Salad", dietary_tag_names=["vegan"]),
        headers=headers,
    )
    await _sync_recipe(mocker, created.json()["id"])

    response = await client.get(
        "/recipe/search", params={"query": "pizza"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json() == []


async def test_search_recipes_ranks_name_match_above_tag_match(mocker, client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)

    name_match = await client.post(
        "/recipe/create",
        json=_recipe_payload(name="Protein Power Bowl", dietary_tag_names=["vegan"]),
        headers=headers,
    )
    tag_match = await client.post(
        "/recipe/create",
        json=_recipe_payload(name="Chicken Soup", dietary_tag_names=["protein"]),
        headers=headers,
    )
    await _sync_recipe(mocker, name_match.json()["id"])
    await _sync_recipe(mocker, tag_match.json()["id"])

    response = await client.get(
        "/recipe/search", params={"query": "protein"}, headers=headers
    )
    assert response.status_code == 200
    names = [recipe["name"] for recipe in response.json()]
    assert names == ["Protein Power Bowl", "Chicken Soup"]


async def test_search_recipes_matches_by_ingredient(mocker, client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    created = await client.post(
        "/recipe/create",
        json=_recipe_payload(name="Garden Bowl", dietary_tag_names=["vegan"]),
        headers=headers,
    )
    await _sync_recipe(mocker, created.json()["id"])

    response = await client.get(
        "/recipe/search", params={"query": "chicken"}, headers=headers
    )
    assert response.status_code == 200
    names = [recipe["name"] for recipe in response.json()]
    assert "Garden Bowl" in names


async def test_search_recipes_filters_by_meal_type(mocker, client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    lunch_recipe = await client.post(
        "/recipe/create",
        json=_recipe_payload(name="Chicken Lunch Bowl", meal_type="lunch"),
        headers=headers,
    )
    dinner_recipe = await client.post(
        "/recipe/create",
        json=_recipe_payload(name="Chicken Dinner Bowl", meal_type="dinner"),
        headers=headers,
    )
    await _sync_recipe(mocker, lunch_recipe.json()["id"])
    await _sync_recipe(mocker, dinner_recipe.json()["id"])

    response = await client.get(
        "/recipe/search",
        params={"query": "chicken", "meal_type": "dinner"},
        headers=headers,
    )
    assert response.status_code == 200
    names = [recipe["name"] for recipe in response.json()]
    assert names == ["Chicken Dinner Bowl"]


async def test_search_recipes_filters_by_max_calories(mocker, client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    light_recipe = await client.post(
        "/recipe/create",
        json=_recipe_payload(name="Light Chicken Bowl", calories=300),
        headers=headers,
    )
    heavy_recipe = await client.post(
        "/recipe/create",
        json=_recipe_payload(name="Heavy Chicken Bowl", calories=900),
        headers=headers,
    )
    await _sync_recipe(mocker, light_recipe.json()["id"])
    await _sync_recipe(mocker, heavy_recipe.json()["id"])

    response = await client.get(
        "/recipe/search",
        params={"query": "chicken", "max_calories": 500},
        headers=headers,
    )
    assert response.status_code == 200
    names = [recipe["name"] for recipe in response.json()]
    assert names == ["Light Chicken Bowl"]


async def test_search_recipes_filters_by_dietary_tag(mocker, client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    vegan_recipe = await client.post(
        "/recipe/create",
        json=_recipe_payload(name="Vegan Chicken Bowl", dietary_tag_names=["vegan"]),
        headers=headers,
    )
    keto_recipe = await client.post(
        "/recipe/create",
        json=_recipe_payload(name="Keto Chicken Bowl", dietary_tag_names=["keto"]),
        headers=headers,
    )
    await _sync_recipe(mocker, vegan_recipe.json()["id"])
    await _sync_recipe(mocker, keto_recipe.json()["id"])

    response = await client.get(
        "/recipe/search",
        params={"query": "chicken", "dietary_tag": "keto"},
        headers=headers,
    )
    assert response.status_code == 200
    names = [recipe["name"] for recipe in response.json()]
    assert names == ["Keto Chicken Bowl"]


async def test_search_recipes_respects_limit(mocker, client, db):
    trainer = await create_test_user(db, UserRole.trainer, "trainer1@example.com")
    headers = auth_headers(trainer)
    for i in range(3):
        created = await client.post(
            "/recipe/create",
            json=_recipe_payload(name=f"Chicken Bowl {i}"),
            headers=headers,
        )
        await _sync_recipe(mocker, created.json()["id"])

    response = await client.get(
        "/recipe/search",
        params={"query": "chicken", "limit": 2},
        headers=headers,
    )
    assert response.status_code == 200
    assert len(response.json()) == 2
