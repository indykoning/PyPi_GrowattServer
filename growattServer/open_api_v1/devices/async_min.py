"""Async Min/TLX device file using httpx."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from growattServer.exceptions import GrowattParameterError

from .abstract_device import AbstractDevice, ParameterValue


class AsyncMin(AbstractDevice):
    """Async Min/TLX device type."""

    DEVICE_TYPE_ID = 7

    async def detail(self) -> dict[str, Any]:
        """Get detailed data for a MIN inverter."""
        response = await self.api.session.get(
            self.api.get_url("device/tlx/tlx_data_info"),
            params={"device_sn": self.device_sn},
        )
        return self.api.process_response(
            response.json(), "getting MIN inverter details"
        )

    async def energy(self) -> dict[str, Any]:
        """Get energy data for a MIN inverter."""
        response = await self.api.session.post(
            url=self.api.get_url("device/tlx/tlx_last_data"),
            data={"tlx_sn": self.device_sn},
        )
        return self.api.process_response(
            response.json(), "getting MIN inverter energy data"
        )

    async def energy_history(
        self, start_date: date | None = None, end_date: date | None = None, timezone: str | None = None, page: int | None = None, limit: int | None = None
    ) -> dict[str, Any]:
        """Get MIN inverter data history."""
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
            url=self.api.get_url("device/tlx/tlx_data"),
            data={
                "tlx_sn": self.device_sn,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "timezone_id": timezone,
                "page": page,
                "perpage": limit,
            },
        )
        return self.api.process_response(
            response.json(), "getting MIN inverter energy history"
        )

    async def settings(self) -> dict[str, Any]:
        """Get settings for a MIN inverter."""
        response = await self.api.session.get(
            self.api.get_url("device/tlx/tlx_set_info"),
            params={"device_sn": self.device_sn},
        )
        return self.api.process_response(
            response.json(), "getting MIN inverter settings"
        )

    async def read_parameter(
        self, parameter_id: str, start_address: int | None = None, end_address: int | None = None
    ) -> dict[str, Any]:
        """Read setting from MIN inverter."""
        self.validate_read_parameter_input(parameter_id, start_address, end_address)

        if parameter_id is not None:
            start_address = 0
            end_address = 0
        else:
            parameter_id = "set_any_reg"
            if start_address is None:
                start_address = end_address
            if end_address is None:
                end_address = start_address

        response = await self.api.session.post(
            self.api.get_url("readMinParam"),
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
        """Set parameters on a MIN inverter."""
        max_min_params = 19
        parameters = dict.fromkeys(range(1, max_min_params + 1), "")

        if parameter_values is not None:
            if isinstance(parameter_values, (str, int, float, bool)):
                parameters[1] = str(parameter_values)
            elif isinstance(parameter_values, list):
                for i, value in enumerate(parameter_values, 1):
                    if i <= max_min_params:
                        parameters[i] = str(value)
            elif isinstance(parameter_values, dict):
                for pos_raw, value in parameter_values.items():
                    pos = int(pos_raw) if not isinstance(pos_raw, int) else pos_raw
                    if 1 <= pos <= max_min_params:
                        parameters[pos] = str(value)

        request_data = {"tlx_sn": self.device_sn, "type": parameter_id}
        for i in range(1, max_min_params + 1):
            request_data[f"param{i}"] = str(parameters[i])

        response = await self.api.session.post(self.api.get_url("tlxSet"), data=request_data)
        return self.api.process_response(
            response.json(), f"writing parameter {parameter_id}"
        )

    async def write_time_segment(
        self, segment_id: int, batt_mode: int, start_time: time, end_time: time, enabled: bool = True
    ) -> dict[str, Any]:
        """Set a time segment for a MIN inverter."""
        max_min_params = 19
        max_min_segments = 9
        max_batt_mode = 2

        if not 1 <= segment_id <= max_min_segments:
            msg = f"segment_id must be between 1 and {max_min_segments}"
            raise GrowattParameterError(msg)

        if not 0 <= batt_mode <= max_batt_mode:
            msg = f"batt_mode must be between 0 and {max_batt_mode}"
            raise GrowattParameterError(msg)

        all_params = {"tlx_sn": self.device_sn, "type": f"time_segment{segment_id}"}
        all_params["param1"] = str(batt_mode)
        all_params["param2"] = str(start_time.hour)
        all_params["param3"] = str(start_time.minute)
        all_params["param4"] = str(end_time.hour)
        all_params["param5"] = str(end_time.minute)
        all_params["param6"] = "1" if enabled else "0"

        for i in range(7, max_min_params + 1):
            all_params[f"param{i}"] = ""

        response = await self.api.session.post(self.api.get_url("tlxSet"), data=all_params)
        return self.api.process_response(
            response.json(), f"writing time segment {segment_id}"
        )

    async def read_time_segments(self, settings_data: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Read Time-of-Use (TOU) settings from a Growatt MIN/TLX inverter."""
        if settings_data is None:
            settings_data = await self.settings()

        mode_names = {0: "Load First", 1: "Battery First", 2: "Grid First"}
        segments = []

        for i in range(1, 10):
            start_time_raw = settings_data.get(f"forcedTimeStart{i}", "0:0")
            end_time_raw = settings_data.get(f"forcedTimeStop{i}", "0:0")

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

            mode_raw = settings_data.get(f"time{i}Mode")
            if mode_raw == "null" or mode_raw is None:
                batt_mode = None
            else:
                try:
                    batt_mode = int(mode_raw)
                except (ValueError, TypeError):
                    batt_mode = None

            enabled_raw = settings_data.get(f"forcedStopSwitch{i}", 0)
            if enabled_raw == "null" or enabled_raw is None:
                enabled = False
            else:
                try:
                    enabled = int(enabled_raw) == 1
                except (ValueError, TypeError):
                    enabled = False

            segments.append({
                "segment_id": i,
                "batt_mode": batt_mode,
                "mode_name": mode_names.get(batt_mode, "Unknown"),
                "start_time": start_time,
                "end_time": end_time,
                "enabled": enabled,
            })

        return segments
