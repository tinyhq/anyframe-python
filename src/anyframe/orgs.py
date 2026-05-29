"""Organisations resource — ``/api/orgs``.

An :class:`Org` is a shared workspace: every member sees the same agents,
templates, sessions, and connectors, and shares the same runtime credit
pool. The control plane gates the whole surface behind a server-side
``ORGS_ENABLED`` flag — every endpoint here returns 404 when the flag is
off.

The flat-resource shape mirrors the rest of the SDK: members,
invitations, join requests, credentials, and audit each hang off the
parent ``Orgs`` client and take a ``slug`` as their first positional
argument so the URL is the source of truth.
"""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, Any

from .models import (
    JoinRequestCreated,
    Org,
    OrgCredentials,
    OrgEvent,
    OrgInvitation,
    OrgInvitationCreated,
    OrgInvitationView,
    OrgJoinRequest,
    OrgMember,
    OrgMembership,
    OrgRole,
    SlugAvailability,
)

if TYPE_CHECKING:  # pragma: no cover
    from ._http import AsyncHTTP, SyncHTTP


def _prune(body: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in body.items() if v is not None}


# ── Sync ────────────────────────────────────────────────────────────────────


class OrgMembers:
    """Members + join-requests subresource — ``/api/orgs/{slug}/members``."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(self, slug: str) -> builtins.list[OrgMember]:
        data = self._http.request("GET", f"/api/orgs/{slug}/members")
        return [OrgMember.model_validate(row) for row in data]

    def change_role(self, slug: str, user_id: int, *, role: OrgRole) -> OrgMember:
        data = self._http.request(
            "PATCH",
            f"/api/orgs/{slug}/members/{user_id}",
            json={"role": role},
        )
        return OrgMember.model_validate(data)

    def remove(self, slug: str, user_id: int) -> None:
        self._http.request("DELETE", f"/api/orgs/{slug}/members/{user_id}")

    def leave(self, slug: str) -> None:
        """Leave the org as the current user. Owners must transfer first."""
        self._http.request("POST", f"/api/orgs/{slug}/members/leave")


class OrgJoinRequests:
    """Join requests subresource — ``/api/orgs/{slug}/join-requests``."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(self, slug: str) -> builtins.list[OrgJoinRequest]:
        """Admin-only: list pending requests."""
        data = self._http.request("GET", f"/api/orgs/{slug}/join-requests")
        return [OrgJoinRequest.model_validate(row) for row in data]

    def create(self, slug: str) -> JoinRequestCreated:
        """Request to join the org as the current user.

        The server gates this on the user's email matching the org's
        ``auto_join_domain`` — it returns 404 if not eligible (identical
        response shape to "slug doesn't exist" so probing reveals nothing).
        """
        data = self._http.request("POST", f"/api/orgs/{slug}/join-requests")
        return JoinRequestCreated.model_validate(data)

    def approve(
        self, slug: str, request_id: int, *, role: OrgRole = "member",
    ) -> OrgMember:
        """Admin: approve a pending join request and add the user as a member."""
        data = self._http.request(
            "POST",
            f"/api/orgs/{slug}/join-requests/{request_id}/approve",
            json={"role": role},
        )
        return OrgMember.model_validate(data)

    def reject(self, slug: str, request_id: int) -> None:
        """Admin: reject a pending join request."""
        self._http.request(
            "POST", f"/api/orgs/{slug}/join-requests/{request_id}/reject",
        )


