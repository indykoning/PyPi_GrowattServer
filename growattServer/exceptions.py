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

from __future__ import annotations

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
        super().__init__(f"{message}: [{error_code}] {error_msg}")
        self.error_code = error_code
        self.error_msg = error_msg


class GrowattRateLimitError(GrowattError):
    """
    Raised when Growatt refuses a login because the account is rate limited.

    Growatt signals this **in the response body**, not as an HTTP status: the
    request succeeds with HTTP 200 and the payload carries ``success: false``
    with ``msg: "507"``. That is the shape behind the
    ``ConfigEntryError: Growatt login failed: 507`` tracebacks in
    home-assistant/core#176831 and home-assistant/core#174789.

    A 507 has been observed to precede an approximately 24 hour lockout rather
    than a short cooldown, so this library never retries on its own: retrying
    immediately is what deepens the lockout. Callers get a distinct exception
    type so they can back off for hours instead of treating it like bad
    credentials or a malformed response.

    Follows the :class:`GrowattV1ApiError` shape so consumers can read the code
    off the exception rather than parsing a message.
    """

    def __init__(self, error_code: str, error_msg: str | None = None) -> None:
        """
        Initialize the GrowattRateLimitError.

        Args:
            error_code: The application-level code from the response body,
                e.g. ``"507"``.
            error_msg: Optional human-readable detail, when the body carries one.

        """
        message = f"Growatt refused the login as rate limited: [{error_code}]"
        if error_msg:
            message += f" {error_msg}"
        message += (
            ". A 507 has been observed to precede an approximately 24 hour "
            "account lockout rather than a short cooldown -- do not retry "
            "immediately."
        )
        super().__init__(message)
        self.error_code = error_code
        self.error_msg = error_msg
