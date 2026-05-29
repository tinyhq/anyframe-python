"""Tests for the orgs resource and its nested sub-resources."""

from __future__ import annotations

import json

import httpx
import respx

import anyframe
from tests.conftest import BASE_URL
from tests.payloads import (
    ORG,
    ORG_CREDENTIALS,
    ORG_EVENT,
    ORG_INVITATION,
    ORG_JOIN_REQUEST,
    ORG_MEMBER,
)

INVITE_RESP: dict = {
    "invitation": ORG_INVITATION,
    "url": "https://anyfrm.com/invites/tok_xyz",
}


# ── CRUD ──────────────────────────────────────────────────────────────────


@respx.mock
def test_check_slug(client):
    respx.get(f"{BASE_URL}/api/orgs/check_slug").mock(
        return_value=httpx.Response(200, json={"available": True, "reason": "ok"}),
    )
    out = client.orgs.check_slug("acme-2")
    assert out.available is True


@respx.mock
def test_list_memberships(client):
    respx.get(f"{BASE_URL}/api/orgs").mock(
        return_value=httpx.Response(200, json=[{"org": ORG, "role": "owner"}]),
    )
    rows = client.orgs.list()
    assert rows[0].role == "owner"
    assert rows[0].org.slug == "acme"


@respx.mock
def test_create_org(client):
    route = respx.post(f"{BASE_URL}/api/orgs").mock(
        return_value=httpx.Response(201, json=ORG),
    )
    out = client.orgs.create(slug="acme", name="Acme", auto_join_domain="acme.com")
    assert isinstance(out, anyframe.Org)
    body = json.loads(route.calls.last.request.read())
    assert body == {"slug": "acme", "name": "Acme", "auto_join_domain": "acme.com"}


@respx.mock
def test_get_org(client):
    respx.get(f"{BASE_URL}/api/orgs/acme").mock(
        return_value=httpx.Response(200, json=ORG),
    )
    out = client.orgs.get("acme")
    assert out.name == "Acme"


@respx.mock
def test_update_org_passes_through_partial_fields(client):
    route = respx.patch(f"{BASE_URL}/api/orgs/acme").mock(
        return_value=httpx.Response(200, json=ORG),
    )
    client.orgs.update("acme", name="Acme Corp")
    assert json.loads(route.calls.last.request.read()) == {"name": "Acme Corp"}


@respx.mock
def test_delete_org(client):
    route = respx.delete(f"{BASE_URL}/api/orgs/acme").mock(
        return_value=httpx.Response(204),
    )
    client.orgs.delete("acme")
    assert route.called


@respx.mock
def test_transfer_ownership(client):
    route = respx.post(f"{BASE_URL}/api/orgs/acme/transfer-ownership").mock(
        return_value=httpx.Response(200, json=ORG),
    )
    client.orgs.transfer_ownership("acme", new_owner_user_id=42)
    body = json.loads(route.calls.last.request.read())
    assert body == {"new_owner_user_id": 42}


# ── Members ────────────────────────────────────────────────────────────────


@respx.mock
def test_members_list(client):
    respx.get(f"{BASE_URL}/api/orgs/acme/members").mock(
        return_value=httpx.Response(200, json=[ORG_MEMBER]),
    )
    rows = client.orgs.members.list("acme")
    assert rows[0].user.login == "alice"


@respx.mock
def test_members_change_role(client):
    route = respx.patch(f"{BASE_URL}/api/orgs/acme/members/5").mock(
        return_value=httpx.Response(200, json=ORG_MEMBER | {"role": "admin"}),
    )
    out = client.orgs.members.change_role("acme", 5, role="admin")
    assert out.role == "admin"
    assert json.loads(route.calls.last.request.read()) == {"role": "admin"}


@respx.mock
def test_members_remove(client):
    route = respx.delete(f"{BASE_URL}/api/orgs/acme/members/5").mock(
        return_value=httpx.Response(204),
    )
    client.orgs.members.remove("acme", 5)
    assert route.called


@respx.mock
def test_members_leave(client):
    route = respx.post(f"{BASE_URL}/api/orgs/acme/members/leave").mock(
        return_value=httpx.Response(204),
    )
    client.orgs.members.leave("acme")
    assert route.called


# ── Join requests ──────────────────────────────────────────────────────────


@respx.mock
def test_join_requests_list(client):
    respx.get(f"{BASE_URL}/api/orgs/acme/join-requests").mock(
        return_value=httpx.Response(200, json=[ORG_JOIN_REQUEST]),
    )
    rows = client.orgs.join_requests.list("acme")
    assert rows[0].status == "pending"


@respx.mock
def test_join_requests_create(client):
    respx.post(f"{BASE_URL}/api/orgs/acme/join-requests").mock(
        return_value=httpx.Response(201, json={"id": 3, "status": "pending"}),
    )
    out = client.orgs.join_requests.create("acme")
    assert out.status == "pending"


@respx.mock
def test_join_requests_approve(client):
    route = respx.post(f"{BASE_URL}/api/orgs/acme/join-requests/3/approve").mock(
        return_value=httpx.Response(200, json=ORG_MEMBER),
    )
    out = client.orgs.join_requests.approve("acme", 3, role="member")
    assert isinstance(out, anyframe.OrgMember)
    assert json.loads(route.calls.last.request.read()) == {"role": "member"}


