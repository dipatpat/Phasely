from decimal import Decimal

from app.core.enums import UserRole
from app.trainer.service import create_trainer_profile
from tests.conftest import auth_headers, create_test_user

# Cycle of 28 days with a 5-day period starting 2026-09-24 puts the week of
# Monday 2026-10-19 at: Mon-Wed luteal (cycle days 26-28), Thu-Sun menstrual (1-4)
WEEK_START = "2026-10-19"
CYCLE_DATA = {
    "last_period_start": "2026-09-24",
    "cycle_length_days": 28,
    "period_length_days": 5,
}


async def _create_test_trainer(db, email="trainer1@trainer.com"):
    trainer_user = await create_test_user(db, UserRole.trainer, email)
    trainer_profile = await create_trainer_profile(
        db, trainer_user.id, "experienced", "fertility"
    )
    return trainer_user, trainer_profile


async def _create_test_client(client, db, trainer_profile_id, **profile_fields):
    client_user = await create_test_user(db, UserRole.client, "client1@client.com")
    response = await client.post(
        "/client/create",
        json={"trainer_id": str(trainer_profile_id), **profile_fields},
        headers=auth_headers(client_user),
    )
    return client_user, response.json()


async def _create_test_recipe(client, trainer_headers, name, meal_type, ingredients):
    response = await client.post(
        "/recipe/create",
        json={
            "name": name,
            "meal_type": meal_type,
            "protein": "10.00",
            "carbs": "10.00",
            "fat": "5.00",
            "calories": 300,
            "serving_size": "1 bowl",
            "ingredients": [
                {"name": ingredient, "quantity": quantity, "unit": unit}
                for ingredient, quantity, unit in ingredients
            ],
            "dietary_tag_names": [],
        },
        headers=trainer_headers,
    )
    return response.json()


async def _create_nutrition_plan(client, trainer_headers, client_id, assignments):
    response = await client.post(
        "/plan/nutrition/create",
        json={
            "client_id": client_id,
            "title": "Cycle Plan",
            "recipes": [
                {
                    "recipe_id": recipe["id"],
                    "meal_type": meal_type,
                    "cycle_phase": phase,
                }
                for recipe, meal_type, phase in assignments
            ],
        },
        headers=trainer_headers,
    )
    assert response.status_code == 201


async def _create_breakfast_plan(client, db):
    trainer_user, trainer_profile = await _create_test_trainer(db)
    trainer_headers = auth_headers(trainer_user)
    client_user, client_profile = await _create_test_client(
        client, db, trainer_profile.id, **CYCLE_DATA
    )
    banana_oats = await _create_test_recipe(
        client,
        trainer_headers,
        "Banana Oats",
        "breakfast",
        [("oats", "50.00", "g"), ("banana", "1.00", "pcs")],
    )
    porridge = await _create_test_recipe(
        client,
        trainer_headers,
        "Porridge",
        "breakfast",
        [("oats", "60.00", "g"), ("milk", "200.00", "ml")],
    )
    eggs = await _create_test_recipe(
        client,
        trainer_headers,
        "Scrambled Eggs",
        "breakfast",
        [("egg", "2.00", "pcs")],
    )
    await _create_nutrition_plan(
        client,
        trainer_headers,
        client_profile["id"],
        [
            (banana_oats, "breakfast", "luteal"),
            (porridge, "breakfast", "luteal"),
            (eggs, "breakfast", "menstrual"),
        ],
    )
    return client_user, trainer_user, client_profile


def _items_by_key(data):
    return {
        (item["ingredient"], item["unit"]): Decimal(item["quantity"])
        for item in data["items"]
    }


