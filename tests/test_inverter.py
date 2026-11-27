"""Classic inverter (device type 1) support in the V1 API."""
from datetime import date

import pytest

import growattServer
from growattServer import GrowattParameterError, GrowattV1ApiError
from growattServer.open_api_v1.devices import Inverter

SN = "ABC1234567"


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class _RecordingSession:
    """Stands in for requests.Session and records every call."""

    def __init__(self, payload=None):
        self.calls = []
        self.payload = payload if payload is not None else {"error_code": 0, "error_msg": "", "data": {"ok": True}}

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return _Response(self.payload)

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return _Response(self.payload)


@pytest.fixture
def api():
    api = growattServer.OpenApiV1(token="test-token")  # noqa: S106
    api.session = _RecordingSession()
    return api


def test_get_device_returns_inverter_for_type_1(api):
    device = api.get_device(SN, growattServer.DeviceType.INVERTER.value)

    assert isinstance(device, Inverter)
    assert device.device_sn == SN


def test_detail_sends_serial_as_query_parameter(api):
    assert api.inverter_detail(SN) == {"ok": True}

    method, url, kwargs = api.session.calls[0]
    assert method == "GET"
    assert url.endswith("v1/device/inverter/inv_data_info")
    assert kwargs["params"] == {"device_sn": SN}


def test_energy_sends_serial_as_query_parameter(api):
    """A GET form body is ignored by the server (it answers 10001 system error)."""
    api.inverter_energy(SN)

    method, url, kwargs = api.session.calls[0]
    assert method == "GET"
    assert url.endswith("v1/device/inverter/last_new_data")
    assert kwargs["params"] == {"device_sn": SN}
    assert "data" not in kwargs


def test_energy_history_sends_query_parameters(api):
    """A GET form body is ignored by the server (it answers 10002 deviceIdError)."""
    api.inverter_energy_history(SN, date(2026, 11, 20), date(2026, 11, 26), timezone="Europe/Brussels", page=2, limit=100)

    method, url, kwargs = api.session.calls[0]
    assert method == "GET"
    assert url.endswith("v1/device/inverter/data")
    assert kwargs["params"] == {
        "device_sn": SN,
        "start_date": "2026-11-20",
        "end_date": "2026-11-26",
        "timezone_id": "Europe/Brussels",
        "page": 2,
        "perpage": 100,
    }
    assert "data" not in kwargs


def test_energy_history_defaults_to_a_single_day(api):
    api.inverter_energy_history(SN, end_date=date(2026, 11, 26))

    params = api.session.calls[0][2]["params"]
    assert params["start_date"] == params["end_date"] == "2026-11-26"


def test_energy_history_rejects_more_than_seven_days(api):
    with pytest.raises(GrowattParameterError):
        api.inverter_energy_history(SN, date(2026, 11, 1), date(2026, 11, 26))

    assert api.session.calls == []


def test_api_errors_are_raised(api):
    api.session.payload = {"error_code": 10012, "error_msg": "error_frequently_access"}

    with pytest.raises(GrowattV1ApiError) as err:
        api.inverter_energy(SN)

    assert err.value.error_code == 10012