class OrgInvitations:
    """Invitations subresource — ``/api/orgs/{slug}/invitations`` and the
    public-token routes under ``/api/invitations/{token}``.
    """

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(
        self, slug: str, *, include_resolved: bool = False,
    ) -> builtins.list[OrgInvitation]:
        """Admin-only: list invitations. Pending only by default."""
        data = self._http.request(
            "GET",
            f"/api/orgs/{slug}/invitations",
            params={"include_resolved": include_resolved},
        )
        return [OrgInvitation.model_validate(row) for row in data]

    def create(
        self,
        slug: str,
        *,
        email: str | None = None,
        github_login: str | None = None,
        role: OrgRole = "member",
        message: str | None = None,
    ) -> OrgInvitationCreated:
        """Invite a single person. Pass exactly one of ``email`` or ``github_login``.

        GitHub-login invitations show up inline in the invitee's org
        switcher (see :class:`User.pending_invitations`); email invitations
        are sent as a one-time link with the returned ``url``.
        """
        body = _prune(
            {
                "email": email,
                "github_login": github_login,
                "role": role,
                "message": message,
            }
        )
        data = self._http.request(
            "POST", f"/api/orgs/{slug}/invitations", json=body,
        )
        return OrgInvitationCreated.model_validate(data)

    def revoke(self, slug: str, invitation_id: int) -> None:
        """Admin-only: revoke a pending invitation."""
        self._http.request(
            "POST", f"/api/orgs/{slug}/invitations/{invitation_id}/revoke",
        )

    def resend(self, slug: str, invitation_id: int) -> OrgInvitationCreated:
        """Admin-only: mint a fresh token and resend the invite.

        The previous link stops working — useful for cycling a leaked link.
        """
        data = self._http.request(
            "POST", f"/api/orgs/{slug}/invitations/{invitation_id}/resend",
        )
        return OrgInvitationCreated.model_validate(data)

    def view_by_token(self, token: str) -> OrgInvitationView:
        """Public-ish: fetch an invitation by its plaintext token.

        Lets the invitee see org name, role, and inviter before signing in.
        """
        data = self._http.request("GET", f"/api/invitations/{token}")
        return OrgInvitationView.model_validate(data)

    def accept_by_token(self, token: str) -> OrgMembership:
        """Accept an email-style invitation using its plaintext token."""
        data = self._http.request("POST", f"/api/invitations/{token}/accept")
        return OrgMembership.model_validate(data)

    def accept_for_me(self, invitation_id: int) -> OrgMembership:
        """Accept a GitHub-username invitation inline (no token needed).

        Pairs with :attr:`User.pending_invitations` — call this with the
        ``id`` from one of those entries to accept it in place.
        """
        data = self._http.request(
            "POST", f"/api/me/invitations/{invitation_id}/accept",
        )
        return OrgMembership.model_validate(data)


class OrgCredentialsResource:
    """Per-org credentials — ``/api/orgs/{slug}/credentials`` (admin-only)."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def get(self, slug: str) -> OrgCredentials:
        data = self._http.request("GET", f"/api/orgs/{slug}/credentials")
        return OrgCredentials.model_validate(data)

    def set_claude(self, slug: str, token: str) -> None:
        self._http.request(
            "PUT",
            f"/api/orgs/{slug}/credentials/claude",
            json={"token": token},
        )

    def set_codex(self, slug: str, token: str) -> None:
        self._http.request(
            "PUT",
            f"/api/orgs/{slug}/credentials/codex",
            json={"token": token},
        )

    def clear_claude(self, slug: str) -> None:
        self._http.request("DELETE", f"/api/orgs/{slug}/credentials/claude")

    def clear_codex(self, slug: str) -> None:
        self._http.request("DELETE", f"/api/orgs/{slug}/credentials/codex")


class OrgAudit:
    """Org audit log — ``/api/orgs/{slug}/events`` (admin-only)."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http

    def list(
        self,
        slug: str,
        *,
        kind: str | None = None,
        since: int | None = None,
        limit: int = 50,
    ) -> builtins.list[OrgEvent]:
        """List recent audit events, newest first.

        Args:
            slug: The org slug.
            kind: Filter by event kind (``"agent.created"``,
                ``"template.updated"``, ``"session.handoff_completed"``, …).
            since: Return only events with ``id > since``.
            limit: Max events to return. Server caps at 500.
        """
        params: dict[str, Any] = {"limit": limit}
        if kind is not None:
            params["kind"] = kind
        if since is not None:
            params["since"] = since
        data = self._http.request(
            "GET", f"/api/orgs/{slug}/events", params=params,
        )
        return [OrgEvent.model_validate(row) for row in data]

    def export_csv(self, slug: str, *, kind: str | None = None) -> bytes:
        """Stream the full audit log as CSV bytes (admin-only)."""
        params: dict[str, Any] = {}
        if kind is not None:
            params["kind"] = kind
        return self._http.get_bytes(
            f"/api/orgs/{slug}/events/export.csv", params=params,
        )


