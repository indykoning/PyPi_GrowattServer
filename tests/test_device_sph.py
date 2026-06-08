"""Tests for Sph / AsyncSph device methods."""

from __future__ import annotations

from datetime import date, time
from typing import Any

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


def _sph_detail_response() -> dict[str, Any]:
    """Build a realistic SPH detail response with charge/discharge settings."""
    return {
        "chargePowerCommand": 80,
        "wchargeSOCLowLimit": 95,
        "acChargeEnable": "1",
        "disChargePowerCommand": 60,
        "wdisChargeSOCLowLimit": 15,
        # Charge periods
        "forcedChargeTimeStart1": "1:0",
        "forcedChargeTimeStop1": "5:30",
        "forcedChargeStopSwitch1": "1",
        "forcedChargeTimeStart2": "0:0",
        "forcedChargeTimeStop2": "0:0",
        "forcedChargeStopSwitch2": "0",
        "forcedChargeTimeStart3": "0:0",
        "forcedChargeTimeStop3": "0:0",
        "forcedChargeStopSwitch3": "0",
        # Discharge periods
        "forcedDischargeTimeStart1": "17:0",
        "forcedDischargeTimeStop1": "21:0",
        "forcedDischargeStopSwitch1": "1",
        "forcedDischargeTimeStart2": "0:0",
        "forcedDischargeTimeStop2": "0:0",
        "forcedDischargeStopSwitch2": "0",
        "forcedDischargeTimeStart3": "0:0",
        "forcedDischargeTimeStop3": "0:0",
        "forcedDischargeStopSwitch3": "0",
    }


# ---------------------------------------------------------------------------
# Sync SPH tests
# ---------------------------------------------------------------------------

class TestSphSync:
    def test_detail(self):
        def handler(request):
            assert "mix_data_info" in str(request.url)
            assert request.url.params["device_sn"] == "SPH001"
            return json_response(v1_success({"vpv1": 250.0}))

        api = _make_sync_v1(handler)
        result = api.sph_detail("SPH001")
        assert result["vpv1"] == 250.0
        api.close()

    def test_energy(self):
        def handler(request):
            assert "mix_last_data" in str(request.url)
            return json_response(v1_success({"eToday": 3.1}))

        api = _make_sync_v1(handler)
        result = api.sph_energy("SPH001")
        assert result["eToday"] == 3.1
        api.close()

    def test_energy_history(self):
        def handler(request):
            assert "mix_data" in str(request.url)
            return json_response(v1_success({"datas": []}))

        api = _make_sync_v1(handler)
        today = date.today()
        result = api.sph_energy_history("SPH001", start_date=today, end_date=today)
        assert result == {"datas": []}
        api.close()

    def test_energy_history_exceeds_7_days(self):
        from growattServer.open_api_v1.devices.sph import Sph
        api = OpenApiV1.__new__(OpenApiV1)
        device = Sph(api, "SPH001")
        with pytest.raises(GrowattParameterError, match="7 days"):
            device.energy_history(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 10),
            )

    def test_read_parameter_named(self):
        def handler(request):
            assert "readMixParam" in str(request.url)
            return json_response(v1_success({"data": "55"}))

        api = _make_sync_v1(handler)
        result = api.sph_read_parameter("SPH001", parameter_id="pv_active_p_rate")
        assert result["data"] == "55"
        api.close()

    def test_read_parameter_no_args_raises(self):
        from growattServer.open_api_v1.devices.sph import Sph
        api = OpenApiV1.__new__(OpenApiV1)
        device = Sph(api, "SPH001")
        with pytest.raises(GrowattParameterError):
            device.read_parameter(None, None, None)

    def test_write_parameter(self):
        def handler(request):
            assert "mixSet" in str(request.url)
            body = request.content.decode()
            assert "param1=42" in body
            assert "type=test_type" in body
            return json_response(v1_success())

        api = _make_sync_v1(handler)
        api.sph_write_parameter("SPH001", "test_type", "42")
        api.close()

    def test_write_ac_charge_times(self):
        def handler(request):
            body = request.content.decode()
            assert "type=mix_ac_charge_time_period" in body
            assert "param1=100" in body  # charge_power
            assert "param2=95" in body   # charge_stop_soc
            assert "param3=1" in body    # mains_enabled
            return json_response(v1_success())

        api = _make_sync_v1(handler)
        api.sph_write_ac_charge_times(
            "SPH001", charge_power=100, charge_stop_soc=95, mains_enabled=True,
            periods=[
                {"start_time": time(1, 0), "end_time": time(5, 0), "enabled": True},
                {"start_time": time(0, 0), "end_time": time(0, 0), "enabled": False},
                {"start_time": time(0, 0), "end_time": time(0, 0), "enabled": False},
            ],
        )
        api.close()

    def test_write_ac_charge_times_invalid_power(self):
        from growattServer.open_api_v1.devices.sph import Sph
        api = OpenApiV1.__new__(OpenApiV1)
        device = Sph(api, "SPH001")
        with pytest.raises(GrowattParameterError, match="charge_power"):
            device.write_ac_charge_times(101, 50, True, [{}] * 3)

    def test_write_ac_charge_times_wrong_period_count(self):
        from growattServer.open_api_v1.devices.sph import Sph
        api = OpenApiV1.__new__(OpenApiV1)
        device = Sph(api, "SPH001")
        with pytest.raises(GrowattParameterError, match="3 period"):
            device.write_ac_charge_times(50, 50, True, [{}] * 2)

    def test_write_ac_discharge_times(self):
        def handler(request):
            body = request.content.decode()
            assert "type=mix_ac_discharge_time_period" in body
            assert "param1=80" in body   # discharge_power
            assert "param2=10" in body   # discharge_stop_soc
            return json_response(v1_success())

        api = _make_sync_v1(handler)
        api.sph_write_ac_discharge_times(
            "SPH001", discharge_power=80, discharge_stop_soc=10,
            periods=[
                {"start_time": time(17, 0), "end_time": time(21, 0), "enabled": True},
                {"start_time": time(0, 0), "end_time": time(0, 0), "enabled": False},
                {"start_time": time(0, 0), "end_time": time(0, 0), "enabled": False},
            ],
        )
        api.close()

    def test_write_ac_discharge_times_invalid_power(self):
        from growattServer.open_api_v1.devices.sph import Sph
        api = OpenApiV1.__new__(OpenApiV1)
        device = Sph(api, "SPH001")
        with pytest.raises(GrowattParameterError, match="discharge_power"):
            device.write_ac_discharge_times(-1, 10, [{}] * 3)


