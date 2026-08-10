from shared.auth.roles import Role


async def _login(client, email: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_create_prompt_as_developer(client, make_user, dynamodb_table):
    await make_user("dev@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    token = await _login(client, "dev@panasa.com", "pw12345")

    response = await client.post(
        "/api/v1/prompts",
        json={"name": "Greeting", "content": "Hello {{name}}", "variables": ["name"]},
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["version"] == 1
    assert body["tenant_id"] == "tenant-a"


async def test_create_prompt_forbidden_for_analyst(client, make_user, dynamodb_table):
    await make_user("analyst@panasa.com", "pw12345", Role.ANALYST, tenant_id="tenant-a")
    token = await _login(client, "analyst@panasa.com", "pw12345")

    response = await client.post(
        "/api/v1/prompts",
        json={"name": "Greeting", "content": "Hello {{name}}", "variables": ["name"]},
        headers=auth_headers(token),
    )

    assert response.status_code == 403


async def test_list_prompts_shows_latest_version_only(client, make_user, dynamodb_table):
    await make_user("dev@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    token = await _login(client, "dev@panasa.com", "pw12345")

    created = await client.post(
        "/api/v1/prompts",
        json={"name": "Greeting", "content": "v1 content", "variables": []},
        headers=auth_headers(token),
    )
    prompt_id = created.json()["prompt_id"]

    await client.post(
        f"/api/v1/prompts/{prompt_id}/versions",
        json={"content": "v2 content"},
        headers=auth_headers(token),
    )

    response = await client.get("/api/v1/prompts", headers=auth_headers(token))

    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["prompt_id"] == prompt_id
    assert items[0]["version"] == 2
    assert items[0]["content"] == "v2 content"


async def test_list_prompts_scoped_to_tenant(client, make_user, dynamodb_table):
    await make_user("devA@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    await make_user("devB@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-b")
    token_a = await _login(client, "devA@panasa.com", "pw12345")
    token_b = await _login(client, "devB@panasa.com", "pw12345")

    await client.post(
        "/api/v1/prompts",
        json={"name": "A", "content": "content", "variables": []},
        headers=auth_headers(token_a),
    )
    await client.post(
        "/api/v1/prompts",
        json={"name": "B", "content": "content", "variables": []},
        headers=auth_headers(token_b),
    )

    response = await client.get("/api/v1/prompts", headers=auth_headers(token_a))

    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert names == {"A"}


async def test_create_version_increments_and_inherits(client, make_user, dynamodb_table):
    await make_user("dev@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    token = await _login(client, "dev@panasa.com", "pw12345")

    created = await client.post(
        "/api/v1/prompts",
        json={"name": "Greeting", "content": "v1", "variables": ["name"]},
        headers=auth_headers(token),
    )
    prompt_id = created.json()["prompt_id"]

    response = await client.post(
        f"/api/v1/prompts/{prompt_id}/versions",
        json={"content": "v2"},
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["version"] == 2
    assert body["content"] == "v2"
    assert body["name"] == "Greeting"
    assert body["variables"] == ["name"]


async def test_create_version_for_unknown_prompt(client, make_user, dynamodb_table):
    await make_user("dev@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    token = await _login(client, "dev@panasa.com", "pw12345")

    response = await client.post(
        "/api/v1/prompts/does-not-exist/versions",
        json={"content": "v2"},
        headers=auth_headers(token),
    )

    assert response.status_code == 404


async def test_list_versions_returns_all_in_order(client, make_user, dynamodb_table):
    await make_user("dev@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    token = await _login(client, "dev@panasa.com", "pw12345")

    created = await client.post(
        "/api/v1/prompts",
        json={"name": "Greeting", "content": "v1", "variables": []},
        headers=auth_headers(token),
    )
    prompt_id = created.json()["prompt_id"]

    await client.post(
        f"/api/v1/prompts/{prompt_id}/versions",
        json={"content": "v2"},
        headers=auth_headers(token),
    )
    await client.post(
        f"/api/v1/prompts/{prompt_id}/versions",
        json={"content": "v3"},
        headers=auth_headers(token),
    )

    response = await client.get(
        f"/api/v1/prompts/{prompt_id}/versions", headers=auth_headers(token)
    )

    assert response.status_code == 200
    versions = response.json()
    assert [v["version"] for v in versions] == [1, 2, 3]
    assert [v["content"] for v in versions] == ["v1", "v2", "v3"]


async def test_list_versions_not_visible_across_tenants(client, make_user, dynamodb_table):
    await make_user("devA@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    await make_user("devB@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-b")
    token_a = await _login(client, "devA@panasa.com", "pw12345")
    token_b = await _login(client, "devB@panasa.com", "pw12345")

    created = await client.post(
        "/api/v1/prompts",
        json={"name": "Greeting", "content": "v1", "variables": []},
        headers=auth_headers(token_a),
    )
    prompt_id = created.json()["prompt_id"]

    response = await client.get(
        f"/api/v1/prompts/{prompt_id}/versions", headers=auth_headers(token_b)
    )

    assert response.status_code == 404
