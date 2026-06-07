"""Async Min/TLX device file."""

from __future__ import annotations

from typing import Any

from .min import Min


class AsyncMin(Min):
    """
    Async Min/TLX device type.

    Inherits all methods from Min. Most methods work transparently in async
    context because they return self.api.v1_request(...) which yields a
    coroutine when the api is async.

    Only methods that chain async calls need explicit overrides.
    """

    async def detail(self) -> dict[str, Any]:  # type: ignore[override]
        """Get detailed data for a MIN inverter (async)."""
        return await self.api.v1_request(
            "GET", "device/tlx/tlx_data_info",
            params={"device_sn": self.device_sn},
            operation_name="getting MIN inverter details",
        )

    async def settings(self) -> dict[str, Any]:  # type: ignore[override]
        """Get settings for a MIN inverter (async)."""
        return await self.api.v1_request(
            "GET", "device/tlx/tlx_set_info",
            params={"device_sn": self.device_sn},
            operation_name="getting MIN inverter settings",
        )

    async def read_time_segments(self, settings_data: dict[str, Any] | None = None) -> list[dict[str, Any]]:  # type: ignore[override]
        """
        Read Time-of-Use (TOU) settings from a Growatt MIN/TLX inverter.

        Retrieves all 9 time segments from a Growatt MIN/TLX inverter and
        parses them into a structured format.

        Note that this function uses min_settings() internally to get the settings data,
        To avoid endpoint rate limit, you can pass the settings_data parameter
        with the data returned from min_settings().

        Args:
            device_sn (str): The device serial number of the inverter
            settings_data (dict, optional): Settings data from min_settings call to avoid repeated API calls.
                                            Can be either the complete response or just the data portion.

        Returns:
            list: A list of dictionaries, each containing details for one time segment:
                - segment_id (int): The segment number (1-9)
                - batt_mode (int): 0=Load First, 1=Battery First, 2=Grid First
                - mode_name (str): String representation of the mode
                - start_time (str): Start time in format "HH:MM"
                - end_time (str): End time in format "HH:MM"
                - enabled (bool): Whether the segment is enabled

        Example:
            # Option 1: Make a single call
            tou_settings = await api.min_read_time_segments("DEVICE_SERIAL_NUMBER")

            # Option 2: Reuse existing settings data
            settings_response = await api.min_settings("DEVICE_SERIAL_NUMBER")
            tou_settings = await api.min_read_time_segments("DEVICE_SERIAL_NUMBER", settings_response)

        Raises:
            GrowattV1ApiError: If the API request fails
            GrowattApiError: If there is an issue with the HTTP request.

        """
        if settings_data is None:
            settings_data = await self.settings()
        return self._parse_time_segments(settings_data)
