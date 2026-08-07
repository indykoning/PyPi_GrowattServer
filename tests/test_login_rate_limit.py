"""Growatt reports a rate-limited login in the body, not as an HTTP status."""
from unittest.mock import MagicMock, patch

import pytest

from growattServer import GrowattApi, GrowattRateLimitError


def _api_with_login_body(body):
    """Build an API whose login POST returns the given `back` payload."""
    api = GrowattApi()
    response = MagicMock()
    response.json.return_value = {"back": body}
    response.status_code = 200  # the real lockout answers 200, not 507
    api.session = MagicMock()
    api.session.post.return_value = response
    return api


def test_login_raises_on_507_in_the_body():
    """`success: false` + `msg: "507"` is the real lockout signal."""
    api = _api_with_login_body({"success": False, "msg": "507"})

    with pytest.raises(GrowattRateLimitError) as exc:
        api.login("user", "pass")

    assert exc.value.error_code == "507"


def test_507_error_mentions_not_retrying():
    """Callers must not be nudged into an immediate retry."""
    api = _api_with_login_body({"success": False, "msg": "507"})

    with pytest.raises(GrowattRateLimitError) as exc:
        api.login("user", "pass")

    assert "do not retry immediately" in str(exc.value)


def test_other_failures_are_left_alone():
    """A wrong password must keep returning the dict, not raise."""
    api = _api_with_login_body({"success": False, "msg": "501"})

    result = api.login("user", "pass")

    assert result["success"] is False
    assert result["msg"] == "501"


def test_numeric_msg_is_still_recognised():
    """Defensive: the code is compared as a string."""
    api = _api_with_login_body({"success": False, "msg": 507})

    with pytest.raises(GrowattRateLimitError):
        api.login("user", "pass")


def test_successful_login_is_unaffected():
    """The happy path keeps its existing shape."""
    api = _api_with_login_body({
        "success": True,
        "user": {"id": "u1", "rightlevel": 1},
    })

    result = api.login("user", "pass")

    assert result["userId"] == "u1"
    assert result["userLevel"] == 1
