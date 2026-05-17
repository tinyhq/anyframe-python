"""Tests for the connector catalog endpoints."""

from __future__ import annotations

import json

import httpx
import respx

import anyframe
from tests.conftest import BASE_URL

CATALOG_ITEM = {
    "slug": "linear",
    "display_name": "Linear",
    "category": "issue-tracking",
    "description": "Linear's MCP server.",
    "mcp_url": "https://mcp.linear.app/sse",
    "transport": "http",
    "setup_kind": "oauth_dcr",
    "publisher": "linear",
    "trust_level": "official",
    "docs_url": "https://anyfrm.com/docs/connectors/linear",
    "tags": ["issues", "projects"],
    "has_logo": True,
    "coming_soon": False,
    "installed": False,
    "connector_id": None,
    "is_authorized": None,
}


CONNECTOR_ROW = {
    "id": 9,
    "display_name": "Linear",
    "mcp_url": "https://mcp.linear.app/sse",
    "catalog_slug": "linear",
    "default_enabled": False,
    "transport": "http",
    "auth_kind": "bearer_token",
    "secret_last4": "wxyz",
    "expires_at": None,
    "scopes": None,
    "is_authorized": True,
    "last_refresh_attempt_at": None,
    "last_refresh_error": None,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
}


AUTHORIZE_OUT = {
    "connector_id": 9,
    "authorize_url": "https://auth.example.com/authorize?...",
    "state": "abcd1234",
}


@respx.mock
def test_list_catalog(client):
    respx.get(f"{BASE_URL}/api/connectors/catalog").mock(
        return_value=httpx.Response(200, json=[CATALOG_ITEM])
    )
    items = client.connectors.list_catalog()
    assert isinstance(items[0], anyframe.ConnectorCatalogItem)
    assert items[0].slug == "linear"
    assert items[0].setup_kind == "oauth_dcr"


@respx.mock
def test_install_catalog_oauth(client):
    route = respx.post(f"{BASE_URL}/api/connectors/catalog/linear/oauth").mock(
        return_value=httpx.Response(200, json=AUTHORIZE_OUT)
    )
    out = client.connectors.install_catalog_oauth("linear")
    assert route.called
    assert isinstance(out, anyframe.ConnectorAuthorize)
    assert out.authorize_url.startswith("https://auth.example.com/")


@respx.mock
def test_install_catalog_bearer(client):
    route = respx.post(f"{BASE_URL}/api/connectors/catalog/linear/bearer").mock(
        return_value=httpx.Response(200, json=CONNECTOR_ROW)
    )
    out = client.connectors.install_catalog_bearer("linear", token="lin_secret")
    assert route.called
    assert json.loads(route.calls.last.request.read()) == {"token": "lin_secret"}
    assert isinstance(out, anyframe.Connector)
    assert out.catalog_slug == "linear"
    assert out.auth_kind == "bearer_token"


@respx.mock
def test_create_oauth_sends_default_enabled(client):
    """The ``default_enabled`` kwarg is forwarded — defaults to True."""
    route = respx.post(f"{BASE_URL}/api/connectors/oauth").mock(
        return_value=httpx.Response(200, json=AUTHORIZE_OUT)
    )
    client.connectors.create_oauth(
        mcp_url="https://mcp.example.com", display_name="Example", default_enabled=False
    )
    body = json.loads(route.calls.last.request.read())
    assert body == {
        "mcp_url": "https://mcp.example.com",
        "display_name": "Example",
        "default_enabled": False,
    }
