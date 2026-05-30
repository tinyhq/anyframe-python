"""Tests for the top-level AnyFrame client.

We pin three things the user sees first:

  - explicit kwargs win over env vars, env vars over defaults
  - a missing API key raises AuthError immediately (before any HTTP)
  - .env files in the working directory are honoured when no env var is set
  - the client behaves as a context manager and exposes me()
"""

from __future__ import annotations

import os

import httpx
import pytest
import respx

import anyframe
from anyframe import exceptions as exc

BASE_ENV = {
    "ANYFRAME_API_KEY": "afm_envkey",
    "ANYFRAME_BASE_URL": "https://api.example.com",
}


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    """Strip any inherited ANYFRAME_* env so each test starts from a known state."""
    for k in list(os.environ):
        if k.startswith("ANYFRAME_"):
            monkeypatch.delenv(k, raising=False)
    yield


def _env(monkeypatch, **vars_: str) -> None:
    for k, v in vars_.items():
        monkeypatch.setenv(k, v)


def test_explicit_kwargs_override_env(monkeypatch):
    _env(monkeypatch, **BASE_ENV)
    af = anyframe.AnyFrame(api_key="afm_explicit", base_url="https://other.example")
    try:
        assert af._http._client.headers["Authorization"] == "Bearer afm_explicit"
        assert str(af._http._client.base_url).rstrip("/") == "https://other.example"
    finally:
        af.close()


def test_env_vars_used_when_kwargs_absent(monkeypatch):
    _env(monkeypatch, **BASE_ENV)
    af = anyframe.AnyFrame()
    try:
        assert af._http._client.headers["Authorization"] == "Bearer afm_envkey"
    finally:
        af.close()


def test_default_base_url_is_anyframe(monkeypatch):
    _env(monkeypatch, ANYFRAME_API_KEY="afm_x")
    af = anyframe.AnyFrame()
    try:
        assert "anyframe.dev" in str(af._http._client.base_url)
    finally:
        af.close()


def test_missing_api_key_raises_auth_error(monkeypatch):
    with pytest.raises(exc.AuthError) as ei:
        anyframe.AnyFrame()
    assert "ANYFRAME_API_KEY" in str(ei.value)


def test_dotenv_file_is_loaded(monkeypatch, tmp_path):
    """When no env var is set, a .env in cwd should provide the key."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "ANYFRAME_API_KEY=afm_fromfile\nANYFRAME_BASE_URL=https://from.file\n"
    )
    af = anyframe.AnyFrame()
    try:
        assert af._http._client.headers["Authorization"] == "Bearer afm_fromfile"
        assert str(af._http._client.base_url).rstrip("/") == "https://from.file"
    finally:
        af.close()


def test_dotenv_does_not_override_existing_env(monkeypatch, tmp_path):
    """python-dotenv default behaviour: env vars set in the shell win."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("ANYFRAME_API_KEY=afm_dotenv\n")
    monkeypatch.setenv("ANYFRAME_API_KEY", "afm_shell")
    af = anyframe.AnyFrame()
    try:
        assert af._http._client.headers["Authorization"] == "Bearer afm_shell"
    finally:
        af.close()


def test_load_dotenv_can_be_disabled(monkeypatch, tmp_path):
    """Callers in libraries embedding the SDK can suppress dotenv loading."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("ANYFRAME_API_KEY=afm_fromfile\n")
    with pytest.raises(exc.AuthError):
        anyframe.AnyFrame(load_dotenv=False)


def test_context_manager_closes_client(monkeypatch):
    _env(monkeypatch, **BASE_ENV)
    with anyframe.AnyFrame() as af:
        assert af._http._client.is_closed is False
    assert af._http._client.is_closed is True


@respx.mock
def test_me_returns_user(monkeypatch):
    _env(monkeypatch, **BASE_ENV)
    respx.get("https://api.example.com/api/me").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 1,
                "github_id": 42,
                "login": "nish",
                "name": "Nish",
                "email": "nish@example.com",
                "avatar_url": None,
                "is_superadmin": False,
            },
        )
    )
    with anyframe.AnyFrame() as af:
        user = af.me()
    assert isinstance(user, anyframe.User)
    assert user.login == "nish"


@respx.mock
def test_me_translates_401_to_auth_error(monkeypatch):
    _env(monkeypatch, **BASE_ENV)
    respx.get("https://api.example.com/api/me").mock(
        return_value=httpx.Response(401, json={"detail": "bad token"})
    )
    with anyframe.AnyFrame() as af, pytest.raises(exc.AuthError):
        af.me()
