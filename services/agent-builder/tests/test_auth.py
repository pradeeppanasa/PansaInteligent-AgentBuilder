from app.core.config import settings
from shared.auth.roles import Role


async def _login(client, email: str, password: str):
    return await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )


async def test_login_success(client, make_user):
    await make_user("dev@panasa.com", "correct-password", Role.DEVELOPER)

    response = await _login(client, "dev@panasa.com", "correct-password")

    assert response.status_code == 200
    body = response.json()
    assert body["expires_in"] == settings.JWT_EXPIRE_MINUTES * 60
    assert body["access_token"]
    assert body["refresh_token"]


async def test_login_invalid_password(client, make_user):
    await make_user("dev@panasa.com", "correct-password", Role.DEVELOPER)

    response = await _login(client, "dev@panasa.com", "wrong-password")

    assert response.status_code == 400


async def test_me_with_valid_token(client, make_user):
    await make_user("analyst@panasa.com", "pw12345", Role.ANALYST)
    tokens = (await _login(client, "analyst@panasa.com", "pw12345")).json()

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "analyst@panasa.com"
    assert body["role"] == Role.ANALYST.value


async def test_me_without_token(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_refresh_flow(client, make_user):
    await make_user("auditor@panasa.com", "pw12345", Role.AUDITOR)
    tokens = (await _login(client, "auditor@panasa.com", "pw12345")).json()

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
    )
    assert me_response.status_code == 200


async def test_refresh_rejects_access_token(client, make_user):
    await make_user("dev2@panasa.com", "pw12345", Role.DEVELOPER)
    tokens = (await _login(client, "dev2@panasa.com", "pw12345")).json()

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )

    assert response.status_code == 401


async def test_register_requires_admin_role(client, make_user):
    await make_user("dev3@panasa.com", "pw12345", Role.DEVELOPER)
    tokens = (await _login(client, "dev3@panasa.com", "pw12345")).json()

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@panasa.com", "password": "pw12345", "role": Role.ANALYST.value},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 403


async def test_register_as_admin_creates_user(client, make_user):
    await make_user("admin@panasa.com", "pw12345", Role.ADMIN)
    tokens = (await _login(client, "admin@panasa.com", "pw12345")).json()

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@panasa.com", "password": "pw12345", "role": Role.DEVELOPER.value},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@panasa.com"
    assert body["role"] == Role.DEVELOPER.value

    new_user_login = await _login(client, "new@panasa.com", "pw12345")
    assert new_user_login.status_code == 200


async def test_register_duplicate_email_rejected(client, make_user):
    await make_user("admin2@panasa.com", "pw12345", Role.ADMIN)
    await make_user("dup@panasa.com", "pw12345", Role.ANALYST)
    tokens = (await _login(client, "admin2@panasa.com", "pw12345")).json()

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@panasa.com", "password": "pw12345", "role": Role.ANALYST.value},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 400
