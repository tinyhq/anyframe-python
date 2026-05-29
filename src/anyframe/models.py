"""Pydantic response models mirroring the AnyFrame control-plane schema.

Every model accepts unknown extra fields (``extra="ignore"``) so a server
that adds a new attribute does not break older SDK pins. Enum-valued fields
are typed as :class:`typing.Literal` rather than :class:`enum.Enum` so callers
never need to import an SDK enum to compare against a status string.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Literal aliases ────────────────────────────────────────────────────────

SessionStatus = Literal["booting", "running", "snapshotting", "terminated", "error"]
PreviewStatus = Literal["starting", "running", "paused", "stopped", "error"]
McpTransport = Literal["http", "sse", "stdio"]
SkillSource = Literal["inline", "git"]
ConnectorAuthKind = Literal[
    "oauth_dcr", "oauth_preregistered", "bearer_token", "custom_header", "stdio",
]
PermissionPreset = Literal["read_only", "standard", "full_trust"]
BuildState = Literal["queued", "running", "succeeded", "failed", "cancelled"]
Runtime = Literal["claude", "codex"]
CatalogSetupKind = Literal[
    "oauth_dcr", "oauth_preregistered", "bearer_token", "custom_mcp",
]
CatalogTrustLevel = Literal["official", "verified", "community"]
OrgRole = Literal["member", "admin", "owner"]
OrgJoinRequestStatus = Literal["pending", "approved", "rejected"]
OrgInvitationState = Literal["pending", "accepted", "revoked", "expired"]
IntegrationProvider = Literal["slack", "github", "discord"]


class _Model(BaseModel):
    """Shared base — forward-compatible parsing of API responses."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


# ── Identity ───────────────────────────────────────────────────────────────


class UserSummary(_Model):
    """Slim user payload embedded in member / invitation / audit rows."""

    id: int
    login: str | None = None
    name: str | None = None
    email: str | None = None
    avatar_url: str | None = None


class OrgMembership(_Model):
    """One row in :attr:`User.memberships` — the org plus the caller's role."""

    org: Org
    role: OrgRole


class OrgInvitationForMe(_Model):
    """A pending GitHub-username invitation surfaced to the invitee in ``/api/me``."""

    id: int
    org: Org
    role: OrgRole
    inviter: UserSummary | None = None
    message: str | None = None
    expires_at: datetime


class User(_Model):
    """The authenticated caller's hydrated identity (``GET /api/me``).

    The org-aware fields (``memberships``, ``active_org_id``, ``suggested_orgs``,
    ``pending_join_requests``, ``pending_invitations``) are populated only when
    the server has organisations enabled; they're ``None`` otherwise.
    """

    id: int
    github_id: int | None = None
    login: str | None = None
    email: str | None = None
    name: str | None = None
    avatar_url: str | None = None
    is_superadmin: bool = False
    memberships: list[OrgMembership] | None = None
    active_org_id: int | None = None
    pending_join_requests: list[Org] | None = None
    suggested_orgs: list[Org] | None = None
    pending_invitations: list[OrgInvitationForMe] | None = None


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

    Subsequent ``af.tokens.list()`` calls only ever see the redacted form.
    """

    token: str


# ── Credentials ────────────────────────────────────────────────────────────


class CredentialPart(_Model):
    """Whether a specific credential (Claude / Codex) is set, and when."""

    set: bool
    last4: str | None = None
    updated_at: datetime | None = None


class Credentials(_Model):
    """A user's stored runtime tokens — only redacted metadata is returned."""

    claude: CredentialPart
    codex: CredentialPart


# ── Credits ────────────────────────────────────────────────────────────────


class CreditBalance(_Model):
    """The caller's free-trial credit pool (``GET /api/credits``).

    ``scope`` reflects whether the balance is the personal pool or the active
    org's shared pool. ``org_token_active`` is only meaningful in org scope —
    it's ``True`` when the org has a BYO runtime token set, in which case
    sessions don't consume from this pool.
    """

    limit: int
    used: int
    remaining: int
    exhausted: bool
    checked_at: datetime | None = None
    scope: Literal["personal", "org"] = "personal"
    org_token_active: bool = False


# ── User-level MCP connectors ──────────────────────────────────────────────


class Connector(_Model):
    """A user-level MCP connector row."""

    id: int
    display_name: str
    mcp_url: str
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


# ── Templates and sub-resources ────────────────────────────────────────────


class TemplateSkill(_Model):
    """A skill attached to one template."""

    id: int
    name: str
    source: SkillSource
    content: dict[str, Any]
    enabled: bool
    created_at: datetime


class TemplateMcp(_Model):
    """An MCP server attached to one template (inline form)."""

    id: int
    name: str
    transport: McpTransport
    config: dict[str, Any]
    secret_ref: str | None = None
    enabled: bool
    created_at: datetime


