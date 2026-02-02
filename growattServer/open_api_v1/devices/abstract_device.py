"""Abstract device file for centralising shared device logic."""
from typing import TypedDict

from growattServer.exceptions import GrowattParameterError
from growattServer.open_api_v1 import OpenApiV1


class ReadParamResponse(TypedDict):
    """Response type for ReadParam endpoints."""

    data: str
    error_code: str
    error_msg: str

class AbstactDevice:
    """Abstract device type. Must not be used directly."""

    def __init__(self, api: OpenApiV1, device_sn: str) -> None:
        """
        Initialize the device with the bare minimum being the device_sn.

        Args:
            api (OpenApiV1): API used for all API calls.
            device_sn (str): Device serial number used for all API calls.

        """
        self.api = api
        self.device_sn = device_sn

    def validate_read_parameter_input(self, parameter_id: str | None, start_address: int | None, end_address: int | None): # noqa: ARG002
        """
        Validate read parameter input and throws an error if it is invalid.

        Args:
            parameter_id (str): Parameter ID to read. Don't use start_address and end_address if this is set.
            start_address (int, optional): Register start address (for set_any_reg). Don't use parameter_id if this is set.
            end_address (int, optional): Register end address (for set_any_reg). Don't use parameter_id if this is set.

        Raises:
            GrowattParameterError: If parameters are invalid.

        """
        if parameter_id is None and start_address is None:
            raise GrowattParameterError(
                "specify either parameter_id or start_address/end_address")
        if parameter_id is not None and start_address is not None:
            raise GrowattParameterError(
                "specify either parameter_id or start_address/end_address - not both."
            )
