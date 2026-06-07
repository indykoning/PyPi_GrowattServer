"""Async OpenApi V1 extensions for Growatt API client."""

from __future__ import annotations

from typing import Any

import httpx

from growattServer.async_base_api import AsyncGrowattApi
from growattServer.exceptions import (
    GrowattApiConnectionError,
    GrowattApiError,
    GrowattApiStatusError,
    GrowattApiTimeoutError,
)

from . import _OpenApiV1Base
from .devices.async_min import AsyncMin
from .devices.async_sph import AsyncSph


class AsyncOpenApiV1(_OpenApiV1Base, AsyncGrowattApi):
    """
    Async extended Growatt API client with V1 API support.

    This class extends the base AsyncGrowattApi class with methods for MIN and SPH devices using
    the public V1 API described here: https://www.showdoc.com.cn/262556420217021/0.

    All methods inherited from ``_OpenApiV1Base`` work transparently in async
    context because they return ``self.v1_request(...)`` or a device method call,
    both of which yield coroutines when the underlying API is async.
    """

    _min_class = AsyncMin
    _sph_class = AsyncSph

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

    async def v1_request(self, method: str, endpoint: str, *, params: dict[str, Any] | None = None, data: dict[str, Any] | None = None, operation_name: str = "API operation") -> dict[str, Any]:
        """Make a V1 API request and process the response."""
        url = self.get_url(endpoint)
        try:
            response = await self.session.request(method, url, params=params, data=data)
        except httpx.TimeoutException as exc:
            msg = f"Request to {url} timed out"
            raise GrowattApiTimeoutError(msg) from exc
        except httpx.ConnectError as exc:
            msg = f"Failed to connect to {url}"
            raise GrowattApiConnectionError(msg) from exc
        except httpx.HTTPStatusError as exc:
            msg = f"HTTP {exc.response.status_code} error for {url}"
            raise GrowattApiStatusError(msg, exc.response.status_code) from exc
        except httpx.HTTPError as exc:
            msg = f"HTTP error during request to {url}: {exc}"
            raise GrowattApiError(msg) from exc
        return self.process_response(response.json(), operation_name)
