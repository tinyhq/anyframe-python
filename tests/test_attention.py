"""Tests for the attention resource — ``/api/attention``."""

from __future__ import annotations

import httpx
import respx

import anyframe
from tests.conftest import BASE_URL

SID = "11111111-2222-3333-4444-555555555555"


PENDING = {
    "kind": "pending",
    "session_id": SID,
    "agent_id": 7,
    "agent_name": "demo",
    "session_status": "running",
    "seq": 42,
    "payload": {"type": "permission_request", "request_id": "r-1"},
    "at": "2025-01-01T00:00:00Z",
    "preview": "Bash(command=ls -la)",
}

IDLE = {
    "kind": "idle",
    "session_id": SID,
    "agent_id": 7,
    "agent_name": "demo",
    "at": "2025-01-01T00:00:00Z",
    "preview": "All done.",
}

PAUSED = {
    "kind": "paused",
    "session_id": SID,
    "agent_id": 7,
    "agent_name": "demo",
    "snapshot_image_id": "im_abc",
    "at": "2025-01-01T00:00:00Z",
}


@respx.mock
def test_attention_list_returns_typed_union(client):
    route = respx.get(f"{BASE_URL}/api/attention").mock(
        return_value=httpx.Response(200, json=[PENDING, IDLE, PAUSED])
    )
    items = client.attention.list()
    assert route.called
    assert route.calls.last.request.url.params["limit"] == "20"
    assert isinstance(items[0], anyframe.AttentionPendingItem)
    assert isinstance(items[1], anyframe.AttentionIdleItem)
    assert isinstance(items[2], anyframe.AttentionPausedItem)
    assert items[0].preview == "Bash(command=ls -la)"
    assert items[1].preview == "All done."
    assert items[2].snapshot_image_id == "im_abc"


@respx.mock
def test_attention_list_passes_limit(client):
    route = respx.get(f"{BASE_URL}/api/attention").mock(return_value=httpx.Response(200, json=[]))
    client.attention.list(limit=5)
    assert route.calls.last.request.url.params["limit"] == "5"


@respx.mock
def test_attention_empty_list_is_ok(client):
    respx.get(f"{BASE_URL}/api/attention").mock(return_value=httpx.Response(200, json=[]))
    assert client.attention.list() == []
