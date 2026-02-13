"""Min/TLX device file."""
from datetime import UTC, datetime, timedelta
from typing import Any

from growattServer.exceptions import GrowattParameterError

from .abstract_device import AbstractDevice


class Min(AbstractDevice):
    """Min/TLX device type."""

    DEVICE_TYPE_ID = 7

    def detail(self) -> dict:
        """
        Get detailed data for a MIN inverter.

        See the API doc: https://www.showdoc.com.cn/262556420217021/6129816412127075.

        Args:
            device_sn (str): The serial number of the MIN inverter.

        Returns:
            dict: A dictionary containing the MIN inverter details.

        Raises:
            GrowattV1ApiError: If the API returns an error response.
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        """
        response = self.api.session.get(
            self.api.get_url("device/tlx/tlx_data_info"),
            params={
                "device_sn": self.device_sn
            }
        )

        return self.api.process_response(response.json(), "getting MIN inverter details")

    def energy(self) -> dict:
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
        response = self.api.session.post(
            url=self.api.get_url("device/tlx/tlx_last_data"),
            data={
                "tlx_sn": self.device_sn,
            },
        )

        return self.api.process_response(response.json(), "getting MIN inverter energy data")

    def energy_history(self, start_date=None, end_date=None, timezone=None, page=None, limit=None) -> dict:
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
        if start_date is None and end_date is None:
            start_date = datetime.now(UTC).date()
            end_date = datetime.now(UTC).date()
        elif start_date is None:
            start_date = end_date
        elif end_date is None:
            end_date = start_date

        # check interval validity
        if end_date - start_date > timedelta(days=7):
            raise GrowattParameterError("date interval must not exceed 7 days")

        response = self.api.session.post(
            url=self.api.get_url("device/tlx/tlx_data"),
            data={
                "tlx_sn": self.device_sn,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "timezone_id": timezone,
                "page": page,
                "perpage": limit,
            }
        )

        return self.api.process_response(response.json(), "getting MIN inverter energy history")

    def settings(self) -> dict:
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
        response = self.api.session.get(
            self.api.get_url("device/tlx/tlx_set_info"),
            params={
                "device_sn": self.device_sn
            }
        )

        return self.api.process_response(response.json(), "getting MIN inverter settings")

    def read_parameter(self, parameter_id, start_address=None, end_address=None) -> dict:
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
        self.validate_read_parameter_input(parameter_id, start_address, end_address)

        if parameter_id is not None:
            # named parameter
            start_address = 0
            end_address = 0
        else:
            # using register-number mode
            parameter_id = "set_any_reg"
            if start_address is None:
                start_address = end_address
            if end_address is None:
                end_address = start_address

        response = self.api.session.post(
            self.api.get_url("readMinParam"),
            data={
                "device_sn": self.device_sn,
                "paramId": parameter_id,
                "startAddr": start_address,
                "endAddr": end_address,
            }
        )

        return self.api.process_response(response.json(), f"reading parameter {parameter_id}")

    def write_parameter(self, parameter_id, parameter_values=None) -> dict:
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
        # Initialize all parameters as empty strings
        max_min_params = 19
        parameters = dict.fromkeys(range(1, max_min_params + 1), "")

        # Process parameter values based on type
        if parameter_values is not None:
            if isinstance(parameter_values, (str, int, float, bool)):
                # Single value goes to param1
                parameters[1] = str(parameter_values)
            elif isinstance(parameter_values, list):
                # List of values go to sequential params
                for i, value in enumerate(parameter_values, 1):
                    if i <= max_min_params:  # Only use up to max_min_params parameters
                        parameters[i] = str(value)
            elif isinstance(parameter_values, dict):
                # Dict maps param positions to values
                for pos_raw, value in parameter_values.items():
                    pos = int(pos_raw) if not isinstance(pos_raw, int) else pos_raw
                    if 1 <= pos <= max_min_params:  # Validate parameter positions
                        parameters[pos] = str(value)

        # IMPORTANT: Create a data dictionary with ALL parameters explicitly included
        request_data = {
            "tlx_sn": self.device_sn,
            "type": parameter_id
        }

        # Add all MIN parameters to the request
        for i in range(1, max_min_params + 1):
            request_data[f"param{i}"] = str(parameters[i])

        # Send the request
        response = self.api.session.post(
            self.api.get_url("tlxSet"),
            data=request_data
        )

        return self.api.process_response(response.json(), f"writing parameter {parameter_id}")

    def write_time_segment(self, segment_id, batt_mode, start_time, end_time, enabled=True) -> dict:
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
        max_min_params = 19
        max_min_segments = 9
        max_batt_mode = 2

        if not 1 <= segment_id <= max_min_segments:
            msg = f"segment_id must be between 1 and {max_min_segments}"
            raise GrowattParameterError(msg)

        if not 0 <= batt_mode <= max_batt_mode:
            msg = f"batt_mode must be between 0 and {max_batt_mode}"
            raise GrowattParameterError(msg)

        # Initialize ALL 19 parameters as empty strings, not just the ones we need
        all_params = {
            "tlx_sn": self.device_sn,
            "type": f"time_segment{segment_id}"
        }

        # Add param1 through param19, setting the values we need
        all_params["param1"] = str(batt_mode)
        all_params["param2"] = str(start_time.hour)
        all_params["param3"] = str(start_time.minute)
        all_params["param4"] = str(end_time.hour)
        all_params["param5"] = str(end_time.minute)
        all_params["param6"] = "1" if enabled else "0"

        # Add empty strings for all unused parameters
        for i in range(7, max_min_params + 1):
            all_params[f"param{i}"] = ""

        # Send the request
        response = self.api.session.post(
            self.api.get_url("tlxSet"),
            data=all_params
        )

        return self.api.process_response(response.json(), f"writing time segment {segment_id}")

    def read_time_segments(self, settings_data=None) -> list[dict[str, Any]]:
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
        # Process the settings data
        if settings_data is None:
            # Fetch settings if not provided
            settings_data = self.settings()

        # Define mode names
        mode_names = {
            0: "Load First",
            1: "Battery First",
            2: "Grid First"
        }

        segments = []

        # Process each time segment
        for i in range(1, 10):  # Segments 1-9
            # Get raw time values
            start_time_raw = settings_data.get(f"forcedTimeStart{i}", "0:0")
            end_time_raw = settings_data.get(f"forcedTimeStop{i}", "0:0")

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

            # Get the mode value safely
            mode_raw = settings_data.get(f"time{i}Mode")
            if mode_raw == "null" or mode_raw is None:
                batt_mode = None
            else:
                try:
                    batt_mode = int(mode_raw)
                except (ValueError, TypeError):
                    batt_mode = None

            # Get the enabled status safely
            enabled_raw = settings_data.get(f"forcedStopSwitch{i}", 0)
            if enabled_raw == "null" or enabled_raw is None:
                enabled = False
            else:
                try:
                    enabled = int(enabled_raw) == 1
                except (ValueError, TypeError):
                    enabled = False

            segment = {
                "segment_id": i,
                "batt_mode": batt_mode,
                "mode_name": mode_names.get(batt_mode, "Unknown"),
                "start_time": start_time,
                "end_time": end_time,
                "enabled": enabled
            }

            segments.append(segment)

        return segments
