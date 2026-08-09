"""Growatt reports rate limiting in the body, not as an HTTP status."""
import json

import pytest
import requests

from growattServer import GrowattApi, GrowattRateLimitError


def _response(payload=None, *, body=None, status=200):
    """Build a real Response -- the check parses the body itself."""
    response = requests.Response()
    response.status_code = status
    if body is None:
        body = json.dumps(payload)
    response._content = body.encode()
    response.headers["Content-Type"] = "application/json"
    return response


class _HookedSession:
    """A session stand-in that runs the response hooks, as requests does.

    The 507 check lives in the hook now, so a plain MagicMock session would
    skip it and every test here would pass for the wrong reason.
    """

    def __init__(self, hooks, response):
        self.hooks = hooks
        self.headers = {}
        self._response = response

    def _dispatch(self, *args, **kwargs):
        for hook in self.hooks["response"]:
            hook(self._response)
        return self._response

    get = _dispatch
    post = _dispatch


def _api_returning(response):
    """An API whose every call answers with `response`, hooks included."""
    api = GrowattApi()
    api.session = _HookedSession(api.session.hooks, response)
    return api


def _api_with_login_body(body):
    """An API whose login answers with the given `back` payload."""
    return _api_returning(_response({"back": body}))


def test_login_raises_on_507_in_the_body():
    """`success: false` + `msg: "507"` is the real lockout signal."""
    api = _api_with_login_body({"success": False, "msg": "507"})

    with pytest.raises(GrowattRateLimitError) as exc:
        api.login("user", "pass")

    assert exc.value.error_code == "507"


def test_the_code_is_readable_off_the_exception():
    """Callers branch on `error_code`, never on the message wording."""
    api = _api_with_login_body({"success": False, "msg": "507"})

    with pytest.raises(GrowattRateLimitError) as exc:
        api.login("user", "pass")

    assert exc.value.error_code == "507"
    assert str(exc.value) == "Growatt rate limit reached: [507]"


def test_a_data_call_is_covered_too():
    """Growatt rate limits per endpoint, so this cannot be login-only."""
    api = _api_returning(_response({"back": {"success": False, "msg": "507"}}))

    with pytest.raises(GrowattRateLimitError):
        api.plant_list("user_1")


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


def test_a_list_back_does_not_raise():
    """`plant_list` answers with `back` as a list -- the guard must hold."""
    api = _api_returning(_response({"back": [{"success": False, "msg": "507"}]}))

    assert api.plant_list("user_1") == [{"success": False, "msg": "507"}]


def test_a_non_json_body_does_not_raise():
    """The hook sees every response, including ones that are not JSON."""
    response = _response(body="<html>maintenance</html>")
    response.headers["Content-Type"] = "text/html"
    api = _api_returning(response)

    for hook in api.session.hooks["response"]:
        hook(response)


def test_a_bare_body_without_the_back_wrapper_is_checked():
    """Not every endpoint wraps its payload, so read the top level too."""
    api = _api_returning(_response({"success": False, "msg": "507"}))

    with pytest.raises(GrowattRateLimitError):
        api.plant_list("user_1")


def test_http_errors_still_raise():
    """The rate-limit check must not shadow raise_for_status."""
    api = _api_returning(_response({"back": {"success": True}}, status=500))

    with pytest.raises(requests.exceptions.HTTPError):
        api.plant_list("user_1")
