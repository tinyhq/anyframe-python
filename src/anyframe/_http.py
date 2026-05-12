"""Internal HTTP transport — sync and async wrappers around httpx.

This module is private: callers go through :class:`anyframe.AnyFrame` and
:class:`anyframe.AsyncAnyFrame`. The two classes here, :class:`SyncHTTP`
and :class:`AsyncHTTP`, share an identical request/response contract so
the resource modules can be written once per surface and instantiated
against either client.

Responsibilities:
  * attach ``Authorization: Bearer <api_key>`` and a stable ``User-Agent``
  * map non-2xx responses to typed exceptions from :mod:`anyframe.exceptions`
  * normalise empty responses (204, no body) to ``None``
  * log one ``DEBUG``-level line per request, including method, path, status,
    and elapsed wall-clock time
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

import httpx

from . import exceptions as exc
from ._version import __version__

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncIterator, Iterator

logger = logging.getLogger("anyframe.http")

_DEFAULT_TIMEOUT = 30.0


def _user_agent() -> str:
    return f"anyframe-python/{__version__}"


def _headers(api_key: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    h = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": _user_agent(),
        "Accept": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def _detail(resp: httpx.Response) -> tuple[str, Any]:
    """Extract a human message and (if available) structured details from a
    FastAPI error response.

    Returns:
        A ``(message, details)`` tuple. ``details`` is the raw ``detail`` field
        when it's structured (e.g. Pydantic 422 list); otherwise ``None``.
    """
    try:
        body = resp.json()
    except ValueError:
        return resp.text or resp.reason_phrase, None
    if isinstance(body, dict) and "detail" in body:
        d = body["detail"]
        if isinstance(d, str):
            return d, None
        return f"validation failed ({len(d)} issue(s))" if isinstance(d, list) else str(d), d
    return resp.text or resp.reason_phrase, None


def _raise_for_status(resp: httpx.Response) -> None:
    """Map an httpx response onto a typed exception, or return on 2xx."""
    if resp.is_success:
        return
    message, details = _detail(resp)
    status = resp.status_code
    if status == 401:
        raise exc.AuthError(message)
    if status == 404:
        raise exc.NotFoundError(message)
    if status == 409:
        raise exc.ConflictError(message)
    if status in (400, 422):
        raise exc.ValidationError(message, details=details, status_code=status)
    if status == 429:
        retry_after_hdr = resp.headers.get("Retry-After")
        retry_after = (
            int(retry_after_hdr) if retry_after_hdr and retry_after_hdr.isdigit() else None
        )
        raise exc.RateLimitError(message, retry_after=retry_after)
    if status >= 500:
        raise exc.ServerError(status, message)
    raise exc.APIError(status, message)


def _parse_body(resp: httpx.Response) -> Any:
    """Return parsed JSON, or ``None`` for empty / 204 responses."""
    if resp.status_code == 204 or not resp.content:
        return None
    return resp.json()


def _log_response(method: str, path: str, status: int, elapsed_ms: float) -> None:
    logger.debug("%s %s -> %s (%.0fms)", method.upper(), path, status, elapsed_ms)


# ── sync ────────────────────────────────────────────────────────────────────


class SyncHTTP:
    """Synchronous HTTP transport. Thread-safe within a single httpx client."""

    def __init__(self, *, base_url: str, api_key: str, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=_headers(api_key),
            timeout=timeout,
        )

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Issue a request and return the parsed body (or ``None``)."""
        start = time.perf_counter()
        try:
            resp = self._client.request(method, path, **kwargs)
        except httpx.ConnectError as e:
            raise exc.APIError(0, f"connection failed: {e}") from e
        except httpx.TimeoutException as e:
            raise exc.APIError(0, f"request timed out: {e}") from e
        elapsed = (time.perf_counter() - start) * 1000.0
        _log_response(method, path, resp.status_code, elapsed)
        _raise_for_status(resp)
        return _parse_body(resp)

    def stream(self, method: str, path: str, **kwargs: Any) -> Iterator[str]:
        """Yield SSE lines from a streaming endpoint.

        Caller is responsible for parsing the SSE frames (see :mod:`anyframe._sse`).
        Raises typed exceptions on non-2xx initial responses.
        """
        with self._client.stream(method, path, **kwargs) as resp:
            _log_response(method, path, resp.status_code, 0.0)
            _raise_for_status(resp)
            yield from resp.iter_lines()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> SyncHTTP:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


# ── async ───────────────────────────────────────────────────────────────────


class AsyncHTTP:
    """Async HTTP transport. Mirrors :class:`SyncHTTP` one-for-one."""

    def __init__(self, *, base_url: str, api_key: str, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers=_headers(api_key),
            timeout=timeout,
        )

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            resp = await self._client.request(method, path, **kwargs)
        except httpx.ConnectError as e:
            raise exc.APIError(0, f"connection failed: {e}") from e
        except httpx.TimeoutException as e:
            raise exc.APIError(0, f"request timed out: {e}") from e
        elapsed = (time.perf_counter() - start) * 1000.0
        _log_response(method, path, resp.status_code, elapsed)
        _raise_for_status(resp)
        return _parse_body(resp)

    async def stream(self, method: str, path: str, **kwargs: Any) -> AsyncIterator[str]:
        async with self._client.stream(method, path, **kwargs) as resp:
            _log_response(method, path, resp.status_code, 0.0)
            _raise_for_status(resp)
            async for line in resp.aiter_lines():
                yield line

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncHTTP:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()


__all__ = ["AsyncHTTP", "SyncHTTP"]
