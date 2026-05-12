"""Sessions resource — ``/api/sessions``.

A session is one live Modal sandbox running an agent. The lifecycle is:
``booting`` → ``running`` → ``snapshotting`` → ``terminated``; resume
re-boots from a snapshot.

This module covers the session record itself plus snapshots; chat (message,
respond, events, transcript) and the preview server (serve_start/stop)
live in :mod:`anyframe.sessions_chat` and :mod:`anyframe.sessions_serve`
imported in below.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any
from uuid import UUID

from ._sse import SSEEvent, parse_sse, parse_sse_async
from .exceptions import AnyFrameError
from .models import ChatEvent, Session, Snapshot

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncIterator, Iterator

    from ._http import AsyncHTTP, SyncHTTP


SessionId = str | UUID

# Anything other than ``running`` after we've started waiting is either a
# transient ``booting`` state (keep polling) or a terminal failure mode that
# means the sandbox will never come up.
_TERMINAL_NON_RUNNING = frozenset({"terminated", "error"})


def _prune(body: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in body.items() if v is not None}


def _sid(session_id: SessionId) -> str:
    return str(session_id)


class Sessions:
    """Manage agent sessions (sandboxes)."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(self) -> list[Session]:
        """Return all sessions owned by the current user, newest first."""
        data = self._http.request("GET", "/api/sessions")
        return [Session.model_validate(row) for row in data]

    def create(
        self,
        *,
        agent_id: int,
        idle_timeout_s: int = 300,
        unsafe: bool = False,
        resume_from_snapshot_id: int | None = None,
    ) -> Session:
        """Boot a new sandbox for an agent.

        Args:
            agent_id: The agent to run.
            idle_timeout_s: Snapshot the sandbox after this many idle seconds.
                Defaults to 5 minutes.
            unsafe: Pass ``--dangerously-skip-permissions`` to the inner Claude
                process. **Strongly** recommended to leave this off.
            resume_from_snapshot_id: Hydrate from a snapshot instead of booting
                a fresh sandbox.

        Returns:
            The created session record. It starts in the ``booting`` state —
            call :meth:`wait_until_running` to block until it's ready.
        """
        body = _prune(
            {
                "agent_id": agent_id,
                "idle_timeout_s": idle_timeout_s,
                "unsafe": unsafe,
                "resume_from_snapshot_id": resume_from_snapshot_id,
            }
        )
        data = self._http.request("POST", "/api/sessions", json=body)
        return Session.model_validate(data)

    def get(self, session_id: SessionId) -> Session:
        """Return the current state of a session."""
        data = self._http.request("GET", f"/api/sessions/{_sid(session_id)}")
        return Session.model_validate(data)

    def terminate(self, session_id: SessionId) -> Session:
        """Snapshot and terminate a session (idempotent)."""
        data = self._http.request("POST", f"/api/sessions/{_sid(session_id)}/terminate")
        return Session.model_validate(data)

    def delete(self, session_id: SessionId) -> None:
        """Hard-delete a session row. Refuses while the sandbox is still live."""
        self._http.request("DELETE", f"/api/sessions/{_sid(session_id)}")

    def resume(self, session_id: SessionId, *, unsafe: bool = False) -> Session:
        """Re-boot a terminated session from its latest snapshot."""
        data = self._http.request(
            "POST", f"/api/sessions/{_sid(session_id)}/resume", json={"unsafe": unsafe}
        )
        return Session.model_validate(data)

    def snapshots(self, session_id: SessionId) -> list[Snapshot]:
        """List snapshots for a session, newest first."""
        data = self._http.request("GET", f"/api/sessions/{_sid(session_id)}/snapshots")
        return [Snapshot.model_validate(row) for row in data]

    def wait_until_running(
        self,
        session_id: SessionId,
        *,
        timeout: float = 180.0,
        poll_interval: float = 1.0,
    ) -> Session:
        """Poll :meth:`get` until the session is in the ``running`` state.

        Args:
            session_id: The session to wait on.
            timeout: Maximum seconds to wait. Defaults to 3 minutes.
            poll_interval: Seconds between polls. Defaults to 1s.

        Returns:
            The running session.

        Raises:
            TimeoutError: If the session is still booting after ``timeout``.
            AnyFrameError: If the session enters a terminal non-running state
                (terminated, error).
        """
        deadline = time.monotonic() + timeout
        while True:
            session = self.get(session_id)
            if session.status == "running":
                return session
            if session.status in _TERMINAL_NON_RUNNING:
                raise AnyFrameError(
                    f"session {session_id} ended in state {session.status!r}",
                )
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"session {session_id} did not reach 'running' within {timeout}s",
                )
            time.sleep(poll_interval)

    # ── chat ──────────────────────────────────────────────────────────────

    def message(self, session_id: SessionId, body: dict[str, Any]) -> dict[str, Any]:
        """Send a user message to the live chat bridge.

        The control plane proxies the body verbatim to the in-sandbox chat
        server, so the exact accepted schema lives there — this method does
        not validate the body.

        Returns:
            The chat server's JSON response (typically ``{"ok": True, "seq": N}``).
        """
        return self._http.request("POST", f"/api/sessions/{_sid(session_id)}/message", json=body)

    def respond(self, session_id: SessionId, body: dict[str, Any]) -> dict[str, Any]:
        """Send a permission-prompt response (approve / reject a tool call)."""
        return self._http.request("POST", f"/api/sessions/{_sid(session_id)}/respond", json=body)

    def transcript(
        self, session_id: SessionId, *, since: int = 0, limit: int = 1000
    ) -> list[ChatEvent]:
        """Return persisted chat events, ordered by ``seq`` ascending.

        Args:
            session_id: The session to read from.
            since: Return events with ``seq > since``. Defaults to 0 (all).
            limit: Maximum events to return. Server caps at 5000.
        """
        data = self._http.request(
            "GET",
            f"/api/sessions/{_sid(session_id)}/transcript",
            params={"since": since, "limit": limit},
        )
        return [ChatEvent.model_validate(row) for row in data]

    def events(
        self, session_id: SessionId, *, last_event_id: str | None = None
    ) -> Iterator[SSEEvent]:
        """Stream chat events as SSE frames in real time.

        Args:
            session_id: The session to subscribe to.
            last_event_id: Resume from this event id (forwarded to the server
                as the ``Last-Event-ID`` header).

        Yields:
            Parsed :class:`SSEEvent` frames. Use :meth:`SSEEvent.json` to
            decode the JSON payload and ``event.id`` to checkpoint progress.
        """
        headers = {"Accept": "text/event-stream"}
        if last_event_id is not None:
            headers["Last-Event-ID"] = last_event_id
        lines = self._http.stream(
            "GET", f"/api/sessions/{_sid(session_id)}/events", headers=headers
        )
        yield from parse_sse(lines)


