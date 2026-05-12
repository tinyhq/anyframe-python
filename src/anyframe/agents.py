"""Agents resource — ``/api/agents`` and its nested sub-resources.

The top-level :class:`Agents` covers create/read/update/delete on the
agent record itself; nested :attr:`Agents.skills`, :attr:`Agents.mcps`,
:attr:`Agents.connectors`, and :attr:`Agents.builds` cover the
sub-resources mounted at ``/api/agents/{id}/...``.

Sub-resources are intentionally hung off the parent (``af.agents.skills``)
rather than off an agent instance — the URL is the source of truth, and
this keeps the resource graph flat and obvious in IDE autocomplete.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

from ._sse import SSEEvent, parse_sse, parse_sse_async
from .exceptions import AnyFrameError
from .models import (
    Agent,
    AgentConnectorToggle,
    AgentDetail,
    AgentMcp,
    AgentSkill,
    Build,
    BuildQueued,
    BuildStatus,
    LogUrl,
    McpTransport,
    SkillSource,
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


class AgentSkills:
    """Per-agent skill subresource — ``/api/agents/{id}/skills``."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(self, agent_id: int) -> list[AgentSkill]:
        data = self._http.request("GET", f"/api/agents/{agent_id}/skills")
        return [AgentSkill.model_validate(row) for row in data]

    def create(
        self,
        agent_id: int,
        *,
        name: str,
        source: SkillSource,
        content: dict[str, Any],
        enabled: bool = True,
    ) -> AgentSkill:
        body = {"name": name, "source": source, "content": content, "enabled": enabled}
        data = self._http.request("POST", f"/api/agents/{agent_id}/skills", json=body)
        return AgentSkill.model_validate(data)

    def update(
        self,
        agent_id: int,
        skill_id: int,
        *,
        name: str | None = None,
        content: dict[str, Any] | None = None,
        enabled: bool | None = None,
    ) -> AgentSkill:
        body = _prune({"name": name, "content": content, "enabled": enabled})
        data = self._http.request("PATCH", f"/api/agents/{agent_id}/skills/{skill_id}", json=body)
        return AgentSkill.model_validate(data)

    def delete(self, agent_id: int, skill_id: int) -> None:
        self._http.request("DELETE", f"/api/agents/{agent_id}/skills/{skill_id}")


class AgentMcps:
    """Per-agent MCP subresource — ``/api/agents/{id}/mcps``.

    These are inline MCP servers defined on the agent. User-level connectors
    (the dashboard-managed kind) live on :class:`AgentConnectorToggles`.
    """

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(self, agent_id: int) -> list[AgentMcp]:
        data = self._http.request("GET", f"/api/agents/{agent_id}/mcps")
        return [AgentMcp.model_validate(row) for row in data]

    def create(
        self,
        agent_id: int,
        *,
        name: str,
        transport: McpTransport,
        config: dict[str, Any],
        secret_ref: str | None = None,
        enabled: bool = True,
    ) -> AgentMcp:
        body = _prune(
            {
                "name": name,
                "transport": transport,
                "config": config,
                "secret_ref": secret_ref,
                "enabled": enabled,
            }
        )
        data = self._http.request("POST", f"/api/agents/{agent_id}/mcps", json=body)
        return AgentMcp.model_validate(data)

    def update(
        self,
        agent_id: int,
        mcp_id: int,
        *,
        name: str | None = None,
        config: dict[str, Any] | None = None,
        secret_ref: str | None = None,
        enabled: bool | None = None,
    ) -> AgentMcp:
        body = _prune(
            {"name": name, "config": config, "secret_ref": secret_ref, "enabled": enabled}
        )
        data = self._http.request("PATCH", f"/api/agents/{agent_id}/mcps/{mcp_id}", json=body)
        return AgentMcp.model_validate(data)

    def delete(self, agent_id: int, mcp_id: int) -> None:
        self._http.request("DELETE", f"/api/agents/{agent_id}/mcps/{mcp_id}")


