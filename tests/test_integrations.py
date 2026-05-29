"""Tests for the integrations resource."""

from __future__ import annotations

import json

import httpx
import respx

import anyframe
from tests.conftest import BASE_URL
from tests.payloads import (
    GITHUB_INSTALL,
    GITHUB_REPO,
    INTEGRATION_BINDING,
    INTEGRATION_INSTALL,
    PROVIDER_APP,
)


@respx.mock
def test_list_installs(client):
    respx.get(f"{BASE_URL}/api/integrations").mock(
        return_value=httpx.Response(200, json=[INTEGRATION_INSTALL]),
    )
    rows = client.integrations.list()
    assert isinstance(rows[0], anyframe.IntegrationInstall)
    assert rows[0].provider == "github"


@respx.mock
def test_delete_install(client):
    route = respx.delete(f"{BASE_URL}/api/integrations/22").mock(
        return_value=httpx.Response(204),
    )
    client.integrations.delete(22)
    assert route.called


@respx.mock
def test_list_github_installs(client):
    respx.get(f"{BASE_URL}/api/integrations/github/installs").mock(
        return_value=httpx.Response(200, json=[GITHUB_INSTALL]),
    )
    rows = client.integrations.list_github_installs()
    assert rows[0].account_login == "tinyhq"


@respx.mock
def test_list_github_repos(client):
    respx.get(f"{BASE_URL}/api/integrations/github/installs/22/repos").mock(
        return_value=httpx.Response(200, json=[GITHUB_REPO]),
    )
    rows = client.integrations.list_github_repos(22)
    assert rows[0].full_name == "tinyhq/box"
    assert rows[0].private is True


@respx.mock
def test_set_binding(client):
    route = respx.post(f"{BASE_URL}/api/integrations/22/binding").mock(
        return_value=httpx.Response(201, json=INTEGRATION_BINDING),
    )
    out = client.integrations.set_binding(22, agent_id=7)
    assert out.agent_id == 7
    assert json.loads(route.calls.last.request.read()) == {"agent_id": 7}


@respx.mock
def test_delete_binding(client):
    route = respx.delete(f"{BASE_URL}/api/integrations/22/binding").mock(
        return_value=httpx.Response(204),
    )
    client.integrations.delete_binding(22)
    assert route.called


@respx.mock
def test_list_provider_apps(client):
    respx.get(f"{BASE_URL}/api/integrations/provider_apps").mock(
        return_value=httpx.Response(200, json=[PROVIDER_APP]),
    )
    rows = client.integrations.list_provider_apps()
    assert rows[0].provider == "github"
    assert rows[0].is_draft is False
