"""User-level MCP connectors — ``/api/connectors``.

A connector points an agent at an MCP server (Linear, Sentry, a custom HTTP
server, …). The setup happens once at the user (or org) level here; each
template then opts each connector on or off via
:class:`anyframe.templates.TemplateConnectors`, and every agent bound to
the template inherits the resolved set.

Four auth flows are supported:

  - **OAuth DCR / pre-registered**: :meth:`Connectors.discover` to probe
    the MCP server, then :meth:`Connectors.create_oauth` to register a
    dynamic client and get an ``authorize_url`` to open in a browser.
  - **Bearer**: :meth:`Connectors.create_bearer` with a pre-issued token,
    for servers that speak ``Authorization: Bearer …``.
  - **Custom header**: :meth:`Connectors.create_custom_header` for servers
    that expect a non-standard header (e.g. ``X-API-Key``).
  - **Stdio**: :meth:`Connectors.create_stdio` to spawn a local command
    inside the sandbox and speak MCP over its stdio.

A curated **catalog** of connectors ships with the control plane — Linear,
Sentry, Google, etc. Use :meth:`Connectors.list_catalog` to list them and
:meth:`Connectors.install_catalog_oauth` /
:meth:`Connectors.install_catalog_bearer` to install one by slug.

If a refresh hard-fails (provider revoked the app, etc.) rerun the OAuth
dance with :meth:`Connectors.reauthorize` — the connector row, its display
name, and every per-template toggle are preserved.
"""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from .models import (
    Connector,
    ConnectorAuthorize,
    ConnectorCatalogItem,
    ConnectorDiscovery,
)

if TYPE_CHECKING:  # pragma: no cover
    from ._http import AsyncHTTP, SyncHTTP


