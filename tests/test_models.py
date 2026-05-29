"""Tests for the Pydantic response models.

Models are constructed from API JSON, so the only properties worth pinning
are the ones the wire format guarantees:

  - they accept the exact field set the server returns
  - they tolerate optional/null fields per the FastAPI schemas
  - string enums round-trip cleanly
  - extra unknown fields are not rejected (forward-compat)
"""

from datetime import datetime, timezone

import pytest

from anyframe import models
from tests.payloads import (
    AGENT,
    AGENT_DETAIL,
    CREDENTIALS,
    CREDITS,
    GITHUB_INSTALL,
    GITHUB_REPO,
    INTEGRATION_BINDING,
    INTEGRATION_INSTALL,
    ME_MINIMAL,
    ME_WITH_ORGS,
    ORG,
    ORG_CREDENTIALS,
    ORG_EVENT,
    ORG_INVITATION,
    ORG_JOIN_REQUEST,
    ORG_MEMBER,
    PRESENCE_USER,
    PUBLIC_CONFIG,
    SESSION,
    TEMPLATE,
    TEMPLATE_CONNECTOR,
    TEMPLATE_DETAIL,
    TEMPLATE_MCP,
    TEMPLATE_SKILL,
)

# ── User / Me ──────────────────────────────────────────────────────────────


def test_user_parses_minimal_payload():
    u = models.User.model_validate(ME_MINIMAL)
    assert u.login == "nish"
    assert u.is_superadmin is False
    # When orgs are disabled the optional fields stay None.
    assert u.memberships is None
    assert u.active_org_id is None


def test_user_parses_full_org_payload():
    u = models.User.model_validate(ME_WITH_ORGS)
    assert u.active_org_id == ORG["id"]
    assert u.memberships and u.memberships[0].role == "owner"
    assert u.memberships[0].org.slug == "acme"


def test_user_tolerates_null_optional_fields():
    """The /api/me payload has many optional fields — none should be required."""
    u = models.User.model_validate({"id": 1})
    assert u.login is None
    assert u.is_superadmin is False


# ── Tokens / Credentials / Credits ─────────────────────────────────────────


def test_token_created_carries_raw_secret():
    t = models.TokenCreated.model_validate(
        {
            "id": 1,
            "name": "ci",
            "prefix": "afm_abcd",
            "last4": "wxyz",
            "created_at": "2026-05-01T00:00:00Z",
            "revoked_at": None,
            "token": "afm_abcdefghijklmnop",
        }
    )
    assert t.token == "afm_abcdefghijklmnop"


def test_credentials_only_claude_and_codex():
    c = models.Credentials.model_validate(CREDENTIALS)
    assert c.claude.set is True
    assert c.codex.set is False
    # github is gone in v2 — the model should not have it.
    assert not hasattr(c, "github")


def test_credit_balance_parses_scope_aware():
    b = models.CreditBalance.model_validate(CREDITS)
    assert b.remaining == 750
    assert b.scope == "personal"
    assert b.org_token_active is False


def test_credit_balance_tolerates_missing_optional():
    b = models.CreditBalance.model_validate(
        {"limit": 0, "used": 0, "remaining": 0, "exhausted": True}
    )
    assert b.checked_at is None
    assert b.scope == "personal"


# ── Templates ──────────────────────────────────────────────────────────────


def test_template_parses_summary():
    t = models.Template.model_validate(TEMPLATE)
    assert t.repo_url == "tinyhq/box"
    assert t.preview_ports == [3000]


def test_template_detail_includes_subresources():
    d = models.TemplateDetail.model_validate(TEMPLATE_DETAIL)
    assert d.agent_count == 1
    assert d.skills == []


def test_template_skill_enum_values():
    s = models.TemplateSkill.model_validate(TEMPLATE_SKILL)
    assert s.source == "inline"


def test_template_mcp_carries_transport():
    m = models.TemplateMcp.model_validate(TEMPLATE_MCP)
    assert m.transport == "http"


def test_template_connector_toggle():
    t = models.TemplateConnectorToggle.model_validate(TEMPLATE_CONNECTOR)
    assert t.is_authorized is True
    assert t.catalog_slug == "linear"


# ── Agents ─────────────────────────────────────────────────────────────────


def test_agent_summary_includes_template_id():
    a = models.Agent.model_validate(AGENT)
    assert a.template_id == 4
    assert a.runtime == "claude"


def test_agent_detail_embeds_template():
    a = models.AgentDetail.model_validate(AGENT_DETAIL)
    assert a.template.id == 4
    assert a.template.repo_url == "tinyhq/box"
    assert a.image is None


def test_agent_override_fields_distinct_from_baseline():
    """Effective vs override is a v2-specific distinction; both must surface."""
    payload = AGENT | {
        "permissions": {"preset": "standard"},
        "permissions_override": {"preset": "full_trust"},
        "env_vars": {"NODE_ENV": "****", "DEBUG": "****"},
        "env_vars_override": {"DEBUG": "****"},
    }
    a = models.Agent.model_validate(payload)
    assert a.permissions["preset"] == "standard"
    assert a.permissions_override == {"preset": "full_trust"}
    assert a.env_vars_override == {"DEBUG": "****"}


