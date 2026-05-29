"""Agents resource — ``/api/agents`` and its build sub-resource.

In v2 the *what to build* lives on a :class:`anyframe.Template` (system
prompt, repo, install/serve commands, skills, MCPs, connector toggles,
permissions baseline, env vars baseline). An :class:`Agent` is a thin
binding to a template plus per-agent overrides (``runtime``,
``permissions_override``, ``env_vars_override``). See
:mod:`anyframe.templates` for the blueprint surface.

The build sub-resource (``/api/agents/{id}/build*``) stays on the agent
since cached images are keyed off the combination of template recipe and
agent runtime.
"""

from __future__ import annotations

import asyncio
import builtins
import time
from typing import TYPE_CHECKING, Any

from ._sse import SSEEvent, parse_sse, parse_sse_async
from .exceptions import AnyFrameError
from .models import (
    Agent,
    AgentDetail,
    Build,
    BuildQueued,
    BuildStatus,
    LogUrl,
    Runtime,
)

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncIterator, Iterator

    from ._http import AsyncHTTP, SyncHTTP


_TERMINAL_BUILD_STATES = frozenset({"succeeded", "failed", "cancelled"})


def _prune(body: dict[str, Any]) -> dict[str, Any]:
    """Drop keys whose value is ``None`` — the server distinguishes "omit"
    from "set to null" and the SDK should never surprise callers there."""
    return {k: v for k, v in body.items() if v is not None}


# ── Sync ────────────────────────────────────────────────────────────────────


class Agents:
    """Manage agents and their build sub-resource.

    Skills, MCPs, and connector toggles live on the bound
    :class:`anyframe.Template` — access them via ``af.templates``.
    """

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(self) -> builtins.list[Agent]:
        """Return all agents owned by the current scope (personal or org)."""
        data = self._http.request("GET", "/api/agents")
        return [Agent.model_validate(row) for row in data]

    def create(
        self,
        *,
        name: str,
        template_id: int,
        description: str | None = None,
        runtime: Runtime | None = None,
        permissions_override: dict[str, Any] | None = None,
        env_vars_override: dict[str, str] | None = None,
    ) -> AgentDetail:
        """Create a new agent bound to ``template_id``.

        Args:
            name: Human-readable agent name (1-255 chars).
            template_id: The :class:`Template` this agent binds to. The
                template owns the repo, install/serve commands, system prompt,
                skills, MCPs, and the baseline permissions and env vars.
            description: Optional free-text description.
            runtime: Which coding-agent runtime drives sessions for this agent
                (``"claude"`` or ``"codex"``). Defaults server-side to
                ``"claude"``.
            permissions_override: If set, replaces the template's baseline
                ``permissions`` for this agent only. Pass ``None`` (the
                default) to inherit from the template.
            env_vars_override: Per-agent env-var overlay merged onto the
                template's env vars (overlay wins). Keys must match
                ``[A-Z_][A-Z0-9_]*``; values are encrypted at rest and masked
                in responses.

        Returns:
            The detail view of the newly created agent.
        """
        body = _prune(
            {
                "name": name,
                "template_id": template_id,
                "description": description,
                "runtime": runtime,
                "permissions_override": permissions_override,
                "env_vars_override": env_vars_override,
            }
        )
        data = self._http.request("POST", "/api/agents", json=body)
        return AgentDetail.model_validate(data)

    def get(self, agent_id: int) -> AgentDetail:
        """Return the detail view, including the bound template and prebuilt image."""
        data = self._http.request("GET", f"/api/agents/{agent_id}")
        return AgentDetail.model_validate(data)

    def update(self, agent_id: int, **fields: Any) -> AgentDetail:
        """Patch any subset of an agent's mutable fields.

        Accepts the same field names as :meth:`create`: ``name``,
        ``description``, ``runtime``, ``template_id``, ``permissions_override``,
        ``env_vars_override``. Only fields you actually pass are sent.

        The override fields have nullable semantics on the server:

        * ``permissions_override=None`` *clears* the override (falls back to
          the template's baseline). Omit the kwarg entirely to leave the
          existing override untouched.
        * ``env_vars_override={}`` clears the overlay. Pass a partial dict to
          merge it onto the existing overlay (the server applies the merge).
        """
        data = self._http.request("PATCH", f"/api/agents/{agent_id}", json=fields)
        return AgentDetail.model_validate(data)

    def delete(self, agent_id: int) -> None:
        """Delete an agent. Cascades to its builds and any non-archived sessions."""
        self._http.request("DELETE", f"/api/agents/{agent_id}")

    # ── builds ────────────────────────────────────────────────────────────

    def build(self, agent_id: int, *, force: bool = False) -> BuildQueued:
        """Trigger an image build for the agent's current template + runtime.

        Args:
            agent_id: The agent to build.
            force: If ``True``, rebuild even when a cached image already exists.

        Returns:
            A :class:`BuildQueued` reporting whether a build was actually queued
            (``queued=False`` with a ``reason`` when the image is already cached
            or a build is already in flight).
        """
        data = self._http.request(
            "POST",
            f"/api/agents/{agent_id}/build",
            json={"force": force},
        )
        return BuildQueued.model_validate(data)

    def build_status(self, agent_id: int) -> BuildStatus:
        """Return the current build status (latest run + cached image, if any)."""
        data = self._http.request("GET", f"/api/agents/{agent_id}/build/status")
        return BuildStatus.model_validate(data)

    def builds(self, agent_id: int, *, limit: int = 20) -> builtins.list[Build]:
        """Return the most recent build runs for this agent, newest first."""
        data = self._http.request(
            "GET",
            f"/api/agents/{agent_id}/builds",
            params={"limit": limit},
        )
        return [Build.model_validate(row) for row in data]

    def build_log_url(self, agent_id: int, build_id: int) -> LogUrl:
        """Return a signed URL for the build's archived log file."""
        data = self._http.request(
            "GET",
            f"/api/agents/{agent_id}/builds/{build_id}/log_url",
        )
        return LogUrl.model_validate(data)

    def stream_build(self, agent_id: int, build_id: int) -> Iterator[SSEEvent]:
        """Stream live build-log events as SSE frames.

        The endpoint emits ``event: line`` frames with chunked stdout/stderr,
        then a final ``event: state`` frame with the terminal state.

        Yields:
            Parsed :class:`SSEEvent` objects. Use :meth:`SSEEvent.json` to
            decode the JSON payload.
        """
        lines = self._http.stream(
            "GET",
            f"/api/agents/{agent_id}/builds/{build_id}/stream",
        )
        yield from parse_sse(lines)

    def wait_for_build(
        self,
        agent_id: int,
        *,
        timeout: float = 600.0,
        poll_interval: float = 2.0,
    ) -> BuildStatus:
        """Poll :meth:`build_status` until the build reaches a terminal state.

        Raises:
            TimeoutError: If the build does not finish before ``timeout``.
            AnyFrameError: If the build finishes in the ``failed`` state.
        """
        deadline = time.monotonic() + timeout
        while True:
            status = self.build_status(agent_id)
            if status.state in _TERMINAL_BUILD_STATES:
                if status.state == "failed":
                    raise AnyFrameError(
                        f"build failed: {status.error or 'unknown error'}",
                    )
                return status
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"build for agent {agent_id} did not finish within {timeout}s",
                )
            time.sleep(poll_interval)


