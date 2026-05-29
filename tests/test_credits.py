"""Tests for the credits resource."""

from __future__ import annotations

import httpx
import respx

import anyframe
from tests.conftest import BASE_URL
from tests.payloads import CREDITS


@respx.mock
def test_get_returns_balance(client):
    respx.get(f"{BASE_URL}/api/credits").mock(
        return_value=httpx.Response(200, json=CREDITS),
    )
    bal = client.credits.get()
    assert isinstance(bal, anyframe.CreditBalance)
    assert bal.remaining == 750
    assert bal.scope == "personal"


@respx.mock
def test_get_reports_org_scope(client):
    respx.get(f"{BASE_URL}/api/credits").mock(
        return_value=httpx.Response(
            200,
            json=CREDITS | {"scope": "org", "org_token_active": True},
        ),
    )
    bal = client.credits.get()
    assert bal.scope == "org"
    assert bal.org_token_active is True
