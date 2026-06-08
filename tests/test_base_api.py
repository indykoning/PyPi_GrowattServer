"""Tests for GrowattApi and AsyncGrowattApi _request() and context managers."""

from __future__ import annotations

import json

import httpx
import pytest

from growattServer import AsyncGrowattApi, GrowattApi

from .conftest import invoke, json_response


# ---------------------------------------------------------------------------
# Sync _request tests
# ---------------------------------------------------------------------------

class TestSyncRequest:
    def _make_api(self, handler):
        transport = httpx.MockTransport(handler)
        api = GrowattApi(timeout=5.0)
        api.session = httpx.Client(transport=transport, headers=api.session.headers)
        return api

    def test_get_json(self):
        def handler(request):
            assert request.method == "GET"
            return json_response({"key": "value"})

        api = self._make_api(handler)
        result = api._request("GET", "https://example.com/test")
        assert result == {"key": "value"}
        api.close()

    def test_post_with_data(self):
        def handler(request):
            assert request.method == "POST"
            body = request.content.decode()
            assert "field=val" in body
            return json_response({"ok": True})

        api = self._make_api(handler)
        result = api._request("POST", "https://example.com/test", data={"field": "val"})
        assert result == {"ok": True}
        api.close()

    def test_extract_callback(self):
        def handler(request):
            return json_response({"back": {"plants": [1, 2]}})

        api = self._make_api(handler)
        result = api._request(
            "GET", "https://example.com/test",
            extract=lambda r: r["back"]["plants"],
        )
        assert result == [1, 2]
        api.close()

    def test_text_mode(self):
        def handler(request):
            return httpx.Response(200, text="<html>hello</html>")

        api = self._make_api(handler)
        result = api._request("GET", "https://example.com/test", text=True)
        assert "<html>" in result
        api.close()

    def test_params_passed(self):
        def handler(request):
            assert request.url.params["userId"] == "123"
            return json_response({"ok": True})

        api = self._make_api(handler)
        api._request("GET", "https://example.com/test", params={"userId": "123"})
        api.close()


# ---------------------------------------------------------------------------
# Async _request tests
# ---------------------------------------------------------------------------

class TestAsyncRequest:
    def _make_api(self, handler):
        transport = httpx.MockTransport(handler)
        session = httpx.AsyncClient(transport=transport)
        return AsyncGrowattApi(session=session, timeout=5.0)

    async def test_get_json(self):
        async def handler(request):
            assert request.method == "GET"
            return json_response({"key": "value"})

        api = self._make_api(handler)
        result = await api._request("GET", "https://example.com/test")
        assert result == {"key": "value"}
        await api.aclose()

    async def test_post_with_data(self):
        async def handler(request):
            assert request.method == "POST"
            return json_response({"ok": True})

        api = self._make_api(handler)
        result = await api._request("POST", "https://example.com/test", data={"field": "val"})
        assert result == {"ok": True}
        await api.aclose()

    async def test_extract_callback(self):
        async def handler(request):
            return json_response({"back": {"plants": [1, 2]}})

        api = self._make_api(handler)
        result = await api._request(
            "GET", "https://example.com/test",
            extract=lambda r: r["back"]["plants"],
        )
        assert result == [1, 2]
        await api.aclose()

    async def test_text_mode(self):
        async def handler(request):
            return httpx.Response(200, text="<html>hello</html>")

        api = self._make_api(handler)
        result = await api._request("GET", "https://example.com/test", text=True)
        assert "<html>" in result
        await api.aclose()


# ---------------------------------------------------------------------------
# Context managers
# ---------------------------------------------------------------------------

class TestContextManagers:
    def test_sync_context_manager(self):
        def handler(request):
            return json_response({"ok": True})

        transport = httpx.MockTransport(handler)
        api = GrowattApi(timeout=5.0)
        api.session = httpx.Client(transport=transport, headers=api.session.headers)
        # Sync GrowattApi doesn't have __enter__/__exit__, just close()
        api._request("GET", "https://example.com/test")
        api.close()

    async def test_async_context_manager(self):
        async def handler(request):
            return json_response({"ok": True})

        transport = httpx.MockTransport(handler)
        session = httpx.AsyncClient(transport=transport)
        async with AsyncGrowattApi(session=session, timeout=5.0) as api:
            result = await api._request("GET", "https://example.com/test")
            assert result == {"ok": True}
