"""Behaviour tests for the public exception hierarchy.

These pin three properties callers actually depend on:
  - every typed error inherits from AnyFrameError, so `except AnyFrameError`
    is a safe catch-all.
  - APIError carries status_code/message attributes (not just a string).
  - RateLimitError exposes retry_after for retry loops.
"""

import pytest

from anyframe import exceptions as exc


def test_all_errors_inherit_from_base():
    for cls in (
        exc.APIError,
        exc.AuthError,
        exc.NotFoundError,
        exc.ValidationError,
        exc.ConflictError,
        exc.RateLimitError,
        exc.ServerError,
    ):
        assert issubclass(cls, exc.AnyFrameError), cls


def test_api_error_carries_status_and_message():
    e = exc.APIError(503, "upstream timeout")
    assert e.status_code == 503
    assert e.message == "upstream timeout"
    assert "503" in str(e)
    assert "upstream timeout" in str(e)


def test_typed_errors_set_their_status_code():
    assert exc.AuthError("nope").status_code == 401
    assert exc.NotFoundError("gone").status_code == 404
    assert exc.ValidationError("bad").status_code == 422
    assert exc.ConflictError("dup").status_code == 409
    assert exc.ServerError(503, "boom").status_code == 503


def test_rate_limit_exposes_retry_after():
    e = exc.RateLimitError("slow down", retry_after=12)
    assert e.status_code == 429
    assert e.retry_after == 12


def test_validation_error_can_carry_field_details():
    e = exc.ValidationError("body invalid", details=[{"loc": ["name"], "msg": "required"}])
    assert e.details == [{"loc": ["name"], "msg": "required"}]


def test_base_error_is_catchable():
    with pytest.raises(exc.AnyFrameError):
        raise exc.NotFoundError("missing")
