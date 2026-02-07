"""SPH/MIX device file."""
from datetime import datetime, timedelta

from growattServer.exceptions import GrowattParameterError

from .abstract_device import AbstractDevice


class Sph(AbstractDevice):
    """SPH/MIX device type."""

    DEVICE_TYPE_ID = 5

    def detail(self):
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
        # API: https://www.showdoc.com.cn/262556420217021/6129763571291058
        response = self.session.get(
            self.get_url("device/mix/mix_data_info"),
            params={
                "device_sn": self.device_sn
            }
        )

        return self.process_response(response.json(), "getting SPH inverter details")

    def energy(self):
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
        # API: https://www.showdoc.com.cn/262556420217021/6129764475556048
        response = self.session.post(
            url=self.get_url("device/mix/mix_last_data"),
            data={
                "mix_sn": self.device_sn,
            },
        )

        return self.process_response(response.json(), "getting SPH inverter energy data")

    def energy_history(self, start_date=None, end_date=None, timezone=None, page=None, limit=None):
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
        if start_date is None and end_date is None:
            start_date = datetime.now(datetime.UTC).date()
            end_date = datetime.now(datetime.UTC).date()
        elif start_date is None:
            start_date = end_date
        elif end_date is None:
            end_date = start_date

        # check interval validity
        if end_date - start_date > timedelta(days=7):
            raise GrowattParameterError("date interval must not exceed 7 days")

        # API: https://www.showdoc.com.cn/262556420217021/6129765461123058
        response = self.session.post(
            url=self.get_url("device/mix/mix_data"),
            data={
                "mix_sn": self.device_sn,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "timezone_id": timezone,
                "page": page,
                "perpage": limit,
            }
        )

        return self.process_response(response.json(), "getting SPH inverter energy history")

    def read_parameter(self, parameter_id=None, start_address=None, end_address=None):
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
        if parameter_id is None and start_address is None:
            raise GrowattParameterError(
                "specify either parameter_id or start_address/end_address")
        if parameter_id is not None and start_address is not None:
            raise GrowattParameterError(
                "specify either parameter_id or start_address/end_address - not both."
            )
        if parameter_id is not None:
            # named parameter
            start_address = 0
            end_address = 0
        else:
            # address range
            parameter_id = "set_any_reg"

        # API: https://www.showdoc.com.cn/262556420217021/6129766954561259
        response = self.session.post(
            self.get_url("readMixParam"),
            data={
                "device_sn": self.device_sn,
                "paramId": parameter_id,
                "startAddr": start_address,
                "endAddr": end_address
            }
        )

        return self.process_response(response.json(), f"reading parameter {parameter_id}")

    def write_parameter(self, parameter_id, parameter_values=None):
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
        # Initialize all parameters as empty strings (API uses param1-param18)
        max_sph_params = 18
        parameters = dict.fromkeys(range(1, max_sph_params + 1), "")

        # Process parameter values based on type
        if parameter_values is not None:
            if isinstance(parameter_values, (str, int, float, bool)):
                # Single value goes to param1
                parameters[1] = str(parameter_values)
            elif isinstance(parameter_values, list):
                # List of values go to sequential params
                for i, value in enumerate(parameter_values, 1):
                    if i <= max_sph_params:  # Only use up to max_sph_params parameters
                        parameters[i] = str(value)
            elif isinstance(parameter_values, dict):
                # Dict maps param positions to values
                for pos_raw, value in parameter_values.items():
                    pos = int(pos_raw) if not isinstance(pos_raw, int) else pos_raw
                    if 1 <= pos <= max_sph_params:  # Validate parameter positions
                        parameters[pos] = str(value)

        # Create a data dictionary with ALL parameters explicitly included
        request_data = {
            "mix_sn": self.device_sn,
            "type": parameter_id
        }

        # Add all SPH parameters to the request
        for i in range(1, max_sph_params + 1):
            request_data[f"param{i}"] = str(parameters[i])

        # API: https://www.showdoc.com.cn/262556420217021/6129761750718760
        response = self.session.post(
            self.get_url("mixSet"),
            data=request_data
        )

        return self.process_response(response.json(), f"writing parameter {parameter_id}")

    def write_ac_charge_times(self, charge_power, charge_stop_soc, mains_enabled, periods):
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
        if not 0 <= charge_power <= 100: # noqa: PLR2004
            raise GrowattParameterError("charge_power must be between 0 and 100")

        if not 0 <= charge_stop_soc <= 100: # noqa: PLR2004
            raise GrowattParameterError("charge_stop_soc must be between 0 and 100")

        if len(periods) != 3: # noqa: PLR2004
            raise GrowattParameterError("periods must contain exactly 3 period definitions")

        # Build request data
        request_data = {
            "mix_sn": self.device_sn,
            "type": "mix_ac_charge_time_period",
            "param1": str(charge_power),
            "param2": str(charge_stop_soc),
            "param3": "1" if mains_enabled else "0",
        }

        # Add period parameters (param4-18)
        for i, period in enumerate(periods):
            base = i * 5 + 4
            request_data[f"param{base}"] = str(period["start_time"].hour)
            request_data[f"param{base + 1}"] = str(period["start_time"].minute)
            request_data[f"param{base + 2}"] = str(period["end_time"].hour)
            request_data[f"param{base + 3}"] = str(period["end_time"].minute)
            request_data[f"param{base + 4}"] = "1" if period["enabled"] else "0"

        # API: https://www.showdoc.com.cn/262556420217021/6129761750718760
        response = self.session.post(
            self.get_url("mixSet"),
            data=request_data
        )

        return self.process_response(response.json(), "writing AC charge time periods")

    def write_ac_discharge_times(self, discharge_power, discharge_stop_soc, periods):
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
        if not 0 <= discharge_power <= 100: # noqa: PLR2004
            raise GrowattParameterError("discharge_power must be between 0 and 100")

        if not 0 <= discharge_stop_soc <= 100: # noqa: PLR2004
            raise GrowattParameterError("discharge_stop_soc must be between 0 and 100")

        if len(periods) != 3: # noqa: PLR2004
            raise GrowattParameterError("periods must contain exactly 3 period definitions")

        # Build request data
        request_data = {
            "mix_sn": self.device_sn,
            "type": "mix_ac_discharge_time_period",
            "param1": str(discharge_power),
            "param2": str(discharge_stop_soc),
        }

        # Add period parameters (param3-17)
        for i, period in enumerate(periods):
            base = i * 5 + 3
            request_data[f"param{base}"] = str(period["start_time"].hour)
            request_data[f"param{base + 1}"] = str(period["start_time"].minute)
            request_data[f"param{base + 2}"] = str(period["end_time"].hour)
            request_data[f"param{base + 3}"] = str(period["end_time"].minute)
            request_data[f"param{base + 4}"] = "1" if period["enabled"] else "0"

        # API: https://www.showdoc.com.cn/262556420217021/6129761750718760
        response = self.session.post(
            self.get_url("mixSet"),
            data=request_data
        )

        return self.process_response(response.json(), "writing AC discharge time periods")

    def _parse_time_periods(self, settings_data, time_type):
        """
        Parse time periods from settings data.

        Internal helper method to extract and format time period data from SPH settings.

        Args:
            settings_data (dict): Settings data from sph_detail call.
            time_type (str): Either "Charge" or "Discharge" to specify which periods to parse.

        Returns:
            list: A list of dictionaries, each containing details for one time period:
                - period_id (int): The period number (1-3)
                - start_time (str): Start time in format "HH:MM"
                - end_time (str): End time in format "HH:MM"
                - enabled (bool): Whether the period is enabled

        """
        periods = []

        # Process each time period (1-3 for SPH)
        for i in range(1, 4):
            # Get raw time values
            start_time_raw = settings_data.get(f"forced{time_type}TimeStart{i}", "0:0")
            end_time_raw = settings_data.get(f"forced{time_type}TimeStop{i}", "0:0")
            enabled_raw = settings_data.get(f"forced{time_type}StopSwitch{i}", 0)

            # Handle 'null' string values
            if start_time_raw == "null" or not start_time_raw:
                start_time_raw = "0:0"
            if end_time_raw == "null" or not end_time_raw:
                end_time_raw = "0:0"

            # Format times with leading zeros (HH:MM)
            try:
                start_parts = start_time_raw.split(":")
                start_hour = int(start_parts[0])
                start_min = int(start_parts[1])
                start_time = f"{start_hour:02d}:{start_min:02d}"
            except (ValueError, IndexError):
                start_time = "00:00"

            try:
                end_parts = end_time_raw.split(":")
                end_hour = int(end_parts[0])
                end_min = int(end_parts[1])
                end_time = f"{end_hour:02d}:{end_min:02d}"
            except (ValueError, IndexError):
                end_time = "00:00"

            # Get the enabled status
            if enabled_raw == "null" or enabled_raw is None:
                enabled = False
            else:
                try:
                    enabled = int(enabled_raw) == 1
                except (ValueError, TypeError):
                    enabled = False

            period = {
                "period_id": i,
                "start_time": start_time,
                "end_time": end_time,
                "enabled": enabled
            }

            periods.append(period)

        return periods

    def read_ac_charge_times(self, settings_data=None):
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
        if settings_data is None:
            settings_data = self.detail()

        # Extract global charge settings
        charge_power = settings_data.get("chargePowerCommand", 0)
        charge_stop_soc = settings_data.get("wchargeSOCLowLimit", 100)
        mains_enabled_raw = settings_data.get("acChargeEnable", 0)

        # Handle null/empty values
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
            "periods": self._parse_time_periods(settings_data, "Charge")
        }

    def read_ac_discharge_times(self, settings_data=None):
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
        if settings_data is None:
            settings_data = self.detail()

        # Extract global discharge settings
        discharge_power = settings_data.get("disChargePowerCommand", 0)
        discharge_stop_soc = settings_data.get("wdisChargeSOCLowLimit", 10)

        # Handle null/empty values
        if discharge_power == "null" or discharge_power is None or discharge_power == "":
            discharge_power = 0
        if discharge_stop_soc == "null" or discharge_stop_soc is None or discharge_stop_soc == "":
            discharge_stop_soc = 10

        return {
            "discharge_power": int(discharge_power),
            "discharge_stop_soc": int(discharge_stop_soc),
            "periods": self._parse_time_periods(settings_data, "Discharge")
        }
