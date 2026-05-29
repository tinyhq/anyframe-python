"""Sessions resource — ``/api/sessions``.

A session is one live sandbox running an agent. The lifecycle is:
``booting`` → ``running`` → ``snapshotting`` → ``terminated``; ``resume``
re-boots from a snapshot.

This module covers the session record and snapshots, plus the chat bridge
(``message`` / ``respond`` / ``events`` / ``transcript``), live preview
servers (``previews_*``), and setup-session promotion (``save_as_base``).
"""

from __future__ import annotations

import asyncio
import builtins
import time
from typing import TYPE_CHECKING, Any
from uuid import UUID

from ._sse import SSEEvent, parse_sse, parse_sse_async
from .exceptions import AnyFrameError
from .models import (
    ChatEvent,
    ControlRequest,
    HandoffResult,
    PresenceUser,
    Preview,
    PreviewActionResult,
    PreviewBatchResult,
    PreviewSpec,
    PrivacyResult,
    SaveAsBaseResult,
    Session,
    Snapshot,
)

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncIterator, Iterator

    from ._http import AsyncHTTP, SyncHTTP

# Inside classes that define a ``list()`` method, a bare ``list[T]`` annotation
# is ambiguous to type checkers — it can resolve to the method rather than the
# built-in. We use ``builtins.list[T]`` explicitly in those positions.


SessionId = str | UUID

# Anything other than ``running`` after we've started waiting is either a
# transient ``booting`` state (keep polling) or a terminal failure mode that
# means the sandbox will never come up.
_TERMINAL_NON_RUNNING = frozenset({"terminated", "error"})


def _prune(body: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in body.items() if v is not None}


def _sid(session_id: SessionId) -> str:
    return str(session_id)


def _spec_payload(spec: PreviewSpec | dict[str, Any]) -> dict[str, Any]:
    """Coerce a :class:`PreviewSpec` (or raw dict) into the wire body shape."""
    if isinstance(spec, PreviewSpec):
        return _prune(spec.model_dump())
    return _prune(dict(spec))


