"""A caller-supplied session lets cookies survive across API instances."""
import json

import pytest
import requests

from growattServer import GrowattApi, GrowattRateLimitError


def test_default_still_creates_its_own_session():
    api = GrowattApi()

    assert isinstance(api.session, requests.Session)


def test_injected_session_is_used_as_is():
    shared = requests.Session()

    api = GrowattApi(session=shared)

    assert api.session is shared


def test_two_instances_share_one_session():
    """The point of the parameter: one login, many API objects."""
    shared = requests.Session()

    first = GrowattApi(session=shared)
    second = GrowattApi(session=shared)

    assert first.session is second.session


def test_cookies_on_the_injected_session_survive():
    """Restoring persisted cookies at startup is the reason this exists."""
    shared = requests.Session()
    shared.cookies.set("JSESSIONID", "restored-from-storage")

    api = GrowattApi(session=shared)

    assert api.session.cookies.get("JSESSIONID") == "restored-from-storage"


def test_existing_hooks_on_the_injected_session_are_kept():
    """A shared session may already carry hooks; they must not be dropped."""
    called = []

    def _mine(response, *args, **kwargs):
        called.append(response)

    shared = requests.Session()
    shared.hooks["response"] = [_mine]

    api = GrowattApi(session=shared)

    assert _mine in api.session.hooks["response"]
    assert len(api.session.hooks["response"]) == 2


def test_sharing_a_session_installs_the_hook_once():
    """N instances on one session must not stack N copies of the hook."""
    def _mine(response, *args, **kwargs):
        pass

    shared = requests.Session()
    shared.hooks["response"] = [_mine]

    for _ in range(3):
        GrowattApi(session=shared)

    assert len(shared.hooks["response"]) == 2
    assert shared.hooks["response"][0] is _mine


def test_shared_session_checks_each_response_once():
    """Each response goes through raise_for_status once, however many instances."""
    shared = requests.Session()
    for _ in range(3):
        GrowattApi(session=shared)

    response = requests.Response()
    response.status_code = 200
    calls = []
    response.raise_for_status = lambda: calls.append(response)

    requests.hooks.dispatch_hook("response", shared.hooks, response)

    assert len(calls) == 1


def test_bare_callable_hook_is_normalised():
    """requests permits a single callable instead of a list."""
    def _mine(response, *args, **kwargs):
        pass

    shared = requests.Session()
    shared.hooks["response"] = _mine

    api = GrowattApi(session=shared)

    assert _mine in api.session.hooks["response"]


def test_user_agent_is_applied_to_the_injected_session():
    shared = requests.Session()

    api = GrowattApi(session=shared, agent_identifier="my-agent")

    assert shared.headers["User-Agent"] == "my-agent"


def test_injected_session_keeps_its_user_agent_by_default():
    """Without agent_identifier, a caller's own User-Agent must survive."""
    shared = requests.Session()
    shared.headers["User-Agent"] = "callers-agent"

    GrowattApi(session=shared)

    assert shared.headers["User-Agent"] == "callers-agent"


def test_own_session_still_gets_the_library_user_agent():
    api = GrowattApi()

    assert api.session.headers["User-Agent"] == GrowattApi.agent_identifier


def test_random_user_id_is_applied_to_the_injected_session():
    """Asking for a random suffix is asking for the header to change."""
    shared = requests.Session()
    shared.headers["User-Agent"] = "callers-agent"

    GrowattApi(session=shared, add_random_user_id=True)

    assert shared.headers["User-Agent"].startswith(GrowattApi.agent_identifier + " - ")


def test_an_unrelated_hook_with_the_same_name_is_not_mistaken_for_ours():
    """De-duplication is by identity, not by name."""
    def _raise_for_status(response, *args, **kwargs):
        pass

    # As if it were a top-level function of the same name in another module.
    _raise_for_status.__qualname__ = "_raise_for_status"
    shared = requests.Session()
    shared.hooks["response"] = [_raise_for_status]

    GrowattApi(session=shared)

    assert len(shared.hooks["response"]) == 2


def test_an_injected_session_still_raises_on_the_507_lockout():
    """The 507 check lives in the hook, so a shared session must carry it too."""
    shared = requests.Session()
    GrowattApi(session=shared)

    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps({"success": False, "msg": "507"}).encode()
    response.headers["Content-Type"] = "application/json"

    with pytest.raises(GrowattRateLimitError):
        requests.hooks.dispatch_hook("response", shared.hooks, response)