# ── Async ───────────────────────────────────────────────────────────────────


class AsyncAgents:
    """Async counterpart to :class:`Agents`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(self) -> builtins.list[Agent]:
        data = await self._http.request("GET", "/api/agents")
        return [Agent.model_validate(row) for row in data]

    async def create(
        self,
        *,
        name: str,
        template_id: int,
        description: str | None = None,
        runtime: Runtime | None = None,
        permissions_override: dict[str, Any] | None = None,
        env_vars_override: dict[str, str] | None = None,
    ) -> AgentDetail:
        body = _prune(
            {
                "name": name,
                "template_id": template_id,
                "description": description,
                "runtime": runtime,
                "permissions_override": permissions_override,
                "env_vars_override": env_vars_override,
            }
        )
        data = await self._http.request("POST", "/api/agents", json=body)
        return AgentDetail.model_validate(data)

    async def get(self, agent_id: int) -> AgentDetail:
        data = await self._http.request("GET", f"/api/agents/{agent_id}")
        return AgentDetail.model_validate(data)

    async def update(self, agent_id: int, **fields: Any) -> AgentDetail:
        data = await self._http.request("PATCH", f"/api/agents/{agent_id}", json=fields)
        return AgentDetail.model_validate(data)

    async def delete(self, agent_id: int) -> None:
        await self._http.request("DELETE", f"/api/agents/{agent_id}")

    # ── builds ────────────────────────────────────────────────────────────

    async def build(self, agent_id: int, *, force: bool = False) -> BuildQueued:
        data = await self._http.request(
            "POST",
            f"/api/agents/{agent_id}/build",
            json={"force": force},
        )
        return BuildQueued.model_validate(data)

    async def build_status(self, agent_id: int) -> BuildStatus:
        data = await self._http.request("GET", f"/api/agents/{agent_id}/build/status")
        return BuildStatus.model_validate(data)

    async def builds(self, agent_id: int, *, limit: int = 20) -> builtins.list[Build]:
        data = await self._http.request(
            "GET",
            f"/api/agents/{agent_id}/builds",
            params={"limit": limit},
        )
        return [Build.model_validate(row) for row in data]

    async def build_log_url(self, agent_id: int, build_id: int) -> LogUrl:
        data = await self._http.request(
            "GET",
            f"/api/agents/{agent_id}/builds/{build_id}/log_url",
        )
        return LogUrl.model_validate(data)

    async def stream_build(
        self,
        agent_id: int,
        build_id: int,
    ) -> AsyncIterator[SSEEvent]:
        lines = self._http.stream(
            "GET",
            f"/api/agents/{agent_id}/builds/{build_id}/stream",
        )
        async for event in parse_sse_async(lines):
            yield event

    async def wait_for_build(
        self,
        agent_id: int,
        *,
        timeout: float = 600.0,
        poll_interval: float = 2.0,
    ) -> BuildStatus:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            status = await self.build_status(agent_id)
            if status.state in _TERMINAL_BUILD_STATES:
                if status.state == "failed":
                    raise AnyFrameError(
                        f"build failed: {status.error or 'unknown error'}",
                    )
                return status
            if loop.time() >= deadline:
                raise TimeoutError(
                    f"build for agent {agent_id} did not finish within {timeout}s",
                )
            await asyncio.sleep(poll_interval)


__all__ = ["Agents", "AsyncAgents"]