class AsyncSessions:
    """Async counterpart to :class:`Sessions`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(self) -> list[Session]:
        data = await self._http.request("GET", "/api/sessions")
        return [Session.model_validate(row) for row in data]

    async def create(
        self,
        *,
        agent_id: int,
        idle_timeout_s: int = 300,
        unsafe: bool = False,
        resume_from_snapshot_id: int | None = None,
    ) -> Session:
        body = _prune(
            {
                "agent_id": agent_id,
                "idle_timeout_s": idle_timeout_s,
                "unsafe": unsafe,
                "resume_from_snapshot_id": resume_from_snapshot_id,
            }
        )
        data = await self._http.request("POST", "/api/sessions", json=body)
        return Session.model_validate(data)

    async def get(self, session_id: SessionId) -> Session:
        data = await self._http.request("GET", f"/api/sessions/{_sid(session_id)}")
        return Session.model_validate(data)

    async def terminate(self, session_id: SessionId) -> Session:
        data = await self._http.request("POST", f"/api/sessions/{_sid(session_id)}/terminate")
        return Session.model_validate(data)

    async def delete(self, session_id: SessionId) -> None:
        await self._http.request("DELETE", f"/api/sessions/{_sid(session_id)}")

    async def resume(self, session_id: SessionId, *, unsafe: bool = False) -> Session:
        data = await self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/resume",
            json={"unsafe": unsafe},
        )
        return Session.model_validate(data)

    async def snapshots(self, session_id: SessionId) -> list[Snapshot]:
        data = await self._http.request("GET", f"/api/sessions/{_sid(session_id)}/snapshots")
        return [Snapshot.model_validate(row) for row in data]

    async def wait_until_running(
        self,
        session_id: SessionId,
        *,
        timeout: float = 180.0,
        poll_interval: float = 1.0,
    ) -> Session:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            session = await self.get(session_id)
            if session.status == "running":
                return session
            if session.status in _TERMINAL_NON_RUNNING:
                raise AnyFrameError(
                    f"session {session_id} ended in state {session.status!r}",
                )
            if loop.time() >= deadline:
                raise TimeoutError(
                    f"session {session_id} did not reach 'running' within {timeout}s",
                )
            await asyncio.sleep(poll_interval)

    # ── chat ──────────────────────────────────────────────────────────────

    async def message(self, session_id: SessionId, body: dict[str, Any]) -> dict[str, Any]:
        return await self._http.request(
            "POST", f"/api/sessions/{_sid(session_id)}/message", json=body
        )

    async def respond(self, session_id: SessionId, body: dict[str, Any]) -> dict[str, Any]:
        return await self._http.request(
            "POST", f"/api/sessions/{_sid(session_id)}/respond", json=body
        )

    async def transcript(
        self, session_id: SessionId, *, since: int = 0, limit: int = 1000
    ) -> list[ChatEvent]:
        data = await self._http.request(
            "GET",
            f"/api/sessions/{_sid(session_id)}/transcript",
            params={"since": since, "limit": limit},
        )
        return [ChatEvent.model_validate(row) for row in data]

    async def events(
        self, session_id: SessionId, *, last_event_id: str | None = None
    ) -> AsyncIterator[SSEEvent]:
        headers = {"Accept": "text/event-stream"}
        if last_event_id is not None:
            headers["Last-Event-ID"] = last_event_id
        lines = self._http.stream(
            "GET", f"/api/sessions/{_sid(session_id)}/events", headers=headers
        )
        async for event in parse_sse_async(lines):
            yield event


__all__ = ["AsyncSessions", "SessionId", "Sessions"]
