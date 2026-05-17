"""Tests for the session previews + save-as-base endpoints."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

import anyframe
from tests.conftest import BASE_URL

SID = "11111111-2222-3333-4444-555555555555"


PREVIEW_ROW = {
    "port": 3000,
    "name": "web",
    "cmd": "bun dev",
    "status": "running",
    "url": "https://tunnel/3000",
    "started_at": 1234567890.0,
    "exit_code": None,
}


ACTION_OK = {
    "ok": True,
    "port": 3000,
    "name": "web",
    "url": "https://tunnel/3000",
    "status": "running",
    "restart_pending": False,
    "already_open": False,
    "error": None,
}


@respx.mock
def test_previews_list(client):
    respx.post(f"{BASE_URL}/api/sessions/{SID}/previews").mock(
        return_value=httpx.Response(200, json=[PREVIEW_ROW])
    )
    out = client.sessions.previews_list(SID)
    assert isinstance(out[0], anyframe.Preview)
    assert out[0].port == 3000


@respx.mock
def test_previews_start_minimal_body(client):
    route = respx.post(f"{BASE_URL}/api/sessions/{SID}/previews").mock(
        return_value=httpx.Response(200, json=ACTION_OK)
    )
    out = client.sessions.previews_start(SID, cmd="bun dev")
    # action + cmd only — no port/name when caller didn't pass them
    assert json.loads(route.calls.last.request.read()) == {"action": "start", "cmd": "bun dev"}
    assert isinstance(out, anyframe.PreviewActionResult)
    assert out.ok is True


@respx.mock
def test_previews_start_with_port_and_name(client):
    route = respx.post(f"{BASE_URL}/api/sessions/{SID}/previews").mock(
        return_value=httpx.Response(200, json=ACTION_OK)
    )
    client.sessions.previews_start(SID, cmd="bun dev", port=3000, name="web")
    assert json.loads(route.calls.last.request.read()) == {
        "action": "start",
        "cmd": "bun dev",
        "port": 3000,
        "name": "web",
    }


@respx.mock
def test_previews_stop(client):
    route = respx.post(f"{BASE_URL}/api/sessions/{SID}/previews").mock(
        return_value=httpx.Response(200, json={"ok": True, "status": "stopped"})
    )
    out = client.sessions.previews_stop(SID, port=3000)
    assert json.loads(route.calls.last.request.read()) == {"action": "stop", "port": 3000}
    assert out.status == "stopped"


@respx.mock
def test_previews_status(client):
    route = respx.post(f"{BASE_URL}/api/sessions/{SID}/previews").mock(
        return_value=httpx.Response(200, json=ACTION_OK)
    )
    client.sessions.previews_status(SID, name="web")
    assert json.loads(route.calls.last.request.read()) == {"action": "status", "name": "web"}


@respx.mock
def test_previews_logs_passes_tail(client):
    route = respx.post(f"{BASE_URL}/api/sessions/{SID}/previews").mock(
        return_value=httpx.Response(200, json={"lines": ["a", "b"]})
    )
    out = client.sessions.previews_logs(SID, port=3000, tail=50)
    assert out == {"lines": ["a", "b"]}
    assert json.loads(route.calls.last.request.read()) == {
        "action": "logs",
        "port": 3000,
        "tail": 50,
    }


@respx.mock
def test_previews_batch_start_accepts_preview_spec(client):
    route = respx.post(f"{BASE_URL}/api/sessions/{SID}/previews").mock(
        return_value=httpx.Response(
            200,
            json={"ok": True, "restart_pending": True, "previews": [PREVIEW_ROW], "error": None},
        )
    )
    out = client.sessions.previews_batch_start(
        SID,
        [
            anyframe.PreviewSpec(cmd="bun dev", port=3000, name="web"),
            {"cmd": "bun api"},
        ],
    )
    body = json.loads(route.calls.last.request.read())
    assert body["action"] == "batch_start"
    assert body["previews"] == [
        {"cmd": "bun dev", "port": 3000, "name": "web"},
        {"cmd": "bun api"},
    ]
    assert isinstance(out, anyframe.PreviewBatchResult)
    assert out.restart_pending is True
    assert out.previews[0].port == 3000


# ── save-as-base ──────────────────────────────────────────────────────────


@respx.mock
def test_save_as_base(client):
    route = respx.post(f"{BASE_URL}/api/sessions/{SID}/save-as-base").mock(
        return_value=httpx.Response(
            200,
            json={"warmup_image_id": "im_abc", "warmup_inputs_hash": "sha256:deadbeef"},
        )
    )
    out = client.sessions.save_as_base(SID)
    assert route.called
    assert isinstance(out, anyframe.SaveAsBaseResult)
    assert out.warmup_image_id == "im_abc"
    assert out.warmup_inputs_hash == "sha256:deadbeef"


@respx.mock
def test_save_as_base_rejects_non_setup_session(client):
    respx.post(f"{BASE_URL}/api/sessions/{SID}/save-as-base").mock(
        return_value=httpx.Response(400, json={"detail": "session is not a setup session"})
    )
    with pytest.raises(anyframe.ValidationError):
        client.sessions.save_as_base(SID)
