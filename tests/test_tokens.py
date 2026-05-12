"""Tests for the tokens resource."""

from __future__ import annotations

import httpx
import pytest
import respx

import anyframe
from tests.conftest import BASE_URL


@respx.mock
def test_list_returns_token_models(client):
    respx.get(f"{BASE_URL}/api/tokens").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": 1,
                    "name": "ci",
                    "prefix": "afm_abcd",
                    "last4": "wxyz",
                    "created_at": "2025-01-01T00:00:00Z",
                    "revoked_at": None,
                }
            ],
        )
    )
    tokens = client.tokens.list()
    assert len(tokens) == 1
    assert isinstance(tokens[0], anyframe.Token)
    assert tokens[0].prefix == "afm_abcd"


@respx.mock
def test_create_returns_raw_token(client):
    route = respx.post(f"{BASE_URL}/api/tokens").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": 1,
                "name": "ci",
                "prefix": "afm_abcd",
                "last4": "wxyz",
                "created_at": "2025-01-01T00:00:00Z",
                "revoked_at": None,
                "token": "afm_secret",
            },
        )
    )
    created = client.tokens.create(name="ci")
    assert created.token == "afm_secret"
    assert route.calls.last.request.read() == b'{"name":"ci"}'


@respx.mock
def test_revoke_sends_delete(client):
    route = respx.delete(f"{BASE_URL}/api/tokens/3").mock(return_value=httpx.Response(204))
    client.tokens.revoke(3)
    assert route.called


@respx.mock
def test_create_validation_error_propagates(client):
    respx.post(f"{BASE_URL}/api/tokens").mock(
        return_value=httpx.Response(422, json={"detail": "name required"})
    )
    with pytest.raises(anyframe.ValidationError):
        client.tokens.create(name="")