class Connectors:
    """Manage user-level MCP connectors."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(self) -> builtins.list[Connector]:
        """Return every connector the user has set up."""
        data = self._http.request("GET", "/api/connectors")
        return [Connector.model_validate(row) for row in data]

    def list_catalog(self) -> builtins.list[ConnectorCatalogItem]:
        """Return the curated catalog of installable connectors.

        Each entry carries an ``installed`` flag (and the existing
        ``connector_id`` when installed) so callers can render install /
        manage states without a second lookup.
        """
        data = self._http.request("GET", "/api/connectors/catalog")
        return [ConnectorCatalogItem.model_validate(row) for row in data]

    def discover(self, mcp_url: str) -> ConnectorDiscovery:
        """Probe an MCP URL for OAuth metadata and DCR support.

        Args:
            mcp_url: The MCP server URL (HTTP or SSE).

        Returns:
            A discovery record showing whether the server supports OAuth DCR
            (use :meth:`create_oauth`) or whether you'll need to paste a
            bearer token (use :meth:`create_bearer`).
        """
        data = self._http.request("POST", "/api/connectors/discover", json={"mcp_url": mcp_url})
        return ConnectorDiscovery.model_validate(data)

    def create_oauth(
        self,
        *,
        mcp_url: str,
        display_name: str,
        default_enabled: bool = True,
    ) -> ConnectorAuthorize:
        """Register a new OAuth-flow connector and return an ``authorize_url``.

        Open the URL in a browser; on success the server stores tokens and
        redirects back to the dashboard.
        """
        data = self._http.request(
            "POST",
            "/api/connectors/oauth",
            json={
                "mcp_url": mcp_url,
                "display_name": display_name,
                "default_enabled": default_enabled,
            },
        )
        return ConnectorAuthorize.model_validate(data)

    def create_bearer(
        self,
        *,
        mcp_url: str,
        display_name: str,
        token: str,
        default_enabled: bool = True,
    ) -> Connector:
        """Create a bearer-token connector with a pre-issued token."""
        data = self._http.request(
            "POST",
            "/api/connectors/bearer",
            json={
                "mcp_url": mcp_url,
                "display_name": display_name,
                "token": token,
                "default_enabled": default_enabled,
            },
        )
        return Connector.model_validate(data)

    def create_custom_header(
        self,
        *,
        mcp_url: str,
        display_name: str,
        header_name: str,
        token: str,
        default_enabled: bool = True,
    ) -> Connector:
        """Create a connector that authenticates with a custom header.

        Args:
            mcp_url: The MCP server URL.
            display_name: Label shown in the dashboard.
            header_name: The header to inject (e.g. ``"X-API-Key"``).
            token: The header value. Encrypted at rest, masked in responses.
            default_enabled: Whether new templates pick this connector up
                by default. Toggle per-template afterwards via
                :class:`anyframe.templates.TemplateConnectors`.
        """
        data = self._http.request(
            "POST",
            "/api/connectors/custom-header",
            json={
                "mcp_url": mcp_url,
                "display_name": display_name,
                "header_name": header_name,
                "token": token,
                "default_enabled": default_enabled,
            },
        )
        return Connector.model_validate(data)

    def create_stdio(
        self,
        *,
        display_name: str,
        command: str,
        args: builtins.list[str] | None = None,
        env: dict[str, str] | None = None,
        default_enabled: bool = True,
    ) -> Connector:
        """Create a stdio connector — spawns ``command args…`` inside the sandbox.

        Args:
            display_name: Label shown in the dashboard.
            command: Executable path or name (must be 1-255 chars).
            args: Command-line arguments passed to ``command``.
            env: Environment variables exposed to the spawned process.
                Values are encrypted at rest.
            default_enabled: Whether new templates pick this connector up
                by default.
        """
        data = self._http.request(
            "POST",
            "/api/connectors/stdio",
            json={
                "display_name": display_name,
                "command": command,
                "args": args or [],
                "env": env or {},
                "default_enabled": default_enabled,
            },
        )
        return Connector.model_validate(data)

    def install_catalog_oauth(self, slug: str) -> ConnectorAuthorize:
        """Install a catalog connector that uses OAuth (DCR or pre-registered).

        The catalog entry supplies the MCP URL and display name; only the
        slug is needed. Returns an ``authorize_url`` to open in a browser.
        """
        data = self._http.request("POST", f"/api/connectors/catalog/{slug}/oauth")
        return ConnectorAuthorize.model_validate(data)

    def install_catalog_bearer(self, slug: str, *, token: str) -> Connector:
        """Install a catalog connector that authenticates with a bearer token."""
        data = self._http.request(
            "POST",
            f"/api/connectors/catalog/{slug}/bearer",
            json={"token": token},
        )
        return Connector.model_validate(data)

    def reauthorize(self, connector_id: int) -> ConnectorAuthorize:
        """Rerun the OAuth dance on an existing connector row.

        Useful when refresh tokens expire or the provider revokes the app —
        the connector row, its display name, and every per-agent toggle are
        preserved.
        """
        data = self._http.request("POST", f"/api/connectors/{connector_id}/reauthorize")
        return ConnectorAuthorize.model_validate(data)

    def delete(self, connector_id: int) -> None:
        """Delete a connector. Best-effort RFC 7592 revocation runs server-side."""
        self._http.request("DELETE", f"/api/connectors/{connector_id}")


class AsyncConnectors:
    """Async counterpart to :class:`Connectors`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(self) -> builtins.list[Connector]:
        data = await self._http.request("GET", "/api/connectors")
        return [Connector.model_validate(row) for row in data]

    async def list_catalog(self) -> builtins.list[ConnectorCatalogItem]:
        data = await self._http.request("GET", "/api/connectors/catalog")
        return [ConnectorCatalogItem.model_validate(row) for row in data]

    async def discover(self, mcp_url: str) -> ConnectorDiscovery:
        data = await self._http.request(
            "POST", "/api/connectors/discover", json={"mcp_url": mcp_url}
        )
        return ConnectorDiscovery.model_validate(data)

    async def create_oauth(
        self,
        *,
        mcp_url: str,
        display_name: str,
        default_enabled: bool = True,
    ) -> ConnectorAuthorize:
        data = await self._http.request(
            "POST",
            "/api/connectors/oauth",
            json={
                "mcp_url": mcp_url,
                "display_name": display_name,
                "default_enabled": default_enabled,
            },
        )
        return ConnectorAuthorize.model_validate(data)

    async def create_bearer(
        self,
        *,
        mcp_url: str,
        display_name: str,
        token: str,
        default_enabled: bool = True,
    ) -> Connector:
        data = await self._http.request(
            "POST",
            "/api/connectors/bearer",
            json={
                "mcp_url": mcp_url,
                "display_name": display_name,
                "token": token,
                "default_enabled": default_enabled,
            },
        )
        return Connector.model_validate(data)

    async def create_custom_header(
        self,
        *,
        mcp_url: str,
        display_name: str,
        header_name: str,
        token: str,
        default_enabled: bool = True,
    ) -> Connector:
        data = await self._http.request(
            "POST",
            "/api/connectors/custom-header",
            json={
                "mcp_url": mcp_url,
                "display_name": display_name,
                "header_name": header_name,
                "token": token,
                "default_enabled": default_enabled,
            },
        )
        return Connector.model_validate(data)

    async def create_stdio(
        self,
        *,
        display_name: str,
        command: str,
        args: builtins.list[str] | None = None,
        env: dict[str, str] | None = None,
        default_enabled: bool = True,
    ) -> Connector:
        data = await self._http.request(
            "POST",
            "/api/connectors/stdio",
            json={
                "display_name": display_name,
                "command": command,
                "args": args or [],
                "env": env or {},
                "default_enabled": default_enabled,
            },
        )
        return Connector.model_validate(data)

    async def install_catalog_oauth(self, slug: str) -> ConnectorAuthorize:
        data = await self._http.request("POST", f"/api/connectors/catalog/{slug}/oauth")
        return ConnectorAuthorize.model_validate(data)

    async def install_catalog_bearer(self, slug: str, *, token: str) -> Connector:
        data = await self._http.request(
            "POST",
            f"/api/connectors/catalog/{slug}/bearer",
            json={"token": token},
        )
        return Connector.model_validate(data)

    async def reauthorize(self, connector_id: int) -> ConnectorAuthorize:
        data = await self._http.request("POST", f"/api/connectors/{connector_id}/reauthorize")
        return ConnectorAuthorize.model_validate(data)

    async def delete(self, connector_id: int) -> None:
        await self._http.request("DELETE", f"/api/connectors/{connector_id}")


__all__ = ["AsyncConnectors", "Connectors"]
