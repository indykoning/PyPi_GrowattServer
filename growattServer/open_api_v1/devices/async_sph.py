"""Async SPH/MIX device file."""

from __future__ import annotations

from typing import Any

from .sph import Sph


class AsyncSph(Sph):
    """
    Async SPH/MIX device type.

    Inherits all methods from Sph. Most methods work transparently in async
    context because they return self.api.v1_request(...) which yields a
    coroutine when the api is async.

    Only methods that chain async calls need explicit overrides.
    """

    async def read_ac_charge_times(self, settings_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Read AC charge time periods and settings from an SPH inverter.

        Retrieves all 3 AC charge time periods plus global charge settings
        (power, stop SOC, mains enabled) from an SPH inverter.

        Note that this function uses sph_detail() internally to get the settings data.
        To avoid endpoint rate limit, you can pass the settings_data parameter
        with the data returned from sph_detail().

        Args:
            device_sn (str): The device serial number of the inverter.
            settings_data (dict, optional): Settings data from sph_detail call to avoid repeated API calls.

        Returns:
            dict: A dictionary containing:
                - charge_power (int): Charging power percentage (0-100)
                - charge_stop_soc (int): Stop charging at this SOC percentage (0-100)
                - mains_enabled (bool): Whether grid/mains charging is enabled
                - periods (list): List of 3 period dicts, each with:
                    - period_id (int): The period number (1-3)
                    - start_time (str): Start time in format "HH:MM"
                    - end_time (str): End time in format "HH:MM"
                    - enabled (bool): Whether the period is enabled

        Example:
            # Option 1: Fetch settings automatically
            charge_config = await api.sph_read_ac_charge_times(device_sn="DEVICE_SERIAL_NUMBER")
            print(f"Charge power: {charge_config['charge_power']}%")
            print(f"Periods: {charge_config['periods']}")

            # Option 2: Reuse existing settings data
            settings_response = await api.sph_detail("DEVICE_SERIAL_NUMBER")
            charge_config = await api.sph_read_ac_charge_times(device_sn="DEVICE_SERIAL_NUMBER", settings_data=settings_response)

        Raises:
            GrowattParameterError: If neither device_sn nor settings_data is provided.
            GrowattV1ApiError: If the API request fails.
            httpx.HTTPError: If there is an issue with the HTTP request.

        """
        if settings_data is None:
            settings_data = await self.detail()
        return self._parse_ac_charge_settings(settings_data)

    async def read_ac_discharge_times(self, settings_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Read AC discharge time periods and settings from an SPH inverter.

        Retrieves all 3 AC discharge time periods plus global discharge settings
        (power, stop SOC) from an SPH inverter.

        Note that this function uses sph_detail() internally to get the settings data.
        To avoid endpoint rate limit, you can pass the settings_data parameter
        with the data returned from sph_detail().

        Args:
            device_sn (str, optional): The device serial number of the inverter.
            settings_data (dict, optional): Settings data from sph_detail call to avoid repeated API calls.

        Returns:
            dict: A dictionary containing:
                - discharge_power (int): Discharging power percentage (0-100)
                - discharge_stop_soc (int): Stop discharging at this SOC percentage (0-100)
                - periods (list): List of 3 period dicts, each with:
                    - period_id (int): The period number (1-3)
                    - start_time (str): Start time in format "HH:MM"
                    - end_time (str): End time in format "HH:MM"
                    - enabled (bool): Whether the period is enabled

        Example:
            # Option 1: Fetch settings automatically
            discharge_config = await api.sph_read_ac_discharge_times(device_sn="DEVICE_SERIAL_NUMBER")
            print(f"Discharge power: {discharge_config['discharge_power']}%")
            print(f"Stop SOC: {discharge_config['discharge_stop_soc']}%")

            # Option 2: Reuse existing settings data
            settings_response = await api.sph_detail("DEVICE_SERIAL_NUMBER")
            discharge_config = await api.sph_read_ac_discharge_times(device_sn="DEVICE_SERIAL_NUMBER", settings_data=settings_response)

        Raises:
            GrowattParameterError: If neither device_sn nor settings_data is provided.
            GrowattV1ApiError: If the API request fails.
            httpx.HTTPError: If there is an issue with the HTTP request.

        """
        if settings_data is None:
            settings_data = await self.detail()
        return self._parse_ac_discharge_settings(settings_data)
