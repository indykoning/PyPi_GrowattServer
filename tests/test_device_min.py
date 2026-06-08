"""Tests for Min / AsyncMin device methods."""

from __future__ import annotations

from datetime import date, time, timedelta

import httpx
import pytest

from growattServer import (
    AsyncOpenApiV1,
    GrowattParameterError,
    OpenApiV1,
)

from .conftest import json_response, v1_success


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
# Sync MIN device tests
# ---------------------------------------------------------------------------

class TestMinSync:
    def test_detail(self):
        def handler(request):
            assert "tlx_data_info" in str(request.url)
            assert request.url.params["device_sn"] == "MIN001"
            return json_response(v1_success({"vpv1": 300.5}))

        api = _make_sync_v1(handler)
        result = api.min_detail("MIN001")
        assert result["vpv1"] == 300.5
        api.close()

    def test_energy(self):
        def handler(request):
            assert "tlx_last_data" in str(request.url)
            return json_response(v1_success({"eToday": 5.2}))

        api = _make_sync_v1(handler)
        result = api.min_energy("MIN001")
        assert result["eToday"] == 5.2
        api.close()

    def test_energy_history(self):
        def handler(request):
            assert "tlx_data" in str(request.url)
            return json_response(v1_success({"datas": []}))

        api = _make_sync_v1(handler)
        today = date.today()
        result = api.min_energy_history("MIN001", start_date=today, end_date=today)
        assert result == {"datas": []}
        api.close()

    def test_energy_history_exceeds_7_days(self):
        api = OpenApiV1.__new__(OpenApiV1)
        with pytest.raises(GrowattParameterError, match="7 days"):
            from growattServer.open_api_v1.devices.min import Min
            device = Min(api, "MIN001")
            device.energy_history(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 10),
            )

    def test_settings(self):
        def handler(request):
            assert "tlx_set_info" in str(request.url)
            return json_response(v1_success({"time1Mode": "1"}))

        api = _make_sync_v1(handler)
        result = api.min_settings("MIN001")
        assert result["time1Mode"] == "1"
        api.close()

    def test_read_parameter_named(self):
        def handler(request):
            assert "readMinParam" in str(request.url)
            return json_response(v1_success({"data": "42"}))

        api = _make_sync_v1(handler)
        result = api.min_read_parameter("MIN001", parameter_id="pv_active_p_rate")
        assert result["data"] == "42"
        api.close()

    def test_read_parameter_address(self):
        def handler(request):
            assert "readMinParam" in str(request.url)
            return json_response(v1_success({"data": "100"}))

        api = _make_sync_v1(handler)
        result = api.min_read_parameter("MIN001", parameter_id=None, start_address=100, end_address=102)
        assert result["data"] == "100"
        api.close()

    def test_read_parameter_no_args_raises(self):
        from growattServer.open_api_v1.devices.min import Min
        api = OpenApiV1.__new__(OpenApiV1)
        device = Min(api, "MIN001")
        with pytest.raises(GrowattParameterError):
            device.read_parameter(None, None, None)

    def test_read_parameter_both_args_raises(self):
        from growattServer.open_api_v1.devices.min import Min
        api = OpenApiV1.__new__(OpenApiV1)
        device = Min(api, "MIN001")
        with pytest.raises(GrowattParameterError, match="not both"):
            device.read_parameter("some_param", 100, None)

    def test_write_parameter_string(self):
        def handler(request):
            assert "tlxSet" in str(request.url)
            body = request.content.decode()
            assert "param1=42" in body
            return json_response(v1_success())

        api = _make_sync_v1(handler)
        api.min_write_parameter("MIN001", "pv_active_p_rate", "42")
        api.close()

    def test_write_parameter_list(self):
        def handler(request):
            body = request.content.decode()
            assert "param1=10" in body
            assert "param2=20" in body
            return json_response(v1_success())

        api = _make_sync_v1(handler)
        api.min_write_parameter("MIN001", "test_type", ["10", "20"])
        api.close()

    def test_write_parameter_dict(self):
        def handler(request):
            body = request.content.decode()
            assert "param3=99" in body
            return json_response(v1_success())

        api = _make_sync_v1(handler)
        api.min_write_parameter("MIN001", "test_type", {3: "99"})
        api.close()

    def test_write_time_segment(self):
        def handler(request):
            assert "tlxSet" in str(request.url)
            body = request.content.decode()
            assert "type=time_segment1" in body
            assert "param1=1" in body  # batt_mode
            assert "param2=2" in body  # start hour
            assert "param3=30" in body  # start minute
            assert "param4=5" in body  # end hour
            assert "param5=0" in body  # end minute
            assert "param6=1" in body  # enabled
            return json_response(v1_success())

        api = _make_sync_v1(handler)
        api.min_write_time_segment(
            "MIN001", segment_id=1, batt_mode=1,
            start_time=time(2, 30), end_time=time(5, 0), enabled=True,
        )
        api.close()

    def test_write_time_segment_invalid_id(self):
        from growattServer.open_api_v1.devices.min import Min
        api = OpenApiV1.__new__(OpenApiV1)
        device = Min(api, "MIN001")
        with pytest.raises(GrowattParameterError, match="segment_id"):
            device.write_time_segment(0, 1, time(0, 0), time(1, 0))

    def test_write_time_segment_invalid_batt_mode(self):
        from growattServer.open_api_v1.devices.min import Min
        api = OpenApiV1.__new__(OpenApiV1)
        device = Min(api, "MIN001")
        with pytest.raises(GrowattParameterError, match="batt_mode"):
            device.write_time_segment(1, 5, time(0, 0), time(1, 0))


