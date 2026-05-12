"""Typed exception hierarchy raised by the SDK.

All errors derive from :class:`AnyFrameError`, so a single ``except`` clause
catches every failure mode the SDK can produce. Specific subclasses are
raised for the common HTTP failure modes so callers can branch on intent
(auth, not-found, validation) rather than scrape status codes.
"""

from __future__ import annotations

from typing import Any


class AnyFrameError(Exception):
    """Base class for every exception raised by the SDK."""


class APIError(AnyFrameError):
    """A non-2xx response from the control plane.

    Attributes:
        status_code: HTTP status code, or ``0`` for transport-level failures
            (connection refused, DNS, timeout).
        message: Human-readable error message — typically the ``detail`` field
            from a FastAPI ``HTTPException`` response body.
    """

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")


class AuthError(APIError):
    """Authentication failed — bad/missing API key, or revoked token (HTTP 401)."""

    def __init__(self, message: str = "authentication failed") -> None:
        super().__init__(401, message)


class NotFoundError(APIError):
    """The requested resource doesn't exist or isn't visible to this caller (HTTP 404)."""

    def __init__(self, message: str = "not found") -> None:
        super().__init__(404, message)


class ConflictError(APIError):
    """Request conflicts with current resource state (HTTP 409).

    Common cases: terminating an already-terminated session, creating a
    duplicate connector, deleting a session while its sandbox is still live.
    """

    def __init__(self, message: str = "conflict") -> None:
        super().__init__(409, message)


class ValidationError(APIError):
    """Request body or query failed server-side validation (HTTP 400 or 422).

    Attributes:
        details: Raw field-level error list when the server returned a
            structured ``detail`` payload (FastAPI's default for 422). ``None``
            for plain string messages.
    """

    def __init__(self, message: str = "validation failed", details: Any | None = None) -> None:
        super().__init__(422, message)
        self.details = details


class RateLimitError(APIError):
    """Caller is being throttled (HTTP 429).

    Attributes:
        retry_after: Seconds the server suggests waiting before retry, parsed
            from the ``Retry-After`` header. ``None`` when the header is absent.
    """

    def __init__(self, message: str = "rate limited", retry_after: int | None = None) -> None:
        super().__init__(429, message)
        self.retry_after = retry_after


class ServerError(APIError):
    """The control plane failed (HTTP 5xx)."""

    def __init__(self, status_code: int = 500, message: str = "server error") -> None:
        super().__init__(status_code, message)


__all__ = [
    "APIError",
    "AnyFrameError",
    "AuthError",
    "ConflictError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "ValidationError",
]
