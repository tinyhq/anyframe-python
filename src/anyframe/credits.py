"""Credits resource — ``/api/credits``.

A thin read-only view on the free-trial credit pool. In personal scope it
reflects the caller's own balance; in org scope it reflects the active
org's shared pool. When the org has its own runtime token set,
``org_token_active`` is ``True`` and sessions don't consume from this pool.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import CreditBalance

if TYPE_CHECKING:  # pragma: no cover
    from ._http import AsyncHTTP, SyncHTTP


class Credits:
    """Synchronous credits resource."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def get(self) -> CreditBalance:
        """Return the current credit balance for the active scope."""
        data = self._http.request("GET", "/api/credits")
        return CreditBalance.model_validate(data)


class AsyncCredits:
    """Async counterpart to :class:`Credits`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def get(self) -> CreditBalance:
        data = await self._http.request("GET", "/api/credits")
        return CreditBalance.model_validate(data)


__all__ = ["AsyncCredits", "Credits"]
