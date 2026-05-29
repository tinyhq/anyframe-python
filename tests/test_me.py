"""Tests for /api/me, /api/me/active_org, and /api/config/public."""

from __future__ import annotations

import json

import httpx
import respx

import anyframe
from tests.conftest import BASE_URL
from tests.payloads import ME_WITH_ORGS, PUBLIC_CONFIG


@respx.mock
def test_me_returns_hydrated_user(client):
    respx.get(f"{BASE_URL}/api/me").mock(
        return_value=httpx.Response(200, json=ME_WITH_ORGS),
    )
    user = client.me()
    assert isinstance(user, anyframe.User)
    assert user.active_org_id == 100
    assert user.memberships and user.memberships[0].role == "owner"


@respx.mock
def test_set_active_org_to_org(client):
    route = respx.post(f"{BASE_URL}/api/me/active_org").mock(
        return_value=httpx.Response(200, json=ME_WITH_ORGS),
    )
    user = client.set_active_org(100)
    assert user.active_org_id == 100
    assert json.loads(route.calls.last.request.read()) == {"org_id": 100}


@respx.mock
def test_set_active_org_to_personal(client):
    """None switches back to personal scope; the SDK must send {"org_id": null}."""
    route = respx.post(f"{BASE_URL}/api/me/active_org").mock(
        return_value=httpx.Response(200, json=ME_WITH_ORGS | {"active_org_id": None}),
    )
    user = client.set_active_org(None)
    assert user.active_org_id is None
    assert json.loads(route.calls.last.request.read()) == {"org_id": None}


@respx.mock
def test_public_config(client):
    respx.get(f"{BASE_URL}/api/config/public").mock(
        return_value=httpx.Response(200, json=PUBLIC_CONFIG),
    )
    cfg = client.public_config()
    assert isinstance(cfg, anyframe.PublicConfig)
    assert cfg.google_enabled is True
