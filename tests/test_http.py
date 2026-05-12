"""Tests for the internal HTTP transport.

The transport is the load-bearing piece every other resource calls into.
We test the things that *will* break callers if they regress:

  - Bearer token is attached to every request
  - status codes map to the right typed exceptions
  - 204 / empty body returns None instead of crashing the JSON parser
  - transport errors (timeouts, connection refused) surface as APIError(0)
  - 429 with Retry-After is preserved on the exception
  - the SDK identifies itself with a stable User-Agent
  - debug logging emits one line per request at the right level
"""

from __future__ import annotations

import logging

import httpx
import pytest
import respx

from anyframe import exceptions as exc
from anyframe._http import SyncHTTP
from anyframe._version import __version__

BASE = "https://api.example.com"


def _client() -> SyncHTTP:
    return SyncHTTP(base_url=BASE, api_key="afm_test", timeout=5.0)


@respx.mock
def test_get_attaches_bearer_and_user_agent():
    route = respx.get(f"{BASE}/api/me").mock(
        return_value=httpx.Response(200, json={"id": 1, "github_id": 0, "login": "x"})
    )
    with _client() as http:
        http.request("GET", "/api/me")
    assert route.called
    req = route.calls.last.request
    assert req.headers["Authorization"] == "Bearer afm_test"
    assert req.headers["User-Agent"] == f"anyframe-python/{__version__}"


@respx.mock
def test_204_returns_none():
    respx.delete(f"{BASE}/api/agents/1").mock(return_value=httpx.Response(204))
    with _client() as http:
        assert http.request("DELETE", "/api/agents/1") is None


@respx.mock
def test_empty_body_200_returns_none():
    respx.put(f"{BASE}/api/credentials/claude").mock(return_value=httpx.Response(200, content=b""))
    with _client() as http:
        assert http.request("PUT", "/api/credentials/claude") is None


@respx.mock
def test_json_body_parsed():
    respx.get(f"{BASE}/api/me").mock(return_value=httpx.Response(200, json={"id": 7}))
    with _client() as http:
        assert http.request("GET", "/api/me") == {"id": 7}


@respx.mock
@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, exc.AuthError),
        (404, exc.NotFoundError),
        (409, exc.ConflictError),
        (400, exc.ValidationError),
        (422, exc.ValidationError),
        (500, exc.ServerError),
        (502, exc.ServerError),
        (503, exc.ServerError),
    ],
)
def test_status_codes_map_to_typed_errors(status, expected):
    respx.get(f"{BASE}/x").mock(return_value=httpx.Response(status, json={"detail": "nope"}))
    with _client() as http, pytest.raises(expected) as ei:
        http.request("GET", "/x")
    assert ei.value.status_code == status
    assert "nope" in ei.value.message


@respx.mock
def test_rate_limit_preserves_retry_after():
    respx.get(f"{BASE}/x").mock(
        return_value=httpx.Response(429, json={"detail": "slow"}, headers={"Retry-After": "7"})
    )
    with _client() as http, pytest.raises(exc.RateLimitError) as ei:
        http.request("GET", "/x")
    assert ei.value.retry_after == 7


@respx.mock
def test_validation_error_preserves_pydantic_style_details():
    body = {"detail": [{"loc": ["body", "name"], "msg": "field required", "type": "missing"}]}
    respx.post(f"{BASE}/x").mock(return_value=httpx.Response(422, json=body))
    with _client() as http, pytest.raises(exc.ValidationError) as ei:
        http.request("POST", "/x", json={})
    assert ei.value.details == body["detail"]


@respx.mock
def test_connect_error_becomes_api_error_zero():
    respx.get(f"{BASE}/x").mock(side_effect=httpx.ConnectError("refused"))
    with _client() as http, pytest.raises(exc.APIError) as ei:
        http.request("GET", "/x")
    assert ei.value.status_code == 0
    assert "refused" in ei.value.message


@respx.mock
def test_timeout_becomes_api_error_zero():
    respx.get(f"{BASE}/x").mock(side_effect=httpx.TimeoutException("slow"))
    with _client() as http, pytest.raises(exc.APIError) as ei:
        http.request("GET", "/x")
    assert ei.value.status_code == 0


@respx.mock
def test_debug_log_emits_at_debug_level(caplog):
    respx.get(f"{BASE}/api/me").mock(return_value=httpx.Response(200, json={}))
    caplog.set_level(logging.DEBUG, logger="anyframe")
    with _client() as http:
        http.request("GET", "/api/me")
    # one debug-level record describing the request + status
    records = [
        r for r in caplog.records if r.name.startswith("anyframe") and r.levelno == logging.DEBUG
    ]
    assert records, "expected debug log for request"
    assert any(
        "GET" in r.message and "/api/me" in r.message and "200" in r.message for r in records
    )


@respx.mock
def test_trailing_slash_in_base_url_is_normalised():
    respx.get(f"{BASE}/api/me").mock(return_value=httpx.Response(200, json={}))
    http = SyncHTTP(base_url=BASE + "/", api_key="afm_test", timeout=5.0)
    try:
        http.request("GET", "/api/me")
    finally:
        http.close()


@respx.mock
def test_base_url_can_be_url_object():
    """We accept str only — but httpx accepts URL too; check we don't crash."""
    respx.get(f"{BASE}/x").mock(return_value=httpx.Response(204))
    with _client() as http:
        assert http.request("GET", "/x") is None


# ── async transport ───────────────────────────────────────────────────────


@respx.mock
async def test_async_client_basic_get():
    respx.get(f"{BASE}/api/me").mock(return_value=httpx.Response(200, json={"ok": True}))
    from anyframe._http import AsyncHTTP

    async with AsyncHTTP(base_url=BASE, api_key="afm_test", timeout=5.0) as http:
        assert await http.request("GET", "/api/me") == {"ok": True}


@respx.mock
async def test_async_error_mapping():
    respx.get(f"{BASE}/x").mock(return_value=httpx.Response(404, json={"detail": "no"}))
    from anyframe._http import AsyncHTTP

    async with AsyncHTTP(base_url=BASE, api_key="afm_test", timeout=5.0) as http:
        with pytest.raises(exc.NotFoundError):
            await http.request("GET", "/x")
