"""Tests for the org-collab endpoints on sessions."""

from __future__ import annotations

import json

import httpx
import respx

import anyframe
from tests.conftest import BASE_URL
from tests.payloads import PRESENCE_USER

SESSION_ID = "00000000-0000-0000-0000-000000000001"


@respx.mock
def test_presence(client):
    respx.get(f"{BASE_URL}/api/sessions/{SESSION_ID}/presence").mock(
        return_value=httpx.Response(200, json=[PRESENCE_USER]),
    )
    rows = client.sessions.presence(SESSION_ID)
    assert isinstance(rows[0], anyframe.PresenceUser)
    assert rows[0].is_driver is True


@respx.mock
def test_request_control_with_message(client):
    route = respx.post(f"{BASE_URL}/api/sessions/{SESSION_ID}/request_control").mock(
        return_value=httpx.Response(201, json={"id": 42, "status": "pending"}),
    )
    out = client.sessions.request_control(SESSION_ID, message="taking over deploy")
    assert out.id == 42
    body = json.loads(route.calls.last.request.read())
    assert body == {"message": "taking over deploy"}


@respx.mock
def test_request_control_without_message(client):
    """Optional message; SDK must not send an empty body."""
    respx.post(f"{BASE_URL}/api/sessions/{SESSION_ID}/request_control").mock(
        return_value=httpx.Response(201, json={"id": 1, "status": "pending"}),
    )
    out = client.sessions.request_control(SESSION_ID)
    assert out.status == "pending"


@respx.mock
def test_handoff_with_request_id(client):
    route = respx.post(f"{BASE_URL}/api/sessions/{SESSION_ID}/handoff").mock(
        return_value=httpx.Response(200, json={"driver_user_id": 5}),
    )
    out = client.sessions.handoff(SESSION_ID, to_user_id=5, request_id=42)
    assert out.driver_user_id == 5
    body = json.loads(route.calls.last.request.read())
    assert body == {"to_user_id": 5, "request_id": 42}


@respx.mock
def test_take_over(client):
    respx.post(f"{BASE_URL}/api/sessions/{SESSION_ID}/take_over").mock(
        return_value=httpx.Response(200, json={"driver_user_id": 9}),
    )
    out = client.sessions.take_over(SESSION_ID)
    assert out.driver_user_id == 9


@respx.mock
def test_set_privacy(client):
    route = respx.post(f"{BASE_URL}/api/sessions/{SESSION_ID}/privacy").mock(
        return_value=httpx.Response(200, json={"private": True}),
    )
    out = client.sessions.set_privacy(SESSION_ID, private=True)
    assert out.private is True
    assert json.loads(route.calls.last.request.read()) == {"private": True}
