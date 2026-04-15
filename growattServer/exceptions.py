"""
Exception classes and error code constants for the growattServer library.

Note that in addition to these custom exceptions, methods may also raise exceptions
from the underlying requests library (requests.exceptions.RequestException and its
subclasses) when network or HTTP errors occur. These are not wrapped and are passed
through directly to the caller.

Common requests exceptions to handle:
- requests.exceptions.HTTPError: For HTTP error responses (4XX, 5XX)
- requests.exceptions.ConnectionError: For network connection issues
- requests.exceptions.Timeout: For request timeouts
- requests.exceptions.RequestException: The base exception for all requests exceptions
"""

from enum import IntEnum


class GrowattV1ApiErrorCode(IntEnum):
    """
    Generic error codes returned by the Growatt V1 (OpenAPI) endpoints.

    These codes are common across all endpoints. Individual endpoints may also
    return additional endpoint-specific error codes — see the docstrings of the
    respective methods for details.

    Reference: https://www.showdoc.com.cn/262556420217021/1494055648380019
    """

    SUCCESS = 0  # Normal (General)
    NO_PRIVILEGE = 10011  # No privilege access (generic)
    RATE_LIMITED = 10012  # Access Frequency Limitation of 5 Minutes/Time (Universal)
    PAGE_SIZE_TOO_LARGE = (
        10013  # The number per page cannot be greater than 100 (general)
    )
    PAGE_COUNT_TOO_LARGE = (
        10014  # The number of pages cannot be greater than 250 pages (general)
    )
    WRONG_DOMAIN = -1  # Please use the new domain name to access


class GrowattError(Exception):
    """Base exception class for all Growatt API related errors."""


class GrowattParameterError(GrowattError):
    """Raised when invalid parameters are provided to API methods."""


class GrowattV1ApiError(GrowattError):
    """Raised when a Growatt V1 API request fails or returns an error."""

    def __init__(self, message: str, error_code: int, error_msg: str) -> None:
        """
        Initialize the GrowattV1ApiError.

        Args:
            message: Human readable error message.
            error_code: Numeric error code returned by the API.
                See :class:`GrowattV1ApiErrorCode` for known generic codes.
            error_msg: Error message returned by the API.

        """
        super().__init__(message)
        self.error_code = error_code
        self.error_msg = error_msg
