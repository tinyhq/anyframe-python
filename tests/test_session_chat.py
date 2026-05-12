"""Tests for session chat: message, respond, events (SSE), transcript."""

from __future__ import annotations

import json

import httpx
import respx

import anyframe
from anyframe._sse import SSEEvent
from tests.conftest import BASE_URL

SID = "11111111-2222-3333-4444-555555555555"


@respx.mock
def test_message_proxies_arbitrary_payload(client):
    """The control plane proxies the body verbatim to the chat bridge —
    the SDK shouldn't impose schema. Just send the payload as JSON."""
    route = respx.post(f"{BASE_URL}/api/sessions/{SID}/message").mock(
        return_value=httpx.Response(200, json={"ok": True, "seq": 1})
    )
    out = client.sessions.message(SID, {"text": "hi", "tools": ["bash"]})
    assert out == {"ok": True, "seq": 1}
    assert json.loads(route.calls.last.request.read()) == {"text": "hi", "tools": ["bash"]}


@respx.mock
def test_respond_proxies_payload(client):
    respx.post(f"{BASE_URL}/api/sessions/{SID}/respond").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    out = client.sessions.respond(SID, {"decision": "approve", "tool_use_id": "x"})
    assert out == {"ok": True}


@respx.mock
def test_transcript_returns_chat_events(client):
    respx.get(f"{BASE_URL}/api/sessions/{SID}/transcript").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "seq": 1,
                    "payload": {"type": "user_message"},
                    "created_at": "2025-01-01T00:00:00Z",
                },
                {
                    "seq": 2,
                    "payload": {"type": "assistant_message"},
                    "created_at": "2025-01-01T00:00:01Z",
                },
            ],
        )
    )
    events = client.sessions.transcript(SID, since=0, limit=100)
    assert len(events) == 2
    assert isinstance(events[0], anyframe.ChatEvent)
    assert events[0].seq == 1


@respx.mock
def test_transcript_passes_since_and_limit_query(client):
    route = respx.get(f"{BASE_URL}/api/sessions/{SID}/transcript").mock(
        return_value=httpx.Response(200, json=[])
    )
    client.sessions.transcript(SID, since=42, limit=5)
    params = route.calls.last.request.url.params
    assert params["since"] == "42"
    assert params["limit"] == "5"


@respx.mock
def test_events_yields_sse_frames(client):
    body = (
        b'id: 1\nevent: assistant\ndata: {"text": "hi"}\n\n'
        b'id: 2\nevent: tool_call\ndata: {"name": "bash"}\n\n'
    )
    respx.get(f"{BASE_URL}/api/sessions/{SID}/events").mock(
        return_value=httpx.Response(
            200, content=body, headers={"content-type": "text/event-stream"}
        )
    )
    events = list(client.sessions.events(SID))
    assert len(events) == 2
    assert isinstance(events[0], SSEEvent)
    assert events[0].id == "1"
    assert events[0].event == "assistant"
    assert events[1].json() == {"name": "bash"}


@respx.mock
def test_events_sends_last_event_id_header(client):
    """Resumable streams: the SDK must forward Last-Event-ID when given."""
    route = respx.get(f"{BASE_URL}/api/sessions/{SID}/events").mock(
        return_value=httpx.Response(200, content=b"", headers={"content-type": "text/event-stream"})
    )
    list(client.sessions.events(SID, last_event_id="42"))
    assert route.calls.last.request.headers.get("Last-Event-ID") == "42"
