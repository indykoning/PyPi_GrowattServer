"""Shared fixtures and helpers for growattServer tests."""

from __future__ import annotations

import inspect
import json
from typing import Any

import httpx
import pytest

from growattServer import (
    AsyncGrowattApi,
    AsyncOpenApiV1,
    GrowattApi,
    OpenApiV1,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def invoke(obj: Any, method_name: str, *args: Any, **kwargs: Any) -> Any:
    """Call a method on either a sync or async API object, awaiting if needed."""
    method = getattr(obj, method_name)
    result = method(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


def json_response(data: dict | list, status_code: int = 200) -> httpx.Response:
    """Build an httpx.Response with a JSON body."""
    return httpx.Response(
        status_code,
        content=json.dumps(data).encode(),
        headers={"content-type": "application/json"},
    )


def v1_success(data: Any = None) -> dict:
    """Build a V1 API success envelope."""
    return {"error_code": 0, "error_msg": "", "data": data or {}}


def v1_error(error_code: int = 10001, error_msg: str = "System error") -> dict:
    """Build a V1 API error envelope."""
    return {"error_code": error_code, "error_msg": error_msg}


# ---------------------------------------------------------------------------
# Transport helpers
# ---------------------------------------------------------------------------

def make_mock_transport(handler):
    """Create a sync mock transport from a request handler.

    ``handler(request) -> httpx.Response``
    """
    return httpx.MockTransport(handler)


def make_async_mock_transport(handler):
    """Create an async mock transport from an async request handler.

    ``async handler(request) -> httpx.Response``
    """
    return httpx.MockTransport(handler)


# ---------------------------------------------------------------------------
# Base API fixtures (sync / async)
# ---------------------------------------------------------------------------

@pytest.fixture()
def sync_api_factory():
    """Factory for creating a sync GrowattApi with a mock transport."""
    apis = []

    def _factory(handler):
        transport = make_mock_transport(handler)
        api = GrowattApi(timeout=5.0)
        api.session = httpx.Client(transport=transport, headers=api.session.headers)
        apis.append(api)
        return api

    yield _factory
    for api in apis:
        api.close()


@pytest.fixture()
def async_api_factory():
    """Factory for creating an AsyncGrowattApi with a mock transport."""
    apis = []

    def _factory(handler):
        transport = make_async_mock_transport(handler)
        session = httpx.AsyncClient(transport=transport)
        api = AsyncGrowattApi(session=session, timeout=5.0)
        apis.append(api)
        return api

    yield _factory
    # async teardown handled by caller


# ---------------------------------------------------------------------------
# V1 API fixtures (sync / async)
# ---------------------------------------------------------------------------

@pytest.fixture()
def sync_v1_factory():
    """Factory for creating a sync OpenApiV1 with a mock transport."""
    apis = []

    def _factory(handler):
        transport = make_mock_transport(handler)
        api = OpenApiV1(token="test-token", timeout=5.0)
        api.session = httpx.Client(
            transport=transport,
            headers={**dict(api.session.headers), "token": "test-token"},
        )
        apis.append(api)
        return api

    yield _factory
    for api in apis:
        api.close()


@pytest.fixture()
def async_v1_factory():
    """Factory for creating an AsyncOpenApiV1 with a mock transport."""
    apis = []

    def _factory(handler):
        transport = make_async_mock_transport(handler)
        session = httpx.AsyncClient(
            transport=transport,
            headers={"token": "test-token"},
        )
        api = AsyncOpenApiV1(token="test-token", session=session, timeout=5.0)
        apis.append(api)
        return api

    yield _factory
