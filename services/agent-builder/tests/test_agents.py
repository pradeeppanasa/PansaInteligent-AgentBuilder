from shared.auth.roles import Role


def agent_payload(**overrides):
    payload = {
        "name": "Support Bot",
        "description": "Handles support tickets",
        "system_prompt": "You are a helpful support agent.",
        "model_config": {"model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0"},
        "guardrail_config": {},
    }
    payload.update(overrides)
    return payload


async def _login(client, email: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_create_agent_as_developer(client, make_user, dynamodb_table):
    await make_user("dev@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    token = await _login(client, "dev@panasa.com", "pw12345")

    response = await client.post(
        "/api/v1/agents", json=agent_payload(), headers=auth_headers(token)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["tenant_id"] == "tenant-a"
    assert body["status"] == "draft"
    assert body["model_config"]["model_id"] == "anthropic.claude-3-5-sonnet-20241022-v2:0"


async def test_create_agent_forbidden_for_analyst(client, make_user, dynamodb_table):
    await make_user("analyst@panasa.com", "pw12345", Role.ANALYST, tenant_id="tenant-a")
    token = await _login(client, "analyst@panasa.com", "pw12345")

    response = await client.post(
        "/api/v1/agents", json=agent_payload(), headers=auth_headers(token)
    )

    assert response.status_code == 403


async def test_list_agents_scoped_to_tenant(client, make_user, dynamodb_table):
    await make_user("devA@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    await make_user("devB@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-b")
    token_a = await _login(client, "devA@panasa.com", "pw12345")
    token_b = await _login(client, "devB@panasa.com", "pw12345")

    await client.post(
        "/api/v1/agents", json=agent_payload(name="A1"), headers=auth_headers(token_a)
    )
    await client.post(
        "/api/v1/agents", json=agent_payload(name="A2"), headers=auth_headers(token_a)
    )
    await client.post(
        "/api/v1/agents", json=agent_payload(name="B1"), headers=auth_headers(token_b)
    )

    response = await client.get("/api/v1/agents", headers=auth_headers(token_a))

    assert response.status_code == 200
    body = response.json()
    names = {item["name"] for item in body["items"]}
    assert names == {"A1", "A2"}


async def test_get_agent_not_found(client, make_user, dynamodb_table):
    await make_user("dev@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    token = await _login(client, "dev@panasa.com", "pw12345")

    response = await client.get("/api/v1/agents/does-not-exist", headers=auth_headers(token))

    assert response.status_code == 404


async def test_get_agent_not_visible_across_tenants(client, make_user, dynamodb_table):
    await make_user("devA@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    await make_user("devB@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-b")
    token_a = await _login(client, "devA@panasa.com", "pw12345")
    token_b = await _login(client, "devB@panasa.com", "pw12345")

    created = await client.post(
        "/api/v1/agents", json=agent_payload(), headers=auth_headers(token_a)
    )
    agent_id = created.json()["agent_id"]

    response = await client.get(f"/api/v1/agents/{agent_id}", headers=auth_headers(token_b))

    assert response.status_code == 404


async def test_update_agent(client, make_user, dynamodb_table):
    await make_user("dev@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    token = await _login(client, "dev@panasa.com", "pw12345")
    created = await client.post("/api/v1/agents", json=agent_payload(), headers=auth_headers(token))
    agent_id = created.json()["agent_id"]

    response = await client.put(
        f"/api/v1/agents/{agent_id}",
        json={"name": "Renamed Bot", "status": "active"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renamed Bot"
    assert body["status"] == "active"
    assert body["updated_at"] != created.json()["updated_at"] or body["created_at"]


async def test_update_agent_forbidden_for_analyst(client, make_user, dynamodb_table):
    await make_user("dev@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    await make_user("analyst@panasa.com", "pw12345", Role.ANALYST, tenant_id="tenant-a")
    dev_token = await _login(client, "dev@panasa.com", "pw12345")
    analyst_token = await _login(client, "analyst@panasa.com", "pw12345")

    created = await client.post(
        "/api/v1/agents", json=agent_payload(), headers=auth_headers(dev_token)
    )
    agent_id = created.json()["agent_id"]

    response = await client.put(
        f"/api/v1/agents/{agent_id}",
        json={"name": "Hacked"},
        headers=auth_headers(analyst_token),
    )

    assert response.status_code == 403


async def test_delete_agent(client, make_user, dynamodb_table):
    await make_user("dev@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    token = await _login(client, "dev@panasa.com", "pw12345")
    created = await client.post("/api/v1/agents", json=agent_payload(), headers=auth_headers(token))
    agent_id = created.json()["agent_id"]

    delete_response = await client.delete(f"/api/v1/agents/{agent_id}", headers=auth_headers(token))
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/agents/{agent_id}", headers=auth_headers(token))
    assert get_response.status_code == 404


async def test_duplicate_agent(client, make_user, dynamodb_table):
    await make_user("dev@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    token = await _login(client, "dev@panasa.com", "pw12345")
    created = await client.post(
        "/api/v1/agents", json=agent_payload(name="Original"), headers=auth_headers(token)
    )
    agent_id = created.json()["agent_id"]

    response = await client.post(
        f"/api/v1/agents/{agent_id}/duplicate", headers=auth_headers(token)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["agent_id"] != agent_id
    assert body["name"] == "Original (copy)"
    assert body["status"] == "draft"