# ---------------------------------------------------------------------------
# Parse time segments (pure logic, no HTTP)
# ---------------------------------------------------------------------------

class TestMinParseTimeSegments:
    def test_parse_segments(self):
        from growattServer.open_api_v1.devices.min import Min
        api = OpenApiV1.__new__(OpenApiV1)
        device = Min(api, "MIN001")

        settings = {
            "forcedTimeStart1": "1:30",
            "forcedTimeStop1": "5:0",
            "time1Mode": "1",
            "forcedStopSwitch1": "1",
        }
        # Fill defaults for segments 2-9
        for i in range(2, 10):
            settings[f"forcedTimeStart{i}"] = "0:0"
            settings[f"forcedTimeStop{i}"] = "0:0"
            settings[f"time{i}Mode"] = "null"
            settings[f"forcedStopSwitch{i}"] = "0"

        result = device.read_time_segments(settings)
        assert len(result) == 9
        assert result[0]["segment_id"] == 1
        assert result[0]["batt_mode"] == 1
        assert result[0]["mode_name"] == "Battery First"
        assert result[0]["start_time"] == "01:30"
        assert result[0]["end_time"] == "05:00"
        assert result[0]["enabled"] is True
        assert result[1]["enabled"] is False

    def test_parse_null_values(self):
        from growattServer.open_api_v1.devices.min import Min
        api = OpenApiV1.__new__(OpenApiV1)
        device = Min(api, "MIN001")

        settings = {}
        for i in range(1, 10):
            settings[f"forcedTimeStart{i}"] = "null"
            settings[f"forcedTimeStop{i}"] = ""
            settings[f"time{i}Mode"] = "null"
            settings[f"forcedStopSwitch{i}"] = "null"

        result = device.read_time_segments(settings)
        assert result[0]["start_time"] == "00:00"
        assert result[0]["end_time"] == "00:00"
        assert result[0]["batt_mode"] is None
        assert result[0]["enabled"] is False


# ---------------------------------------------------------------------------
# Async MIN device tests
# ---------------------------------------------------------------------------

class TestMinAsync:
    async def test_detail(self):
        async def handler(request):
            assert "tlx_data_info" in str(request.url)
            return json_response(v1_success({"vpv1": 300.5}))

        api = _make_async_v1(handler)
        result = await api.min_detail("MIN001")
        assert result["vpv1"] == 300.5
        await api.aclose()

    async def test_energy(self):
        async def handler(request):
            assert "tlx_last_data" in str(request.url)
            return json_response(v1_success({"eToday": 5.2}))

        api = _make_async_v1(handler)
        result = await api.min_energy("MIN001")
        assert result["eToday"] == 5.2
        await api.aclose()

    async def test_settings(self):
        async def handler(request):
            assert "tlx_set_info" in str(request.url)
            return json_response(v1_success({"time1Mode": "1"}))

        api = _make_async_v1(handler)
        result = await api.min_settings("MIN001")
        assert result["time1Mode"] == "1"
        await api.aclose()

    async def test_read_time_segments_from_api(self):
        """Tests async chaining: read_time_segments -> settings()."""
        call_count = 0

        async def handler(request):
            nonlocal call_count
            call_count += 1
            if "tlx_set_info" in str(request.url):
                settings = {}
                for i in range(1, 10):
                    settings[f"forcedTimeStart{i}"] = "0:0"
                    settings[f"forcedTimeStop{i}"] = "0:0"
                    settings[f"time{i}Mode"] = "0"
                    settings[f"forcedStopSwitch{i}"] = "0"
                return json_response(v1_success(settings))
            return json_response(v1_success())

        api = _make_async_v1(handler)
        result = await api.min_read_time_segments("MIN001")
        assert len(result) == 9
        assert call_count >= 1
        await api.aclose()

    async def test_write_time_segment(self):
        async def handler(request):
            assert "tlxSet" in str(request.url)
            return json_response(v1_success())

        api = _make_async_v1(handler)
        await api.min_write_time_segment(
            "MIN001", segment_id=1, batt_mode=1,
            start_time=time(2, 30), end_time=time(5, 0), enabled=True,
        )
        await api.aclose()