class TemplateConnectorToggle(_Model):
    """A user connector seen through one template's toggle row."""

    connector_id: int
    display_name: str
    mcp_url: str
    catalog_slug: str | None = None
    auth_kind: ConnectorAuthKind
    enabled: bool
    is_authorized: bool


class Template(_Model):
    """Summary view of a template — the reusable blueprint behind agents."""

    id: int
    name: str
    description: str | None = None
    system_prompt: str | None = None
    repo_url: str | None = None
    repo_ref: str | None = None
    install_cmd: str | None = None
    serve_cmd: str | None = None
    preview_ports: list[int] = Field(default_factory=list)
    permissions: dict[str, Any] = Field(default_factory=dict)
    # Values are always masked in API responses; only the keys are meaningful
    # client-side. Set via the ``env_vars=`` kwarg on
    # :meth:`Templates.create` / :meth:`Templates.update`.
    env_vars: dict[str, str] = Field(default_factory=dict)
    install_id: int | None = None
    created_at: datetime
    updated_at: datetime


class TemplateDetail(Template):
    """Detail view — adds skills, MCPs, connector toggles, and the agent count."""

    skills: list[TemplateSkill] = Field(default_factory=list)
    mcps: list[TemplateMcp] = Field(default_factory=list)
    connectors: list[TemplateConnectorToggle] = Field(default_factory=list)
    agent_count: int = 0


# ── Agents ─────────────────────────────────────────────────────────────────


class AgentImage(_Model):
    """A cached prebuilt sandbox image for one agent's ``build_key``."""

    build_key: str
    modal_image_id: str
    built_at: datetime


class Agent(_Model):
    """Summary view returned by ``GET /api/agents`` and create/update endpoints.

    An agent binds to a :class:`Template` (``template_id``). The
    ``permissions`` and ``env_vars`` fields show the *effective* values — the
    template's baseline merged with this agent's overrides. The override fields
    (``permissions_override``, ``env_vars_override``) expose what's set directly
    on this agent so callers can tell inherited vs overridden apart.
    """

    id: int
    name: str
    description: str | None = None
    template_id: int
    runtime: Runtime = "claude"
    build_key: str | None = None
    # Surfaced for list-page consumers that don't want to round-trip through
    # the bound template. ``repo_url`` and ``repo_ref`` come directly off the
    # template; ``permissions`` and ``env_vars`` apply the override on top.
    repo_url: str | None = None
    repo_ref: str | None = None
    permissions: dict[str, Any] = Field(default_factory=dict)
    env_vars: dict[str, str] = Field(default_factory=dict)
    permissions_override: dict[str, Any] | None = None
    env_vars_override: dict[str, str] = Field(default_factory=dict)
    warmup_image_id: str | None = None
    created_at: datetime
    updated_at: datetime


class AgentDetail(Agent):
    """Detail view — embeds the bound template and the latest prebuilt image."""

    template: Template
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
    """Current state of an agent's image build."""

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
    """Signed URL for a build log archive."""

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
    vnc_url: str | None = None
    snapshot_image_id: str | None = None
    idle_timeout_s: int
    previews: list[Preview] = Field(default_factory=list)
    is_setup_session: bool = False
    error_reason: str | None = None
    private: bool = False
    driver_user_id: int | None = None
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


class PresenceUser(_Model):
    """One row in ``GET /api/sessions/{id}/presence`` — a watcher in the session."""

    user_id: int
    login: str | None = None
    name: str | None = None
    avatar_url: str | None = None
    last_seen: datetime
    is_driver: bool


class ControlRequest(_Model):
    """Acknowledgement returned by ``POST .../request_control``."""

    id: int
    status: Literal["pending", "approved", "rejected", "cancelled"]


class HandoffResult(_Model):
    """Result of a handoff or take-over — the new driver."""

    driver_user_id: int


class PrivacyResult(_Model):
    """Result of ``POST .../privacy``."""

    private: bool


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


# ── Organisations ──────────────────────────────────────────────────────────


class Org(_Model):
    """An organisation (workspace)."""

    id: int
    slug: str
    name: str
    owner_user_id: int
    auto_join_domain: str | None = None
    created_at: datetime
    updated_at: datetime


class SlugAvailability(_Model):
    """Result of ``GET /api/orgs/check_slug?slug=…``."""

    available: bool
    reason: Literal["ok", "invalid", "reserved", "taken"]


class OrgMember(_Model):
    """One row in ``GET /api/orgs/{slug}/members``."""

    user: UserSummary
    role: OrgRole
    created_at: datetime
    last_active_at: datetime | None = None


class OrgJoinRequest(_Model):
    """A pending request to join an organisation."""

    id: int
    user: UserSummary
    status: OrgJoinRequestStatus
    created_at: datetime
    resolved_at: datetime | None = None


