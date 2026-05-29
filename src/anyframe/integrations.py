"""Integrations resource — ``/api/integrations``.

An **integration install** is one OAuth/App install of a third-party
service (a GitHub App on an org, a Slack workspace bot, …) that the
control plane uses to mint short-lived tokens at sandbox boot time.

The most common path: install a GitHub App, then point a
:class:`anyframe.Template` at one of its repos by passing
``install_id=`` to :meth:`anyframe.templates.Templates.create`.

The OAuth dance itself runs in a browser; this SDK exposes the read /
delete surface plus the GitHub repo picker.
"""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from .models import (
    GithubInstall,
    GithubRepo,
    IntegrationBinding,
    IntegrationInstall,
    ProviderApp,
)

if TYPE_CHECKING:  # pragma: no cover
    from ._http import AsyncHTTP, SyncHTTP


class Integrations:
    """Manage integration installs and provider-app bindings."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    # ── installs ──────────────────────────────────────────────────────────

    def list(self) -> builtins.list[IntegrationInstall]:
        """List every integration install in the current scope (personal or org)."""
        data = self._http.request("GET", "/api/integrations")
        return [IntegrationInstall.model_validate(row) for row in data]

    def delete(self, install_id: int) -> None:
        """Revoke and delete an install."""
        self._http.request("DELETE", f"/api/integrations/{install_id}")

    # ── GitHub ────────────────────────────────────────────────────────────

    def list_github_installs(self) -> builtins.list[GithubInstall]:
        """List GitHub App installs available to bind to a template.

        Returns the slim shape the template-create flow uses — each entry
        carries the GitHub-side ``installation_id`` and the account login
        (the user or org the App was installed under).
        """
        data = self._http.request("GET", "/api/integrations/github/installs")
        return [GithubInstall.model_validate(row) for row in data]

    def list_github_repos(self, install_id: int) -> builtins.list[GithubRepo]:
        """List the repos a GitHub App install can access.

        Calls GitHub's ``/installation/repositories`` server-side with a
        freshly-minted installation token. Paginates internally so the full
        set comes back in one round-trip.
        """
        data = self._http.request(
            "GET", f"/api/integrations/github/installs/{install_id}/repos",
        )
        return [GithubRepo.model_validate(row) for row in data]

    # ── webhook routing ─────────────────────────────────────────────────

    def set_binding(self, install_id: int, *, agent_id: int) -> IntegrationBinding:
        """Bind (or re-bind) an install's events to a single agent.

        Each install has at most one agent binding (1:1, "steal" semantics).
        Pointing the install at a different agent updates the existing row.
        """
        data = self._http.request(
            "POST",
            f"/api/integrations/{install_id}/binding",
            json={"agent_id": agent_id},
        )
        return IntegrationBinding.model_validate(data)

    def delete_binding(self, install_id: int) -> None:
        """Unbind an install — the install stays connected but events are dropped."""
        self._http.request("DELETE", f"/api/integrations/{install_id}/binding")

    # ── provider apps (advanced) ────────────────────────────────────────

    def list_provider_apps(self) -> builtins.list[ProviderApp]:
        """List the provider apps registered in the current scope.

        Most callers don't need this — provider apps are the AnyFrame side
        of the OAuth/App config (a single Slack workspace app or GitHub App
        you've registered with credentials). End users install *into* one
        of these via the browser flow.
        """
        data = self._http.request("GET", "/api/integrations/provider_apps")
        return [ProviderApp.model_validate(row) for row in data]


class AsyncIntegrations:
    """Async counterpart to :class:`Integrations`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(self) -> builtins.list[IntegrationInstall]:
        data = await self._http.request("GET", "/api/integrations")
        return [IntegrationInstall.model_validate(row) for row in data]

    async def delete(self, install_id: int) -> None:
        await self._http.request("DELETE", f"/api/integrations/{install_id}")

    async def list_github_installs(self) -> builtins.list[GithubInstall]:
        data = await self._http.request("GET", "/api/integrations/github/installs")
        return [GithubInstall.model_validate(row) for row in data]

    async def list_github_repos(self, install_id: int) -> builtins.list[GithubRepo]:
        data = await self._http.request(
            "GET", f"/api/integrations/github/installs/{install_id}/repos",
        )
        return [GithubRepo.model_validate(row) for row in data]

    async def set_binding(
        self, install_id: int, *, agent_id: int,
    ) -> IntegrationBinding:
        data = await self._http.request(
            "POST",
            f"/api/integrations/{install_id}/binding",
            json={"agent_id": agent_id},
        )
        return IntegrationBinding.model_validate(data)

    async def delete_binding(self, install_id: int) -> None:
        await self._http.request("DELETE", f"/api/integrations/{install_id}/binding")

    async def list_provider_apps(self) -> builtins.list[ProviderApp]:
        data = await self._http.request("GET", "/api/integrations/provider_apps")
        return [ProviderApp.model_validate(row) for row in data]


__all__ = ["AsyncIntegrations", "Integrations"]