class Sessions:
    """Manage agent sessions (sandboxes)."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(self) -> builtins.list[Session]:
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
        is_setup_session: bool = False,
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
            is_setup_session: Mark this session as user-driven setup. Boots
                from the Deps image (ignoring any prior warmup) and unlocks
                :meth:`save_as_base`.

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
                "is_setup_session": is_setup_session or None,
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

    def snapshots(self, session_id: SessionId) -> builtins.list[Snapshot]:
        """List snapshots for a session, newest first."""
        data = self._http.request("GET", f"/api/sessions/{_sid(session_id)}/snapshots")
        return [Snapshot.model_validate(row) for row in data]

    def save_as_base(self, session_id: SessionId) -> SaveAsBaseResult:
        """Snapshot a setup session and promote it to the agent's warmup image.

        Only valid for setup sessions (those created with
        ``is_setup_session=True``). Future normal sessions for the same agent
        will warm-hydrate from the resulting snapshot. Overwrites any prior
        warmup image — setup sessions can re-promote multiple times.
        """
        data = self._http.request("POST", f"/api/sessions/{_sid(session_id)}/save-as-base")
        return SaveAsBaseResult.model_validate(data)

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

    def message(self, session_id: SessionId, body: dict[str, Any]) -> Any:
        """Send a user message to the live chat bridge.

        The control plane proxies the body verbatim to the in-sandbox chat
        server, so the exact accepted schema lives there — this method does
        not validate the body or the response.

        Returns:
            The chat server's JSON response (typically ``{"ok": True, "seq": N}``).
        """
        return self._http.request("POST", f"/api/sessions/{_sid(session_id)}/message", json=body)

    def respond(self, session_id: SessionId, body: dict[str, Any]) -> Any:
        """Send a permission-prompt response (approve / reject a tool call)."""
        return self._http.request("POST", f"/api/sessions/{_sid(session_id)}/respond", json=body)

    def transcript(
        self, session_id: SessionId, *, since: int = 0, limit: int = 1000
    ) -> builtins.list[ChatEvent]:
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

    # ── previews (in-sandbox dev servers) ─────────────────────────────────

    def previews_list(self, session_id: SessionId) -> builtins.list[Preview]:
        """Return every live or stopped preview server for a session."""
        data = self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/previews",
            json={"action": "list"},
        )
        return [Preview.model_validate(row) for row in data]

    def previews_start(
        self,
        session_id: SessionId,
        *,
        cmd: str,
        port: int | None = None,
        name: str | None = None,
    ) -> PreviewActionResult:
        """Start a preview server inside the sandbox.

        When ``port`` is omitted the control plane picks one from the agent's
        ``preview_ports`` (or allocates a new one, which triggers a sandbox
        restart — observable via ``restart_pending=True``).
        """
        data = self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/previews",
            json=_prune({"action": "start", "cmd": cmd, "port": port, "name": name}),
        )
        return PreviewActionResult.model_validate(data)

    def previews_stop(
        self,
        session_id: SessionId,
        *,
        port: int | None = None,
        name: str | None = None,
    ) -> PreviewActionResult:
        """Stop a running preview. Pass either ``port`` or ``name`` to target one."""
        data = self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/previews",
            json=_prune({"action": "stop", "port": port, "name": name}),
        )
        return PreviewActionResult.model_validate(data)

    def previews_status(
        self,
        session_id: SessionId,
        *,
        port: int | None = None,
        name: str | None = None,
    ) -> PreviewActionResult:
        """Probe one preview's current status."""
        data = self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/previews",
            json=_prune({"action": "status", "port": port, "name": name}),
        )
        return PreviewActionResult.model_validate(data)

    def previews_logs(
        self,
        session_id: SessionId,
        *,
        port: int | None = None,
        name: str | None = None,
        tail: int = 200,
    ) -> Any:
        """Return the last ``tail`` lines of a preview's stdout/stderr."""
        return self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/previews",
            json=_prune({"action": "logs", "port": port, "name": name, "tail": tail}),
        )

    def previews_batch_start(
        self,
        session_id: SessionId,
        previews: builtins.list[PreviewSpec | dict[str, Any]],
    ) -> PreviewBatchResult:
        """Start a batch of previews atomically — restart-once semantics."""
        data = self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/previews",
            json={
                "action": "batch_start",
                "previews": [_spec_payload(s) for s in previews],
            },
        )
        return PreviewBatchResult.model_validate(data)

    # ── collaboration (org-scoped) ────────────────────────────────────────

    def presence(self, session_id: SessionId) -> builtins.list[PresenceUser]:
        """List the users currently watching this session.

        Driven by SSE-stream open/close: only members who currently have an
        ``events`` subscription show up. The ``is_driver`` flag points out
        who's allowed to send messages right now. Available in both personal
        and org modes (personal sessions only ever return the caller).
        """
        data = self._http.request(
            "GET", f"/api/sessions/{_sid(session_id)}/presence",
        )
        return [PresenceUser.model_validate(row) for row in data]

    def request_control(
        self, session_id: SessionId, *, message: str | None = None,
    ) -> ControlRequest:
        """Ask the current driver to hand the session off (org sessions only).

        A no-op outside an org context; the server returns 400 in personal
        mode. The driver sees the request in their attention rail and can
        approve it via :meth:`handoff` with the returned ``id``.
        """
        body = _prune({"message": message})
        data = self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/request_control",
            json=body or None,
        )
        return ControlRequest.model_validate(data)

    def handoff(
        self,
        session_id: SessionId,
        *,
        to_user_id: int,
        request_id: int | None = None,
    ) -> HandoffResult:
        """Hand the driver seat to another org member.

        Args:
            session_id: The session.
            to_user_id: The target member's user id.
            request_id: If this handoff resolves a pending
                :meth:`request_control`, pass that request's id so the
                server marks it approved.
        """
        body: dict[str, Any] = {"to_user_id": to_user_id}
        if request_id is not None:
            body["request_id"] = request_id
        data = self._http.request(
            "POST", f"/api/sessions/{_sid(session_id)}/handoff", json=body,
        )
        return HandoffResult.model_validate(data)

    def take_over(self, session_id: SessionId) -> HandoffResult:
        """Forcibly take the driver seat (admin / owner only).

        Audited as a distinct event so a takeover is visible in the org
        audit log even though the session behaves the same afterwards.
        """
        data = self._http.request(
            "POST", f"/api/sessions/{_sid(session_id)}/take_over",
        )
        return HandoffResult.model_validate(data)

    def set_privacy(self, session_id: SessionId, *, private: bool) -> PrivacyResult:
        """Toggle a session's ``private`` flag (creator-only).

        Private org sessions stay in the org but disappear from other
        members' session lists and the activity feed. Admins can still
        see them for audit purposes.
        """
        data = self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/privacy",
            json={"private": private},
        )
        return PrivacyResult.model_validate(data)


