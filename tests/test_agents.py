"""Tests for the v2 agents CRUD surface.

Sub-resources (skills, mcps, connector toggles) moved to ``af.templates``
in v2 — see ``test_templates.py``. Build orchestration tests live in
``test_builds.py``.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

import anyframe
from tests.conftest import BASE_URL
from tests.payloads import AGENT, AGENT_DETAIL


@respx.mock
def test_list_agents(client):
    respx.get(f"{BASE_URL}/api/agents").mock(
        return_value=httpx.Response(200, json=[AGENT]),
    )
    agents = client.agents.list()
    assert len(agents) == 1
    assert isinstance(agents[0], anyframe.Agent)
    assert agents[0].template_id == 4
    assert agents[0].runtime == "claude"


@respx.mock
def test_create_requires_template_id(client):
    """v2 agents bind to a template — name + template_id are the minimum."""
    route = respx.post(f"{BASE_URL}/api/agents").mock(
        return_value=httpx.Response(201, json=AGENT_DETAIL),
    )
    agent = client.agents.create(name="demo", template_id=4)
    assert isinstance(agent, anyframe.AgentDetail)
    assert agent.template.id == 4
    body = json.loads(route.calls.last.request.read())
    # Optional fields the caller didn't pass must not appear on the wire —
    # the server distinguishes "omit" from "explicit null" for overrides.
    assert body == {"name": "demo", "template_id": 4}


@respx.mock
def test_create_passes_overrides(client):
    route = respx.post(f"{BASE_URL}/api/agents").mock(
        return_value=httpx.Response(201, json=AGENT_DETAIL),
    )
    client.agents.create(
        name="prod-bot",
        template_id=4,
        runtime="codex",
        permissions_override={"preset": "full_trust"},
        env_vars_override={"API_KEY": "shh"},
    )
    body = json.loads(route.calls.last.request.read())
    assert body["runtime"] == "codex"
    assert body["permissions_override"] == {"preset": "full_trust"}
    assert body["env_vars_override"] == {"API_KEY": "shh"}


@respx.mock
def test_get_returns_detail_with_template_embedded(client):
    respx.get(f"{BASE_URL}/api/agents/7").mock(
        return_value=httpx.Response(200, json=AGENT_DETAIL),
    )
    agent = client.agents.get(7)
    assert isinstance(agent, anyframe.AgentDetail)
    assert agent.template.repo_url == "tinyhq/box"


@respx.mock
def test_update_sends_only_fields_passed(client):
    route = respx.patch(f"{BASE_URL}/api/agents/7").mock(
        return_value=httpx.Response(200, json=AGENT_DETAIL),
    )
    client.agents.update(7, name="renamed")
    assert json.loads(route.calls.last.request.read()) == {"name": "renamed"}


@respx.mock
def test_update_can_clear_permissions_override(client):
    """Pass ``permissions_override=None`` to fall back to the template."""
    route = respx.patch(f"{BASE_URL}/api/agents/7").mock(
        return_value=httpx.Response(200, json=AGENT_DETAIL),
    )
    client.agents.update(7, permissions_override=None)
    body = json.loads(route.calls.last.request.read())
    assert body == {"permissions_override": None}


@respx.mock
def test_delete_sends_delete(client):
    route = respx.delete(f"{BASE_URL}/api/agents/7").mock(
        return_value=httpx.Response(204),
    )
    client.agents.delete(7)
    assert route.called


@respx.mock
def test_create_validation_error_translates(client):
    respx.post(f"{BASE_URL}/api/agents").mock(
        return_value=httpx.Response(422, json={"detail": "template_id required"}),
    )
    with pytest.raises(anyframe.ValidationError):
        client.agents.create(name="x", template_id=0)