class AgentConnectorToggles:
    """Per-agent toggle for user-level MCP connectors — ``/api/agents/{id}/connectors``.

    User connectors are configured once at the user level (see
    :class:`anyframe.connectors.Connectors`). This resource controls which
    of those connectors apply to one specific agent.
    """

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(self, agent_id: int) -> list[AgentConnectorToggle]:
        data = self._http.request("GET", f"/api/agents/{agent_id}/connectors")
        return [AgentConnectorToggle.model_validate(row) for row in data]

    def set(self, agent_id: int, connector_id: int, *, enabled: bool) -> AgentConnectorToggle:
        data = self._http.request(
            "PUT",
            f"/api/agents/{agent_id}/connectors/{connector_id}",
            json={"enabled": enabled},
        )
        return AgentConnectorToggle.model_validate(data)


class Agents:
    """Manage agents and their attached sub-resources."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http
        self.skills = AgentSkills(http)
        self.mcps = AgentMcps(http)
        self.connectors = AgentConnectorToggles(http)

    def list(self) -> list[Agent]:
        """Return all agents owned by the current user."""
        data = self._http.request("GET", "/api/agents")
        return [Agent.model_validate(row) for row in data]

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        system_prompt: str | None = None,
        repo_url: str | None = None,
        repo_ref: str | None = None,
        install_cmd: str | None = None,
        serve_cmd: str | None = None,
        preview_ports: list[int] | None = None,
        permissions: dict[str, Any] | None = None,
    ) -> Agent:
        """Create a new agent.

        Args:
            name: Human-readable agent name.
            description: Optional free-text description.
            system_prompt: Optional system prompt prefix sent to Claude.
            repo_url: GitHub ``owner/name``. Omit for a general-purpose agent
                with no repo bound.
            repo_ref: Branch / tag / SHA. Defaults server-side to ``main``.
            install_cmd: Shell command run during build to install deps.
            serve_cmd: Optional preview-server command (e.g. ``bun dev``).
            preview_ports: Ports to expose for preview tunnels.
            permissions: Permissions config — see the dashboard for presets.

        Returns:
            The newly created agent record.
        """
        body = _prune(
            {
                "name": name,
                "description": description,
                "system_prompt": system_prompt,
                "repo_url": repo_url,
                "repo_ref": repo_ref,
                "install_cmd": install_cmd,
                "serve_cmd": serve_cmd,
                "preview_ports": preview_ports,
                "permissions": permissions,
            }
        )
        data = self._http.request("POST", "/api/agents", json=body)
        return Agent.model_validate(data)

    def get(self, agent_id: int) -> AgentDetail:
        """Return the detail view, including skills / mcps / connectors / image."""
        data = self._http.request("GET", f"/api/agents/{agent_id}")
        return AgentDetail.model_validate(data)

    def update(self, agent_id: int, **fields: Any) -> AgentDetail:
        """Patch any subset of an agent's mutable fields.

        Args:
            agent_id: The agent to update.
            **fields: Any of the fields accepted by :meth:`create`.

        Returns:
            The updated detail view.
        """
        data = self._http.request("PATCH", f"/api/agents/{agent_id}", json=_prune(fields))
        return AgentDetail.model_validate(data)

    def delete(self, agent_id: int) -> None:
        """Delete an agent. Cascades to skills, mcps, builds, sessions."""
        self._http.request("DELETE", f"/api/agents/{agent_id}")

    # ── builds ────────────────────────────────────────────────────────────

    def build(self, agent_id: int, *, force: bool = False) -> BuildQueued:
        """Trigger an image build for the agent's current repo config.

        Args:
            agent_id: The agent to build.
            force: If ``True``, rebuild even when a cached image already exists.

        Returns:
            A :class:`BuildQueued` reporting whether a build was actually queued
            (``queued=False`` with a ``reason`` when the image already exists or
            a build is already running).
        """
        data = self._http.request("POST", f"/api/agents/{agent_id}/build", json={"force": force})
        return BuildQueued.model_validate(data)

    def build_status(self, agent_id: int) -> BuildStatus:
        """Return the current build status (latest run + cached image, if any)."""
        data = self._http.request("GET", f"/api/agents/{agent_id}/build/status")
        return BuildStatus.model_validate(data)

    def builds(self, agent_id: int, *, limit: int = 20) -> list[Build]:
        """Return the most recent build runs for this agent, newest first."""
        data = self._http.request("GET", f"/api/agents/{agent_id}/builds", params={"limit": limit})
        return [Build.model_validate(row) for row in data]

    def build_log_url(self, agent_id: int, build_id: int) -> LogUrl:
        """Return a signed URL for the build's archived log file."""
        data = self._http.request("GET", f"/api/agents/{agent_id}/builds/{build_id}/log_url")
        return LogUrl.model_validate(data)

    def stream_build(self, agent_id: int, build_id: int) -> Iterator[SSEEvent]:
        """Stream live build-log events as SSE frames.

        The endpoint emits ``event: line`` frames with chunked stdout/stderr
        content, and a final ``event: state`` frame with the terminal state.

        Yields:
            Parsed :class:`SSEEvent` objects. Use :meth:`SSEEvent.json` to
            decode the JSON payload.
        """
        lines = self._http.stream("GET", f"/api/agents/{agent_id}/builds/{build_id}/stream")
        yield from parse_sse(lines)

    def wait_for_build(
        self,
        agent_id: int,
        *,
        timeout: float = 600.0,
        poll_interval: float = 2.0,
    ) -> BuildStatus:
        """Poll :meth:`build_status` until the build reaches a terminal state.

        Args:
            agent_id: The agent whose build to wait on.
            timeout: Maximum seconds to wait. Defaults to 10 minutes.
            poll_interval: Seconds between polls. Defaults to 2s.

        Returns:
            The terminal :class:`BuildStatus` (state in
            ``succeeded`` / ``cancelled``).

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


class AsyncAgentSkills:
    """Async counterpart to :class:`AgentSkills`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(self, agent_id: int) -> list[AgentSkill]:
        data = await self._http.request("GET", f"/api/agents/{agent_id}/skills")
        return [AgentSkill.model_validate(row) for row in data]

    async def create(
        self,
        agent_id: int,
        *,
        name: str,
        source: SkillSource,
        content: dict[str, Any],
        enabled: bool = True,
    ) -> AgentSkill:
        body = {"name": name, "source": source, "content": content, "enabled": enabled}
        data = await self._http.request("POST", f"/api/agents/{agent_id}/skills", json=body)
        return AgentSkill.model_validate(data)

    async def update(
        self,
        agent_id: int,
        skill_id: int,
        *,
        name: str | None = None,
        content: dict[str, Any] | None = None,
        enabled: bool | None = None,
    ) -> AgentSkill:
        body = _prune({"name": name, "content": content, "enabled": enabled})
        data = await self._http.request(
            "PATCH", f"/api/agents/{agent_id}/skills/{skill_id}", json=body
        )
        return AgentSkill.model_validate(data)

    async def delete(self, agent_id: int, skill_id: int) -> None:
        await self._http.request("DELETE", f"/api/agents/{agent_id}/skills/{skill_id}")


