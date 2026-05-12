"""Tests for the user-level connectors resource."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

import anyframe
from tests.conftest import BASE_URL

CONNECTOR = {
    "id": 1,
    "display_name": "Linear",
    "mcp_url": "https://mcp.linear.app/sse",
    "transport": "http",
    "auth_kind": "oauth_dcr",
    "secret_last4": None,
    "expires_at": None,
    "scopes": None,
    "is_authorized": True,
    "last_refresh_attempt_at": None,
    "last_refresh_error": None,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
}


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
    assert body == {"mcp_url": "https://mcp.example.com", "display_name": "Example"}


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
