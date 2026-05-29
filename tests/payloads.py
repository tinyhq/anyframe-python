"""Reusable wire-format payloads for the test suite.

Each constant mirrors what the v2 control plane returns for a single row of
the corresponding resource. Tests compose them with ``|`` to override
specific fields without re-declaring the whole shape.
"""

from __future__ import annotations

from typing import Any

# ── Templates / Agents ─────────────────────────────────────────────────────

TEMPLATE: dict[str, Any] = {
    "id": 4,
    "name": "web-stack",
    "description": "Bun + React preview stack",
    "system_prompt": "You are a web dev.",
    "repo_url": "tinyhq/box",
    "repo_ref": "main",
    "install_cmd": "bun install",
    "serve_cmd": "bun dev",
    "preview_ports": [3000],
    "permissions": {"preset": "standard"},
    "env_vars": {"NODE_ENV": "****"},
    "install_id": 11,
    "created_at": "2026-05-01T00:00:00Z",
    "updated_at": "2026-05-01T00:00:00Z",
}

TEMPLATE_DETAIL: dict[str, Any] = TEMPLATE | {
    "skills": [],
    "mcps": [],
    "connectors": [],
    "agent_count": 1,
}

AGENT: dict[str, Any] = {
    "id": 7,
    "name": "demo",
    "description": None,
    "template_id": 4,
    "runtime": "claude",
    "build_key": "abc123",
    "repo_url": "tinyhq/box",
    "repo_ref": "main",
    "permissions": {"preset": "standard"},
    "env_vars": {"NODE_ENV": "****"},
    "permissions_override": None,
    "env_vars_override": {},
    "warmup_image_id": None,
    "created_at": "2026-05-01T00:00:00Z",
    "updated_at": "2026-05-01T00:00:00Z",
}

AGENT_DETAIL: dict[str, Any] = AGENT | {
    "template": TEMPLATE,
    "image": None,
}

# ── Templates: nested ──────────────────────────────────────────────────────

TEMPLATE_SKILL: dict[str, Any] = {
    "id": 1,
    "name": "deploy",
    "source": "inline",
    "content": {"body": "…"},
    "enabled": True,
    "created_at": "2026-05-01T00:00:00Z",
}

TEMPLATE_MCP: dict[str, Any] = {
    "id": 1,
    "name": "git",
    "transport": "http",
    "config": {"url": "https://mcp.example.com"},
    "secret_ref": None,
    "enabled": True,
    "created_at": "2026-05-01T00:00:00Z",
}

TEMPLATE_CONNECTOR: dict[str, Any] = {
    "connector_id": 1,
    "display_name": "Linear",
    "mcp_url": "https://mcp.linear.app/sse",
    "catalog_slug": "linear",
    "auth_kind": "oauth_dcr",
    "enabled": True,
    "is_authorized": True,
}

# ── Credentials ────────────────────────────────────────────────────────────

CREDENTIALS: dict[str, Any] = {
    "claude": {"set": True, "last4": "wxyz", "updated_at": "2026-05-01T00:00:00Z"},
    "codex": {"set": False, "last4": None, "updated_at": None},
}

# ── Credits ────────────────────────────────────────────────────────────────

CREDITS: dict[str, Any] = {
    "limit": 1000,
    "used": 250,
    "remaining": 750,
    "exhausted": False,
    "checked_at": "2026-05-29T12:00:00Z",
    "scope": "personal",
    "org_token_active": False,
}

# ── Connectors ─────────────────────────────────────────────────────────────

CONNECTOR: dict[str, Any] = {
    "id": 1,
    "display_name": "Linear",
    "mcp_url": "https://mcp.linear.app/sse",
    "catalog_slug": "linear",
    "default_enabled": True,
    "transport": "http",
    "auth_kind": "oauth_dcr",
    "secret_last4": None,
    "expires_at": None,
    "scopes": None,
    "is_authorized": True,
    "last_refresh_attempt_at": None,
    "last_refresh_error": None,
    "created_at": "2026-05-01T00:00:00Z",
    "updated_at": "2026-05-01T00:00:00Z",
}

# ── Orgs ───────────────────────────────────────────────────────────────────

ORG: dict[str, Any] = {
    "id": 100,
    "slug": "acme",
    "name": "Acme",
    "owner_user_id": 1,
    "auto_join_domain": "acme.com",
    "created_at": "2026-05-01T00:00:00Z",
    "updated_at": "2026-05-01T00:00:00Z",
}

USER_SUMMARY: dict[str, Any] = {
    "id": 5,
    "login": "alice",
    "name": "Alice",
    "email": "alice@acme.com",
    "avatar_url": None,
}

