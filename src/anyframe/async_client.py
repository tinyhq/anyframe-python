"""The top-level asynchronous :class:`AsyncAnyFrame` client.

Mirrors :class:`anyframe.AnyFrame` one-for-one — every method on every
resource has the same signature, just with ``await``. This way switching
between sync and async is a search-and-replace, not a re-architecture.

Construction reads the same ``ANYFRAME_API_KEY`` / ``ANYFRAME_BASE_URL``
env vars and honours ``.env`` files identically.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from dotenv import find_dotenv as _dotenv_find
from dotenv import load_dotenv as _dotenv_load

from ._http import AsyncHTTP
from .agents import AsyncAgents
from .attention import AsyncAttention
from .client import (
    DEFAULT_BASE_URL,
    ENV_API_KEY,
    ENV_BASE_URL,
    _configure_logging,
)
from .connectors import AsyncConnectors
from .credentials import AsyncCredentials
from .credits import AsyncCredits
from .exceptions import AuthError
from .integrations import AsyncIntegrations
from .models import PublicConfig, User
from .orgs import AsyncOrgs
from .sessions import AsyncSessions
from .templates import AsyncTemplates
from .tokens import AsyncTokens

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

logger = logging.getLogger("anyframe")


class AsyncAnyFrame:
    """Asynchronous client for the AnyFrame control plane.

    Args:
        api_key: Personal API token. Falls back to ``ANYFRAME_API_KEY``.
        base_url: Override the control-plane URL.
        timeout: Per-request timeout in seconds. Defaults to 30s.
        load_dotenv: If ``True`` (default), load a ``.env`` file from the
            current working directory before reading env vars.

    Raises:
        AuthError: If no API key was provided and ``ANYFRAME_API_KEY`` is unset.

    Example:
        >>> import anyframe, asyncio
        >>> async def main():
        ...     async with anyframe.AsyncAnyFrame() as af:
        ...         me = await af.me()
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
        load_dotenv: bool = True,
    ) -> None:
        if load_dotenv:
            _dotenv_load(dotenv_path=_dotenv_find(usecwd=True), override=False)
        _configure_logging()

        resolved_key = api_key or os.environ.get(ENV_API_KEY)
        if not resolved_key:
            raise AuthError(
                f"missing API key — pass api_key=... or set {ENV_API_KEY} in your environment",
            )
        resolved_base = base_url or os.environ.get(ENV_BASE_URL) or DEFAULT_BASE_URL

        logger.info("anyframe async client initialised (base_url=%s)", resolved_base)
        self._http = AsyncHTTP(base_url=resolved_base, api_key=resolved_key, timeout=timeout)

        # ── resources ─────────────────────────────────────────────────────
        self.tokens = AsyncTokens(self._http)
        self.credentials = AsyncCredentials(self._http)
        self.credits = AsyncCredits(self._http)
        self.connectors = AsyncConnectors(self._http)
        self.templates = AsyncTemplates(self._http)
        self.agents = AsyncAgents(self._http)
        self.sessions = AsyncSessions(self._http)
        self.attention = AsyncAttention(self._http)
        self.integrations = AsyncIntegrations(self._http)
        self.orgs = AsyncOrgs(self._http)

    # ── identity ──────────────────────────────────────────────────────────

    async def me(self) -> User:
        """Return the hydrated identity for the authenticated caller."""
        data = await self._http.request("GET", "/api/me")
        return User.model_validate(data)

    async def set_active_org(self, org_id: int | None) -> User:
        """Switch the active workspace context (personal ↔ org)."""
        data = await self._http.request(
            "POST", "/api/me/active_org", json={"org_id": org_id},
        )
        return User.model_validate(data)

    async def public_config(self) -> PublicConfig:
        """Return the server's public feature flags (unauthenticated)."""
        data = await self._http.request("GET", "/api/config/public")
        return PublicConfig.model_validate(data)

    # ── lifecycle ─────────────────────────────────────────────────────────

    async def aclose(self) -> None:
        """Close the underlying async HTTP connection pool."""
        await self._http.aclose()

    async def __aenter__(self) -> AsyncAnyFrame:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()


__all__ = ["AsyncAnyFrame"]
