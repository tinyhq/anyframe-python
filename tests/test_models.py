"""Tests for the Pydantic response models.

Models are constructed from API JSON, so the only properties worth pinning
are the ones the wire format guarantees:

  - they accept the exact field set the server returns (no rejected fields)
  - they tolerate optional/null fields per the FastAPI schemas
  - string enums round-trip cleanly (status values, transport, auth_kind)
  - extra unknown fields are not rejected (forward-compat)
"""

from datetime import datetime, timezone

import pytest

from anyframe import models

# ── User / Tokens / Credentials ────────────────────────────────────────────


def test_user_parses_full_payload():
    u = models.User.model_validate(
        {
            "id": 1,
            "github_id": 42,
            "login": "nish",
            "name": "Nish",
            "avatar_url": "https://example.com/a.png",
        }
    )
    assert u.login == "nish"
    assert u.avatar_url == "https://example.com/a.png"


def test_user_tolerates_null_optional_fields():
    u = models.User.model_validate(
        {"id": 1, "github_id": 42, "login": "nish", "name": None, "avatar_url": None}
    )
    assert u.name is None


def test_token_created_carries_raw_secret():
    t = models.TokenCreated.model_validate(
        {
            "id": 1,
            "name": "ci",
            "prefix": "afm_abcd",
            "last4": "wxyz",
            "created_at": "2025-01-01T00:00:00Z",
            "revoked_at": None,
            "token": "afm_abcdefghijklmnop",
        }
    )
    assert t.token == "afm_abcdefghijklmnop"
    assert t.revoked_at is None


def test_credentials_part_set_flag():
    c = models.Credentials.model_validate(
        {
            "claude": {"set": True, "last4": "wxyz", "updated_at": "2025-01-01T00:00:00Z"},
            "codex": {"set": False, "last4": None, "updated_at": None},
            "github": {"set": False, "last4": None, "updated_at": None},
        }
    )
    assert c.claude.set is True
    assert c.codex.set is False
    assert c.github.set is False


def test_credentials_tolerates_missing_codex():
    """Older servers don't return codex — must still parse (default applied)."""
    c = models.Credentials.model_validate(
        {
            "claude": {"set": True, "last4": "wxyz", "updated_at": None},
            "github": {"set": False, "last4": None, "updated_at": None},
        }
    )
    assert c.codex.set is False


# ── Agents ────────────────────────────────────────────────────────────────


AGENT_PAYLOAD = {
    "id": 7,
    "name": "demo",
    "description": None,
    "system_prompt": None,
    "repo_url": "tinyhq/box",
    "repo_ref": "main",
    "install_cmd": "bun install",
    "serve_cmd": None,
    "preview_ports": [3000],
    "build_key": "abc123",
    "permissions": {"preset": "standard", "extra_allowed_tools": []},
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
}


def test_agent_parses_summary():
    a = models.Agent.model_validate(AGENT_PAYLOAD)
    assert a.id == 7
    assert a.preview_ports == [3000]
    assert a.permissions["preset"] == "standard"


def test_agent_detail_includes_subresources():
    detail = AGENT_PAYLOAD | {
        "skills": [],
        "mcps": [],
        "connectors": [],
        "image": {
            "build_key": "abc123",
            "modal_image_id": "im_1",
            "built_at": "2025-01-01T00:00:00Z",
        },
    }
    a = models.AgentDetail.model_validate(detail)
    assert a.image is not None
    assert a.image.modal_image_id == "im_1"


def test_agent_skill_enum_values():
    s = models.AgentSkill.model_validate(
        {
            "id": 1,
            "name": "deploy",
            "source": "inline",
            "content": {},
            "enabled": True,
            "created_at": "2025-01-01T00:00:00Z",
        }
    )
    assert s.source == "inline"


def test_agent_mcp_carries_transport():
    m = models.AgentMcp.model_validate(
        {
            "id": 1,
            "name": "git",
            "transport": "http",
            "config": {"url": "x"},
            "secret_ref": None,
            "enabled": True,
            "created_at": "2025-01-01T00:00:00Z",
        }
    )
    assert m.transport == "http"


def test_agent_connector_toggle():
    t = models.AgentConnectorToggle.model_validate(
        {
            "connector_id": 1,
            "display_name": "Linear",
            "mcp_url": "https://mcp.linear.app/sse",
            "auth_kind": "oauth_dcr",
            "enabled": True,
            "is_authorized": False,
        }
    )
    assert t.is_authorized is False


# ── Connectors / Builds / Sessions ────────────────────────────────────────


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
    assert d.scopes_supported == []


def test_build_status_with_no_build_yet():
    s = models.BuildStatus.model_validate({"agent_id": 1, "build_key": None})
    assert s.state is None
    assert s.built_image_id is None


def test_session_parses_all_optional_fields_null():
    s = models.Session.model_validate(
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "agent_id": 1,
            "status": "booting",
            "modal_sandbox_id": None,
            "sandbox_url": None,
            "snapshot_image_id": None,
            "idle_timeout_s": 300,
            "previews": [],
            "is_setup_session": False,
            "created_at": "2025-01-01T00:00:00Z",
            "last_active": "2025-01-01T00:00:00Z",
        }
    )
    assert s.status == "booting"
    assert s.previews == []
    assert s.is_setup_session is False
    assert isinstance(s.created_at, datetime)


def test_session_parses_with_running_preview():
    s = models.Session.model_validate(
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "agent_id": 1,
            "status": "running",
            "idle_timeout_s": 300,
            "previews": [
                {
                    "port": 3000,
                    "name": "web",
                    "cmd": "bun dev",
                    "status": "running",
                    "url": "https://tunnel/3000",
                    "started_at": 1234567890.0,
                    "exit_code": None,
                }
            ],
            "is_setup_session": True,
            "created_at": "2025-01-01T00:00:00Z",
            "last_active": "2025-01-01T00:00:00Z",
        }
    )
    assert s.previews[0].port == 3000
    assert s.previews[0].url == "https://tunnel/3000"
    assert s.is_setup_session is True


def test_session_status_terminal_states_valid():
    """Every status string the server emits must parse — guards against
    enum drift between server and SDK."""
    for state in ("booting", "running", "snapshotting", "terminated", "error"):
        s = models.Session.model_validate(
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "agent_id": 1,
                "status": state,
                "modal_sandbox_id": None,
                "sandbox_url": None,
                "snapshot_image_id": None,
                "idle_timeout_s": 300,
                "previews": [],
                "is_setup_session": False,
                "created_at": "2025-01-01T00:00:00Z",
                "last_active": "2025-01-01T00:00:00Z",
            }
        )
        assert s.status == state


def test_models_tolerate_unknown_fields():
    """Forward-compat: a server adding a new field must not break old SDKs."""
    payload = AGENT_PAYLOAD | {"newly_added_field": "ignore me"}
    a = models.Agent.model_validate(payload)
    assert a.id == 7


def test_invalid_status_rejected():
    """We don't silently accept unknown status strings — that hides bugs."""
    bad = AGENT_PAYLOAD | {"id": "not-an-int"}
    with pytest.raises(Exception):
        models.Agent.model_validate(bad)


def test_chat_event_roundtrip():
    e = models.ChatEvent.model_validate(
        {
            "seq": 1,
            "payload": {"type": "assistant_message", "text": "hi"},
            "created_at": "2025-01-01T00:00:00Z",
        }
    )
    assert e.seq == 1
    assert e.payload["text"] == "hi"
    assert e.created_at.tzinfo == timezone.utc