class AsyncSessions:
    """Async counterpart to :class:`Sessions`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(self) -> builtins.list[Session]:
        data = await self._http.request("GET", "/api/sessions")
        return [Session.model_validate(row) for row in data]

    async def create(
        self,
        *,
        agent_id: int,
        idle_timeout_s: int = 300,
        unsafe: bool = False,
        resume_from_snapshot_id: int | None = None,
        is_setup_session: bool = False,
    ) -> Session:
        body = _prune(
            {
                "agent_id": agent_id,
                "idle_timeout_s": idle_timeout_s,
                "unsafe": unsafe,
                "resume_from_snapshot_id": resume_from_snapshot_id,
                "is_setup_session": is_setup_session or None,
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

    async def snapshots(self, session_id: SessionId) -> builtins.list[Snapshot]:
        data = await self._http.request("GET", f"/api/sessions/{_sid(session_id)}/snapshots")
        return [Snapshot.model_validate(row) for row in data]

    async def save_as_base(self, session_id: SessionId) -> SaveAsBaseResult:
        data = await self._http.request("POST", f"/api/sessions/{_sid(session_id)}/save-as-base")
        return SaveAsBaseResult.model_validate(data)

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

    async def message(self, session_id: SessionId, body: dict[str, Any]) -> Any:
        return await self._http.request(
            "POST", f"/api/sessions/{_sid(session_id)}/message", json=body
        )

    async def respond(self, session_id: SessionId, body: dict[str, Any]) -> Any:
        return await self._http.request(
            "POST", f"/api/sessions/{_sid(session_id)}/respond", json=body
        )

    async def transcript(
        self, session_id: SessionId, *, since: int = 0, limit: int = 1000
    ) -> builtins.list[ChatEvent]:
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

    # ── previews ──────────────────────────────────────────────────────────

    async def previews_list(self, session_id: SessionId) -> builtins.list[Preview]:
        data = await self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/previews",
            json={"action": "list"},
        )
        return [Preview.model_validate(row) for row in data]

    async def previews_start(
        self,
        session_id: SessionId,
        *,
        cmd: str,
        port: int | None = None,
        name: str | None = None,
    ) -> PreviewActionResult:
        data = await self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/previews",
            json=_prune({"action": "start", "cmd": cmd, "port": port, "name": name}),
        )
        return PreviewActionResult.model_validate(data)

    async def previews_stop(
        self,
        session_id: SessionId,
        *,
        port: int | None = None,
        name: str | None = None,
    ) -> PreviewActionResult:
        data = await self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/previews",
            json=_prune({"action": "stop", "port": port, "name": name}),
        )
        return PreviewActionResult.model_validate(data)

    async def previews_status(
        self,
        session_id: SessionId,
        *,
        port: int | None = None,
        name: str | None = None,
    ) -> PreviewActionResult:
        data = await self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/previews",
            json=_prune({"action": "status", "port": port, "name": name}),
        )
        return PreviewActionResult.model_validate(data)

    async def previews_logs(
        self,
        session_id: SessionId,
        *,
        port: int | None = None,
        name: str | None = None,
        tail: int = 200,
    ) -> Any:
        return await self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/previews",
            json=_prune({"action": "logs", "port": port, "name": name, "tail": tail}),
        )

    async def previews_batch_start(
        self,
        session_id: SessionId,
        previews: builtins.list[PreviewSpec | dict[str, Any]],
    ) -> PreviewBatchResult:
        data = await self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/previews",
            json={
                "action": "batch_start",
                "previews": [_spec_payload(s) for s in previews],
            },
        )
        return PreviewBatchResult.model_validate(data)

    # ── collaboration ────────────────────────────────────────────────────

    async def presence(self, session_id: SessionId) -> builtins.list[PresenceUser]:
        data = await self._http.request(
            "GET", f"/api/sessions/{_sid(session_id)}/presence",
        )
        return [PresenceUser.model_validate(row) for row in data]

    async def request_control(
        self, session_id: SessionId, *, message: str | None = None,
    ) -> ControlRequest:
        body = _prune({"message": message})
        data = await self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/request_control",
            json=body or None,
        )
        return ControlRequest.model_validate(data)

    async def handoff(
        self,
        session_id: SessionId,
        *,
        to_user_id: int,
        request_id: int | None = None,
    ) -> HandoffResult:
        body: dict[str, Any] = {"to_user_id": to_user_id}
        if request_id is not None:
            body["request_id"] = request_id
        data = await self._http.request(
            "POST", f"/api/sessions/{_sid(session_id)}/handoff", json=body,
        )
        return HandoffResult.model_validate(data)

    async def take_over(self, session_id: SessionId) -> HandoffResult:
        data = await self._http.request(
            "POST", f"/api/sessions/{_sid(session_id)}/take_over",
        )
        return HandoffResult.model_validate(data)

    async def set_privacy(
        self, session_id: SessionId, *, private: bool,
    ) -> PrivacyResult:
        data = await self._http.request(
            "POST",
            f"/api/sessions/{_sid(session_id)}/privacy",
            json={"private": private},
        )
        return PrivacyResult.model_validate(data)


__all__ = ["AsyncSessions", "SessionId", "Sessions"]
