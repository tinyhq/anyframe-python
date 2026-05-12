"""Tests for the agent builds sub-resource (trigger, status, streaming, waiter)."""

from __future__ import annotations

import httpx
import pytest
import respx

import anyframe
from anyframe._sse import SSEEvent
from tests.conftest import BASE_URL


@respx.mock
def test_build_queued(client):
    respx.post(f"{BASE_URL}/api/agents/7/build").mock(
        return_value=httpx.Response(202, json={"agent_id": 7, "build_key": "k1", "queued": True})
    )
    out = client.agents.build(7)
    assert isinstance(out, anyframe.BuildQueued)
    assert out.queued is True


@respx.mock
def test_build_force_sent_in_body(client):
    route = respx.post(f"{BASE_URL}/api/agents/7/build").mock(
        return_value=httpx.Response(202, json={"agent_id": 7, "build_key": "k1", "queued": True})
    )
    client.agents.build(7, force=True)
    assert b'"force":true' in route.calls.last.request.read()


@respx.mock
def test_build_status_no_build_yet(client):
    respx.get(f"{BASE_URL}/api/agents/7/build/status").mock(
        return_value=httpx.Response(200, json={"agent_id": 7, "build_key": None})
    )
    s = client.agents.build_status(7)
    assert s.state is None


@respx.mock
def test_builds_list(client):
    respx.get(f"{BASE_URL}/api/agents/7/builds").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": 1,
                    "build_key": "k1",
                    "state": "succeeded",
                    "started_at": "2025-01-01T00:00:00Z",
                    "finished_at": "2025-01-01T00:01:00Z",
                    "error": None,
                    "log_size": 1024,
                }
            ],
        )
    )
    builds = client.agents.builds(7)
    assert builds[0].state == "succeeded"


@respx.mock
def test_builds_list_respects_limit_param(client):
    route = respx.get(f"{BASE_URL}/api/agents/7/builds").mock(
        return_value=httpx.Response(200, json=[])
    )
    client.agents.builds(7, limit=5)
    assert route.calls.last.request.url.params["limit"] == "5"


@respx.mock
def test_build_log_url(client):
    respx.get(f"{BASE_URL}/api/agents/7/builds/3/log_url").mock(
        return_value=httpx.Response(200, json={"url": "https://r2/...", "expires_in": 300})
    )
    out = client.agents.build_log_url(7, 3)
    assert out.expires_in == 300


@respx.mock
def test_stream_build_yields_sse_events(client):
    """The build stream is SSE — we should hand callers parsed frames."""
    body = (
        b'event: line\ndata: {"offset": 1, "content": "hello"}\n\n'
        b'event: state\ndata: {"state": "succeeded"}\n\n'
    )
    respx.get(f"{BASE_URL}/api/agents/7/builds/3/stream").mock(
        return_value=httpx.Response(
            200, content=body, headers={"content-type": "text/event-stream"}
        )
    )
    events = list(client.agents.stream_build(7, 3))
    assert len(events) == 2
    assert isinstance(events[0], SSEEvent)
    assert events[0].event == "line"
    assert events[0].json() == {"offset": 1, "content": "hello"}
    assert events[1].event == "state"


@respx.mock
def test_wait_for_build_returns_on_terminal_state(client, monkeypatch):
    """The waiter polls build_status until state is terminal, no sleeping."""
    calls = iter(
        [
            httpx.Response(200, json={"agent_id": 7, "build_key": "k", "state": "running"}),
            httpx.Response(200, json={"agent_id": 7, "build_key": "k", "state": "running"}),
            httpx.Response(
                200,
                json={
                    "agent_id": 7,
                    "build_key": "k",
                    "state": "succeeded",
                    "built_image_id": "im_1",
                },
            ),
        ]
    )
    respx.get(f"{BASE_URL}/api/agents/7/build/status").mock(
        side_effect=lambda *_a, **_kw: next(calls)
    )
    monkeypatch.setattr("anyframe.agents.time.sleep", lambda _: None)
    out = client.agents.wait_for_build(7, poll_interval=0.0, timeout=5.0)
    assert out.state == "succeeded"


@respx.mock
def test_wait_for_build_raises_on_timeout(client, monkeypatch):
    respx.get(f"{BASE_URL}/api/agents/7/build/status").mock(
        return_value=httpx.Response(200, json={"agent_id": 7, "build_key": "k", "state": "running"})
    )
    monkeypatch.setattr("anyframe.agents.time.sleep", lambda _: None)
    # Force time.monotonic to advance past the timeout on the second tick.
    ticks = iter([0.0, 100.0, 200.0])
    monkeypatch.setattr("anyframe.agents.time.monotonic", lambda: next(ticks))
    with pytest.raises(TimeoutError):
        client.agents.wait_for_build(7, poll_interval=0.0, timeout=1.0)


@respx.mock
def test_wait_for_build_raises_on_failure(client, monkeypatch):
    respx.get(f"{BASE_URL}/api/agents/7/build/status").mock(
        return_value=httpx.Response(
            200,
            json={
                "agent_id": 7,
                "build_key": "k",
                "state": "failed",
                "error": "compile broke",
            },
        )
    )
    monkeypatch.setattr("anyframe.agents.time.sleep", lambda _: None)
    with pytest.raises(anyframe.AnyFrameError) as ei:
        client.agents.wait_for_build(7, poll_interval=0.0)
    assert "compile broke" in str(ei.value)
