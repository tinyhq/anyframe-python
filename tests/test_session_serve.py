"""Tests for the session serve (preview server) endpoints."""

from __future__ import annotations

import json

import httpx
import respx

import anyframe
from tests.conftest import BASE_URL

SID = "11111111-2222-3333-4444-555555555555"


def _session(serve_status="running", serve_port=3000, serve_url="https://tunnel/3000"):
    return {
        "id": SID,
        "agent_id": 1,
        "status": "running",
        "modal_sandbox_id": None,
        "sandbox_url": None,
        "snapshot_image_id": None,
        "idle_timeout_s": 300,
        "serve_status": serve_status,
        "serve_port": serve_port,
        "serve_url": serve_url,
        "created_at": "2025-01-01T00:00:00Z",
        "last_active": "2025-01-01T00:00:00Z",
    }


@respx.mock
def test_serve_start(client):
    route = respx.post(f"{BASE_URL}/api/sessions/{SID}/serve/start").mock(
        return_value=httpx.Response(200, json=_session())
    )
    s = client.sessions.serve_start(SID, cmd="bun dev", port=3000)
    assert isinstance(s, anyframe.Session)
    assert s.serve_status == "running"
    assert json.loads(route.calls.last.request.read()) == {"cmd": "bun dev", "port": 3000}


@respx.mock
def test_serve_stop(client):
    respx.post(f"{BASE_URL}/api/sessions/{SID}/serve/stop").mock(
        return_value=httpx.Response(
            200, json=_session(serve_status="stopped", serve_port=None, serve_url=None)
        )
    )
    s = client.sessions.serve_stop(SID)
    assert s.serve_status == "stopped"


@respx.mock
def test_serve_status(client):
    respx.get(f"{BASE_URL}/api/sessions/{SID}/serve/status").mock(
        return_value=httpx.Response(200, json=_session())
    )
    s = client.sessions.serve_status(SID)
    assert s.serve_port == 3000


@respx.mock
def test_serve_logs_passes_tail(client):
    route = respx.get(f"{BASE_URL}/api/sessions/{SID}/serve/logs").mock(
        return_value=httpx.Response(200, json={"lines": ["a", "b"]})
    )
    out = client.sessions.serve_logs(SID, tail=50)
    assert out == {"lines": ["a", "b"]}
    assert route.calls.last.request.url.params["tail"] == "50"