class AsyncAgentMcps:
    """Async counterpart to :class:`AgentMcps`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(self, agent_id: int) -> list[AgentMcp]:
        data = await self._http.request("GET", f"/api/agents/{agent_id}/mcps")
        return [AgentMcp.model_validate(row) for row in data]

    async def create(
        self,
        agent_id: int,
        *,
        name: str,
        transport: McpTransport,
        config: dict[str, Any],
        secret_ref: str | None = None,
        enabled: bool = True,
    ) -> AgentMcp:
        body = _prune(
            {
                "name": name,
                "transport": transport,
                "config": config,
                "secret_ref": secret_ref,
                "enabled": enabled,
            }
        )
        data = await self._http.request("POST", f"/api/agents/{agent_id}/mcps", json=body)
        return AgentMcp.model_validate(data)

    async def update(
        self,
        agent_id: int,
        mcp_id: int,
        *,
        name: str | None = None,
        config: dict[str, Any] | None = None,
        secret_ref: str | None = None,
        enabled: bool | None = None,
    ) -> AgentMcp:
        body = _prune(
            {"name": name, "config": config, "secret_ref": secret_ref, "enabled": enabled}
        )
        data = await self._http.request("PATCH", f"/api/agents/{agent_id}/mcps/{mcp_id}", json=body)
        return AgentMcp.model_validate(data)

    async def delete(self, agent_id: int, mcp_id: int) -> None:
        await self._http.request("DELETE", f"/api/agents/{agent_id}/mcps/{mcp_id}")


class AsyncAgentConnectorToggles:
    """Async counterpart to :class:`AgentConnectorToggles`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(self, agent_id: int) -> list[AgentConnectorToggle]:
        data = await self._http.request("GET", f"/api/agents/{agent_id}/connectors")
        return [AgentConnectorToggle.model_validate(row) for row in data]

    async def set(self, agent_id: int, connector_id: int, *, enabled: bool) -> AgentConnectorToggle:
        data = await self._http.request(
            "PUT",
            f"/api/agents/{agent_id}/connectors/{connector_id}",
            json={"enabled": enabled},
        )
        return AgentConnectorToggle.model_validate(data)


