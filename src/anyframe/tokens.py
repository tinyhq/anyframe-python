"""Personal API tokens — ``/api/tokens``.

API tokens authenticate this very SDK. Mint one via :meth:`Tokens.create`
(the raw secret is returned exactly once), list them with :meth:`Tokens.list`,
or revoke one with :meth:`Tokens.revoke`. List responses are redacted —
they expose only ``prefix`` and ``last4``, never the secret.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import Token, TokenCreated

if TYPE_CHECKING:  # pragma: no cover
    from ._http import AsyncHTTP, SyncHTTP


class Tokens:
    """Manage personal API tokens for the authenticated user."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(self) -> list[Token]:
        """Return all non-revoked tokens for the current user."""
        data = self._http.request("GET", "/api/tokens")
        return [Token.model_validate(row) for row in data]

    def create(self, *, name: str) -> TokenCreated:
        """Mint a new API token.

        Args:
            name: A human label for the token (visible in the dashboard).

        Returns:
            The new token. The raw secret is on :attr:`TokenCreated.token` —
            it cannot be retrieved later, so store it now.
        """
        data = self._http.request("POST", "/api/tokens", json={"name": name})
        return TokenCreated.model_validate(data)

    def revoke(self, token_id: int) -> None:
        """Soft-delete a token. Subsequent requests using it return 401."""
        self._http.request("DELETE", f"/api/tokens/{token_id}")


class AsyncTokens:
    """Async counterpart to :class:`Tokens`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(self) -> list[Token]:
        data = await self._http.request("GET", "/api/tokens")
        return [Token.model_validate(row) for row in data]

    async def create(self, *, name: str) -> TokenCreated:
        data = await self._http.request("POST", "/api/tokens", json={"name": name})
        return TokenCreated.model_validate(data)

    async def revoke(self, token_id: int) -> None:
        await self._http.request("DELETE", f"/api/tokens/{token_id}")


__all__ = ["AsyncTokens", "Tokens"]