class Orgs:
    """Manage organisations (workspaces) and their members / invitations / credentials."""

    def __init__(self, http: SyncHTTP) -> None:
        self._http = http
        self.members = OrgMembers(http)
        self.join_requests = OrgJoinRequests(http)
        self.invitations = OrgInvitations(http)
        self.credentials = OrgCredentialsResource(http)
        self.audit = OrgAudit(http)

    def check_slug(self, slug: str) -> SlugAvailability:
        """Check whether ``slug`` is available for a new org."""
        data = self._http.request(
            "GET", "/api/orgs/check_slug", params={"slug": slug},
        )
        return SlugAvailability.model_validate(data)

    def list(self) -> builtins.list[OrgMembership]:
        """List the orgs the current user is a member of, with their role."""
        data = self._http.request("GET", "/api/orgs")
        return [OrgMembership.model_validate(row) for row in data]

    def create(
        self, *, slug: str, name: str, auto_join_domain: str | None = None,
    ) -> Org:
        """Create a new org. The current user becomes its owner.

        Args:
            slug: URL slug — 2–32 chars, ``a-z0-9-`` with no leading,
                trailing, or consecutive hyphens. Reserved words like
                ``new``, ``settings``, ``api`` are blocked.
            name: Display name.
            auto_join_domain: Optional email domain (e.g. ``acme.com``).
                Users with a matching address see a "request to join"
                banner — admin approval still required.
        """
        body = _prune(
            {"slug": slug, "name": name, "auto_join_domain": auto_join_domain},
        )
        data = self._http.request("POST", "/api/orgs", json=body)
        return Org.model_validate(data)

    def get(self, slug: str) -> Org:
        """Return one org by slug (member-only)."""
        data = self._http.request("GET", f"/api/orgs/{slug}")
        return Org.model_validate(data)

    def update(self, slug: str, **fields: Any) -> Org:
        """Patch ``name``, ``slug``, or ``auto_join_domain`` (owner-only).

        Passing ``auto_join_domain=None`` clears the domain;
        omit the kwarg entirely to leave it unchanged.
        """
        data = self._http.request("PATCH", f"/api/orgs/{slug}", json=fields)
        return Org.model_validate(data)

    def delete(self, slug: str) -> None:
        """Archive the org (owner-only).

        The slug is freed for re-use. All data is soft-deleted; contact
        support to restore.
        """
        self._http.request("DELETE", f"/api/orgs/{slug}")

    def transfer_ownership(self, slug: str, *, new_owner_user_id: int) -> Org:
        """Hand ownership to another current member (owner-only)."""
        data = self._http.request(
            "POST",
            f"/api/orgs/{slug}/transfer-ownership",
            json={"new_owner_user_id": new_owner_user_id},
        )
        return Org.model_validate(data)

    def activity(self, slug: str) -> dict[str, Any]:
        """Return the dashboard activity summary for the org (member-only).

        Cheap aggregates (counts, recent events) — the exact shape evolves
        with the dashboard's needs, so this returns the raw response dict.
        """
        return self._http.request("GET", f"/api/orgs/{slug}/activity")


# ── Async ───────────────────────────────────────────────────────────────────


