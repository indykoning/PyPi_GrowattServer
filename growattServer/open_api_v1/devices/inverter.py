"""Inverterdevice file."""
from datetime import UTC, datetime, timedelta

from growattServer.exceptions import GrowattParameterError

from .abstract_device import AbstractDevice


class Inverter(AbstractDevice):
    """Inverter device type."""

    DEVICE_TYPE_ID = 1

    def detail(self) -> dict:
        """
        Get detailed data for an inverter.

        Args:
            device_sn (str): The serial number of the inverter.

        Returns:
            dict: A dictionary containing the inverter details.

        Raises:
            GrowattV1ApiError: If the API returns an error response. Endpoint-specific error codes:
                10001 - System error
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        References:
            https://www.showdoc.com.cn/262556420217021/6118559963559236

        """
        response = self.api.session.get(
            self.api.get_url("device/inverter/inv_data_info"),
            params={
                "device_sn": self.device_sn
            }
        )

        return self.api.process_response(response.json(), "getting inverter details")

    def energy(self) -> dict:
        """
        Get energy data for a inverter.

        Args:
            device_sn (str): The serial number of the inverter.

        Returns:
            dict: A dictionary containing the inverter energy data.

        Raises:
            GrowattV1ApiError: If the API returns an error response. Endpoint-specific error codes:
                10001 - system error
                10005 - device does not exist
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        References:
            https://www.showdoc.com.cn/262556420217021/6118571427302257

        """
        response = self.api.session.get(
            url=self.api.get_url("device/inverter/last_new_data"),
            data={
                "device_sn": self.device_sn,
            },
        )

        return self.api.process_response(response.json(), "getting inverter energy data")

    def energy_history(self, start_date=None, end_date=None, timezone=None, page=None, limit=None) -> dict:
        """
        Get inverter data history.

        Args:
            device_sn (str): The ID of the inverter.
            start_date (date, optional): Start date. Defaults to today.
            end_date (date, optional): End date. Defaults to today.
            timezone (str, optional): Timezone ID.
            page (int, optional): Page number.
            limit (int, optional): Results per page.

        Returns:
            dict: A dictionary containing the inverter history data.

        Raises:
            GrowattParameterError: If date interval is invalid (exceeds 7 days).
            GrowattV1ApiError: If the API returns an error response. Endpoint-specific error codes:
                10001 - system error
                10002 - device serial number error
                10003 - date format error
                10004 - date interval exceeds seven days
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        References:
            https://www.showdoc.com.cn/262556420217021/6118823163304569

        """
        if start_date is None and end_date is None:
            start_date = datetime.now(tz=UTC).astimezone().date()
            end_date = datetime.now(tz=UTC).astimezone().date()
        elif start_date is None:
            start_date = end_date
        elif end_date is None:
            end_date = start_date

        # check interval validity
        if end_date - start_date > timedelta(days=7):
            raise GrowattParameterError("date interval must not exceed 7 days")

        response = self.api.session.get(
            url=self.api.get_url("device/inverter/data"),
            data={
                "device_sn": self.device_sn,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "timezone_id": timezone,
                "page": page,
                "perpage": limit,
            }
        )

        return self.api.process_response(response.json(), "getting inverter energy history")

    def read_parameter(self, parameter_id, start_address=None, end_address=None) -> dict:
        """
        Read setting from inverter.

        Args:
            parameter_id (str): Parameter ID to read. Don't use start_address and end_address if this is set.
            start_address (int, optional): Register start address (for set_any_reg). Don't use parameter_id if this is set.
            end_address (int, optional): Register end address (for set_any_reg). Don't use parameter_id if this is set.

        Returns:
            dict: A dictionary containing the setting value.

        Raises:
            GrowattParameterError: If parameters are invalid.
            GrowattV1ApiError: If the API returns an error response. Endpoint-specific error codes:
                10001 - Reading failed
                10002 - Device does not exist
                10003 - Device offline
                10004 - Collector serial number is empty
                10005 - Collector offline
                10006 - Collector type does not support reading Get function
                10007 - The collector version does not support the reading function
                10008 - The collector connects to the server error, please restart and try again
                10009 - The read setting parameter type does not exist
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        References:
            https://www.showdoc.com.cn/262556420217021/6119495760116670

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
            self.api.get_url("readInverterParam"),
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
        Set parameters on a inverter.

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
            GrowattV1ApiError: If the API returns an error response. Endpoint-specific error codes:
                10001 - system error
                10002 - inverter server error
                10003 - inverter offline
                10004 - collector serial number is empty
                10005 - collector offline
                10006 - set The parameter type does not exist
                10007 - the parameter value is empty
                10008 - the parameter value is not in the range
                10009 - the date and time format is wrong
            requests.exceptions.RequestException: If there is an issue with the HTTP request.

        References:
            https://www.showdoc.com.cn/262556420217021/6118532122241417

        """
        # Initialize all parameters as empty strings
        max_inv_params = 2
        parameters = dict.fromkeys(range(1, max_inv_params + 1), "")

        # Process parameter values based on type
        if parameter_values is not None:
            if isinstance(parameter_values, (str, int, float, bool)):
                # Single value goes to param1
                parameters[1] = str(parameter_values)
            elif isinstance(parameter_values, list):
                # List of values go to sequential params
                for i, value in enumerate(parameter_values, 1):
                    if i <= max_inv_params:  # Only use up to max_inv_params parameters
                        parameters[i] = str(value)
            elif isinstance(parameter_values, dict):
                # Dict maps param positions to values
                for pos_raw, value in parameter_values.items():
                    pos = int(pos_raw) if not isinstance(pos_raw, int) else pos_raw
                    if 1 <= pos <= max_inv_params:  # Validate parameter positions
                        parameters[pos] = str(value)

        # IMPORTANT: Create a data dictionary with ALL parameters explicitly included
        request_data = {
            "device_sn": self.device_sn,
            "paramId": parameter_id
        }

        # Add all Inverter parameters to the request
        for i in range(1, max_inv_params + 1):
            request_data[f"command_{i}"] = str(parameters[i])

        # Send the request
        response = self.api.session.post(
            self.api.get_url("inverterSet"),
            data=request_data
        )

        return self.api.process_response(response.json(), f"writing parameter {parameter_id}")
