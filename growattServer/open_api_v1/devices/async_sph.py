"""Async SPH/MIX device file using httpx."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from growattServer.exceptions import GrowattParameterError

from .abstract_device import AbstractDevice, ParameterValue


class AsyncSph(AbstractDevice):
    """Async SPH/MIX device type."""

    DEVICE_TYPE_ID = 5

    async def detail(self) -> dict[str, Any]:
        """Get detailed data for an SPH inverter."""
        response = await self.api.session.get(
            self.api.get_url("device/mix/mix_data_info"),
            params={"device_sn": self.device_sn},
        )
        return self.api.process_response(
            response.json(), "getting SPH inverter details"
        )

    async def energy(self) -> dict[str, Any]:
        """Get energy data for an SPH inverter."""
        response = await self.api.session.post(
            url=self.api.get_url("device/mix/mix_last_data"),
            data={"mix_sn": self.device_sn},
        )
        return self.api.process_response(
            response.json(), "getting SPH inverter energy data"
        )

    async def energy_history(
        self, start_date: date | None = None, end_date: date | None = None, timezone: str | None = None, page: int | None = None, limit: int | None = None
    ) -> dict[str, Any]:
        """Get SPH inverter data history."""
        if start_date is None and end_date is None:
            start_date = datetime.now(tz=UTC).astimezone().date()
            end_date = datetime.now(tz=UTC).astimezone().date()
        elif start_date is None:
            start_date = end_date
        elif end_date is None:
            end_date = start_date

        if end_date - start_date > timedelta(days=7):
            raise GrowattParameterError("date interval must not exceed 7 days")

        response = await self.api.session.post(
            url=self.api.get_url("device/mix/mix_data"),
            data={
                "mix_sn": self.device_sn,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "timezone_id": timezone,
                "page": page,
                "perpage": limit,
            },
        )
        return self.api.process_response(
            response.json(), "getting SPH inverter energy history"
        )

    async def read_parameter(self, parameter_id: str | None = None, start_address: int | None = None, end_address: int | None = None) -> dict[str, Any]:
        """Read setting from SPH inverter."""
        if parameter_id is None and start_address is None:
            raise GrowattParameterError(
                "specify either parameter_id or start_address/end_address"
            )
        if parameter_id is not None and start_address is not None:
            raise GrowattParameterError(
                "specify either parameter_id or start_address/end_address - not both."
            )
        if parameter_id is not None:
            start_address = 0
            end_address = 0
        else:
            parameter_id = "set_any_reg"

        response = await self.api.session.post(
            self.api.get_url("readMixParam"),
            data={
                "device_sn": self.device_sn,
                "paramId": parameter_id,
                "startAddr": start_address,
                "endAddr": end_address,
            },
        )
        return self.api.process_response(
            response.json(), f"reading parameter {parameter_id}"
        )

    async def write_parameter(self, parameter_id: str, parameter_values: ParameterValue | None = None) -> dict[str, Any]:
        """Set parameters on an SPH inverter."""
        max_sph_params = 18
        parameters = dict.fromkeys(range(1, max_sph_params + 1), "")

        if parameter_values is not None:
            if isinstance(parameter_values, (str, int, float, bool)):
                parameters[1] = str(parameter_values)
            elif isinstance(parameter_values, list):
                for i, value in enumerate(parameter_values, 1):
                    if i <= max_sph_params:
                        parameters[i] = str(value)
            elif isinstance(parameter_values, dict):
                for pos_raw, value in parameter_values.items():
                    pos = int(pos_raw) if not isinstance(pos_raw, int) else pos_raw
                    if 1 <= pos <= max_sph_params:
                        parameters[pos] = str(value)

        request_data = {"mix_sn": self.device_sn, "type": parameter_id}
        for i in range(1, max_sph_params + 1):
            request_data[f"param{i}"] = str(parameters[i])

        response = await self.api.session.post(self.api.get_url("mixSet"), data=request_data)
        return self.api.process_response(
            response.json(), f"writing parameter {parameter_id}"
        )

    async def write_ac_charge_times(
        self, charge_power: int, charge_stop_soc: int, mains_enabled: bool, periods: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Set AC charge time periods for an SPH inverter."""
        if not 0 <= charge_power <= 100:  # noqa: PLR2004
            raise GrowattParameterError("charge_power must be between 0 and 100")
        if not 0 <= charge_stop_soc <= 100:  # noqa: PLR2004
            raise GrowattParameterError("charge_stop_soc must be between 0 and 100")
        if len(periods) != 3:  # noqa: PLR2004
            raise GrowattParameterError("periods must contain exactly 3 period definitions")

        request_data = {
            "mix_sn": self.device_sn,
            "type": "mix_ac_charge_time_period",
            "param1": str(charge_power),
            "param2": str(charge_stop_soc),
            "param3": "1" if mains_enabled else "0",
        }

        for i, period in enumerate(periods):
            base = i * 5 + 4
            request_data[f"param{base}"] = str(period["start_time"].hour)
            request_data[f"param{base + 1}"] = str(period["start_time"].minute)
            request_data[f"param{base + 2}"] = str(period["end_time"].hour)
            request_data[f"param{base + 3}"] = str(period["end_time"].minute)
            request_data[f"param{base + 4}"] = "1" if period["enabled"] else "0"

        response = await self.api.session.post(self.api.get_url("mixSet"), data=request_data)
        return self.api.process_response(
            response.json(), "writing AC charge time periods"
        )

    async def write_ac_discharge_times(self, discharge_power: int, discharge_stop_soc: int, periods: list[dict[str, Any]]) -> dict[str, Any]:
        """Set AC discharge time periods for an SPH inverter."""
        if not 0 <= discharge_power <= 100:  # noqa: PLR2004
            raise GrowattParameterError("discharge_power must be between 0 and 100")
        if not 0 <= discharge_stop_soc <= 100:  # noqa: PLR2004
            raise GrowattParameterError("discharge_stop_soc must be between 0 and 100")
        if len(periods) != 3:  # noqa: PLR2004
            raise GrowattParameterError("periods must contain exactly 3 period definitions")

        request_data = {
            "mix_sn": self.device_sn,
            "type": "mix_ac_discharge_time_period",
            "param1": str(discharge_power),
            "param2": str(discharge_stop_soc),
        }

        for i, period in enumerate(periods):
            base = i * 5 + 3
            request_data[f"param{base}"] = str(period["start_time"].hour)
            request_data[f"param{base + 1}"] = str(period["start_time"].minute)
            request_data[f"param{base + 2}"] = str(period["end_time"].hour)
            request_data[f"param{base + 3}"] = str(period["end_time"].minute)
            request_data[f"param{base + 4}"] = "1" if period["enabled"] else "0"

        response = await self.api.session.post(self.api.get_url("mixSet"), data=request_data)
        return self.api.process_response(
            response.json(), "writing AC discharge time periods"
        )

    def _parse_time_periods(self, settings_data: dict[str, Any], time_type: str) -> list[dict[str, Any]]:
        """Parse time periods from settings data."""
        periods = []

        for i in range(1, 4):
            start_time_raw = settings_data.get(f"forced{time_type}TimeStart{i}", "0:0")
            end_time_raw = settings_data.get(f"forced{time_type}TimeStop{i}", "0:0")
            enabled_raw = settings_data.get(f"forced{time_type}StopSwitch{i}", 0)

            if start_time_raw == "null" or not start_time_raw:
                start_time_raw = "0:0"
            if end_time_raw == "null" or not end_time_raw:
                end_time_raw = "0:0"

            try:
                start_parts = start_time_raw.split(":")
                start_time = f"{int(start_parts[0]):02d}:{int(start_parts[1]):02d}"
            except (ValueError, IndexError):
                start_time = "00:00"

            try:
                end_parts = end_time_raw.split(":")
                end_time = f"{int(end_parts[0]):02d}:{int(end_parts[1]):02d}"
            except (ValueError, IndexError):
                end_time = "00:00"

            if enabled_raw == "null" or enabled_raw is None:
                enabled = False
            else:
                try:
                    enabled = int(enabled_raw) == 1
                except (ValueError, TypeError):
                    enabled = False

            periods.append({
                "period_id": i,
                "start_time": start_time,
                "end_time": end_time,
                "enabled": enabled,
            })

        return periods

    async def read_ac_charge_times(self, settings_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Read AC charge time periods and settings from an SPH inverter."""
        if settings_data is None:
            settings_data = await self.detail()

        charge_power = settings_data.get("chargePowerCommand", 0)
        charge_stop_soc = settings_data.get("wchargeSOCLowLimit", 100)
        mains_enabled_raw = settings_data.get("acChargeEnable", 0)

        if charge_power == "null" or charge_power is None or charge_power == "":
            charge_power = 0
        if charge_stop_soc == "null" or charge_stop_soc is None or charge_stop_soc == "":
            charge_stop_soc = 100
        if mains_enabled_raw == "null" or mains_enabled_raw is None or mains_enabled_raw == "":
            mains_enabled = False
        else:
            mains_enabled = int(mains_enabled_raw) == 1

        return {
            "charge_power": int(charge_power),
            "charge_stop_soc": int(charge_stop_soc),
            "mains_enabled": mains_enabled,
            "periods": self._parse_time_periods(settings_data, "Charge"),
        }

    async def read_ac_discharge_times(self, settings_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Read AC discharge time periods and settings from an SPH inverter."""
        if settings_data is None:
            settings_data = await self.detail()

        discharge_power = settings_data.get("disChargePowerCommand", 0)
        discharge_stop_soc = settings_data.get("wdisChargeSOCLowLimit", 10)

        if discharge_power == "null" or discharge_power is None or discharge_power == "":
            discharge_power = 0
        if discharge_stop_soc == "null" or discharge_stop_soc is None or discharge_stop_soc == "":
            discharge_stop_soc = 10

        return {
            "discharge_power": int(discharge_power),
            "discharge_stop_soc": int(discharge_stop_soc),
            "periods": self._parse_time_periods(settings_data, "Discharge"),
        }
