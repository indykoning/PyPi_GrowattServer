"""
Exception classes for the growattServer library.

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


class GrowattError(Exception):
    """Base exception class for all Growatt API related errors."""
    pass


class GrowattParameterError(GrowattError):
    """Raised when invalid parameters are provided to API methods."""
    pass


class GrowattV1ApiError(GrowattError):
    """Raised when a Growatt V1 API request fails or returns an error."""

    def __init__(self, message, error_code=None, error_msg=None):
        super().__init__(message)
        self.error_code = error_code
        self.error_msg = error_msg