class AsyncAgents:
    """Async counterpart to :class:`Agents`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http
        self.skills = AsyncAgentSkills(http)
        self.mcps = AsyncAgentMcps(http)
        self.connectors = AsyncAgentConnectorToggles(http)

    async def list(self) -> list[Agent]:
        data = await self._http.request("GET", "/api/agents")
        return [Agent.model_validate(row) for row in data]

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        system_prompt: str | None = None,
        repo_url: str | None = None,
        repo_ref: str | None = None,
        install_cmd: str | None = None,
        serve_cmd: str | None = None,
        preview_ports: list[int] | None = None,
        permissions: dict[str, Any] | None = None,
    ) -> Agent:
        body = _prune(
            {
                "name": name,
                "description": description,
                "system_prompt": system_prompt,
                "repo_url": repo_url,
                "repo_ref": repo_ref,
                "install_cmd": install_cmd,
                "serve_cmd": serve_cmd,
                "preview_ports": preview_ports,
                "permissions": permissions,
            }
        )
        data = await self._http.request("POST", "/api/agents", json=body)
        return Agent.model_validate(data)

    async def get(self, agent_id: int) -> AgentDetail:
        data = await self._http.request("GET", f"/api/agents/{agent_id}")
        return AgentDetail.model_validate(data)

    async def update(self, agent_id: int, **fields: Any) -> AgentDetail:
        data = await self._http.request("PATCH", f"/api/agents/{agent_id}", json=_prune(fields))
        return AgentDetail.model_validate(data)

    async def delete(self, agent_id: int) -> None:
        await self._http.request("DELETE", f"/api/agents/{agent_id}")

    # ── builds ────────────────────────────────────────────────────────────

    async def build(self, agent_id: int, *, force: bool = False) -> BuildQueued:
        data = await self._http.request(
            "POST", f"/api/agents/{agent_id}/build", json={"force": force}
        )
        return BuildQueued.model_validate(data)

    async def build_status(self, agent_id: int) -> BuildStatus:
        data = await self._http.request("GET", f"/api/agents/{agent_id}/build/status")
        return BuildStatus.model_validate(data)

    async def builds(self, agent_id: int, *, limit: int = 20) -> list[Build]:
        data = await self._http.request(
            "GET", f"/api/agents/{agent_id}/builds", params={"limit": limit}
        )
        return [Build.model_validate(row) for row in data]

    async def build_log_url(self, agent_id: int, build_id: int) -> LogUrl:
        data = await self._http.request("GET", f"/api/agents/{agent_id}/builds/{build_id}/log_url")
        return LogUrl.model_validate(data)

    async def stream_build(self, agent_id: int, build_id: int) -> AsyncIterator[SSEEvent]:
        lines = self._http.stream("GET", f"/api/agents/{agent_id}/builds/{build_id}/stream")
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


__all__ = [
    "AgentConnectorToggles",
    "AgentMcps",
    "AgentSkills",
    "Agents",
    "AsyncAgentConnectorToggles",
    "AsyncAgentMcps",
    "AsyncAgentSkills",
    "AsyncAgents",
]