async def test_shopping_list_follows_predicted_phases_and_rotates_alternatives(
    client, db
):
    client_user, _, _ = await _create_breakfast_plan(client, db)

    response = await client.get(
        "/shopping-list/weekly",
        params={"week_start": WEEK_START},
        headers=auth_headers(client_user),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["week_end"] == "2026-10-25"
    assert data["unpredictable_dates"] == []
    assert [day["cycle_phase"] for day in data["days"]] == [
        "luteal",
        "luteal",
        "luteal",
        "menstrual",
        "menstrual",
        "menstrual",
        "menstrual",
    ]
    breakfasts = [day["meals"][0]["recipe_name"] for day in data["days"]]
    assert breakfasts == [
        "Banana Oats",
        "Porridge",
        "Banana Oats",
        "Scrambled Eggs",
        "Scrambled Eggs",
        "Scrambled Eggs",
        "Scrambled Eggs",
    ]
    # Banana Oats x2, Porridge x1, Scrambled Eggs x4
    assert _items_by_key(data) == {
        ("banana", "pcs"): Decimal("2"),
        ("egg", "pcs"): Decimal("8"),
        ("milk", "ml"): Decimal("200"),
        ("oats", "g"): Decimal("160"),
    }


async def test_shopping_list_logged_phase_overrides_prediction(client, db):
    client_user, _, _ = await _create_breakfast_plan(client, db)
    headers = auth_headers(client_user)
    await client.post(
        "/log/daily/create",
        json={"log_date": "2026-10-22", "cycle_phase": "follicular"},
        headers=headers,
    )

    response = await client.get(
        "/shopping-list/weekly", params={"week_start": WEEK_START}, headers=headers
    )

    data = response.json()
    assert data["days"][3]["cycle_phase"] == "follicular"
    assert data["days"][3]["meals"] == []
    assert _items_by_key(data)[("egg", "pcs")] == Decimal("6")


async def test_shopping_list_keeps_different_units_separate(client, db):
    trainer_user, trainer_profile = await _create_test_trainer(db)
    trainer_headers = auth_headers(trainer_user)
    client_user, client_profile = await _create_test_client(
        client, db, trainer_profile.id, **CYCLE_DATA
    )
    salad = await _create_test_recipe(
        client, trainer_headers, "Chicken Salad", "lunch", [("chicken", "200.00", "g")]
    )
    skewer = await _create_test_recipe(
        client,
        trainer_headers,
        "Chicken Skewer",
        "dinner",
        [("chicken", "1.00", "pcs")],
    )
    await _create_nutrition_plan(
        client,
        trainer_headers,
        client_profile["id"],
        [(salad, "lunch", "luteal"), (skewer, "dinner", "luteal")],
    )

    response = await client.get(
        "/shopping-list/weekly",
        params={"week_start": WEEK_START},
        headers=auth_headers(client_user),
    )

    assert _items_by_key(response.json()) == {
        ("chicken", "g"): Decimal("600"),
        ("chicken", "pcs"): Decimal("3"),
    }


async def test_shopping_list_without_cycle_data_reports_unpredictable_days(client, db):
    _, trainer_profile = await _create_test_trainer(db)
    client_user, _ = await _create_test_client(client, db, trainer_profile.id)

    response = await client.get(
        "/shopping-list/weekly",
        params={"week_start": WEEK_START},
        headers=auth_headers(client_user),
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["unpredictable_dates"]) == 7
    assert all(day["cycle_phase"] is None for day in data["days"])
    assert data["items"] == []


async def test_shopping_list_without_active_plan_is_empty(client, db):
    _, trainer_profile = await _create_test_trainer(db)
    client_user, _ = await _create_test_client(
        client, db, trainer_profile.id, **CYCLE_DATA
    )

    response = await client.get(
        "/shopping-list/weekly",
        params={"week_start": WEEK_START},
        headers=auth_headers(client_user),
    )

    data = response.json()
    assert data["days"][0]["cycle_phase"] == "luteal"
    assert all(day["meals"] == [] for day in data["days"])
    assert data["items"] == []


async def test_shopping_list_as_trainer_for_own_client(client, db):
    _, trainer_user, client_profile = await _create_breakfast_plan(client, db)

    response = await client.get(
        "/shopping-list/weekly",
        params={"week_start": WEEK_START, "client_id": client_profile["id"]},
        headers=auth_headers(trainer_user),
    )

    assert response.status_code == 200
    assert _items_by_key(response.json())[("egg", "pcs")] == Decimal("8")


async def test_shopping_list_as_trainer_for_unrelated_client_not_found(client, db):
    _, _, client_profile = await _create_breakfast_plan(client, db)
    other_trainer, _ = await _create_test_trainer(db, "trainer2@trainer.com")

    response = await client.get(
        "/shopping-list/weekly",
        params={"week_start": WEEK_START, "client_id": client_profile["id"]},
        headers=auth_headers(other_trainer),
    )

    assert response.status_code == 404


async def test_shopping_list_as_trainer_without_client_id_fails(client, db):
    trainer_user, _ = await _create_test_trainer(db)

    response = await client.get(
        "/shopping-list/weekly",
        params={"week_start": WEEK_START},
        headers=auth_headers(trainer_user),
    )

    assert response.status_code == 422


async def test_shopping_list_rejects_non_monday(client, db):
    client_user, _, _ = await _create_breakfast_plan(client, db)

    response = await client.get(
        "/shopping-list/weekly",
        params={"week_start": "2026-10-20"},
        headers=auth_headers(client_user),
    )

    assert response.status_code == 422