@respx.mock
def test_join_requests_reject(client):
    route = respx.post(f"{BASE_URL}/api/orgs/acme/join-requests/3/reject").mock(
        return_value=httpx.Response(204),
    )
    client.orgs.join_requests.reject("acme", 3)
    assert route.called


# ── Invitations ────────────────────────────────────────────────────────────


@respx.mock
def test_invitations_list(client):
    respx.get(f"{BASE_URL}/api/orgs/acme/invitations").mock(
        return_value=httpx.Response(200, json=[ORG_INVITATION]),
    )
    rows = client.orgs.invitations.list("acme")
    assert rows[0].github_login == "alice"


@respx.mock
def test_invitations_create_by_github_login(client):
    route = respx.post(f"{BASE_URL}/api/orgs/acme/invitations").mock(
        return_value=httpx.Response(201, json=INVITE_RESP),
    )
    out = client.orgs.invitations.create("acme", github_login="alice", message="hi")
    assert out.url.startswith("https://")
    body = json.loads(route.calls.last.request.read())
    assert body == {"github_login": "alice", "role": "member", "message": "hi"}


@respx.mock
def test_invitations_revoke_and_resend(client):
    revoke = respx.post(f"{BASE_URL}/api/orgs/acme/invitations/9/revoke").mock(
        return_value=httpx.Response(204),
    )
    resend = respx.post(f"{BASE_URL}/api/orgs/acme/invitations/9/resend").mock(
        return_value=httpx.Response(200, json=INVITE_RESP),
    )
    client.orgs.invitations.revoke("acme", 9)
    assert revoke.called
    client.orgs.invitations.resend("acme", 9)
    assert resend.called


@respx.mock
def test_invitations_view_and_accept_by_token(client):
    respx.get(f"{BASE_URL}/api/invitations/tok_xyz").mock(
        return_value=httpx.Response(
            200,
            json={
                "org": ORG,
                "role": "member",
                "inviter": None,
                "message": None,
                "expires_at": "2026-06-01T00:00:00Z",
                "state": "pending",
                "email": None,
                "github_login": "alice",
                "matches_current_user": True,
            },
        ),
    )
    view = client.orgs.invitations.view_by_token("tok_xyz")
    assert view.state == "pending"

    respx.post(f"{BASE_URL}/api/invitations/tok_xyz/accept").mock(
        return_value=httpx.Response(201, json={"org": ORG, "role": "member"}),
    )
    out = client.orgs.invitations.accept_by_token("tok_xyz")
    assert out.role == "member"


@respx.mock
def test_invitations_accept_for_me(client):
    respx.post(f"{BASE_URL}/api/me/invitations/9/accept").mock(
        return_value=httpx.Response(201, json={"org": ORG, "role": "member"}),
    )
    out = client.orgs.invitations.accept_for_me(9)
    assert out.org.slug == "acme"


# ── Credentials ────────────────────────────────────────────────────────────


@respx.mock
def test_org_credentials_get(client):
    respx.get(f"{BASE_URL}/api/orgs/acme/credentials").mock(
        return_value=httpx.Response(200, json=ORG_CREDENTIALS),
    )
    out = client.orgs.credentials.get("acme")
    assert out.claude.set is True


@respx.mock
def test_org_credentials_set_claude(client):
    route = respx.put(f"{BASE_URL}/api/orgs/acme/credentials/claude").mock(
        return_value=httpx.Response(204),
    )
    client.orgs.credentials.set_claude("acme", "tok")
    assert route.called
    assert json.loads(route.calls.last.request.read()) == {"token": "tok"}


@respx.mock
def test_org_credentials_clear_codex(client):
    route = respx.delete(f"{BASE_URL}/api/orgs/acme/credentials/codex").mock(
        return_value=httpx.Response(204),
    )
    client.orgs.credentials.clear_codex("acme")
    assert route.called


# ── Audit + activity ──────────────────────────────────────────────────────


@respx.mock
def test_audit_list_with_filters(client):
    route = respx.get(f"{BASE_URL}/api/orgs/acme/events").mock(
        return_value=httpx.Response(200, json=[ORG_EVENT]),
    )
    rows = client.orgs.audit.list("acme", kind="agent.created", limit=10)
    assert rows[0].kind == "agent.created"
    sent_params = dict(route.calls.last.request.url.params)
    assert sent_params["kind"] == "agent.created"
    assert sent_params["limit"] == "10"


@respx.mock
def test_audit_export_csv_returns_bytes(client):
    respx.get(f"{BASE_URL}/api/orgs/acme/events/export.csv").mock(
        return_value=httpx.Response(
            200,
            content=b"id,kind\n1,agent.created\n",
            headers={"content-type": "text/csv"},
        ),
    )
    out = client.orgs.audit.export_csv("acme")
    assert b"agent.created" in out


@respx.mock
def test_activity(client):
    respx.get(f"{BASE_URL}/api/orgs/acme/activity").mock(
        return_value=httpx.Response(200, json={"agent_count": 7, "session_count": 12}),
    )
    out = client.orgs.activity("acme")
    assert out["agent_count"] == 7
