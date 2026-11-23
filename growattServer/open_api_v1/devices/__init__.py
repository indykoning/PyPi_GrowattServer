# noqa: D104
from __future__ import annotations

from .abstract_device import AbstractDevice, ParameterValue  # noqa: F401
from .min import Min  # noqa: F401
from .sph import Sph  # noqa: F401


def __getattr__(name: str):
    """Lazy imports for async device classes (requires httpx)."""
    if name == "AsyncMin":
        from .async_min import AsyncMin  # noqa: PLC0415

        return AsyncMin
    if name == "AsyncSph":
        from .async_sph import AsyncSph  # noqa: PLC0415

        return AsyncSph
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
