"""Tests for the personal credentials resource."""

from __future__ import annotations

import httpx
import pytest
import respx

import anyframe
from tests.conftest import BASE_URL
from tests.payloads import CREDENTIALS


@respx.mock
def test_get_returns_credentials_model(client):
    respx.get(f"{BASE_URL}/api/credentials").mock(
        return_value=httpx.Response(200, json=CREDENTIALS),
    )
    creds = client.credentials.get()
    assert isinstance(creds, anyframe.Credentials)
    assert creds.claude.set is True
    assert creds.codex.set is False


@respx.mock
@pytest.mark.parametrize("which", ["claude", "codex"])
def test_set_token_routes_to_correct_endpoint(client, which):
    route = respx.put(f"{BASE_URL}/api/credentials/{which}").mock(
        return_value=httpx.Response(204),
    )
    getattr(client.credentials, f"set_{which}")("the-token")
    assert route.called
    assert route.calls.last.request.read() == b'{"token":"the-token"}'


@respx.mock
@pytest.mark.parametrize("which", ["claude", "codex"])
def test_clear_token_sends_delete(client, which):
    route = respx.delete(f"{BASE_URL}/api/credentials/{which}").mock(
        return_value=httpx.Response(204),
    )
    getattr(client.credentials, f"clear_{which}")()
    assert route.called


def test_github_credential_methods_are_gone():
    """v2 ripped /api/credentials/github out — GitHub access is now an
    Integration install. Catch any accidental re-add of the obsolete methods."""
    import anyframe as af

    creds_cls = af.AnyFrame.__init__.__globals__["Credentials"]
    for attr in ("set_github", "clear_github"):
        assert not hasattr(creds_cls, attr), f"obsolete method {attr} re-introduced"
