"""Tests verifying sync/async feature parity via the coroutine-passthrough pattern."""

from __future__ import annotations

import inspect

import httpx
import pytest

from growattServer import AsyncGrowattApi, AsyncOpenApiV1, GrowattApi, OpenApiV1
from growattServer.base_api import _GrowattApiBase
from growattServer.open_api_v1 import _OpenApiV1Base

from .conftest import invoke, json_response, v1_success


# ---------------------------------------------------------------------------
# Introspection: all base methods exist on both sync and async classes
# ---------------------------------------------------------------------------

def _get_public_methods(cls):
    """Return names of public, non-dunder methods defined on cls (not inherited from object)."""
    return {
        name for name, method in inspect.getmembers(cls, predicate=inspect.isfunction)
        if not name.startswith("_")
    }


class TestBaseApiParity:
    def test_all_base_methods_exist_on_async(self):
        base_methods = _get_public_methods(_GrowattApiBase)
        async_methods = _get_public_methods(AsyncGrowattApi)
        missing = base_methods - async_methods
        assert not missing, f"Methods missing from AsyncGrowattApi: {missing}"

    def test_all_base_methods_exist_on_sync(self):
        base_methods = _get_public_methods(_GrowattApiBase)
        sync_methods = _get_public_methods(GrowattApi)
        missing = base_methods - sync_methods
        assert not missing, f"Methods missing from GrowattApi: {missing}"


class TestV1ApiParity:
    def test_all_v1_base_methods_exist_on_async(self):
        base_methods = _get_public_methods(_OpenApiV1Base)
        async_methods = _get_public_methods(AsyncOpenApiV1)
        missing = base_methods - async_methods
        assert not missing, f"Methods missing from AsyncOpenApiV1: {missing}"

    def test_all_v1_base_methods_exist_on_sync(self):
        base_methods = _get_public_methods(_OpenApiV1Base)
        sync_methods = _get_public_methods(OpenApiV1)
        missing = base_methods - sync_methods
        assert not missing, f"Methods missing from OpenApiV1: {missing}"


# ---------------------------------------------------------------------------
# Coroutine passthrough: async API methods return awaitables
# ---------------------------------------------------------------------------

class TestAsyncReturnsAwaitables:
    async def test_plant_detail_returns_awaitable(self):
        """A passthrough method on AsyncGrowattApi returns an awaitable."""
        async def handler(request):
            return json_response({"back": {"plantId": "1"}})

        transport = httpx.MockTransport(handler)
        session = httpx.AsyncClient(transport=transport)
        api = AsyncGrowattApi(session=session, timeout=5.0)

        # plant_detail is defined as regular def in _GrowattApiBase but should
        # return a coroutine because _request is async on AsyncGrowattApi.
        import datetime
        from growattServer import Timespan
        result = api.plant_detail("1", Timespan.day, datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC))
        assert inspect.isawaitable(result)
        value = await result
        assert value == {"plantId": "1"}
        await api.aclose()

    async def test_v1_plant_details_returns_awaitable(self):
        """A passthrough method on AsyncOpenApiV1 returns an awaitable."""
        async def handler(request):
            return json_response(v1_success({"plantName": "Test"}))

        transport = httpx.MockTransport(handler)
        session = httpx.AsyncClient(transport=transport, headers={"token": "t"})
        api = AsyncOpenApiV1(token="t", session=session, timeout=5.0)

        result = api.plant_details(1)
        assert inspect.isawaitable(result)
        value = await result
        assert value["plantName"] == "Test"
        await api.aclose()


# ---------------------------------------------------------------------------
# Same result from sync and async for the same mock response
# ---------------------------------------------------------------------------

class TestSyncAsyncResultParity:
    def test_sync_plant_details(self):
        def handler(request):
            return json_response(v1_success({"plantName": "Solar Farm"}))

        transport = httpx.MockTransport(handler)
        api = OpenApiV1(token="t", timeout=5.0)
        api.session = httpx.Client(transport=transport, headers={**dict(api.session.headers), "token": "t"})
        result = api.plant_details(1)
        assert result == {"plantName": "Solar Farm"}
        api.close()

    async def test_async_plant_details(self):
        async def handler(request):
            return json_response(v1_success({"plantName": "Solar Farm"}))

        transport = httpx.MockTransport(handler)
        session = httpx.AsyncClient(transport=transport, headers={"token": "t"})
        api = AsyncOpenApiV1(token="t", session=session, timeout=5.0)
        result = await api.plant_details(1)
        assert result == {"plantName": "Solar Farm"}
        await api.aclose()

    def test_sync_min_detail(self):
        def handler(request):
            return json_response(v1_success({"vpv1": 310.0}))

        transport = httpx.MockTransport(handler)
        api = OpenApiV1(token="t", timeout=5.0)
        api.session = httpx.Client(transport=transport, headers={**dict(api.session.headers), "token": "t"})
        result = api.min_detail("SN1")
        assert result == {"vpv1": 310.0}
        api.close()

    async def test_async_min_detail(self):
        async def handler(request):
            return json_response(v1_success({"vpv1": 310.0}))

        transport = httpx.MockTransport(handler)
        session = httpx.AsyncClient(transport=transport, headers={"token": "t"})
        api = AsyncOpenApiV1(token="t", session=session, timeout=5.0)
        result = await api.min_detail("SN1")
        assert result == {"vpv1": 310.0}
        await api.aclose()
