"""Shared pytest fixtures for the SDK test suite."""

from __future__ import annotations

import os

import pytest

import anyframe

BASE_URL = "https://api.test.local"


@pytest.fixture(autouse=True)
def _clear_anyframe_env(monkeypatch):
    """Strip inherited ANYFRAME_* env so tests start from a known state."""
    for k in list(os.environ):
        if k.startswith("ANYFRAME_"):
            monkeypatch.delenv(k, raising=False)
    yield


@pytest.fixture
def client():
    """A sync AnyFrame pointed at the mocked BASE_URL."""
    with anyframe.AnyFrame(
        api_key="afm_test",
        base_url=BASE_URL,
        load_dotenv=False,
    ) as af:
        yield af


@pytest.fixture
async def aclient():
    """An async AnyFrame pointed at the mocked BASE_URL."""
    af = anyframe.AsyncAnyFrame(
        api_key="afm_test",
        base_url=BASE_URL,
        load_dotenv=False,
    )
    try:
        yield af
    finally:
        await af.aclose()
