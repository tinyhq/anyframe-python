"""Tests for the sessions resource — CRUD + snapshots + wait_until_running."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

import anyframe
from tests.conftest import BASE_URL

SID = "11111111-2222-3333-4444-555555555555"


def _session(status="booting", serve_status="stopped"):
    return {
        "id": SID,
        "agent_id": 1,
        "status": status,
        "modal_sandbox_id": None,
        "sandbox_url": None,
        "snapshot_image_id": None,
        "idle_timeout_s": 300,
        "serve_status": serve_status,
        "serve_port": None,
        "serve_url": None,
        "created_at": "2025-01-01T00:00:00Z",
        "last_active": "2025-01-01T00:00:00Z",
    }


@respx.mock
def test_list_sessions(client):
    respx.get(f"{BASE_URL}/api/sessions").mock(return_value=httpx.Response(200, json=[_session()]))
    sessions = client.sessions.list()
    assert isinstance(sessions[0], anyframe.Session)


@respx.mock
def test_create_with_full_kwargs(client):
    route = respx.post(f"{BASE_URL}/api/sessions").mock(
        return_value=httpx.Response(202, json=_session())
    )
    client.sessions.create(agent_id=1, idle_timeout_s=900, unsafe=True, resume_from_snapshot_id=42)
    body = json.loads(route.calls.last.request.read())
    assert body == {
        "agent_id": 1,
        "idle_timeout_s": 900,
        "unsafe": True,
        "resume_from_snapshot_id": 42,
    }


@respx.mock
def test_get_session(client):
    respx.get(f"{BASE_URL}/api/sessions/{SID}").mock(
        return_value=httpx.Response(200, json=_session(status="running"))
    )
    s = client.sessions.get(SID)
    assert s.status == "running"


@respx.mock
def test_terminate(client):
    respx.post(f"{BASE_URL}/api/sessions/{SID}/terminate").mock(
        return_value=httpx.Response(202, json=_session(status="snapshotting"))
    )
    s = client.sessions.terminate(SID)
    assert s.status == "snapshotting"


@respx.mock
def test_delete(client):
    respx.delete(f"{BASE_URL}/api/sessions/{SID}").mock(return_value=httpx.Response(204))
    client.sessions.delete(SID)


@respx.mock
def test_resume_with_unsafe(client):
    route = respx.post(f"{BASE_URL}/api/sessions/{SID}/resume").mock(
        return_value=httpx.Response(202, json=_session())
    )
    client.sessions.resume(SID, unsafe=True)
    assert json.loads(route.calls.last.request.read()) == {"unsafe": True}


@respx.mock
def test_snapshots(client):
    respx.get(f"{BASE_URL}/api/sessions/{SID}/snapshots").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": 1,
                    "modal_image_id": "im_1",
                    "label": "v1",
                    "created_at": "2025-01-01T00:00:00Z",
                }
            ],
        )
    )
    snaps = client.sessions.snapshots(SID)
    assert isinstance(snaps[0], anyframe.Snapshot)


@respx.mock
def test_delete_while_running_raises_conflict(client):
    respx.delete(f"{BASE_URL}/api/sessions/{SID}").mock(
        return_value=httpx.Response(409, json={"detail": "session is running"})
    )
    with pytest.raises(anyframe.ConflictError):
        client.sessions.delete(SID)


@respx.mock
def test_wait_until_running_polls_until_running(client, monkeypatch):
    seq = iter(
        [
            httpx.Response(200, json=_session(status="booting")),
            httpx.Response(200, json=_session(status="running")),
        ]
    )
    respx.get(f"{BASE_URL}/api/sessions/{SID}").mock(side_effect=lambda *_a, **_kw: next(seq))
    monkeypatch.setattr("anyframe.sessions.time.sleep", lambda _: None)
    s = client.sessions.wait_until_running(SID, poll_interval=0.0, timeout=5.0)
    assert s.status == "running"


@respx.mock
def test_wait_until_running_raises_on_terminated(client, monkeypatch):
    respx.get(f"{BASE_URL}/api/sessions/{SID}").mock(
        return_value=httpx.Response(200, json=_session(status="terminated"))
    )
    monkeypatch.setattr("anyframe.sessions.time.sleep", lambda _: None)
    with pytest.raises(anyframe.AnyFrameError):
        client.sessions.wait_until_running(SID, poll_interval=0.0)


@respx.mock
def test_wait_until_running_timeout(client, monkeypatch):
    respx.get(f"{BASE_URL}/api/sessions/{SID}").mock(
        return_value=httpx.Response(200, json=_session(status="booting"))
    )
    monkeypatch.setattr("anyframe.sessions.time.sleep", lambda _: None)
    ticks = iter([0.0, 100.0, 200.0])
    monkeypatch.setattr("anyframe.sessions.time.monotonic", lambda: next(ticks))
    with pytest.raises(TimeoutError):
        client.sessions.wait_until_running(SID, poll_interval=0.0, timeout=1.0)
