"""Templates resource — ``/api/templates`` and its nested sub-resources.

A :class:`Template` is the reusable blueprint behind agents: it owns the
repo binding, install / serve commands, system prompt, skills, MCP servers,
connector toggles, baseline permissions, and baseline env vars. Many agents
can bind to the same template; each agent adds only its own
``runtime``, ``permissions_override``, and ``env_vars_override`` on top.

This module mirrors the same flat-resource shape used elsewhere in the SDK
— sub-resources hang off the parent (``af.templates.skills`` rather than
off a template instance) so the URL is the source of truth and IDE
autocomplete stays predictable.
"""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, Any

from .models import (
    McpTransport,
    SkillSource,
    Template,
    TemplateConnectorToggle,
    TemplateDetail,
    TemplateMcp,
    TemplateSkill,
)

if TYPE_CHECKING:  # pragma: no cover
    from ._http import AsyncHTTP, SyncHTTP


def _prune(body: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in body.items() if v is not None}


# ── Sync ────────────────────────────────────────────────────────────────────


class TemplateSkills:
    """Per-template skill subresource — ``/api/templates/{id}/skills``."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(self, template_id: int) -> builtins.list[TemplateSkill]:
        data = self._http.request("GET", f"/api/templates/{template_id}/skills")
        return [TemplateSkill.model_validate(row) for row in data]

    def create(
        self,
        template_id: int,
        *,
        name: str,
        source: SkillSource,
        content: dict[str, Any],
        enabled: bool = True,
    ) -> TemplateSkill:
        body = {"name": name, "source": source, "content": content, "enabled": enabled}
        data = self._http.request(
            "POST", f"/api/templates/{template_id}/skills", json=body,
        )
        return TemplateSkill.model_validate(data)

    def update(
        self,
        template_id: int,
        skill_id: int,
        *,
        name: str | None = None,
        content: dict[str, Any] | None = None,
        enabled: bool | None = None,
    ) -> TemplateSkill:
        body = _prune({"name": name, "content": content, "enabled": enabled})
        data = self._http.request(
            "PATCH",
            f"/api/templates/{template_id}/skills/{skill_id}",
            json=body,
        )
        return TemplateSkill.model_validate(data)

    def delete(self, template_id: int, skill_id: int) -> None:
        self._http.request(
            "DELETE", f"/api/templates/{template_id}/skills/{skill_id}",
        )


class TemplateMcps:
    """Per-template MCP-server subresource — ``/api/templates/{id}/mcps``.

    These are *inline* MCP servers defined on the template. User-level
    connectors (the dashboard-managed kind) toggle via
    :class:`TemplateConnectors`.
    """

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(self, template_id: int) -> builtins.list[TemplateMcp]:
        data = self._http.request("GET", f"/api/templates/{template_id}/mcps")
        return [TemplateMcp.model_validate(row) for row in data]

    def create(
        self,
        template_id: int,
        *,
        name: str,
        transport: McpTransport,
        config: dict[str, Any],
        secret_ref: str | None = None,
        enabled: bool = True,
    ) -> TemplateMcp:
        body = _prune(
            {
                "name": name,
                "transport": transport,
                "config": config,
                "secret_ref": secret_ref,
                "enabled": enabled,
            }
        )
        data = self._http.request(
            "POST", f"/api/templates/{template_id}/mcps", json=body,
        )
        return TemplateMcp.model_validate(data)

    def update(
        self,
        template_id: int,
        mcp_id: int,
        *,
        name: str | None = None,
        config: dict[str, Any] | None = None,
        secret_ref: str | None = None,
        enabled: bool | None = None,
    ) -> TemplateMcp:
        body = _prune(
            {
                "name": name,
                "config": config,
                "secret_ref": secret_ref,
                "enabled": enabled,
            }
        )
        data = self._http.request(
            "PATCH", f"/api/templates/{template_id}/mcps/{mcp_id}", json=body,
        )
        return TemplateMcp.model_validate(data)

    def delete(self, template_id: int, mcp_id: int) -> None:
        self._http.request(
            "DELETE", f"/api/templates/{template_id}/mcps/{mcp_id}",
        )


class TemplateConnectors:
    """Per-template toggles for user-level MCP connectors.

    Connectors are configured once at the user (or org) level via
    :class:`anyframe.connectors.Connectors`. This resource controls which
    of those connectors apply to one template — every agent bound to the
    template inherits the resolved set.
    """

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(self, template_id: int) -> builtins.list[TemplateConnectorToggle]:
        data = self._http.request(
            "GET", f"/api/templates/{template_id}/connectors",
        )
        return [TemplateConnectorToggle.model_validate(row) for row in data]

    def set(
        self, template_id: int, connector_id: int, *, enabled: bool,
    ) -> TemplateConnectorToggle:
        data = self._http.request(
            "PUT",
            f"/api/templates/{template_id}/connectors/{connector_id}",
            json={"enabled": enabled},
        )
        return TemplateConnectorToggle.model_validate(data)


class Templates:
    """Manage templates and their attached sub-resources."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http
        self.skills = TemplateSkills(http)
        self.mcps = TemplateMcps(http)
        self.connectors = TemplateConnectors(http)

    def list(self) -> builtins.list[Template]:
        """Return all templates in the current scope (personal or org)."""
        data = self._http.request("GET", "/api/templates")
        return [Template.model_validate(row) for row in data]

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
        preview_ports: builtins.list[int] | None = None,
        permissions: dict[str, Any] | None = None,
        env_vars: dict[str, str] | None = None,
        install_id: int | None = None,
    ) -> TemplateDetail:
        """Create a new template.

        Args:
            name: Human-readable template name (1–255 chars).
            description: Optional free-text description.
            system_prompt: Optional system prompt prefix sent to the runtime.
            repo_url: GitHub ``owner/name``. Omit for a general-purpose
                template with no repo bound.
            repo_ref: Branch / tag / SHA. Defaults server-side to ``main``.
            install_cmd: Shell command run during build to install deps.
            serve_cmd: Optional preview-server command (e.g. ``bun dev``).
            preview_ports: Ports to expose for preview tunnels.
            permissions: Baseline permissions config — see the dashboard for
                presets (``read_only``, ``standard``, ``full_trust``).
            env_vars: Baseline env vars injected into every session.
                Keys must match ``[A-Z_][A-Z0-9_]*``; values are encrypted at
                rest and masked in responses.
            install_id: ID of the :class:`IntegrationInstall` (GitHub App)
                that grants access to ``repo_url``. **Required** when
                ``repo_url`` is set.

        Returns:
            The detail view of the newly created template.
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
                "env_vars": env_vars,
                "install_id": install_id,
            }
        )
        data = self._http.request("POST", "/api/templates", json=body)
        return TemplateDetail.model_validate(data)

    def get(self, template_id: int) -> TemplateDetail:
        """Return the detail view, including skills, MCPs, and connector toggles."""
        data = self._http.request("GET", f"/api/templates/{template_id}")
        return TemplateDetail.model_validate(data)

    def update(self, template_id: int, **fields: Any) -> TemplateDetail:
        """Patch any subset of a template's mutable fields.

        Accepts the same field names as :meth:`create`. For ``env_vars``,
        pass a partial dict to merge it onto the existing vars (a value of
        ``""`` deletes a key); pass ``env_vars={}`` to clear everything.
        Changing ``repo_url``, ``repo_ref``, or ``install_cmd`` rebuilds and
        re-warms every bound agent.
        """
        data = self._http.request(
            "PATCH", f"/api/templates/{template_id}", json=fields,
        )
        return TemplateDetail.model_validate(data)

    def delete(self, template_id: int) -> None:
        """Delete a template.

        The server returns 409 if any agent is still bound to this template;
        detach or delete those agents first.
        """
        self._http.request("DELETE", f"/api/templates/{template_id}")


# ── Async ───────────────────────────────────────────────────────────────────


class AsyncTemplateSkills:
    """Async counterpart to :class:`TemplateSkills`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(self, template_id: int) -> builtins.list[TemplateSkill]:
        data = await self._http.request("GET", f"/api/templates/{template_id}/skills")
        return [TemplateSkill.model_validate(row) for row in data]

    async def create(
        self,
        template_id: int,
        *,
        name: str,
        source: SkillSource,
        content: dict[str, Any],
        enabled: bool = True,
    ) -> TemplateSkill:
        body = {"name": name, "source": source, "content": content, "enabled": enabled}
        data = await self._http.request(
            "POST", f"/api/templates/{template_id}/skills", json=body,
        )
        return TemplateSkill.model_validate(data)

    async def update(
        self,
        template_id: int,
        skill_id: int,
        *,
        name: str | None = None,
        content: dict[str, Any] | None = None,
        enabled: bool | None = None,
    ) -> TemplateSkill:
        body = _prune({"name": name, "content": content, "enabled": enabled})
        data = await self._http.request(
            "PATCH",
            f"/api/templates/{template_id}/skills/{skill_id}",
            json=body,
        )
        return TemplateSkill.model_validate(data)

    async def delete(self, template_id: int, skill_id: int) -> None:
        await self._http.request(
            "DELETE", f"/api/templates/{template_id}/skills/{skill_id}",
        )