# ── Sessions ───────────────────────────────────────────────────────────────


def test_session_parses_with_collab_fields():
    s = models.Session.model_validate(SESSION)
    assert s.private is False
    assert s.driver_user_id == 1


def test_session_status_terminal_states_valid():
    for state in ("booting", "running", "snapshotting", "terminated", "error"):
        s = models.Session.model_validate(SESSION | {"status": state})
        assert s.status == state


def test_presence_user_marks_driver():
    p = models.PresenceUser.model_validate(PRESENCE_USER)
    assert p.is_driver is True


# ── Connectors ─────────────────────────────────────────────────────────────


def test_connector_auth_kind_accepts_v2_kinds():
    """v2 added custom_header and stdio to the auth_kind enum."""
    base = {
        "id": 1,
        "display_name": "x",
        "mcp_url": "https://x",
        "catalog_slug": None,
        "default_enabled": True,
        "transport": "http",
        "secret_last4": None,
        "expires_at": None,
        "scopes": None,
        "is_authorized": True,
        "last_refresh_attempt_at": None,
        "last_refresh_error": None,
        "created_at": "2026-05-01T00:00:00Z",
        "updated_at": "2026-05-01T00:00:00Z",
    }
    for kind in (
        "oauth_dcr",
        "oauth_preregistered",
        "bearer_token",
        "custom_header",
        "stdio",
    ):
        c = models.Connector.model_validate(base | {"auth_kind": kind})
        assert c.auth_kind == kind


def test_connector_discovery_optional_endpoints():
    d = models.ConnectorDiscovery.model_validate(
        {
            "mcp_url": "https://mcp.example.com",
            "supports_dcr": False,
            "suggested_display_name": "Example",
            "authorization_endpoint": None,
            "token_endpoint": None,
            "scopes_supported": [],
        }
    )
    assert d.supports_dcr is False


# ── Builds ─────────────────────────────────────────────────────────────────


def test_build_status_with_no_build_yet():
    s = models.BuildStatus.model_validate({"agent_id": 1, "build_key": None})
    assert s.state is None


# ── Orgs ───────────────────────────────────────────────────────────────────


def test_org_parses():
    o = models.Org.model_validate(ORG)
    assert o.slug == "acme"


def test_org_member_parses():
    m = models.OrgMember.model_validate(ORG_MEMBER)
    assert m.role == "member"
    assert m.user.login == "alice"


def test_org_invitation_parses_github_login():
    inv = models.OrgInvitation.model_validate(ORG_INVITATION)
    assert inv.github_login == "alice"
    assert inv.email is None
    assert inv.state == "pending"


def test_org_join_request_parses():
    r = models.OrgJoinRequest.model_validate(ORG_JOIN_REQUEST)
    assert r.status == "pending"


def test_org_credentials_parses():
    c = models.OrgCredentials.model_validate(ORG_CREDENTIALS)
    assert c.claude.set is True


def test_org_event_parses_with_actor():
    e = models.OrgEvent.model_validate(ORG_EVENT)
    assert e.actor and e.actor.login == "alice"
    assert e.payload["agent_id"] == 7


# ── Integrations ──────────────────────────────────────────────────────────


def test_integration_install_optional_binding():
    inst = models.IntegrationInstall.model_validate(INTEGRATION_INSTALL)
    assert inst.binding is None


def test_integration_binding_parses():
    b = models.IntegrationBinding.model_validate(INTEGRATION_BINDING)
    assert b.agent_id == 7


def test_github_install_parses():
    g = models.GithubInstall.model_validate(GITHUB_INSTALL)
    assert g.account_login == "tinyhq"


def test_github_repo_parses():
    r = models.GithubRepo.model_validate(GITHUB_REPO)
    assert r.private is True


# ── Public config ─────────────────────────────────────────────────────────


def test_public_config_parses():
    c = models.PublicConfig.model_validate(PUBLIC_CONFIG)
    assert c.google_enabled is True


# ── Forward compat ─────────────────────────────────────────────────────────


def test_models_tolerate_unknown_fields():
    """Forward-compat: a server adding a new field must not break old SDKs."""
    a = models.Agent.model_validate(AGENT | {"newly_added_field": "ignore me"})
    assert a.id == 7


def test_invalid_status_rejected():
    """We don't silently accept malformed ids — that hides bugs."""
    bad = AGENT | {"id": "not-an-int"}
    with pytest.raises(Exception):
        models.Agent.model_validate(bad)


def test_chat_event_roundtrip():
    e = models.ChatEvent.model_validate(
        {
            "seq": 1,
            "payload": {"type": "assistant_message", "text": "hi"},
            "created_at": "2026-05-01T00:00:00Z",
        }
    )
    assert e.seq == 1
    assert e.created_at.tzinfo == timezone.utc


def test_session_created_at_is_datetime():
    s = models.Session.model_validate(SESSION)
    assert isinstance(s.created_at, datetime)
