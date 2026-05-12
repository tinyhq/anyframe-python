"""Tests for the agent sub-resources: skills, mcps, connector toggles."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

import anyframe
from tests.conftest import BASE_URL

SKILL = {
    "id": 1,
    "name": "deploy",
    "source": "builtin",
    "content": {},
    "enabled": True,
    "created_at": "2025-01-01T00:00:00Z",
}

MCP = {
    "id": 1,
    "name": "git",
    "transport": "http",
    "config": {"url": "x"},
    "secret_ref": None,
    "enabled": True,
    "created_at": "2025-01-01T00:00:00Z",
}

TOGGLE = {
    "connector_id": 1,
    "display_name": "Linear",
    "mcp_url": "https://mcp.linear.app/sse",
    "auth_kind": "oauth_dcr",
    "enabled": True,
    "is_authorized": True,
}


# ── skills ────────────────────────────────────────────────────────────────


@respx.mock
def test_skills_list(client):
    respx.get(f"{BASE_URL}/api/agents/7/skills").mock(
        return_value=httpx.Response(200, json=[SKILL])
    )
    skills = client.agents.skills.list(7)
    assert isinstance(skills[0], anyframe.AgentSkill)


@respx.mock
def test_skills_create(client):
    route = respx.post(f"{BASE_URL}/api/agents/7/skills").mock(
        return_value=httpx.Response(201, json=SKILL)
    )
    skill = client.agents.skills.create(
        7, name="deploy", source="builtin", content={"x": 1}, enabled=False
    )
    body = json.loads(route.calls.last.request.read())
    assert body == {"name": "deploy", "source": "builtin", "content": {"x": 1}, "enabled": False}
    assert skill.name == "deploy"


@respx.mock
def test_skills_update_partial(client):
    """PATCH must only send the fields the caller actually wants to change."""
    respx.patch(f"{BASE_URL}/api/agents/7/skills/1").mock(
        return_value=httpx.Response(200, json=SKILL)
    )
    client.agents.skills.update(7, 1, enabled=False)
    sent = json.loads(respx.calls.last.request.read())
    assert sent == {"enabled": False}


@respx.mock
def test_skills_delete(client):
    route = respx.delete(f"{BASE_URL}/api/agents/7/skills/1").mock(return_value=httpx.Response(204))
    client.agents.skills.delete(7, 1)
    assert route.called


# ── mcps ──────────────────────────────────────────────────────────────────


@respx.mock
def test_mcps_create(client):
    route = respx.post(f"{BASE_URL}/api/agents/7/mcps").mock(
        return_value=httpx.Response(201, json=MCP)
    )
    mcp = client.agents.mcps.create(7, name="git", transport="http", config={"url": "x"})
    body = json.loads(route.calls.last.request.read())
    assert body["transport"] == "http"
    assert mcp.transport == "http"


@respx.mock
def test_mcps_update_drops_unspecified(client):
    respx.patch(f"{BASE_URL}/api/agents/7/mcps/1").mock(return_value=httpx.Response(200, json=MCP))
    client.agents.mcps.update(7, 1, name="renamed")
    assert json.loads(respx.calls.last.request.read()) == {"name": "renamed"}


@respx.mock
def test_mcps_delete(client):
    respx.delete(f"{BASE_URL}/api/agents/7/mcps/1").mock(return_value=httpx.Response(204))
    client.agents.mcps.delete(7, 1)


# ── connector toggles ─────────────────────────────────────────────────────


@respx.mock
def test_connector_toggle_list(client):
    respx.get(f"{BASE_URL}/api/agents/7/connectors").mock(
        return_value=httpx.Response(200, json=[TOGGLE])
    )
    rows = client.agents.connectors.list(7)
    assert rows[0].enabled is True


@respx.mock
def test_connector_toggle_set(client):
    route = respx.put(f"{BASE_URL}/api/agents/7/connectors/1").mock(
        return_value=httpx.Response(200, json=TOGGLE)
    )
    client.agents.connectors.set(7, 1, enabled=True)
    assert json.loads(route.calls.last.request.read()) == {"enabled": True}


@respx.mock
def test_skill_not_found_propagates(client):
    respx.delete(f"{BASE_URL}/api/agents/7/skills/99").mock(
        return_value=httpx.Response(404, json={"detail": "skill gone"})
    )
    with pytest.raises(anyframe.NotFoundError):
        client.agents.skills.delete(7, 99)