class AsyncTemplateMcps:
    """Async counterpart to :class:`TemplateMcps`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(self, template_id: int) -> builtins.list[TemplateMcp]:
        data = await self._http.request("GET", f"/api/templates/{template_id}/mcps")
        return [TemplateMcp.model_validate(row) for row in data]

    async def create(
        self,
        template_id: int,
        *,
        name: str,
        transport: McpTransport,
        config: dict[str, Any],
        secret_ref: str | None = None,
        enabled: bool = True,
    ) -> TemplateMcp:
        body = _prune(
            {
                "name": name,
                "transport": transport,
                "config": config,
                "secret_ref": secret_ref,
                "enabled": enabled,
            }
        )
        data = await self._http.request(
            "POST", f"/api/templates/{template_id}/mcps", json=body,
        )
        return TemplateMcp.model_validate(data)

    async def update(
        self,
        template_id: int,
        mcp_id: int,
        *,
        name: str | None = None,
        config: dict[str, Any] | None = None,
        secret_ref: str | None = None,
        enabled: bool | None = None,
    ) -> TemplateMcp:
        body = _prune(
            {
                "name": name,
                "config": config,
                "secret_ref": secret_ref,
                "enabled": enabled,
            }
        )
        data = await self._http.request(
            "PATCH", f"/api/templates/{template_id}/mcps/{mcp_id}", json=body,
        )
        return TemplateMcp.model_validate(data)

    async def delete(self, template_id: int, mcp_id: int) -> None:
        await self._http.request(
            "DELETE", f"/api/templates/{template_id}/mcps/{mcp_id}",
        )


class AsyncTemplateConnectors:
    """Async counterpart to :class:`TemplateConnectors`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(
        self, template_id: int,
    ) -> builtins.list[TemplateConnectorToggle]:
        data = await self._http.request(
            "GET", f"/api/templates/{template_id}/connectors",
        )
        return [TemplateConnectorToggle.model_validate(row) for row in data]

    async def set(
        self, template_id: int, connector_id: int, *, enabled: bool,
    ) -> TemplateConnectorToggle:
        data = await self._http.request(
            "PUT",
            f"/api/templates/{template_id}/connectors/{connector_id}",
            json={"enabled": enabled},
        )
        return TemplateConnectorToggle.model_validate(data)