# ---------------------------------------------------------------------------
# Parse AC charge/discharge settings (pure logic, no HTTP)
# ---------------------------------------------------------------------------

class TestSphParseSettings:
    def test_parse_ac_charge_settings(self):
        from growattServer.open_api_v1.devices.sph import Sph
        api = OpenApiV1.__new__(OpenApiV1)
        device = Sph(api, "SPH001")

        result = device._parse_ac_charge_settings(_sph_detail_response())
        assert result["charge_power"] == 80
        assert result["charge_stop_soc"] == 95
        assert result["mains_enabled"] is True
        assert len(result["periods"]) == 3
        assert result["periods"][0]["start_time"] == "01:00"
        assert result["periods"][0]["end_time"] == "05:30"
        assert result["periods"][0]["enabled"] is True
        assert result["periods"][1]["enabled"] is False

    def test_parse_ac_discharge_settings(self):
        from growattServer.open_api_v1.devices.sph import Sph
        api = OpenApiV1.__new__(OpenApiV1)
        device = Sph(api, "SPH001")

        result = device._parse_ac_discharge_settings(_sph_detail_response())
        assert result["discharge_power"] == 60
        assert result["discharge_stop_soc"] == 15
        assert len(result["periods"]) == 3
        assert result["periods"][0]["start_time"] == "17:00"
        assert result["periods"][0]["end_time"] == "21:00"
        assert result["periods"][0]["enabled"] is True

    def test_parse_null_charge_values(self):
        from growattServer.open_api_v1.devices.sph import Sph
        api = OpenApiV1.__new__(OpenApiV1)
        device = Sph(api, "SPH001")

        settings = {
            "chargePowerCommand": "null",
            "wchargeSOCLowLimit": "",
            "acChargeEnable": "null",
        }
        for i in range(1, 4):
            settings[f"forcedChargeTimeStart{i}"] = "null"
            settings[f"forcedChargeTimeStop{i}"] = ""
            settings[f"forcedChargeStopSwitch{i}"] = "null"

        result = device._parse_ac_charge_settings(settings)
        assert result["charge_power"] == 0
        assert result["charge_stop_soc"] == 100
        assert result["mains_enabled"] is False


# ---------------------------------------------------------------------------
# Async SPH tests
# ---------------------------------------------------------------------------

class TestSphAsync:
    async def test_detail(self):
        async def handler(request):
            assert "mix_data_info" in str(request.url)
            return json_response(v1_success({"vpv1": 250.0}))

        api = _make_async_v1(handler)
        result = await api.sph_detail("SPH001")
        assert result["vpv1"] == 250.0
        await api.aclose()

    async def test_read_ac_charge_times_from_api(self):
        """Tests async chaining: read_ac_charge_times -> detail()."""
        async def handler(request):
            if "mix_data_info" in str(request.url):
                return json_response(v1_success(_sph_detail_response()))
            return json_response(v1_success())

        api = _make_async_v1(handler)
        result = await api.sph_read_ac_charge_times("SPH001")
        assert result["charge_power"] == 80
        assert len(result["periods"]) == 3
        await api.aclose()

    async def test_read_ac_discharge_times_from_api(self):
        """Tests async chaining: read_ac_discharge_times -> detail()."""
        async def handler(request):
            if "mix_data_info" in str(request.url):
                return json_response(v1_success(_sph_detail_response()))
            return json_response(v1_success())

        api = _make_async_v1(handler)
        result = await api.sph_read_ac_discharge_times("SPH001")
        assert result["discharge_power"] == 60
        assert len(result["periods"]) == 3
        await api.aclose()

    async def test_write_ac_charge_times(self):
        async def handler(request):
            body = request.content.decode()
            assert "mix_ac_charge_time_period" in body
            return json_response(v1_success())

        api = _make_async_v1(handler)
        await api.sph_write_ac_charge_times(
            "SPH001", charge_power=100, charge_stop_soc=95, mains_enabled=True,
            periods=[
                {"start_time": time(1, 0), "end_time": time(5, 0), "enabled": True},
                {"start_time": time(0, 0), "end_time": time(0, 0), "enabled": False},
                {"start_time": time(0, 0), "end_time": time(0, 0), "enabled": False},
            ],
        )
        await api.aclose()
