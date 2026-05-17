"""The top-level synchronous :class:`AnyFrame` client.

Construction is the only place env-var resolution happens: callers either
pass ``api_key`` / ``base_url`` explicitly or rely on the ``ANYFRAME_API_KEY``
and ``ANYFRAME_BASE_URL`` environment variables. A ``.env`` file in the
current working directory is loaded automatically (matching the AnyFrame
control-plane server's own behaviour); pass ``load_dotenv=False`` to skip
that step when embedding the SDK inside a library.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from dotenv import find_dotenv as _dotenv_find
from dotenv import load_dotenv as _dotenv_load

from ._http import SyncHTTP
from .agents import Agents
from .attention import Attention
from .connectors import Connectors
from .credentials import Credentials
from .exceptions import AuthError
from .models import User
from .sessions import Sessions
from .tokens import Tokens

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

logger = logging.getLogger("anyframe")

DEFAULT_BASE_URL = "https://api.anyfrm.com"

# Env var names — kept in one place so the docs, tests, and the resource
# init message all agree.
ENV_API_KEY = "ANYFRAME_API_KEY"
ENV_BASE_URL = "ANYFRAME_BASE_URL"
ENV_LOG_LEVEL = "ANYFRAME_LOG_LEVEL"


def _configure_logging() -> None:
    """Attach a default handler if the caller didn't configure logging.

    The log level is read from ``ANYFRAME_LOG_LEVEL`` (defaults to INFO) so
    users can enable per-request DEBUG traces without touching their code.
    """
    level_name = os.environ.get(ENV_LOG_LEVEL, "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)
    if not logger.handlers and not logging.getLogger().handlers:
        # Only add our own handler if the root logger is also unconfigured —
        # otherwise we'd double-emit in apps that already use logging.basicConfig.
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
        logger.addHandler(h)


class AnyFrame:
    """Synchronous client for the AnyFrame control plane.

    Args:
        api_key: Personal API token (starts with ``afm_``). When omitted, the
            value of the ``ANYFRAME_API_KEY`` environment variable is used.
        base_url: Override the control-plane URL. When omitted, the value of
            ``ANYFRAME_BASE_URL`` is used, falling back to ``https://api.anyfrm.com``.
        timeout: Per-request timeout in seconds. Defaults to 30s.
        load_dotenv: If ``True`` (default), load a ``.env`` file from the
            current working directory before reading env vars. Set to ``False``
            inside libraries that don't want their environment touched.

    Raises:
        AuthError: If no API key was provided and ``ANYFRAME_API_KEY`` is unset.

    Example:
        >>> import anyframe
        >>> with anyframe.AnyFrame() as af:
        ...     me = af.me()
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
            # Search from the current working directory so apps that run from
            # their project root pick up a .env there. ``override=False`` matches
            # python-dotenv's default and the API server's behaviour: shell env
            # wins, .env fills the gaps.
            _dotenv_load(dotenv_path=_dotenv_find(usecwd=True), override=False)
        _configure_logging()

        resolved_key = api_key or os.environ.get(ENV_API_KEY)
        if not resolved_key:
            raise AuthError(
                f"missing API key — pass api_key=... or set {ENV_API_KEY} in your environment",
            )
        resolved_base = base_url or os.environ.get(ENV_BASE_URL) or DEFAULT_BASE_URL

        logger.info("anyframe client initialised (base_url=%s)", resolved_base)
        self._http = SyncHTTP(base_url=resolved_base, api_key=resolved_key, timeout=timeout)

        # ── resources ─────────────────────────────────────────────────────
        self.tokens = Tokens(self._http)
        self.credentials = Credentials(self._http)
        self.connectors = Connectors(self._http)
        self.agents = Agents(self._http)
        self.sessions = Sessions(self._http)
        self.attention = Attention(self._http)

    # ── identity ──────────────────────────────────────────────────────────

    def me(self) -> User:
        """Return the authenticated user (``GET /api/me``)."""
        data = self._http.request("GET", "/api/me")
        return User.model_validate(data)

    # ── lifecycle ─────────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> AnyFrame:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()


__all__ = ["DEFAULT_BASE_URL", "AnyFrame"]
