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

from typing import TYPE_CHECKING, Any

from .models import Agent, AgentDetail

if TYPE_CHECKING:  # pragma: no cover
    from ._http import AsyncHTTP, SyncHTTP


def _prune(body: dict[str, Any]) -> dict[str, Any]:
    """Drop keys whose value is ``None`` — the server distinguishes "omit"
    from "set to null" and the SDK should never surprise callers there."""
    return {k: v for k, v in body.items() if v is not None}


# ── Sync ────────────────────────────────────────────────────────────────────


class Agents:
    """Manage agents and their attached sub-resources."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

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


# ── Async ───────────────────────────────────────────────────────────────────


class AsyncAgents:
    """Async counterpart to :class:`Agents`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

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


__all__ = ["Agents", "AsyncAgents"]