class JoinRequestCreated(_Model):
    """Acknowledgement returned by ``POST .../join-requests``."""

    id: int
    status: OrgJoinRequestStatus


class OrgInvitation(_Model):
    """A pending or historical invitation as seen by an org admin."""

    id: int
    email: str | None = None
    github_login: str | None = None
    role: OrgRole
    state: OrgInvitationState
    invited_by: UserSummary | None = None
    message: str | None = None
    created_at: datetime
    expires_at: datetime
    accepted_at: datetime | None = None
    accepted_by_user_id: int | None = None
    revoked_at: datetime | None = None


class OrgInvitationCreated(_Model):
    """Return shape from ``POST /api/orgs/{slug}/invitations``.

    ``url`` is the one-time invite link — the only place the plaintext token
    ever appears in any response. Send this to the invitee.
    """

    invitation: OrgInvitation
    url: str


class OrgInvitationView(_Model):
    """Public view of an invitation by its plaintext token."""

    org: Org
    role: OrgRole
    inviter: UserSummary | None = None
    message: str | None = None
    expires_at: datetime
    state: OrgInvitationState
    email: str | None = None
    github_login: str | None = None
    matches_current_user: bool | None = None


class OrgCredentials(_Model):
    """An organisation's stored runtime tokens (admin-only)."""

    claude: CredentialPart
    codex: CredentialPart


class OrgEvent(_Model):
    """One row in the org audit log (``GET /api/orgs/{slug}/events``)."""

    id: int
    kind: str
    payload: dict[str, Any]
    created_at: datetime
    actor: UserSummary | None = None


# ── Integrations ───────────────────────────────────────────────────────────


class ProviderApp(_Model):
    """A registered provider app (Slack workspace app, GitHub App, …)."""

    id: int
    provider: IntegrationProvider
    display_name: str
    client_id: str | None = None
    app_slug: str | None = None
    webhook_url: str
    redirect_url: str
    is_draft: bool
    is_shared: bool
    created_at: datetime
    updated_at: datetime


class IntegrationBinding(_Model):
    """The single agent binding attached to one install."""

    id: int
    install_id: int
    agent_id: int
    created_at: datetime
    updated_at: datetime


class IntegrationInstall(_Model):
    """A user/org install of a provider app."""

    id: int
    provider_app_id: int
    provider: IntegrationProvider
    external_workspace_id: str
    external_workspace_name: str | None = None
    binding: IntegrationBinding | None = None
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class GithubInstall(_Model):
    """Slim shape returned by the GitHub install picker."""

    id: int
    account_login: str | None = None
    installation_id: str


class GithubRepo(_Model):
    """A repo entry from ``GET /api/integrations/github/installs/{id}/repos``."""

    full_name: str
    default_branch: str
    private: bool


# ── Public config ──────────────────────────────────────────────────────────


class PublicConfig(_Model):
    """Server-derived feature flags from ``GET /api/config/public`` (unauth)."""

    free_trial_enabled: bool
    chat_widget_enabled: bool
    google_enabled: bool


# Forward references — User and OrgMembership refer to Org which is declared
# later in the file. Resolve them now that every class is in scope.
OrgMembership.model_rebuild()
OrgInvitationForMe.model_rebuild()
User.model_rebuild()


__all__ = [
    "Agent",
    "AgentDetail",
    "AgentImage",
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
    "ControlRequest",
    "CredentialPart",
    "Credentials",
    "CreditBalance",
    "GithubInstall",
    "GithubRepo",
    "HandoffResult",
    "IntegrationBinding",
    "IntegrationInstall",
    "IntegrationProvider",
    "JoinRequestCreated",
    "LogUrl",
    "McpTransport",
    "Org",
    "OrgCredentials",
    "OrgEvent",
    "OrgInvitation",
    "OrgInvitationCreated",
    "OrgInvitationForMe",
    "OrgInvitationState",
    "OrgInvitationView",
    "OrgJoinRequest",
    "OrgJoinRequestStatus",
    "OrgMember",
    "OrgMembership",
    "OrgRole",
    "PermissionPreset",
    "PresenceUser",
    "Preview",
    "PreviewActionResult",
    "PreviewBatchResult",
    "PreviewSpec",
    "PreviewStatus",
    "PrivacyResult",
    "ProviderApp",
    "PublicConfig",
    "Runtime",
    "SaveAsBaseResult",
    "Session",
    "SessionStatus",
    "SkillSource",
    "SlugAvailability",
    "Snapshot",
    "Template",
    "TemplateConnectorToggle",
    "TemplateDetail",
    "TemplateMcp",
    "TemplateSkill",
    "Token",
    "TokenCreated",
    "User",
    "UserSummary",
]
