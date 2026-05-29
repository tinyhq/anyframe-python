"""Tests for the templates resource and its nested sub-resources."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

import anyframe
from tests.conftest import BASE_URL
from tests.payloads import (
    TEMPLATE,
    TEMPLATE_CONNECTOR,
    TEMPLATE_DETAIL,
    TEMPLATE_MCP,
    TEMPLATE_SKILL,
)

# ── Templates CRUD ─────────────────────────────────────────────────────────


@respx.mock
def test_list_templates(client):
    respx.get(f"{BASE_URL}/api/templates").mock(
        return_value=httpx.Response(200, json=[TEMPLATE]),
    )
    rows = client.templates.list()
    assert isinstance(rows[0], anyframe.Template)


@respx.mock
def test_create_template_sends_only_provided_fields(client):
    route = respx.post(f"{BASE_URL}/api/templates").mock(
        return_value=httpx.Response(201, json=TEMPLATE_DETAIL),
    )
    client.templates.create(
        name="web-stack",
        repo_url="tinyhq/box",
        install_cmd="bun install",
        install_id=11,
    )
    body = json.loads(route.calls.last.request.read())
    assert body == {
        "name": "web-stack",
        "repo_url": "tinyhq/box",
        "install_cmd": "bun install",
        "install_id": 11,
    }


@respx.mock
def test_get_template_returns_detail(client):
    respx.get(f"{BASE_URL}/api/templates/4").mock(
        return_value=httpx.Response(200, json=TEMPLATE_DETAIL),
    )
    t = client.templates.get(4)
    assert isinstance(t, anyframe.TemplateDetail)
    assert t.agent_count == 1


@respx.mock
def test_update_template_uses_patch(client):
    route = respx.patch(f"{BASE_URL}/api/templates/4").mock(
        return_value=httpx.Response(200, json=TEMPLATE_DETAIL),
    )
    client.templates.update(4, system_prompt="new")
    assert json.loads(route.calls.last.request.read()) == {"system_prompt": "new"}


@respx.mock
def test_delete_template(client):
    route = respx.delete(f"{BASE_URL}/api/templates/4").mock(
        return_value=httpx.Response(204),
    )
    client.templates.delete(4)
    assert route.called


@respx.mock
def test_delete_template_conflict_when_agents_bound(client):
    respx.delete(f"{BASE_URL}/api/templates/4").mock(
        return_value=httpx.Response(409, json={"detail": "1 agent(s) bound"}),
    )
    with pytest.raises(anyframe.ConflictError):
        client.templates.delete(4)


# ── Skills ─────────────────────────────────────────────────────────────────


@respx.mock
def test_skills_list_and_create(client):
    respx.get(f"{BASE_URL}/api/templates/4/skills").mock(
        return_value=httpx.Response(200, json=[TEMPLATE_SKILL]),
    )
    rows = client.templates.skills.list(4)
    assert rows[0].name == "deploy"

    route = respx.post(f"{BASE_URL}/api/templates/4/skills").mock(
        return_value=httpx.Response(201, json=TEMPLATE_SKILL),
    )
    client.templates.skills.create(
        4,
        name="deploy",
        source="inline",
        content={"body": "…"},
    )
    body = json.loads(route.calls.last.request.read())
    assert body["source"] == "inline"
    assert body["enabled"] is True


@respx.mock
def test_skills_update_drops_unspecified(client):
    route = respx.patch(f"{BASE_URL}/api/templates/4/skills/1").mock(
        return_value=httpx.Response(200, json=TEMPLATE_SKILL),
    )
    client.templates.skills.update(4, 1, enabled=False)
    body = json.loads(route.calls.last.request.read())
    assert body == {"enabled": False}


@respx.mock
def test_skills_delete(client):
    route = respx.delete(f"{BASE_URL}/api/templates/4/skills/1").mock(
        return_value=httpx.Response(204),
    )
    client.templates.skills.delete(4, 1)
    assert route.called


# ── MCPs ───────────────────────────────────────────────────────────────────


@respx.mock
def test_mcps_create(client):
    route = respx.post(f"{BASE_URL}/api/templates/4/mcps").mock(
        return_value=httpx.Response(201, json=TEMPLATE_MCP),
    )
    client.templates.mcps.create(
        4,
        name="git",
        transport="http",
        config={"url": "https://x"},
    )
    body = json.loads(route.calls.last.request.read())
    assert body["transport"] == "http"


@respx.mock
def test_mcps_update(client):
    route = respx.patch(f"{BASE_URL}/api/templates/4/mcps/1").mock(
        return_value=httpx.Response(200, json=TEMPLATE_MCP),
    )
    client.templates.mcps.update(4, 1, enabled=False)
    body = json.loads(route.calls.last.request.read())
    assert body == {"enabled": False}


@respx.mock
def test_mcps_delete(client):
    route = respx.delete(f"{BASE_URL}/api/templates/4/mcps/1").mock(
        return_value=httpx.Response(204),
    )
    client.templates.mcps.delete(4, 1)
    assert route.called


# ── Connector toggles ──────────────────────────────────────────────────────


@respx.mock
def test_connector_toggle_list(client):
    respx.get(f"{BASE_URL}/api/templates/4/connectors").mock(
        return_value=httpx.Response(200, json=[TEMPLATE_CONNECTOR]),
    )
    rows = client.templates.connectors.list(4)
    assert rows[0].enabled is True


@respx.mock
def test_connector_toggle_set(client):
    route = respx.put(f"{BASE_URL}/api/templates/4/connectors/1").mock(
        return_value=httpx.Response(200, json=TEMPLATE_CONNECTOR),
    )
    out = client.templates.connectors.set(4, 1, enabled=False)
    assert out.enabled is True  # the mock returns the canonical row
    assert json.loads(route.calls.last.request.read()) == {"enabled": False}
