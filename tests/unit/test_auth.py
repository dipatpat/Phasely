async def test_register_user_success(client):
    response = await client.post(
        "/auth/register",
        json={
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@smith.com",
            "password": "123456789",
            "role": "client",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "john@smith.com"
    assert data["last_name"] == "Smith"
    assert "hashed_password" not in data


async def test_register_duplicate_email_fails(client):
    payload = {
        "first_name": "Marek",
        "last_name": "Nowy",
        "email": "marek@nowy.com",
        "password": "123456789",
        "role": "trainer",
    }
    first_attempt = await client.post("/auth/register", json=payload)
    assert first_attempt.status_code == 201

    second_attempt = await client.post("/auth/register", json=payload)
    assert second_attempt.status_code == 409


async def test_login_success(client):
    await client.post(
        "/auth/register",
        json={
            "first_name": "Anna",
            "last_name": "Nowak",
            "email": "anna@nowak.com",
            "password": "123456789",
            "role": "client",
        },
    )
    response = await client.post(
        "/auth/login",
        data={"username": "anna@nowak.com", "password": "123456789"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password_fails(client):
    await client.post(
        "/auth/register",
        json={
            "first_name": "Joanna",
            "last_name": "Brzeska",
            "email": "joanna@brzeska.com",
            "password": "123456789",
            "role": "client",
        },
    )
    response = await client.post(
        "/auth/login",
        data={"username": "joanna@brzeska.com", "password": "rewrerer"},
    )
    assert response.status_code == 401


async def test_me_requires_authentication(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_me_returns_current_user(client):
    await client.post(
        "/auth/register",
        json={
            "first_name": "Krystyna",
            "last_name": "Czubowna",
            "email": "krystyna@gmail.com",
            "password": "123456789",
            "role": "client",
        },
    )
    login = await client.post(
        "/auth/login",
        data={"username": "krystyna@gmail.com", "password": "123456789"},
    )
    token = login.json()["access_token"]

    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "krystyna@gmail.com"


async def test_logout_blacklists_token(client):
    await client.post(
        "/auth/register",
        json={
            "first_name": "Robert",
            "last_name": "Lewandowski",
            "email": "robert@barca.com",
            "password": "123456789",
            "role": "client",
        },
    )
    login = await client.post(
        "/auth/login",
        data={"username": "robert@barca.com", "password": "123456789"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.get("/auth/me", headers=headers)
    assert response.status_code == 200

    logout = await client.post("/auth/logout", headers=headers)
    assert logout.status_code == 204

    response = await client.get("/auth/me", headers=headers)
    assert response.status_code == 401
