#!/usr/bin/env python3
"""growattServer package exports."""

from __future__ import annotations

from .base_api import GrowattApi, Timespan, hash_password
from .exceptions import (
    GrowattError,
    GrowattParameterError,
    GrowattV1ApiError,
    GrowattV1ApiErrorCode,
)
from .open_api_v1 import DeviceType, OpenApiV1

# Package name
name = "growattServer"

__all__ = [
    "DeviceType",
    "GrowattApi",
    "GrowattError",
    "GrowattParameterError",
    "GrowattV1ApiError",
    "GrowattV1ApiErrorCode",
    "OpenApiV1",
    "Timespan",
    "hash_password",
]


def __getattr__(name: str):
    """Lazy imports for async classes (requires httpx)."""
    if name == "AsyncGrowattApi":
        from .async_base_api import AsyncGrowattApi  # noqa: PLC0415

        return AsyncGrowattApi
    if name == "AsyncOpenApiV1":
        from .open_api_v1.async_open_api_v1 import AsyncOpenApiV1  # noqa: PLC0415

        return AsyncOpenApiV1
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
