"""Attention rail — ``/api/attention``.

A curated, newest-first list of items the operator should act on:

  - ``pending``: an unresolved permission_request or ask_user_question. The
    agent is blocked until the operator acts.
  - ``idle``: a running session whose agent finished its last turn and is
    waiting on the user's next prompt.
  - ``paused``: a session that paused within the last 24h — a candidate to
    resume or archive.

The server returns items already ordered (pending, then idle, then paused;
newest first within each group) and trims old paused rows past the window,
so callers can render the response directly without re-sorting.
"""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from .models import AttentionIdleItem, AttentionItem, AttentionPausedItem, AttentionPendingItem

if TYPE_CHECKING:  # pragma: no cover
    from ._http import AsyncHTTP, SyncHTTP


def _parse_item(row: dict[str, object]) -> AttentionItem:
    """Pick the right discriminated-union member by the ``kind`` tag.

    Unknown ``kind`` values raise a Pydantic validation error rather than
    silently mis-typing the row — better to surface the drift loudly than
    paper over it.
    """
    kind = row.get("kind")
    if kind == "paused":
        return AttentionPausedItem.model_validate(row)
    if kind == "idle":
        return AttentionIdleItem.model_validate(row)
    # Default to ``pending`` — server orders pending first and the shape has
    # the loosest field set, so falling through here gives the most useful
    # validation error message when a new kind appears.
    return AttentionPendingItem.model_validate(row)


class Attention:
    """Read the attention rail — items that need the operator."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(self, *, limit: int = 20) -> builtins.list[AttentionItem]:
        """Return up to ``limit`` items, server-ordered.

        Args:
            limit: Maximum items to return. Server clamps to ``[1, 100]``;
                defaults to 20 (matching the API).
        """
        data = self._http.request(
            "GET", "/api/attention", params={"limit": limit}
        )
        return [_parse_item(row) for row in data]


class AsyncAttention:
    """Async counterpart to :class:`Attention`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(self, *, limit: int = 20) -> builtins.list[AttentionItem]:
        data = await self._http.request(
            "GET", "/api/attention", params={"limit": limit}
        )
        return [_parse_item(row) for row in data]


__all__ = ["AsyncAttention", "Attention"]
