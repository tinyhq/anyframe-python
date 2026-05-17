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
PreviewStatus = Literal["starting", "running", "paused", "stopped", "error"]
# ``ServeStatus`` retained as a backwards-compatible alias for legacy
# imports — the live preview surface has moved to :data:`PreviewStatus`.
ServeStatus = PreviewStatus
McpTransport = Literal["http", "sse", "stdio"]
SkillSource = Literal["inline", "git"]
ConnectorAuthKind = Literal["oauth_dcr", "oauth_preregistered", "bearer_token"]
PermissionPreset = Literal["read_only", "standard", "full_trust"]
BuildState = Literal["queued", "running", "succeeded", "failed", "cancelled"]
Runtime = Literal["claude", "codex"]
CatalogSetupKind = Literal["oauth_dcr", "oauth_preregistered", "bearer_token", "custom_mcp"]
CatalogTrustLevel = Literal["official", "verified", "community"]


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
    """Whether a specific credential (Claude / Codex / GitHub) is set."""

    set: bool
    last4: str | None = None
    updated_at: datetime | None = None


class Credentials(_Model):
    """A user's stored secrets — never the raw values, only redacted metadata."""

    claude: CredentialPart
    # ``codex`` was added when the control plane gained the OpenAI Codex
    # runtime. Defaulted so older servers that don't return the key still parse.
    codex: CredentialPart = Field(default_factory=lambda: CredentialPart(set=False))
    github: CredentialPart


# ── User-level MCP connectors ──────────────────────────────────────────────


class Connector(_Model):
    """A user-level MCP connector row."""

    id: int
    display_name: str
    mcp_url: str
    # Catalog slug when the connector was installed from the catalog, else None.
    catalog_slug: str | None = None
    default_enabled: bool = True
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


class ConnectorCatalogItem(_Model):
    """One entry from the connector catalog (``GET /api/connectors/catalog``)."""

    slug: str
    display_name: str
    category: str
    description: str
    mcp_url: str
    transport: McpTransport
    setup_kind: CatalogSetupKind
    publisher: str
    trust_level: CatalogTrustLevel
    docs_url: str
    tags: list[str] = Field(default_factory=list)
    has_logo: bool = False
    coming_soon: bool = False
    installed: bool = False
    connector_id: int | None = None
    is_authorized: bool | None = None


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
    runtime: Runtime = "claude"
    repo_url: str | None = None
    repo_ref: str | None = None
    install_cmd: str | None = None
    serve_cmd: str | None = None
    preview_ports: list[int] = Field(default_factory=list)
    build_key: str | None = None
    permissions: dict[str, Any] = Field(default_factory=dict)
    # Values are always masked ("****") in API responses; only the keys are
    # meaningful client-side. Set via ``env_vars=`` on ``agents.create()`` /
    # ``agents.update()``.
    env_vars: dict[str, str] = Field(default_factory=dict)
    warmup_image_id: str | None = None
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


# ── Sessions, snapshots, chat, previews ────────────────────────────────────


class Preview(_Model):
    """One row in a session's live previews list."""

    port: int
    name: str
    cmd: str | None = None
    status: PreviewStatus
    url: str | None = None
    started_at: float | None = None
    exit_code: int | None = None


class PreviewSpec(_Model):
    """Spec for a single preview to start (used by ``batch_start``)."""

    cmd: str
    port: int | None = None
    name: str | None = None


class PreviewActionResult(_Model):
    """Generic result for non-list preview actions (start / stop / logs / …)."""

    ok: bool
    port: int | None = None
    name: str | None = None
    url: str | None = None
    status: PreviewStatus | None = None
    restart_pending: bool = False
    already_open: bool = False
    error: str | None = None


class PreviewBatchResult(_Model):
    """Result for the ``batch_start`` preview action."""

    ok: bool
    restart_pending: bool = False
    previews: list[Preview] = Field(default_factory=list)
    error: str | None = None


class SaveAsBaseResult(_Model):
    """Result of ``POST /api/sessions/{id}/save-as-base``."""

    warmup_image_id: str
    warmup_inputs_hash: str


class Session(_Model):
    """A live (or terminated) sandbox session."""

    id: UUID
    agent_id: int
    status: SessionStatus
    modal_sandbox_id: str | None = None
    sandbox_url: str | None = None
    snapshot_image_id: str | None = None
    idle_timeout_s: int
    # ``previews`` replaces the older serve_status/serve_port/serve_url triple.
    # Defaults to an empty list so a session with no preview yet still parses.
    previews: list[Preview] = Field(default_factory=list)
    is_setup_session: bool = False
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


# ── Attention rail ─────────────────────────────────────────────────────────


class AttentionPendingItem(_Model):
    """An unresolved permission_request or ask_user_question."""

    kind: Literal["pending"] = "pending"
    session_id: UUID
    agent_id: int
    agent_name: str
    session_status: SessionStatus
    seq: int
    payload: dict[str, Any]
    at: datetime
    preview: str | None = None


class AttentionIdleItem(_Model):
    """A running session whose agent finished its last turn."""

    kind: Literal["idle"] = "idle"
    session_id: UUID
    agent_id: int
    agent_name: str
    at: datetime
    preview: str | None = None


class AttentionPausedItem(_Model):
    """A session paused within the recent window — a candidate to resume."""

    kind: Literal["paused"] = "paused"
    session_id: UUID
    agent_id: int
    agent_name: str
    snapshot_image_id: str | None = None
    at: datetime


AttentionItem = AttentionPendingItem | AttentionIdleItem | AttentionPausedItem


__all__ = [
    "Agent",
    "AgentConnectorToggle",
    "AgentDetail",
    "AgentImage",
    "AgentMcp",
    "AgentSkill",
    "AttentionIdleItem",
    "AttentionItem",
    "AttentionPausedItem",
    "AttentionPendingItem",
    "Build",
    "BuildQueued",
    "BuildState",
    "BuildStatus",
    "CatalogSetupKind",
    "CatalogTrustLevel",
    "ChatEvent",
    "Connector",
    "ConnectorAuthKind",
    "ConnectorAuthorize",
    "ConnectorCatalogItem",
    "ConnectorDiscovery",
    "CredentialPart",
    "Credentials",
    "LogUrl",
    "McpTransport",
    "PermissionPreset",
    "Preview",
    "PreviewActionResult",
    "PreviewBatchResult",
    "PreviewSpec",
    "PreviewStatus",
    "Runtime",
    "SaveAsBaseResult",
    "ServeStatus",
    "Session",
    "SessionStatus",
    "SkillSource",
    "Snapshot",
    "Token",
    "TokenCreated",
    "User",
]
