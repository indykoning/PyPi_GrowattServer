"""
Exception classes and error code constants for the growattServer library.

All transport and HTTP errors from the underlying HTTP library (httpx) are caught
and re-raised as :class:`GrowattApiError` subclasses so that consumers do not need
to depend on the transport library directly.

**Deprecation notice (v3.0):**
During the transition from ``requests`` to ``httpx``, if the ``requests`` package is
installed, :class:`GrowattApiError` also inherits from
``requests.exceptions.RequestException``.  This allows existing consumers that catch
``RequestException`` to continue working, but a deprecation warning will be emitted.
Consumers should migrate to catching :class:`GrowattApiError` (or its subclasses)
instead.  The ``requests`` compatibility base class will be removed in a future
major release.
"""

from __future__ import annotations

import warnings
from enum import IntEnum

# ---------------------------------------------------------------------------
# Deprecation compatibility: if ``requests`` is installed, GrowattApiError
# will also inherit from requests.exceptions.RequestException so that
# existing ``except RequestException`` blocks still work during the
# transition period.
# ---------------------------------------------------------------------------
_has_requests = False
try:
    from requests.exceptions import RequestException as _RequestsRequestException
    _has_requests = True
except ImportError:
    pass


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


# Build GrowattApiError with optional requests.RequestException base for
# backwards compatibility.  Using a tuple of bases lets us conditionally
# include the requests base only when the package is available.
_api_error_bases: tuple[type, ...] = (GrowattError,)
if _has_requests:
    _api_error_bases = (GrowattError, _RequestsRequestException)


class GrowattApiError(*_api_error_bases):  # type: ignore[misc]
    """
    Raised when an HTTP or network error occurs during an API request.

    This wraps transport-level errors (e.g. connection failures, timeouts,
    HTTP error responses) so that consumers can catch a single library
    exception instead of depending on the underlying HTTP library.

    During the deprecation period, this also inherits from
    ``requests.exceptions.RequestException`` (if ``requests`` is installed)
    for backwards compatibility.  A deprecation warning is emitted once to
    alert consumers to migrate to catching ``GrowattApiError`` directly.
    """

    _deprecation_warned = False

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Initialize and emit a one-time deprecation warning if requests is installed."""
        super().__init__(*args, **kwargs)
        if _has_requests and not GrowattApiError._deprecation_warned:
            GrowattApiError._deprecation_warned = True
            warnings.warn(
                "growattServer now raises GrowattApiError instead of "
                "requests.RequestException for HTTP/network errors. "
                "GrowattApiError currently inherits from RequestException "
                "for backwards compatibility, but this will be removed in a "
                "future major release. Please update your exception handlers "
                "to catch growattServer.GrowattApiError instead.",
                DeprecationWarning,
                stacklevel=2,
            )


class GrowattApiConnectionError(GrowattApiError):
    """Raised when a connection to the Growatt API cannot be established."""


class GrowattApiTimeoutError(GrowattApiError):
    """Raised when a request to the Growatt API times out."""


class GrowattApiStatusError(GrowattApiError):
    """Raised when the Growatt API returns an HTTP error status (4XX/5XX)."""

    def __init__(self, message: str, status_code: int) -> None:
        """
        Initialize the GrowattApiStatusError.

        Args:
            message: Human readable error message.
            status_code: HTTP status code from the response.

        """
        super().__init__(message)
        self.status_code = status_code


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


