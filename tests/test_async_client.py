"""Smoke tests for the AsyncAnyFrame client.

We don't re-test every resource here — the async classes were already
exercised via the shared respx contract. These tests confirm:

  - the async top-level client wires resources up identically
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


@respx.mock
async def test_async_client_me():
    respx.get(f"{BASE_URL}/api/me").mock(
        return_value=httpx.Response(
            200,
            json={"id": 1, "github_id": 0, "login": "x", "name": None, "avatar_url": None},
        )
    )
    async with anyframe.AsyncAnyFrame(
        api_key="afm_test", base_url=BASE_URL, load_dotenv=False
    ) as af:
        u = await af.me()
        assert u.login == "x"


@respx.mock
async def test_async_resources_attached():
    """Every sync attribute must also exist on the async client."""
    async with anyframe.AsyncAnyFrame(
        api_key="afm_test", base_url=BASE_URL, load_dotenv=False
    ) as af:
        for attr in ("tokens", "credentials", "agents", "connectors", "sessions"):
            assert hasattr(af, attr), attr
        assert hasattr(af.agents, "skills")
        assert hasattr(af.agents, "mcps")
        assert hasattr(af.agents, "connectors")


@respx.mock
async def test_async_agents_create_call():
    """Spot-check one async resource path actually goes through to the wire."""
    respx.post(f"{BASE_URL}/api/agents").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": 7,
                "name": "demo",
                "description": None,
                "system_prompt": None,
                "repo_url": None,
                "repo_ref": None,
                "install_cmd": None,
                "serve_cmd": None,
                "preview_ports": [],
                "build_key": None,
                "permissions": {"preset": "standard"},
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            },
        )
    )
    async with anyframe.AsyncAnyFrame(
        api_key="afm_test", base_url=BASE_URL, load_dotenv=False
    ) as af:
        agent = await af.agents.create(name="demo")
    assert agent.id == 7


async def test_async_missing_api_key_raises_auth_error():
    with pytest.raises(exc.AuthError):
        anyframe.AsyncAnyFrame(load_dotenv=False)


@respx.mock
async def test_async_context_manager_closes():
    respx.get(f"{BASE_URL}/api/me").mock(
        return_value=httpx.Response(
            200,
            json={"id": 1, "github_id": 0, "login": "x", "name": None, "avatar_url": None},
        )
    )
    async with anyframe.AsyncAnyFrame(
        api_key="afm_test", base_url=BASE_URL, load_dotenv=False
    ) as af:
        await af.me()
    assert af._http._client.is_closed is True
