"""Tests for the agents CRUD surface (excluding sub-resources)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

import anyframe
from tests.conftest import BASE_URL

AGENT_PAYLOAD = {
    "id": 7,
    "name": "demo",
    "description": None,
    "system_prompt": None,
    "repo_url": "tinyhq/box",
    "repo_ref": "main",
    "install_cmd": "bun install",
    "serve_cmd": None,
    "preview_ports": [3000],
    "build_key": "abc",
    "permissions": {"preset": "standard"},
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
}


@respx.mock
def test_list_agents(client):
    respx.get(f"{BASE_URL}/api/agents").mock(return_value=httpx.Response(200, json=[AGENT_PAYLOAD]))
    agents = client.agents.list()
    assert len(agents) == 1
    assert isinstance(agents[0], anyframe.Agent)
    assert agents[0].id == 7


@respx.mock
def test_create_sends_only_provided_fields(client):
    """We don't want to spam the wire with `null` for every optional field —
    the server interprets that differently from `omit`. Only the args the
    caller passes (plus their defaults) should land in the JSON body."""
    route = respx.post(f"{BASE_URL}/api/agents").mock(
        return_value=httpx.Response(201, json=AGENT_PAYLOAD)
    )
    client.agents.create(name="demo", repo_url="tinyhq/box", install_cmd="bun install")
    sent = json.loads(route.calls.last.request.read())
    assert sent["name"] == "demo"
    assert sent["repo_url"] == "tinyhq/box"
    assert sent["install_cmd"] == "bun install"
    # Optional fields the user didn't pass must not appear in the body.
    assert "description" not in sent
    assert "system_prompt" not in sent
    assert "serve_cmd" not in sent


@respx.mock
def test_create_accepts_permissions(client):
    route = respx.post(f"{BASE_URL}/api/agents").mock(
        return_value=httpx.Response(201, json=AGENT_PAYLOAD)
    )
    client.agents.create(name="demo", permissions={"preset": "full_trust"})
    sent = json.loads(route.calls.last.request.read())
    assert sent["permissions"] == {"preset": "full_trust"}


@respx.mock
def test_get_returns_detail(client):
    detail = AGENT_PAYLOAD | {"skills": [], "mcps": [], "connectors": [], "image": None}
    respx.get(f"{BASE_URL}/api/agents/7").mock(return_value=httpx.Response(200, json=detail))
    agent = client.agents.get(7)
    assert isinstance(agent, anyframe.AgentDetail)
    assert agent.image is None


@respx.mock
def test_update_uses_patch(client):
    detail = AGENT_PAYLOAD | {"skills": [], "mcps": [], "connectors": [], "image": None}
    route = respx.patch(f"{BASE_URL}/api/agents/7").mock(
        return_value=httpx.Response(200, json=detail)
    )
    client.agents.update(7, name="renamed")
    assert route.called
    sent = json.loads(route.calls.last.request.read())
    assert sent == {"name": "renamed"}


@respx.mock
def test_delete_sends_delete(client):
    route = respx.delete(f"{BASE_URL}/api/agents/7").mock(return_value=httpx.Response(204))
    client.agents.delete(7)
    assert route.called


@respx.mock
def test_create_404_translates(client):
    respx.post(f"{BASE_URL}/api/agents").mock(
        return_value=httpx.Response(422, json={"detail": "name required"})
    )
    with pytest.raises(anyframe.ValidationError):
        client.agents.create(name="")