class AsyncOrgMembers:
    """Async counterpart to :class:`OrgMembers`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(self, slug: str) -> builtins.list[OrgMember]:
        data = await self._http.request("GET", f"/api/orgs/{slug}/members")
        return [OrgMember.model_validate(row) for row in data]

    async def change_role(
        self, slug: str, user_id: int, *, role: OrgRole,
    ) -> OrgMember:
        data = await self._http.request(
            "PATCH",
            f"/api/orgs/{slug}/members/{user_id}",
            json={"role": role},
        )
        return OrgMember.model_validate(data)

    async def remove(self, slug: str, user_id: int) -> None:
        await self._http.request("DELETE", f"/api/orgs/{slug}/members/{user_id}")

    async def leave(self, slug: str) -> None:
        await self._http.request("POST", f"/api/orgs/{slug}/members/leave")


class AsyncOrgJoinRequests:
    """Async counterpart to :class:`OrgJoinRequests`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(self, slug: str) -> builtins.list[OrgJoinRequest]:
        data = await self._http.request("GET", f"/api/orgs/{slug}/join-requests")
        return [OrgJoinRequest.model_validate(row) for row in data]

    async def create(self, slug: str) -> JoinRequestCreated:
        data = await self._http.request("POST", f"/api/orgs/{slug}/join-requests")
        return JoinRequestCreated.model_validate(data)

    async def approve(
        self, slug: str, request_id: int, *, role: OrgRole = "member",
    ) -> OrgMember:
        data = await self._http.request(
            "POST",
            f"/api/orgs/{slug}/join-requests/{request_id}/approve",
            json={"role": role},
        )
        return OrgMember.model_validate(data)

    async def reject(self, slug: str, request_id: int) -> None:
        await self._http.request(
            "POST", f"/api/orgs/{slug}/join-requests/{request_id}/reject",
        )


class AsyncOrgInvitations:
    """Async counterpart to :class:`OrgInvitations`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(
        self, slug: str, *, include_resolved: bool = False,
    ) -> builtins.list[OrgInvitation]:
        data = await self._http.request(
            "GET",
            f"/api/orgs/{slug}/invitations",
            params={"include_resolved": include_resolved},
        )
        return [OrgInvitation.model_validate(row) for row in data]

    async def create(
        self,
        slug: str,
        *,
        email: str | None = None,
        github_login: str | None = None,
        role: OrgRole = "member",
        message: str | None = None,
    ) -> OrgInvitationCreated:
        body = _prune(
            {
                "email": email,
                "github_login": github_login,
                "role": role,
                "message": message,
            }
        )
        data = await self._http.request(
            "POST", f"/api/orgs/{slug}/invitations", json=body,
        )
        return OrgInvitationCreated.model_validate(data)

    async def revoke(self, slug: str, invitation_id: int) -> None:
        await self._http.request(
            "POST", f"/api/orgs/{slug}/invitations/{invitation_id}/revoke",
        )

    async def resend(self, slug: str, invitation_id: int) -> OrgInvitationCreated:
        data = await self._http.request(
            "POST", f"/api/orgs/{slug}/invitations/{invitation_id}/resend",
        )
        return OrgInvitationCreated.model_validate(data)

    async def view_by_token(self, token: str) -> OrgInvitationView:
        data = await self._http.request("GET", f"/api/invitations/{token}")
        return OrgInvitationView.model_validate(data)

    async def accept_by_token(self, token: str) -> OrgMembership:
        data = await self._http.request("POST", f"/api/invitations/{token}/accept")
        return OrgMembership.model_validate(data)

    async def accept_for_me(self, invitation_id: int) -> OrgMembership:
        data = await self._http.request(
            "POST", f"/api/me/invitations/{invitation_id}/accept",
        )
        return OrgMembership.model_validate(data)


class AsyncOrgCredentialsResource:
    """Async counterpart to :class:`OrgCredentialsResource`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def get(self, slug: str) -> OrgCredentials:
        data = await self._http.request("GET", f"/api/orgs/{slug}/credentials")
        return OrgCredentials.model_validate(data)

    async def set_claude(self, slug: str, token: str) -> None:
        await self._http.request(
            "PUT",
            f"/api/orgs/{slug}/credentials/claude",
            json={"token": token},
        )

    async def set_codex(self, slug: str, token: str) -> None:
        await self._http.request(
            "PUT",
            f"/api/orgs/{slug}/credentials/codex",
            json={"token": token},
        )

    async def clear_claude(self, slug: str) -> None:
        await self._http.request("DELETE", f"/api/orgs/{slug}/credentials/claude")

    async def clear_codex(self, slug: str) -> None:
        await self._http.request("DELETE", f"/api/orgs/{slug}/credentials/codex")


