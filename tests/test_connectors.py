"""Tests for the user-level connectors resource."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

import anyframe
from tests.conftest import BASE_URL
from tests.payloads import CONNECTOR


@respx.mock
def test_list(client):
    respx.get(f"{BASE_URL}/api/connectors").mock(return_value=httpx.Response(200, json=[CONNECTOR]))
    rows = client.connectors.list()
    assert isinstance(rows[0], anyframe.Connector)
    assert rows[0].is_authorized is True


@respx.mock
def test_discover(client):
    route = respx.post(f"{BASE_URL}/api/connectors/discover").mock(
        return_value=httpx.Response(
            200,
            json={
                "mcp_url": "https://mcp.example.com",
                "supports_dcr": True,
                "suggested_display_name": "Example",
                "authorization_endpoint": "https://auth.example.com/authorize",
                "token_endpoint": "https://auth.example.com/token",
                "scopes_supported": ["read", "write"],
            },
        )
    )
    d = client.connectors.discover("https://mcp.example.com")
    assert d.supports_dcr is True
    assert json.loads(route.calls.last.request.read()) == {"mcp_url": "https://mcp.example.com"}


@respx.mock
def test_create_oauth_returns_authorize_url(client):
    route = respx.post(f"{BASE_URL}/api/connectors/oauth").mock(
        return_value=httpx.Response(
            200,
            json={
                "connector_id": 1,
                "authorize_url": "https://auth.example.com/authorize?...",
                "state": "abcd",
            },
        )
    )
    out = client.connectors.create_oauth(mcp_url="https://mcp.example.com", display_name="Example")
    assert "authorize" in out.authorize_url
    body = json.loads(route.calls.last.request.read())
    assert body == {
        "mcp_url": "https://mcp.example.com",
        "display_name": "Example",
        "default_enabled": True,
    }


@respx.mock
def test_create_bearer(client):
    respx.post(f"{BASE_URL}/api/connectors/bearer").mock(
        return_value=httpx.Response(200, json=CONNECTOR)
    )
    out = client.connectors.create_bearer(
        mcp_url="https://mcp.example.com", display_name="Ex", token="t"
    )
    assert isinstance(out, anyframe.Connector)


@respx.mock
def test_reauthorize(client):
    respx.post(f"{BASE_URL}/api/connectors/1/reauthorize").mock(
        return_value=httpx.Response(
            200, json={"connector_id": 1, "authorize_url": "https://x", "state": "s"}
        )
    )
    out = client.connectors.reauthorize(1)
    assert out.state == "s"


@respx.mock
def test_delete(client):
    route = respx.delete(f"{BASE_URL}/api/connectors/1").mock(return_value=httpx.Response(204))
    client.connectors.delete(1)
    assert route.called


@respx.mock
def test_create_oauth_conflict_propagates(client):
    respx.post(f"{BASE_URL}/api/connectors/oauth").mock(
        return_value=httpx.Response(409, json={"detail": "already exists"})
    )
    with pytest.raises(anyframe.ConflictError):
        client.connectors.create_oauth(mcp_url="x", display_name="y")


@respx.mock
def test_create_custom_header(client):
    """v2 adds custom-header auth — header_name lets you target X-API-Key etc."""
    route = respx.post(f"{BASE_URL}/api/connectors/custom-header").mock(
        return_value=httpx.Response(
            200,
            json=CONNECTOR | {"auth_kind": "custom_header"},
        ),
    )
    out = client.connectors.create_custom_header(
        mcp_url="https://mcp.example.com",
        display_name="Ex",
        header_name="X-API-Key",
        token="t",
    )
    assert out.auth_kind == "custom_header"
    body = json.loads(route.calls.last.request.read())
    assert body == {
        "mcp_url": "https://mcp.example.com",
        "display_name": "Ex",
        "header_name": "X-API-Key",
        "token": "t",
        "default_enabled": True,
    }


@respx.mock
def test_create_stdio_defaults_args_and_env(client):
    """v2 adds stdio connectors — args + env are optional, the SDK fills empties."""
    route = respx.post(f"{BASE_URL}/api/connectors/stdio").mock(
        return_value=httpx.Response(
            200,
            json=CONNECTOR | {"auth_kind": "stdio", "transport": "stdio"},
        ),
    )
    client.connectors.create_stdio(display_name="local-mcp", command="my-mcp")
    body = json.loads(route.calls.last.request.read())
    assert body["command"] == "my-mcp"
    assert body["args"] == []
    assert body["env"] == {}
