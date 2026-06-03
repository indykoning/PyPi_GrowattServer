"""Async OpenApi V1 extensions for Growatt API client using httpx."""

from __future__ import annotations

import platform
import warnings
from datetime import UTC, date, datetime, time
from typing import Any

from growattServer.async_base_api import AsyncGrowattApi
from growattServer.exceptions import GrowattV1ApiError

from .devices.async_min import AsyncMin
from .devices.async_sph import AsyncSph


class AsyncOpenApiV1(AsyncGrowattApi):
    """
    Async extended Growatt API client with V1 API support using httpx.

    This class extends the base AsyncGrowattApi class with methods for MIN and SPH devices using
    the public V1 API described here: https://www.showdoc.com.cn/262556420217021/0.
    """

    def _create_user_agent(self) -> str:
        python_version = platform.python_version()
        system = platform.system()
        release = platform.release()
        machine = platform.machine()

        return f"Python/{python_version} ({system} {release}; {machine})"

    def __init__(self, token: str, session: Any = None) -> None:
        """
        Initialize the async Growatt API client with V1 API support.

        Args:
            token (str): API token for authentication (required for V1 API access).
            session: Optional httpx.AsyncClient to reuse.

        """
        super().__init__(agent_identifier=self._create_user_agent(), session=session)

        self.api_url = f"{self.server_url}v1/"
        self.session.headers.update({"token": token})

    def process_response(self, response: dict[str, Any], operation_name: str = "API operation") -> dict[str, Any]:
        """
        Process API response and handle errors.

        Args:
            response (dict): The JSON response from the API
            operation_name (str): Name of the operation for error messages

        Returns:
            dict: The 'data' field from the response

        Raises:
            GrowattV1ApiError: If the API returns an error response

        """
        if response.get("error_code", 1) != 0:
            msg = f"Error during {operation_name}"
            raise GrowattV1ApiError(
                msg,
                error_code=response["error_code"],
                error_msg=response.get("error_msg", "Unknown error"),
            )
        return response.get("data")

    def get_url(self, page: str) -> str:
        """Return the page URL for the v1 API."""
        return self.api_url + page

    async def plant_list(self) -> dict[str, Any]:
        """
        Get a list of all plants with detailed information.

        Returns:
            dict: A dictionary containing plants information with 'count' and 'plants' keys.

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            httpx.HTTPError: If there is an issue with the HTTP request.

        """
        request_data = {
            "page": "", "perpage": "", "search_type": "", "search_keyword": "",
        }
        response = await self.session.get(url=self.get_url("plant/list"), data=request_data)
        return self.process_response(response.json(), "getting plant list")

    async def plant_details(self, plant_id: int) -> dict[str, Any]:
        """
        Get basic information about a power station.

        Args:
            plant_id (int): Power Station ID

        Returns:
            dict: A dictionary containing the plant details.

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            httpx.HTTPError: If there is an issue with the HTTP request.

        """
        response = await self.session.get(
            self.get_url("plant/details"), params={"plant_id": plant_id}
        )
        return self.process_response(response.json(), "getting plant details")

    async def plant_energy_overview(self, plant_id: int) -> dict[str, Any]:
        """
        Get an overview of a plant's energy data.

        Args:
            plant_id (int): Power Station ID

        Returns:
            dict: A dictionary containing the plant energy overview.

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            httpx.HTTPError: If there is an issue with the HTTP request.

        """
        response = await self.session.get(
            self.get_url("plant/data"), params={"plant_id": plant_id}
        )
        return self.process_response(response.json(), "getting plant energy overview")

    async def plant_power_overview(self, plant_id: int, day: str | date | None = None) -> dict:
        """
        Obtain power data of a certain power station.

        Args:
            plant_id (int): Power Station ID
            day (date): Date - defaults to today in the local system timezone

        Returns:
            dict: A dictionary containing the plants power data.

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            httpx.HTTPError: If there is an issue with the HTTP request.

        """
        if day is None:
            day = datetime.now(tz=UTC).astimezone().date()

        response = await self.session.get(
            self.get_url("plant/power"),
            params={"plant_id": plant_id, "date": day},
        )
        return self.process_response(response.json(), "getting plant power overview")

    async def plant_energy_history(
        self,
        plant_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        time_unit: str = "day",
        page: int | None = None,
        perpage: int | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve plant energy data for multiple days/months/years.

        Args:
            plant_id (int): Power Station ID
            start_date (date, optional): Start Date - defaults to today in the local system timezone
            end_date (date, optional): End Date - defaults to today in the local system timezone
            time_unit (str, optional): Time unit ('day', 'month', 'year') - defaults to 'day'
            page (int, optional): Page number - defaults to 1
            perpage (int, optional): Number of items per page - defaults to 20, max 100

        Returns:
            dict: A dictionary containing the plant energy history.

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            httpx.HTTPError: If there is an issue with the HTTP request.

        """
        max_day_interval = 7
        max_year_interval = 20

        if start_date is None and end_date is None:
            start_date = datetime.now(tz=UTC).astimezone().date()
            end_date = datetime.now(tz=UTC).astimezone().date()
        elif start_date is None:
            start_date = end_date
        elif end_date is None:
            end_date = start_date

        if time_unit == "day" and (end_date - start_date).days > max_day_interval:
            warnings.warn(
                "Date interval must not exceed 7 days in 'day' mode.",
                RuntimeWarning, stacklevel=2,
            )
        elif time_unit == "month" and (end_date.year - start_date.year > 1):
            warnings.warn(
                "Start date must be within same or previous year in 'month' mode.",
                RuntimeWarning, stacklevel=2,
            )
        elif time_unit == "year" and (end_date.year - start_date.year > max_year_interval):
            warnings.warn(
                "Date interval must not exceed 20 years in 'year' mode.",
                RuntimeWarning, stacklevel=2,
            )

        response = await self.session.get(
            self.get_url("plant/energy"),
            params={
                "plant_id": plant_id,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "time_unit": time_unit,
                "page": page,
                "perpage": perpage,
            },
        )
        return self.process_response(response.json(), "getting plant energy history")

    async def device_list(self, plant_id: int) -> dict[str, Any]:
        """
        Get devices associated with plant.

        Args:
            plant_id (int): Power Station ID

        Returns:
            dict: A dictionary containing device list data.

        """
        response = await self.session.get(
            url=self.get_url("device/list"),
            params={"plant_id": plant_id, "page": "", "perpage": ""},
        )
        return self.process_response(response.json(), "getting device list")

    def get_device(self, device_sn: str, device_type: int):
        """Get the device class by serial number and device_type id."""
        match device_type:
            case AsyncSph.DEVICE_TYPE_ID:
                return AsyncSph(self, device_sn)
            case AsyncMin.DEVICE_TYPE_ID:
                return AsyncMin(self, device_sn)
            case _:
                warnings.warn(
                    f"Device for type id: {device_type} has not been implemented yet.",
                    stacklevel=2,
                )
                return None

    async def min_detail(self, device_sn: str) -> dict[str, Any]:
        """Get detailed data for a MIN inverter."""
        return await AsyncMin(self, device_sn).detail()

    async def min_energy(self, device_sn: str) -> dict[str, Any]:
        """Get energy data for a MIN inverter."""
        return await AsyncMin(self, device_sn).energy()

    async def min_energy_history(
        self, device_sn: str, start_date: date | None = None, end_date: date | None = None,
        timezone: str | None = None, page: int | None = None, limit: int | None = None,
    ) -> dict[str, Any]:
        """Get MIN inverter data history."""
        return await AsyncMin(self, device_sn).energy_history(
            start_date, end_date, timezone, page, limit
        )

    async def min_settings(self, device_sn: str) -> dict[str, Any]:
        """Get settings for a MIN inverter."""
        return await AsyncMin(self, device_sn).settings()

    async def min_read_parameter(
        self, device_sn: str, parameter_id: str, start_address: int | None = None, end_address: int | None = None
    ) -> dict[str, Any]:
        """Read setting from MIN inverter."""
        return await AsyncMin(self, device_sn).read_parameter(
            parameter_id, start_address, end_address
        )

    async def min_write_parameter(self, device_sn: str, parameter_id: str, parameter_values=None) -> dict[str, Any]:
        """Set parameters on a MIN inverter."""
        return await AsyncMin(self, device_sn).write_parameter(parameter_id, parameter_values)

    async def min_write_time_segment(
        self, device_sn: str, segment_id: int, batt_mode: int, start_time: time, end_time: time, enabled: bool = True
    ) -> dict[str, Any]:
        """Set a time segment for a MIN inverter."""
        return await AsyncMin(self, device_sn).write_time_segment(
            segment_id, batt_mode, start_time, end_time, enabled
        )

    async def min_read_time_segments(self, device_sn: str, settings_data: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Read Time-of-Use (TOU) settings from a Growatt MIN/TLX inverter."""
        return await AsyncMin(self, device_sn).read_time_segments(settings_data)

    # SPH Device Methods (Device Type 5)

    async def sph_detail(self, device_sn: str) -> dict[str, Any]:
        """Get detailed data for an SPH inverter."""
        return await AsyncSph(self, device_sn).detail()

    async def sph_energy(self, device_sn: str) -> dict[str, Any]:
        """Get energy data for an SPH inverter."""
        return await AsyncSph(self, device_sn).energy()

    async def sph_energy_history(
        self, device_sn: str, start_date: date | None = None, end_date: date | None = None,
        timezone: str | None = None, page: int | None = None, limit: int | None = None,
    ) -> dict[str, Any]:
        """Get SPH inverter data history."""
        return await AsyncSph(self, device_sn).energy_history(
            start_date, end_date, timezone, page, limit
        )

    async def sph_read_parameter(
        self, device_sn: str, parameter_id: str | None = None, start_address: int | None = None, end_address: int | None = None
    ) -> dict[str, Any]:
        """Read setting from SPH inverter."""
        return await AsyncSph(self, device_sn).read_parameter(
            parameter_id, start_address, end_address
        )

    async def sph_write_parameter(self, device_sn: str, parameter_id: str, parameter_values=None) -> dict[str, Any]:
        """Set parameters on an SPH inverter."""
        return await AsyncSph(self, device_sn).write_parameter(parameter_id, parameter_values)

    async def sph_write_ac_charge_times(
        self, device_sn: str, charge_power: int, charge_stop_soc: int, mains_enabled: bool, periods: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Set AC charge time periods for an SPH inverter."""
        return await AsyncSph(self, device_sn).write_ac_charge_times(
            charge_power, charge_stop_soc, mains_enabled, periods
        )

    async def sph_write_ac_discharge_times(
        self, device_sn: str, discharge_power: int, discharge_stop_soc: int, periods: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Set AC discharge time periods for an SPH inverter."""
        return await AsyncSph(self, device_sn).write_ac_discharge_times(
            discharge_power, discharge_stop_soc, periods
        )

    async def sph_read_ac_charge_times(self, device_sn: str, settings_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Read AC charge time periods and settings from an SPH inverter."""
        return await AsyncSph(self, device_sn).read_ac_charge_times(settings_data)

    async def sph_read_ac_discharge_times(self, device_sn: str, settings_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Read AC discharge time periods and settings from an SPH inverter."""
        return await AsyncSph(self, device_sn).read_ac_discharge_times(settings_data)
