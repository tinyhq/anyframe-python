"""Per-user Claude / Codex runtime credentials — ``/api/credentials``.

The control plane needs at least one runtime token (Claude OAuth or Codex
API key) to run agents. This resource sets, clears, or inspects each one.
The server never returns the raw tokens — :meth:`Credentials.get` returns
a redacted view (``set`` flag, ``last4``, ``updated_at``).

Personal scope only. To manage an org's credentials see
:class:`anyframe.orgs.OrgCredentialsResource`.

GitHub repo access is no longer a credential — it's an *integration*
install (a GitHub App). See :class:`anyframe.integrations.Integrations`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import Credentials as CredentialsModel

if TYPE_CHECKING:  # pragma: no cover
    from ._http import AsyncHTTP, SyncHTTP


class Credentials:
    """Manage the caller's personal runtime credentials."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def get(self) -> CredentialsModel:
        """Return the redacted credential metadata for the current user."""
        data = self._http.request("GET", "/api/credentials")
        return CredentialsModel.model_validate(data)

    def set_claude(self, token: str) -> None:
        """Store a Claude OAuth token. Agents on the Claude runtime require one."""
        self._http.request("PUT", "/api/credentials/claude", json={"token": token})

    def set_codex(self, token: str) -> None:
        """Store an OpenAI Codex token. Required for agents on the Codex runtime."""
        self._http.request("PUT", "/api/credentials/codex", json={"token": token})

    def clear_claude(self) -> None:
        """Delete the stored Claude token."""
        self._http.request("DELETE", "/api/credentials/claude")

    def clear_codex(self) -> None:
        """Delete the stored Codex token."""
        self._http.request("DELETE", "/api/credentials/codex")


class AsyncCredentials:
    """Async counterpart to :class:`Credentials`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def get(self) -> CredentialsModel:
        data = await self._http.request("GET", "/api/credentials")
        return CredentialsModel.model_validate(data)

    async def set_claude(self, token: str) -> None:
        await self._http.request(
            "PUT",
            "/api/credentials/claude",
            json={"token": token},
        )

    async def set_codex(self, token: str) -> None:
        await self._http.request(
            "PUT",
            "/api/credentials/codex",
            json={"token": token},
        )

    async def clear_claude(self) -> None:
        await self._http.request("DELETE", "/api/credentials/claude")

    async def clear_codex(self) -> None:
        await self._http.request("DELETE", "/api/credentials/codex")


__all__ = ["AsyncCredentials", "Credentials"]
