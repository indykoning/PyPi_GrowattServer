"""A caller-supplied session lets cookies survive across API instances."""
import requests

from growattServer import GrowattApi


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
