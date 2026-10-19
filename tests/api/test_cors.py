FRONTEND_ORIGIN = "http://localhost:5173"


async def test_preflight_allows_frontend_origin(client):
    response = await client.options(
        "/auth/me",
        headers={
            "Origin": FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


async def test_preflight_rejects_unknown_origin(client):
    response = await client.options(
        "/auth/me",
        headers={
            "Origin": "http://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers


async def test_normal_response_carries_allow_origin_header(client):
    response = await client.get("/health", headers={"Origin": FRONTEND_ORIGIN})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN
