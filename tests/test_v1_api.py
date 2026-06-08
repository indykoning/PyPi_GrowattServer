"""Tests for OpenApiV1 / AsyncOpenApiV1 v1_request and process_response."""

from __future__ import annotations

import json
import warnings

import httpx
import pytest

from growattServer import (
    AsyncOpenApiV1,
    GrowattApiError,
    GrowattV1ApiError,
    OpenApiV1,
)
from growattServer.open_api_v1.devices.min import Min
from growattServer.open_api_v1.devices.sph import Sph
from growattServer.open_api_v1.devices.async_min import AsyncMin
from growattServer.open_api_v1.devices.async_sph import AsyncSph

from .conftest import json_response, v1_error, v1_success


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sync_v1(handler):
    transport = httpx.MockTransport(handler)
    api = OpenApiV1(token="test-token", timeout=5.0)
    api.session = httpx.Client(
        transport=transport,
        headers={**dict(api.session.headers), "token": "test-token"},
    )
    return api


def _make_async_v1(handler):
    transport = httpx.MockTransport(handler)
    session = httpx.AsyncClient(transport=transport, headers={"token": "test-token"})
    return AsyncOpenApiV1(token="test-token", session=session, timeout=5.0)


# ---------------------------------------------------------------------------
# process_response
# ---------------------------------------------------------------------------

class TestProcessResponse:
    def test_success_extracts_data(self):
        api = OpenApiV1.__new__(OpenApiV1)
        result = api.process_response(v1_success({"plants": [1, 2]}))
        assert result == {"plants": [1, 2]}

    def test_error_raises_v1_api_error(self):
        api = OpenApiV1.__new__(OpenApiV1)
        with pytest.raises(GrowattV1ApiError) as exc_info:
            api.process_response(v1_error(10001, "System error"), "test op")
        assert exc_info.value.error_code == 10001
        assert exc_info.value.error_msg == "System error"

    def test_error_with_unknown_msg(self):
        api = OpenApiV1.__new__(OpenApiV1)
        with pytest.raises(GrowattV1ApiError) as exc_info:
            api.process_response({"error_code": 99})
        assert exc_info.value.error_msg == "Unknown error"


# ---------------------------------------------------------------------------
# Sync v1_request
# ---------------------------------------------------------------------------

class TestSyncV1Request:
    def test_success(self):
        def handler(request):
            return json_response(v1_success({"count": 5}))

        api = _make_sync_v1(handler)
        result = api.v1_request("GET", "plant/list", operation_name="test")
        assert result == {"count": 5}
        api.close()

    def test_v1_error_raised(self):
        def handler(request):
            return json_response(v1_error(10012, "Rate limited"))

        api = _make_sync_v1(handler)
        with pytest.raises(GrowattV1ApiError) as exc_info:
            api.v1_request("GET", "plant/list", operation_name="test")
        assert exc_info.value.error_code == 10012
        api.close()

    def test_http_error_wrapped(self):
        def handler(request):
            return httpx.Response(500, text="error")

        api = _make_sync_v1(handler)
        with pytest.raises(GrowattApiError):
            api.v1_request("GET", "plant/list")
        api.close()

    def test_plant_list(self):
        def handler(request):
            assert "plant/list" in str(request.url)
            return json_response(v1_success({"count": 2, "plants": []}))

        api = _make_sync_v1(handler)
        result = api.plant_list()
        assert result["count"] == 2
        api.close()

    def test_plant_details(self):
        def handler(request):
            assert "plant/details" in str(request.url)
            assert request.url.params["plant_id"] == "42"
            return json_response(v1_success({"plantName": "Test"}))

        api = _make_sync_v1(handler)
        result = api.plant_details(42)
        assert result["plantName"] == "Test"
        api.close()

    def test_device_list(self):
        def handler(request):
            assert "device/list" in str(request.url)
            return json_response(v1_success({"count": 1, "devices": []}))

        api = _make_sync_v1(handler)
        result = api.device_list(42)
        assert result["count"] == 1
        api.close()

    def test_token_in_headers(self):
        def handler(request):
            assert request.headers["token"] == "test-token"
            return json_response(v1_success())

        api = _make_sync_v1(handler)
        api.v1_request("GET", "plant/list")
        api.close()


# ---------------------------------------------------------------------------
# Async v1_request
# ---------------------------------------------------------------------------

class TestAsyncV1Request:
    async def test_success(self):
        async def handler(request):
            return json_response(v1_success({"count": 5}))

        api = _make_async_v1(handler)
        result = await api.v1_request("GET", "plant/list", operation_name="test")
        assert result == {"count": 5}
        await api.aclose()

    async def test_v1_error_raised(self):
        async def handler(request):
            return json_response(v1_error(10012, "Rate limited"))

        api = _make_async_v1(handler)
        with pytest.raises(GrowattV1ApiError) as exc_info:
            await api.v1_request("GET", "plant/list", operation_name="test")
        assert exc_info.value.error_code == 10012
        await api.aclose()

    async def test_plant_list(self):
        async def handler(request):
            assert "plant/list" in str(request.url)
            return json_response(v1_success({"count": 2, "plants": []}))

        api = _make_async_v1(handler)
        result = await api.plant_list()
        assert result["count"] == 2
        await api.aclose()


# ---------------------------------------------------------------------------
# get_device
# ---------------------------------------------------------------------------

class TestGetDevice:
    def test_min_device(self):
        api = OpenApiV1.__new__(OpenApiV1)
        api._min_class = Min
        api._sph_class = Sph
        device = api.get_device("SN123", Min.DEVICE_TYPE_ID)
        assert isinstance(device, Min)
        assert device.device_sn == "SN123"

    def test_sph_device(self):
        api = OpenApiV1.__new__(OpenApiV1)
        api._min_class = Min
        api._sph_class = Sph
        device = api.get_device("SN456", Sph.DEVICE_TYPE_ID)
        assert isinstance(device, Sph)

    def test_unknown_device_returns_none(self):
        api = OpenApiV1.__new__(OpenApiV1)
        api._min_class = Min
        api._sph_class = Sph
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            device = api.get_device("SN789", 99)
            assert device is None
            assert len(w) == 1
            assert "not been implemented" in str(w[0].message)

    def test_async_get_device_uses_async_classes(self):
        api = AsyncOpenApiV1.__new__(AsyncOpenApiV1)
        api._min_class = AsyncMin
        api._sph_class = AsyncSph
        device = api.get_device("SN123", Min.DEVICE_TYPE_ID)
        assert isinstance(device, AsyncMin)
