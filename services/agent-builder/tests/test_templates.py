from shared.auth.roles import Role


async def _login(client, email: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_list_templates_returns_all_defaults(client, make_user, dynamodb_table):
    await make_user("analyst@panasa.com", "pw12345", Role.ANALYST)
    token = await _login(client, "analyst@panasa.com", "pw12345")

    response = await client.get("/api/v1/templates", headers=auth_headers(token))

    assert response.status_code == 200
    template_ids = {item["template_id"] for item in response.json()}
    assert template_ids == {
        "customer-support-v1",
        "data-analyst-v1",
        "code-review-v1",
        "document-qa-v1",
        "hr-assistant-v1",
    }


async def test_list_templates_filtered_by_category(client, make_user, dynamodb_table):
    await make_user("analyst@panasa.com", "pw12345", Role.ANALYST)
    token = await _login(client, "analyst@panasa.com", "pw12345")

    response = await client.get(
        "/api/v1/templates", params={"category": "hr"}, headers=auth_headers(token)
    )

    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["template_id"] == "hr-assistant-v1"


async def test_get_template_by_id(client, make_user, dynamodb_table):
    await make_user("analyst@panasa.com", "pw12345", Role.ANALYST)
    token = await _login(client, "analyst@panasa.com", "pw12345")

    response = await client.get("/api/v1/templates/code-review-v1", headers=auth_headers(token))

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Code Review Agent"
    assert body["suggested_model"]["model_id"]


async def test_get_template_not_found(client, make_user, dynamodb_table):
    await make_user("analyst@panasa.com", "pw12345", Role.ANALYST)
    token = await _login(client, "analyst@panasa.com", "pw12345")

    response = await client.get("/api/v1/templates/does-not-exist", headers=auth_headers(token))

    assert response.status_code == 404


async def test_create_agent_from_template(client, make_user, dynamodb_table):
    await make_user("dev@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    token = await _login(client, "dev@panasa.com", "pw12345")

    response = await client.post(
        "/api/v1/agents/from-template/hr-assistant-v1", headers=auth_headers(token)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["tenant_id"] == "tenant-a"
    assert body["template_id"] == "hr-assistant-v1"
    assert body["name"] == "HR Assistant"
    assert body["guardrail_config"]["pii_action"] == "block"
    assert body["status"] == "draft"


async def test_create_agent_from_template_forbidden_for_analyst(client, make_user, dynamodb_table):
    await make_user("analyst@panasa.com", "pw12345", Role.ANALYST, tenant_id="tenant-a")
    token = await _login(client, "analyst@panasa.com", "pw12345")

    response = await client.post(
        "/api/v1/agents/from-template/hr-assistant-v1", headers=auth_headers(token)
    )

    assert response.status_code == 403


async def test_create_agent_from_unknown_template(client, make_user, dynamodb_table):
    await make_user("dev@panasa.com", "pw12345", Role.DEVELOPER, tenant_id="tenant-a")
    token = await _login(client, "dev@panasa.com", "pw12345")

    response = await client.post(
        "/api/v1/agents/from-template/does-not-exist", headers=auth_headers(token)
    )

    assert response.status_code == 404