class AsyncTemplates:
    """Async counterpart to :class:`Templates`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http
        self.skills = AsyncTemplateSkills(http)
        self.mcps = AsyncTemplateMcps(http)
        self.connectors = AsyncTemplateConnectors(http)

    async def list(self) -> builtins.list[Template]:
        data = await self._http.request("GET", "/api/templates")
        return [Template.model_validate(row) for row in data]

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
        preview_ports: builtins.list[int] | None = None,
        permissions: dict[str, Any] | None = None,
        env_vars: dict[str, str] | None = None,
        install_id: int | None = None,
    ) -> TemplateDetail:
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
                "env_vars": env_vars,
                "install_id": install_id,
            }
        )
        data = await self._http.request("POST", "/api/templates", json=body)
        return TemplateDetail.model_validate(data)

    async def get(self, template_id: int) -> TemplateDetail:
        data = await self._http.request("GET", f"/api/templates/{template_id}")
        return TemplateDetail.model_validate(data)

    async def update(self, template_id: int, **fields: Any) -> TemplateDetail:
        data = await self._http.request(
            "PATCH", f"/api/templates/{template_id}", json=fields,
        )
        return TemplateDetail.model_validate(data)

    async def delete(self, template_id: int) -> None:
        await self._http.request("DELETE", f"/api/templates/{template_id}")


__all__ = [
    "AsyncTemplateConnectors",
    "AsyncTemplateMcps",
    "AsyncTemplateSkills",
    "AsyncTemplates",
    "TemplateConnectors",
    "TemplateMcps",
    "TemplateSkills",
    "Templates",
]
