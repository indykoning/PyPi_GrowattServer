"""OpenApi V1 extensions for Growatt API client."""
import platform
import warnings
from datetime import UTC, date, datetime
from enum import Enum

from growattServer import GrowattApi
from growattServer.exceptions import GrowattV1ApiError

from .devices import AbstractDevice, Min, Sph


class DeviceType(Enum):
    """Enumeration of Growatt device types."""

    INVERTER = 1
    STORAGE = 2
    OTHER = 3
    MAX = 4
    SPH = Sph.DEVICE_TYPE_ID # (MIX)
    SPA = 6
    MIN = Min.DEVICE_TYPE_ID
    PCS = 8
    HPS = 9
    PBD = 10


class OpenApiV1(GrowattApi):
    """
    Extended Growatt API client with V1 API support.

    This class extends the base GrowattApi class with methods for MIN and SPH devices using
    the public V1 API described here: https://www.showdoc.com.cn/262556420217021/0.
    """

    def _create_user_agent(self) -> str:
        python_version = platform.python_version()
        system = platform.system()
        release = platform.release()
        machine = platform.machine()

        return f"Python/{python_version} ({system} {release}; {machine})"

    def __init__(self, token) -> None:
        """
        Initialize the Growatt API client with V1 API support.

        Args:
            token (str): API token for authentication (required for V1 API access).

        """
        # Initialize the base class
        super().__init__(agent_identifier=self._create_user_agent())

        # Add V1 API specific properties
        self.api_url = f"{self.server_url}v1/"

        # Set up authentication for V1 API using the provided token
        self.session.headers.update({"token": token})

    def process_response(self, response, operation_name="API operation"):
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
                error_code=response.get("error_code"),
                error_msg=response.get("error_msg", "Unknown error")
            )
        return response.get("data")

    def get_url(self, page):
        """Return the page URL for the v1 API."""
        return self.api_url + page

    def plant_list(self):
        """
        Get a list of all plants with detailed information.

        Returns:
            dict: A dictionary containing plants information with 'count' and 'plants' keys.

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        # Prepare request data
        request_data = {
            "page": "",
            "perpage": "",
            "search_type": "",
            "search_keyword": ""
        }

        # Make the request
        response = self.session.get(
            url=self.get_url("plant/list"),
            data=request_data
        )

        return self.process_response(response.json(), "getting plant list")

    def plant_details(self, plant_id):
        """
        Get basic information about a power station.

        Args:
            plant_id (int): Power Station ID

        Returns:
            dict: A dictionary containing the plant details.

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        response = self.session.get(
            self.get_url("plant/details"),
            params={"plant_id": plant_id}
        )

        return self.process_response(response.json(), "getting plant details")

    def plant_energy_overview(self, plant_id):
        """
        Get an overview of a plant's energy data.

        Args:
            plant_id (int): Power Station ID

        Returns:
            dict: A dictionary containing the plant energy overview.

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        response = self.session.get(
            self.get_url("plant/data"),
            params={"plant_id": plant_id}
        )

        return self.process_response(response.json(), "getting plant energy overview")

    def plant_power_overview(self, plant_id: int, day: str | date | None = None) -> dict:
        """
        Obtain power data of a certain power station.

        Get the frequency once every 5 minutes

        Args:
            plant_id (int): Power Station ID
            day (date): Date - defaults to today

        Returns:
            dict: A dictionary containing the plants power data.
            .. code-block:: python
                {
                    'count': int,  # Total number of records
                    'powers': list[dict],  # List of power data entries
                    # Each entry in 'powers' is a dictionary with:
                    #   'time': str,  # Time of the power reading
                    #   'power': float | None  # Power value in Watts (can be None)
                }.

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        API-Doc: https://www.showdoc.com.cn/262556420217021/1494062656174173

        """
        if day is None:
            day = datetime.now(UTC).date()

        response = self.session.get(
            self.get_url("plant/power"),
            params={
                "plant_id": plant_id,
                "date": day,
            }
        )

        return self.process_response(response.json(), "getting plant power overview")

    def plant_energy_history(self, plant_id, start_date=None, end_date=None, time_unit="day", page=None, perpage=None):
        """
        Retrieve plant energy data for multiple days/months/years.

        Args:
            plant_id (int): Power Station ID
            start_date (date, optional): Start Date - defaults to today
            end_date (date, optional): End Date - defaults to today
            time_unit (str, optional): Time unit ('day', 'month', 'year') - defaults to 'day'
            page (int, optional): Page number - defaults to 1
            perpage (int, optional): Number of items per page - defaults to 20, max 100

        Returns:
            dict: A dictionary containing the plant energy history.

        Notes:
            - When time_unit is 'day', date interval cannot exceed 7 days
            - When time_unit is 'month', start date must be within same or previous year
            - When time_unit is 'year', date interval must not exceed 20 years

        Raises:
            GrowattParameterError: If date parameters are invalid.
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        max_day_interval = 7
        max_year_interval = 20

        if start_date is None and end_date is None:
            start_date = datetime.now(UTC).date()
            end_date = datetime.now(UTC).date()
        elif start_date is None:
            start_date = end_date
        elif end_date is None:
            end_date = start_date

        # Validate date ranges based on time_unit
        if time_unit == "day" and (end_date - start_date).days > max_day_interval:
            warnings.warn(
                "Date interval must not exceed 7 days in 'day' mode.", RuntimeWarning, stacklevel=2)
        elif time_unit == "month" and (end_date.year - start_date.year > 1):
            warnings.warn(
                "Start date must be within same or previous year in 'month' mode.", RuntimeWarning, stacklevel=2)
        elif time_unit == "year" and (end_date.year - start_date.year > max_year_interval):
            warnings.warn(
                "Date interval must not exceed 20 years in 'year' mode.", RuntimeWarning, stacklevel=2)

        response = self.session.get(
            self.get_url("plant/energy"),
            params={
                "plant_id": plant_id,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "time_unit": time_unit,
                "page": page,
                "perpage": perpage
            }
        )

        return self.process_response(response.json(), "getting plant energy history")

    def device_list(self, plant_id):
        """
        Get devices associated with plant.

        Note:
            returned "device_type" mappings:
             1: inverter (including MAX)
             2: storage
             3: other
             4: max (single MAX)
             5: sph
             6: spa
             7: min (including TLX)
             8: pcs
             9: hps
            10: pbd

        Args:
            plant_id (int): Power Station ID

        Returns:
            DeviceList
            e.g.
            {
                "data": {
                    "count": 3,
                    "devices": [
                        {
                            "device_sn": "ZT00100001",
                            "last_update_time": "2018-12-13 11:03:52",
                            "model": "A0B0D0T0PFU1M3S4",
                            "lost": True,
                            "status": 0,
                            "manufacturer": "Growatt",
                            "device_id": 116,
                            "datalogger_sn": "CRAZT00001",
                            "type": 1
                        },
                    ]
                },
                "error_code": 0,
                "error_msg": ""
            }

        """
        response = self.session.get(
            url=self.get_url("device/list"),
            params={
                "plant_id": plant_id,
                "page": "",
                "perpage": "",
            },
        )
        return self.process_response(response.json(), "getting device list")

    def get_device(self, device_sn: str, device_type: int) -> AbstractDevice|None:
        """Get the device class by serial number and device_type id."""
        match device_type:
            case Sph.DEVICE_TYPE_ID:
                return Sph(device_sn)
            case Min.DEVICE_TYPE_ID:
                return Min(device_sn)
            case _:
                warnings.warn(f"Device for type id: {device_type} has not been implemented yet.", stacklevel=2)
                return None

    def min_detail(self, device_sn):
        """
        Get detailed data for a MIN inverter.

        Args:
            device_sn (str): The serial number of the MIN inverter.

        Returns:
            dict: A dictionary containing the MIN inverter details.

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Min(self, device_sn).detail()

    def min_energy(self, device_sn):
        """
        Get energy data for a MIN inverter.

        Args:
            device_sn (str): The serial number of the MIN inverter.

        Returns:
            dict: A dictionary containing the MIN inverter energy data.

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Min(self, device_sn).energy()

    def min_energy_history(self, device_sn, start_date=None, end_date=None, timezone=None, page=None, limit=None):
        """
        Get MIN inverter data history.

        Args:
            device_sn (str): The ID of the MIN inverter.
            start_date (date, optional): Start date. Defaults to today.
            end_date (date, optional): End date. Defaults to today.
            timezone (str, optional): Timezone ID.
            page (int, optional): Page number.
            limit (int, optional): Results per page.

        Returns:
            dict: A dictionary containing the MIN inverter history data.

        Raises:
            GrowattParameterError: If date interval is invalid (exceeds 7 days).
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Min(self, device_sn).energy_history(start_date, end_date, timezone, page, limit)

    def min_settings(self, device_sn):
        """
        Get settings for a MIN inverter.

        Args:
            device_sn (str): The serial number of the MIN inverter.

        Returns:
            dict: A dictionary containing the MIN inverter settings.

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Min(self, device_sn).settings(device_sn)

    def min_read_parameter(self, device_sn, parameter_id, start_address=None, end_address=None):
        """
        Read setting from MIN inverter.

        Args:
            device_sn (str): The ID of the TLX inverter.
            parameter_id (str): Parameter ID to read. Don't use start_address and end_address if this is set.
            start_address (int, optional): Register start address (for set_any_reg). Don't use parameter_id if this is set.
            end_address (int, optional): Register end address (for set_any_reg). Don't use parameter_id if this is set.

        Returns:
            dict: A dictionary containing the setting value.

        Raises:
            GrowattParameterError: If parameters are invalid.
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Min(self, device_sn).read_parameter(parameter_id, start_address, end_address)

    def min_write_parameter(self, device_sn, parameter_id, parameter_values=None):
        """
        Set parameters on a MIN inverter.

        Args:
            device_sn (str): Serial number of the inverter
            parameter_id (str): Setting type to be configured
            parameter_values: Parameter values to be sent to the system.
                Can be a single string (for param1 only),
                a list of strings (for sequential params),
                or a dictionary mapping param positions to values

        Returns:
            dict: JSON response from the server

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Min(self, device_sn).write_parameter(parameter_id, parameter_values)

    def min_write_time_segment(self, device_sn, segment_id, batt_mode, start_time, end_time, enabled=True):
        """
        Set a time segment for a MIN inverter.

        Args:
            device_sn (str): The serial number of the inverter.
            segment_id (int): Time segment ID (1-9).
            batt_mode (int): 0=load priority, 1=battery priority, 2=grid priority.
            start_time (datetime.time): Start time for the segment.
            end_time (datetime.time): End time for the segment.
            enabled (bool): Whether this segment is enabled.

        Returns:
            dict: The server response.

        Raises:
            GrowattParameterError: If parameters are invalid.
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Min(self, device_sn).write_time_segment(segment_id, batt_mode, start_time, end_time, enabled)

    def min_read_time_segments(self, device_sn, settings_data=None):
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
            tou_settings = api.min_read_time_segments("DEVICE_SERIAL_NUMBER")

            # Option 2: Reuse existing settings data
            settings_response = api.min_settings("DEVICE_SERIAL_NUMBER")
            tou_settings = api.min_read_time_segments("DEVICE_SERIAL_NUMBER", settings_response)

        Raises:
            GrowattV1ApiError: If the API request fails
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Min(self, device_sn).read_time_segments(settings_data)

    # SPH Device Methods (Device Type 5)

    def sph_detail(self, device_sn):
        """
        Get detailed data for an SPH inverter.

        Args:
            device_sn (str): The serial number of the SPH inverter.

        Returns:
            dict: A dictionary containing the SPH inverter details.

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Sph(device_sn).detail()

    def sph_energy(self, device_sn):
        """
        Get energy data for an SPH inverter.

        Args:
            device_sn (str): The serial number of the SPH inverter.

        Returns:
            dict: A dictionary containing the SPH inverter energy data.

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Sph(device_sn).energy()

    def sph_energy_history(self, device_sn, start_date=None, end_date=None, timezone=None, page=None, limit=None):
        """
        Get SPH inverter data history.

        Args:
            device_sn (str): The ID of the SPH inverter.
            start_date (date, optional): Start date. Defaults to today.
            end_date (date, optional): End date. Defaults to today.
            timezone (str, optional): Timezone ID.
            page (int, optional): Page number.
            limit (int, optional): Results per page.

        Returns:
            dict: A dictionary containing the SPH inverter history data.

        Raises:
            GrowattParameterError: If date interval is invalid (exceeds 7 days).
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Sph(device_sn).energy_history(start_date, end_date, timezone, page, limit)

    def sph_read_parameter(self, device_sn, parameter_id=None, start_address=None, end_address=None):
        """
        Read setting from SPH inverter.

        Args:
            device_sn (str): The ID of the SPH inverter.
            parameter_id (str, optional): Parameter ID to read. Don't use start_address and end_address if this is set.
            start_address (int, optional): Register start address (for set_any_reg). Don't use parameter_id if this is set.
            end_address (int, optional): Register end address (for set_any_reg). Don't use parameter_id if this is set.

        Returns:
            dict: A dictionary containing the setting value.

        Raises:
            GrowattParameterError: If parameters are invalid.
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Sph(device_sn).read_parameter(parameter_id, start_address, end_address)

    def sph_write_parameter(self, device_sn, parameter_id, parameter_values=None):
        """
        Set parameters on an SPH inverter.

        Args:
            device_sn (str): Serial number of the inverter
            parameter_id (str): Setting type to be configured
            parameter_values: Parameter values to be sent to the system.
                Can be a single string (for param1 only),
                a list of strings (for sequential params),
                or a dictionary mapping param positions to values

        Returns:
            dict: JSON response from the server

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Sph(device_sn).write_parameter(parameter_id, parameter_values)

    def sph_write_ac_charge_times(self, device_sn, charge_power, charge_stop_soc, mains_enabled, periods):
        """
        Set AC charge time periods for an SPH inverter.

        Args:
            device_sn (str): The serial number of the inverter.
            charge_power (int): Charging power percentage (0-100).
            charge_stop_soc (int): Stop charging at this SOC percentage (0-100).
            mains_enabled (bool): Enable grid charging.
            periods (list): List of 3 period dicts, each with keys:
                - start_time (datetime.time): Start time for the period
                - end_time (datetime.time): End time for the period
                - enabled (bool): Whether this period is enabled

        Returns:
            dict: The server response.

        Example:
            from datetime import time

            api.sph_write_ac_charge_times(
                device_sn="ABC123",
                charge_power=100,
                charge_stop_soc=100,
                mains_enabled=True,
                periods=[
                    {"start_time": time(1, 0), "end_time": time(5, 0), "enabled": True},
                    {"start_time": time(0, 0), "end_time": time(0, 0), "enabled": False},
                    {"start_time": time(0, 0), "end_time": time(0, 0), "enabled": False},
                ]
            )

        Raises:
            GrowattParameterError: If parameters are invalid.
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Sph(device_sn).write_ac_charge_times(charge_power, charge_stop_soc, mains_enabled, periods)

    def sph_write_ac_discharge_times(self, device_sn, discharge_power, discharge_stop_soc, periods):
        """
        Set AC discharge time periods for an SPH inverter.

        Args:
            device_sn (str): The serial number of the inverter.
            discharge_power (int): Discharging power percentage (0-100).
            discharge_stop_soc (int): Stop discharging at this SOC percentage (0-100).
            periods (list): List of 3 period dicts, each with keys:
                - start_time (datetime.time): Start time for the period
                - end_time (datetime.time): End time for the period
                - enabled (bool): Whether this period is enabled

        Returns:
            dict: The server response.

        Example:
            from datetime import time

            api.sph_write_ac_discharge_times(
                device_sn="ABC123",
                discharge_power=100,
                discharge_stop_soc=10,
                periods=[
                    {"start_time": time(17, 0), "end_time": time(21, 0), "enabled": True},
                    {"start_time": time(0, 0), "end_time": time(0, 0), "enabled": False},
                    {"start_time": time(0, 0), "end_time": time(0, 0), "enabled": False},
                ]
            )

        Raises:
            GrowattParameterError: If parameters are invalid.
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Sph(device_sn).write_ac_discharge_times(discharge_power, discharge_stop_soc, periods)

    def sph_read_ac_charge_times(self, device_sn, settings_data=None):
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
            charge_config = api.sph_read_ac_charge_times(device_sn="DEVICE_SERIAL_NUMBER")
            print(f"Charge power: {charge_config['charge_power']}%")
            print(f"Periods: {charge_config['periods']}")

            # Option 2: Reuse existing settings data
            settings_response = api.sph_detail("DEVICE_SERIAL_NUMBER")
            charge_config = api.sph_read_ac_charge_times(device_sn="DEVICE_SERIAL_NUMBER", settings_data=settings_response)

        Raises:
            GrowattParameterError: If neither device_sn nor settings_data is provided.
            GrowattV1ApiError: If the API request fails.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Sph(device_sn).read_ac_charge_times(settings_data)

    def sph_read_ac_discharge_times(self, device_sn, settings_data=None):
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
            discharge_config = api.sph_read_ac_discharge_times(device_sn="DEVICE_SERIAL_NUMBER")
            print(f"Discharge power: {discharge_config['discharge_power']}%")
            print(f"Stop SOC: {discharge_config['discharge_stop_soc']}%")

            # Option 2: Reuse existing settings data
            settings_response = api.sph_detail("DEVICE_SERIAL_NUMBER")
            discharge_config = api.sph_read_ac_discharge_times(device_sn="DEVICE_SERIAL_NUMBER", settings_data=settings_response)

        Raises:
            GrowattParameterError: If neither device_sn nor settings_data is provided.
            GrowattV1ApiError: If the API request fails.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        return Sph(device_sn).read_ac_discharge_times(device_sn, settings_data)
