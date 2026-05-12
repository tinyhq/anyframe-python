"""Per-user Claude / GitHub credentials — ``/api/credentials``.

The control plane needs a Claude OAuth token to run agents, and a GitHub
PAT to clone private repos. This resource sets, clears, or inspects each
one. The server never returns the raw tokens — :meth:`Credentials.get`
returns a redacted view (``set`` flag, ``last4``, ``updated_at``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import Credentials as CredentialsModel

if TYPE_CHECKING:  # pragma: no cover
    from ._http import AsyncHTTP, SyncHTTP


class Credentials:
    """Manage the per-user Claude and GitHub credentials."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def get(self) -> CredentialsModel:
        """Return the redacted credential metadata for the current user."""
        data = self._http.request("GET", "/api/credentials")
        return CredentialsModel.model_validate(data)

    def set_claude(self, token: str) -> None:
        """Store a Claude OAuth token. Agents cannot run without one."""
        self._http.request("PUT", "/api/credentials/claude", json={"token": token})

    def set_github(self, token: str) -> None:
        """Store a GitHub PAT. Required for cloning private repos / builds."""
        self._http.request("PUT", "/api/credentials/github", json={"token": token})

    def clear_claude(self) -> None:
        """Delete the stored Claude token."""
        self._http.request("DELETE", "/api/credentials/claude")

    def clear_github(self) -> None:
        """Delete the stored GitHub token."""
        self._http.request("DELETE", "/api/credentials/github")


class AsyncCredentials:
    """Async counterpart to :class:`Credentials`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def get(self) -> CredentialsModel:
        data = await self._http.request("GET", "/api/credentials")
        return CredentialsModel.model_validate(data)

    async def set_claude(self, token: str) -> None:
        await self._http.request("PUT", "/api/credentials/claude", json={"token": token})

    async def set_github(self, token: str) -> None:
        await self._http.request("PUT", "/api/credentials/github", json={"token": token})

    async def clear_claude(self) -> None:
        await self._http.request("DELETE", "/api/credentials/claude")

    async def clear_github(self) -> None:
        await self._http.request("DELETE", "/api/credentials/github")


__all__ = ["AsyncCredentials", "Credentials"]
