"""Smoke tests for the AsyncAnyFrame client.

We don't re-test every resource here — the async classes share the same
respx contract as their sync counterparts. These tests confirm:

  - the async top-level client wires every v2 resource up
  - the async context manager closes the connection pool
  - one representative call (me) works end-to-end
"""

from __future__ import annotations

import httpx
import pytest
import respx

import anyframe
from anyframe import exceptions as exc
from tests.conftest import BASE_URL
from tests.payloads import AGENT_DETAIL, ME_MINIMAL


@respx.mock
async def test_async_client_me():
    respx.get(f"{BASE_URL}/api/me").mock(
        return_value=httpx.Response(200, json=ME_MINIMAL),
    )
    async with anyframe.AsyncAnyFrame(
        api_key="afm_test",
        base_url=BASE_URL,
        load_dotenv=False,
    ) as af:
        u = await af.me()
    assert u.login == "nish"


async def test_async_resources_attached():
    """Every v2 resource must hang off the async client."""
    async with anyframe.AsyncAnyFrame(
        api_key="afm_test",
        base_url=BASE_URL,
        load_dotenv=False,
    ) as af:
        for attr in (
            "tokens",
            "credentials",
            "credits",
            "connectors",
            "templates",
            "agents",
            "sessions",
            "attention",
            "integrations",
            "orgs",
        ):
            assert hasattr(af, attr), attr
        for nested in ("skills", "mcps", "connectors"):
            assert hasattr(af.templates, nested), nested
        for nested in ("members", "join_requests", "invitations", "credentials", "audit"):
            assert hasattr(af.orgs, nested), nested


@respx.mock
async def test_async_agents_create_call():
    """Spot-check one async resource path actually goes through to the wire."""
    respx.post(f"{BASE_URL}/api/agents").mock(
        return_value=httpx.Response(201, json=AGENT_DETAIL),
    )
    async with anyframe.AsyncAnyFrame(
        api_key="afm_test",
        base_url=BASE_URL,
        load_dotenv=False,
    ) as af:
        agent = await af.agents.create(name="demo", template_id=4)
    assert agent.id == 7


async def test_async_missing_api_key_raises_auth_error():
    with pytest.raises(exc.AuthError):
        anyframe.AsyncAnyFrame(load_dotenv=False)


@respx.mock
async def test_async_context_manager_closes():
    respx.get(f"{BASE_URL}/api/me").mock(
        return_value=httpx.Response(200, json=ME_MINIMAL),
    )
    async with anyframe.AsyncAnyFrame(
        api_key="afm_test",
        base_url=BASE_URL,
        load_dotenv=False,
    ) as af:
        await af.me()
    assert af._http._client.is_closed is True
