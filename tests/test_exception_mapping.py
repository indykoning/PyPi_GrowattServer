"""Tests for httpx exception → GrowattApiError hierarchy mapping."""

from __future__ import annotations

import httpx
import pytest

from growattServer import (
    GrowattApi,
    AsyncGrowattApi,
    GrowattApiConnectionError,
    GrowattApiError,
    GrowattApiStatusError,
    GrowattApiTimeoutError,
    GrowattError,
)


# ---------------------------------------------------------------------------
# Sync exception mapping
# ---------------------------------------------------------------------------

class TestSyncExceptionMapping:
    def _make_api(self, handler):
        transport = httpx.MockTransport(handler)
        api = GrowattApi(timeout=5.0)
        api.session = httpx.Client(transport=transport, headers=api.session.headers)
        return api

    def test_timeout_maps_to_growatt_timeout(self):
        def handler(request):
            raise httpx.ReadTimeout("read timed out")

        api = self._make_api(handler)
        with pytest.raises(GrowattApiTimeoutError, match="timed out"):
            api._request("GET", "https://example.com/test")
        api.close()

    def test_connect_error_maps_to_connection_error(self):
        def handler(request):
            raise httpx.ConnectError("connection refused")

        api = self._make_api(handler)
        with pytest.raises(GrowattApiConnectionError, match="Failed to connect"):
            api._request("GET", "https://example.com/test")
        api.close()

    def test_http_status_error_maps_to_status_error(self):
        def handler(request):
            return httpx.Response(500, text="Internal Server Error")

        api = self._make_api(handler)
        with pytest.raises(GrowattApiStatusError) as exc_info:
            api._request("GET", "https://example.com/test")
        assert exc_info.value.status_code == 500
        api.close()

    @pytest.mark.parametrize("status_code", [400, 401, 403, 404, 500, 503])
    def test_various_status_codes(self, status_code):
        def handler(request):
            return httpx.Response(status_code, text="error")

        api = self._make_api(handler)
        with pytest.raises(GrowattApiStatusError) as exc_info:
            api._request("GET", "https://example.com/test")
        assert exc_info.value.status_code == status_code
        api.close()

    def test_generic_http_error_maps_to_api_error(self):
        def handler(request):
            raise httpx.DecodingError("decode failed")

        api = self._make_api(handler)
        with pytest.raises(GrowattApiError, match="HTTP error"):
            api._request("GET", "https://example.com/test")
        api.close()


# ---------------------------------------------------------------------------
# Async exception mapping
# ---------------------------------------------------------------------------

class TestAsyncExceptionMapping:
    def _make_api(self, handler):
        transport = httpx.MockTransport(handler)
        session = httpx.AsyncClient(transport=transport)
        return AsyncGrowattApi(session=session, timeout=5.0)

    async def test_timeout_maps_to_growatt_timeout(self):
        async def handler(request):
            raise httpx.ReadTimeout("read timed out")

        api = self._make_api(handler)
        with pytest.raises(GrowattApiTimeoutError, match="timed out"):
            await api._request("GET", "https://example.com/test")
        await api.aclose()

    async def test_connect_error_maps_to_connection_error(self):
        async def handler(request):
            raise httpx.ConnectError("connection refused")

        api = self._make_api(handler)
        with pytest.raises(GrowattApiConnectionError, match="Failed to connect"):
            await api._request("GET", "https://example.com/test")
        await api.aclose()

    async def test_http_status_error_maps_to_status_error(self):
        async def handler(request):
            return httpx.Response(500, text="Internal Server Error")

        api = self._make_api(handler)
        with pytest.raises(GrowattApiStatusError) as exc_info:
            await api._request("GET", "https://example.com/test")
        assert exc_info.value.status_code == 500
        await api.aclose()

    @pytest.mark.parametrize("status_code", [400, 401, 403, 404, 500, 503])
    async def test_various_status_codes(self, status_code):
        async def handler(request):
            return httpx.Response(status_code, text="error")

        api = self._make_api(handler)
        with pytest.raises(GrowattApiStatusError) as exc_info:
            await api._request("GET", "https://example.com/test")
        assert exc_info.value.status_code == status_code
        await api.aclose()

    async def test_generic_http_error_maps_to_api_error(self):
        async def handler(request):
            raise httpx.DecodingError("decode failed")

        api = self._make_api(handler)
        with pytest.raises(GrowattApiError, match="HTTP error"):
            await api._request("GET", "https://example.com/test")
        await api.aclose()


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class TestExceptionHierarchy:
    def test_timeout_is_api_error(self):
        assert issubclass(GrowattApiTimeoutError, GrowattApiError)

    def test_connection_is_api_error(self):
        assert issubclass(GrowattApiConnectionError, GrowattApiError)

    def test_status_is_api_error(self):
        assert issubclass(GrowattApiStatusError, GrowattApiError)

    def test_api_error_is_growatt_error(self):
        assert issubclass(GrowattApiError, GrowattError)

    def test_status_error_has_status_code(self):
        exc = GrowattApiStatusError("test", 404)
        assert exc.status_code == 404

    def test_requests_compat(self):
        """If requests is installed, GrowattApiError is also a RequestException."""
        try:
            from requests.exceptions import RequestException
        except ImportError:
            pytest.skip("requests not installed")
        assert issubclass(GrowattApiError, RequestException)
