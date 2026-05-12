"""Pydantic response models mirroring the AnyFrame control plane schema.

Every model accepts unknown extra fields (``extra="ignore"``) so a server
that adds a new attribute does not break older SDK pins. Enum-valued fields
are typed as :class:`typing.Literal` rather than :class:`enum.Enum` to keep
the public type surface trivial — callers never need to import an SDK enum
to compare against a status string.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Aliased literal types ──────────────────────────────────────────────────

SessionStatus = Literal["booting", "running", "snapshotting", "terminated", "error"]
ServeStatus = Literal["stopped", "starting", "running", "error"]
McpTransport = Literal["http", "sse", "stdio"]
SkillSource = Literal["builtin", "custom"]
ConnectorAuthKind = Literal["oauth_dcr", "bearer_token"]
PermissionPreset = Literal["read_only", "standard", "full_trust"]
BuildState = Literal["queued", "running", "succeeded", "failed", "cancelled"]


class _Model(BaseModel):
    """Shared base: forward-compatible parsing of API responses."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


# ── Identity ───────────────────────────────────────────────────────────────


class User(_Model):
    """The authenticated caller's profile (``GET /api/me``)."""

    id: int
    github_id: int
    login: str
    name: str | None = None
    avatar_url: str | None = None


# ── Personal API tokens ────────────────────────────────────────────────────


class Token(_Model):
    """A redacted view of a personal API token."""

    id: int
    name: str
    prefix: str
    last4: str
    created_at: datetime
    revoked_at: datetime | None = None


class TokenCreated(Token):
    """Returned once at creation. ``token`` is the raw secret — store it now.

    Subsequent ``af.tokens.list()`` calls will only ever see the redacted form.
    """

    token: str


# ── Credentials ────────────────────────────────────────────────────────────


class CredentialPart(_Model):
    """Whether a specific credential (Claude / GitHub) is set."""

    set: bool
    last4: str | None = None
    updated_at: datetime | None = None


class Credentials(_Model):
    """A user's stored secrets — never the raw values, only redacted metadata."""

    claude: CredentialPart
    github: CredentialPart


# ── User-level MCP connectors ──────────────────────────────────────────────


class Connector(_Model):
    """A user-level MCP connector row."""

    id: int
    display_name: str
    mcp_url: str
    transport: McpTransport
    auth_kind: ConnectorAuthKind
    secret_last4: str | None = None
    expires_at: datetime | None = None
    scopes: str | None = None
    is_authorized: bool
    last_refresh_attempt_at: datetime | None = None
    last_refresh_error: str | None = None
    created_at: datetime
    updated_at: datetime


class ConnectorDiscovery(_Model):
    """Result of ``POST /api/connectors/discover``."""

    mcp_url: str
    supports_dcr: bool
    suggested_display_name: str
    authorization_endpoint: str | None = None
    token_endpoint: str | None = None
    scopes_supported: list[str] = Field(default_factory=list)


class ConnectorAuthorize(_Model):
    """Returned by OAuth-flow endpoints — open ``authorize_url`` in a browser."""

    connector_id: int
    authorize_url: str
    state: str


# ── Agents and sub-resources ───────────────────────────────────────────────


class AgentSkill(_Model):
    """A skill attached to one agent."""

    id: int
    name: str
    source: SkillSource
    content: dict[str, Any]
    enabled: bool
    created_at: datetime


class AgentMcp(_Model):
    """An MCP server attached to one agent (the inline form, not the user-level connector)."""

    id: int
    name: str
    transport: McpTransport
    config: dict[str, Any]
    secret_ref: str | None = None
    enabled: bool
    created_at: datetime


class AgentConnectorToggle(_Model):
    """A user connector seen through one agent's toggle row."""

    connector_id: int
    display_name: str
    mcp_url: str
    auth_kind: ConnectorAuthKind
    enabled: bool
    is_authorized: bool


class AgentImage(_Model):
    """A cached prebuilt sandbox image for one agent build_key."""

    build_key: str
    modal_image_id: str
    built_at: datetime


class Agent(_Model):
    """Summary view returned by list / create endpoints."""

    id: int
    name: str
    description: str | None = None
    system_prompt: str | None = None
    repo_url: str | None = None
    repo_ref: str | None = None
    install_cmd: str | None = None
    serve_cmd: str | None = None
    preview_ports: list[int] = Field(default_factory=list)
    build_key: str | None = None
    permissions: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class AgentDetail(Agent):
    """Detail view — adds skills / mcps / connectors / image."""

    skills: list[AgentSkill] = Field(default_factory=list)
    mcps: list[AgentMcp] = Field(default_factory=list)
    connectors: list[AgentConnectorToggle] = Field(default_factory=list)
    image: AgentImage | None = None


# ── Builds ─────────────────────────────────────────────────────────────────


class BuildQueued(_Model):
    """Response from ``POST /api/agents/{id}/build``."""

    agent_id: int
    build_key: str | None = None
    queued: bool
    reason: str | None = None
    build_id: int | None = None


class BuildStatus(_Model):
    """Current state of an agent's image build (``GET .../build/status``)."""

    agent_id: int
    build_key: str | None = None
    state: BuildState | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    built_image_id: str | None = None


class Build(_Model):
    """A historical build row."""

    id: int
    build_key: str
    state: BuildState
    started_at: datetime
    finished_at: datetime | None = None
    error: str | None = None
    log_size: int | None = None


class LogUrl(_Model):
    """Signed URL for a build log archive in R2."""

    url: str
    expires_in: int


# ── Sessions, snapshots, chat ──────────────────────────────────────────────


class Session(_Model):
    """A live (or terminated) sandbox session."""

    id: UUID
    agent_id: int
    status: SessionStatus
    modal_sandbox_id: str | None = None
    sandbox_url: str | None = None
    snapshot_image_id: str | None = None
    idle_timeout_s: int
    serve_status: ServeStatus
    serve_port: int | None = None
    serve_url: str | None = None
    created_at: datetime
    last_active: datetime


class Snapshot(_Model):
    """A persisted snapshot of a session sandbox."""

    id: int
    modal_image_id: str
    label: str | None = None
    created_at: datetime


class ChatEvent(_Model):
    """One event from a session's chat transcript."""

    seq: int
    payload: dict[str, Any]
    created_at: datetime


__all__ = [
    "Agent",
    "AgentConnectorToggle",
    "AgentDetail",
    "AgentImage",
    "AgentMcp",
    "AgentSkill",
    "Build",
    "BuildQueued",
    "BuildState",
    "BuildStatus",
    "ChatEvent",
    "Connector",
    "ConnectorAuthKind",
    "ConnectorAuthorize",
    "ConnectorDiscovery",
    "CredentialPart",
    "Credentials",
    "LogUrl",
    "McpTransport",
    "PermissionPreset",
    "ServeStatus",
    "Session",
    "SessionStatus",
    "SkillSource",
    "Snapshot",
    "Token",
    "TokenCreated",
    "User",
]