ORG_MEMBER: dict[str, Any] = {
    "user": USER_SUMMARY,
    "role": "member",
    "created_at": "2026-05-01T00:00:00Z",
    "last_active_at": None,
}

ORG_INVITATION: dict[str, Any] = {
    "id": 9,
    "email": None,
    "github_login": "alice",
    "role": "member",
    "state": "pending",
    "invited_by": USER_SUMMARY,
    "message": "join us",
    "created_at": "2026-05-01T00:00:00Z",
    "expires_at": "2026-06-01T00:00:00Z",
    "accepted_at": None,
    "accepted_by_user_id": None,
    "revoked_at": None,
}

ORG_JOIN_REQUEST: dict[str, Any] = {
    "id": 3,
    "user": USER_SUMMARY,
    "status": "pending",
    "created_at": "2026-05-01T00:00:00Z",
    "resolved_at": None,
}

ORG_CREDENTIALS: dict[str, Any] = {
    "claude": {"set": True, "last4": "abcd", "updated_at": "2026-05-01T00:00:00Z"},
    "codex": {"set": False, "last4": None, "updated_at": None},
}

ORG_EVENT: dict[str, Any] = {
    "id": 17,
    "kind": "agent.created",
    "payload": {"agent_id": 7, "name": "demo"},
    "created_at": "2026-05-01T00:00:00Z",
    "actor": USER_SUMMARY,
}

# ── Integrations ───────────────────────────────────────────────────────────

INTEGRATION_INSTALL: dict[str, Any] = {
    "id": 22,
    "provider_app_id": 1,
    "provider": "github",
    "external_workspace_id": "12345",
    "external_workspace_name": "tinyhq",
    "binding": None,
    "expires_at": None,
    "created_at": "2026-05-01T00:00:00Z",
    "updated_at": "2026-05-01T00:00:00Z",
}

INTEGRATION_BINDING: dict[str, Any] = {
    "id": 33,
    "install_id": 22,
    "agent_id": 7,
    "created_at": "2026-05-01T00:00:00Z",
    "updated_at": "2026-05-01T00:00:00Z",
}

PROVIDER_APP: dict[str, Any] = {
    "id": 1,
    "provider": "github",
    "display_name": "AnyFrame GitHub",
    "client_id": "Iv1.abc",
    "app_slug": "anyframe",
    "webhook_url": "https://api.anyfrm.com/webhook/github",
    "redirect_url": "https://api.anyfrm.com/oauth/callback",
    "is_draft": False,
    "is_shared": False,
    "created_at": "2026-05-01T00:00:00Z",
    "updated_at": "2026-05-01T00:00:00Z",
}

GITHUB_INSTALL: dict[str, Any] = {
    "id": 22,
    "account_login": "tinyhq",
    "installation_id": "12345",
}

GITHUB_REPO: dict[str, Any] = {
    "full_name": "tinyhq/box",
    "default_branch": "main",
    "private": True,
}

# ── Sessions ───────────────────────────────────────────────────────────────

SESSION: dict[str, Any] = {
    "id": "00000000-0000-0000-0000-000000000001",
    "agent_id": 7,
    "status": "running",
    "modal_sandbox_id": "sb_1",
    "sandbox_url": "https://sandbox.example",
    "vnc_url": None,
    "snapshot_image_id": None,
    "idle_timeout_s": 300,
    "previews": [],
    "is_setup_session": False,
    "error_reason": None,
    "private": False,
    "driver_user_id": 1,
    "created_at": "2026-05-01T00:00:00Z",
    "last_active": "2026-05-01T00:00:00Z",
}

PRESENCE_USER: dict[str, Any] = {
    "user_id": 1,
    "login": "nish",
    "name": "Nish",
    "avatar_url": None,
    "last_seen": "2026-05-29T12:00:00Z",
    "is_driver": True,
}

# ── Me ─────────────────────────────────────────────────────────────────────

ME_MINIMAL: dict[str, Any] = {
    "id": 1,
    "github_id": 42,
    "login": "nish",
    "email": "nish@example.com",
    "name": "Nish",
    "avatar_url": None,
    "is_superadmin": False,
}

ME_WITH_ORGS: dict[str, Any] = ME_MINIMAL | {
    "memberships": [{"org": ORG, "role": "owner"}],
    "active_org_id": ORG["id"],
    "pending_join_requests": [],
    "suggested_orgs": [],
    "pending_invitations": [],
}

PUBLIC_CONFIG: dict[str, Any] = {
    "free_trial_enabled": True,
    "chat_widget_enabled": False,
    "google_enabled": True,
}
