"""Server-Sent Events frame parser.

The SDK speaks to two SSE endpoints (build logs and chat events), so we
implement the frame-assembly logic exactly once and reuse it for both the
sync and async transports.

A frame is a sequence of ``field: value`` lines terminated by a blank line.
``event:``, ``data:``, and ``id:`` fields aggregate into a single event
object; comment lines (``:`` prefix) act as keepalive heartbeats and are
silently dropped. Multi-line ``data:`` values are joined with ``"\\n"`` per
the W3C SSE spec.

Why not use an off-the-shelf parser? httpx already gives us a line iterator
and the spec is ~30 lines of code — pulling in another dep would be churn.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncIterable, AsyncIterator, Iterable, Iterator


@dataclass(frozen=True, slots=True)
class SSEEvent:
    """One parsed SSE frame.

    Attributes:
        event: The ``event:`` field, or ``None`` if unset (the SSE default,
            which the spec calls "message").
        data: The concatenated ``data:`` field — multi-line frames are joined
            with ``"\\n"``. Always a string; never ``None``.
        id: The ``id:`` field, used for resumable streams (``Last-Event-ID``).
    """

    event: str | None
    data: str
    id: str | None

    def json(self) -> Any:
        """Decode :attr:`data` as JSON, or return ``None`` if empty.

        Returns:
            The parsed JSON value, or ``None`` when :attr:`data` is the empty
            string (typical for keepalive frames the server still labelled).
        """
        if not self.data:
            return None
        return json.loads(self.data)


def _parse_field(line: str) -> tuple[str, str] | None:
    """Parse one SSE field line into (name, value), or None if it's a comment.

    Per spec, the first whitespace after ``:`` is the separator; any further
    whitespace is part of the value.
    """
    if line.startswith(":"):
        return None  # comment / keepalive
    if ":" not in line:
        # A bare field name with no colon — treat the whole line as the field
        # name with an empty value.
        return line, ""
    name, _, value = line.partition(":")
    if value.startswith(" "):
        value = value[1:]
    return name, value


def _flush(buf: dict[str, list[str]]) -> SSEEvent | None:
    """Convert an accumulated field buffer into an event, or ``None`` if empty."""
    if not buf:
        return None
    data_lines = buf.get("data", [])
    return SSEEvent(
        event=buf["event"][-1] if "event" in buf else None,
        data="\n".join(data_lines),
        id=buf["id"][-1] if "id" in buf else None,
    )


def parse_sse(lines: Iterable[str]) -> Iterator[SSEEvent]:
    """Yield :class:`SSEEvent` instances from a sync iterable of lines.

    Args:
        lines: An iterable producing raw SSE lines (no trailing newlines),
            such as :meth:`httpx.Response.iter_lines`.

    Yields:
        One :class:`SSEEvent` per terminated frame, plus a final event for
        any trailing fields if the stream closes mid-frame.
    """
    buf: dict[str, list[str]] = {}
    for line in lines:
        if line == "":
            event = _flush(buf)
            buf = {}
            if event is not None:
                yield event
            continue
        parsed = _parse_field(line)
        if parsed is None:
            continue
        name, value = parsed
        buf.setdefault(name, []).append(value)
    trailing = _flush(buf)
    if trailing is not None:
        yield trailing


async def parse_sse_async(lines: AsyncIterable[str]) -> AsyncIterator[SSEEvent]:
    """Async counterpart to :func:`parse_sse`."""
    buf: dict[str, list[str]] = {}
    async for line in lines:
        if line == "":
            event = _flush(buf)
            buf = {}
            if event is not None:
                yield event
            continue
        parsed = _parse_field(line)
        if parsed is None:
            continue
        name, value = parsed
        buf.setdefault(name, []).append(value)
    trailing = _flush(buf)
    if trailing is not None:
        yield trailing


__all__ = ["SSEEvent", "parse_sse", "parse_sse_async"]
