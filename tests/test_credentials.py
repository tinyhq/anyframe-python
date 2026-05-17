"""Tests for the credentials resource."""

from __future__ import annotations

import httpx
import pytest
import respx

import anyframe
from tests.conftest import BASE_URL


@respx.mock
def test_get_returns_credentials_model(client):
    respx.get(f"{BASE_URL}/api/credentials").mock(
        return_value=httpx.Response(
            200,
            json={
                "claude": {"set": True, "last4": "wxyz", "updated_at": "2025-01-01T00:00:00Z"},
                "codex": {"set": False, "last4": None, "updated_at": None},
                "github": {"set": False, "last4": None, "updated_at": None},
            },
        )
    )
    creds = client.credentials.get()
    assert isinstance(creds, anyframe.Credentials)
    assert creds.claude.set is True


@respx.mock
@pytest.mark.parametrize("which", ["claude", "codex", "github"])
def test_set_token_routes_to_correct_endpoint(client, which):
    route = respx.put(f"{BASE_URL}/api/credentials/{which}").mock(return_value=httpx.Response(204))
    getattr(client.credentials, f"set_{which}")("the-token")
    assert route.called
    assert route.calls.last.request.read() == b'{"token":"the-token"}'


@respx.mock
@pytest.mark.parametrize("which", ["claude", "codex", "github"])
def test_clear_token_sends_delete(client, which):
    route = respx.delete(f"{BASE_URL}/api/credentials/{which}").mock(
        return_value=httpx.Response(204)
    )
    getattr(client.credentials, f"clear_{which}")()
    assert route.called