class AsyncOrgAudit:
    """Async counterpart to :class:`OrgAudit`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http

    async def list(
        self,
        slug: str,
        *,
        kind: str | None = None,
        since: int | None = None,
        limit: int = 50,
    ) -> builtins.list[OrgEvent]:
        params: dict[str, Any] = {"limit": limit}
        if kind is not None:
            params["kind"] = kind
        if since is not None:
            params["since"] = since
        data = await self._http.request(
            "GET", f"/api/orgs/{slug}/events", params=params,
        )
        return [OrgEvent.model_validate(row) for row in data]

    async def export_csv(self, slug: str, *, kind: str | None = None) -> bytes:
        params: dict[str, Any] = {}
        if kind is not None:
            params["kind"] = kind
        return await self._http.get_bytes(
            f"/api/orgs/{slug}/events/export.csv", params=params,
        )


class AsyncOrgs:
    """Async counterpart to :class:`Orgs`."""

    def __init__(self, http: AsyncHTTP) -> None:
        self._http = http
        self.members = AsyncOrgMembers(http)
        self.join_requests = AsyncOrgJoinRequests(http)
        self.invitations = AsyncOrgInvitations(http)
        self.credentials = AsyncOrgCredentialsResource(http)
        self.audit = AsyncOrgAudit(http)

    async def check_slug(self, slug: str) -> SlugAvailability:
        data = await self._http.request(
            "GET", "/api/orgs/check_slug", params={"slug": slug},
        )
        return SlugAvailability.model_validate(data)

    async def list(self) -> builtins.list[OrgMembership]:
        data = await self._http.request("GET", "/api/orgs")
        return [OrgMembership.model_validate(row) for row in data]

    async def create(
        self, *, slug: str, name: str, auto_join_domain: str | None = None,
    ) -> Org:
        body = _prune(
            {"slug": slug, "name": name, "auto_join_domain": auto_join_domain},
        )
        data = await self._http.request("POST", "/api/orgs", json=body)
        return Org.model_validate(data)

    async def get(self, slug: str) -> Org:
        data = await self._http.request("GET", f"/api/orgs/{slug}")
        return Org.model_validate(data)

    async def update(self, slug: str, **fields: Any) -> Org:
        data = await self._http.request("PATCH", f"/api/orgs/{slug}", json=fields)
        return Org.model_validate(data)

    async def delete(self, slug: str) -> None:
        await self._http.request("DELETE", f"/api/orgs/{slug}")

    async def transfer_ownership(
        self, slug: str, *, new_owner_user_id: int,
    ) -> Org:
        data = await self._http.request(
            "POST",
            f"/api/orgs/{slug}/transfer-ownership",
            json={"new_owner_user_id": new_owner_user_id},
        )
        return Org.model_validate(data)

    async def activity(self, slug: str) -> dict[str, Any]:
        return await self._http.request("GET", f"/api/orgs/{slug}/activity")


__all__ = [
    "AsyncOrgAudit",
    "AsyncOrgCredentialsResource",
    "AsyncOrgInvitations",
    "AsyncOrgJoinRequests",
    "AsyncOrgMembers",
    "AsyncOrgs",
    "OrgAudit",
    "OrgCredentialsResource",
    "OrgInvitations",
    "OrgJoinRequests",
    "OrgMembers",
    "Orgs",
]
