# Architecture: Sync/Async Design

The Growatt server has two separate APIs:

1. **Legacy API** (ShinePhone mobile app endpoints) — `plant_list`, `inverter_data`, `mix_info`, etc.
2. **V1 API** (OpenAPI) — `plant/list`, `plant/details`, `device/min/detail`, etc.

Different base URLs, different auth, different response formats. That's why there are two layers.

## Layer 1: Legacy API

```
_GrowattApiBase          — 45 methods that define WHAT to call
                           e.g. plant_list() returns self._request("GET", .../PlantListAPI.do)
                           No HTTP code here. Just URLs, params, and extract logic.

GrowattApi               — HOW to make the HTTP call (sync)
                           _request() uses httpx.Client
                           3 overrides: login, device_list, update_plant_settings

AsyncGrowattApi          — HOW to make the HTTP call (async)
                           _request() uses await httpx.AsyncClient
                           Same 3 overrides, with await
```

The 3 overrides exist in both `GrowattApi` and `AsyncGrowattApi` because those methods need to
do multiple HTTP calls in sequence — they can't use the simple `_request` helper.

## Layer 2: V1 API

```
_OpenApiV1Base           — 27 methods that define WHAT to call on the V1 API
                           e.g. plant_list() returns self.v1_request("GET", "plant/list")
                           Also overrides get_url() to point at the V1 base URL.

OpenApiV1                — inherits from BOTH _OpenApiV1Base AND GrowattApi
                           v1_request() uses httpx.Client (sync)

AsyncOpenApiV1           — inherits from BOTH _OpenApiV1Base AND AsyncGrowattApi
                           v1_request() uses await httpx.AsyncClient (async)
```

So `OpenApiV1` gets the 43 legacy methods from `GrowattApi` *plus* the 27 V1 methods
from `_OpenApiV1Base`. Same for the async variant.

## Device Classes

```
AbstractDevice           — Base class with device_sn and validation helpers

Min / Sph                — Device-specific methods (detail, energy, settings, etc.)
                           Use self.api.v1_request() which returns a coroutine
                           in async context (passthrough pattern)

AsyncMin / AsyncSph      — Only override methods that chain async calls:
                           AsyncMin:  read_time_segments
                           AsyncSph:  read_ac_charge_times, read_ac_discharge_times
```

## How It Works: Coroutine Passthrough

The key insight is that a regular `def` method can return a coroutine
without awaiting it. The caller (user code) is responsible for awaiting.

```python
# In the base class (regular def, NOT async def):
class _OpenApiV1Base:
    def plant_details(self, plant_id):
        return self.v1_request("GET", "plant/details", ...)

# Sync subclass:
class OpenApiV1(_OpenApiV1Base, GrowattApi):
    def v1_request(self, ...):           # returns dict
        response = self.session.request(...)
        return self.process_response(response.json(), ...)

# Async subclass:
class AsyncOpenApiV1(_OpenApiV1Base, AsyncGrowattApi):
    async def v1_request(self, ...):     # returns coroutine
        response = await self.session.request(...)
        return self.process_response(response.json(), ...)
```

When user code calls `api.plant_details(123)`:
- **Sync**: `v1_request()` executes, returns `dict` -> `plant_details()` returns `dict`
- **Async**: `v1_request()` is `async def`, calling it returns a `coroutine`
  -> `plant_details()` returns that `coroutine` -> user does `await api.plant_details(123)`

This eliminates the need to duplicate every method as both `def` and `async def`.

## When Passthrough Doesn't Work

Methods that **chain** async calls cannot use passthrough because they
need to process an intermediate result:

```python
# This CANNOT be shared -- self.detail() returns a coroutine in async context,
# and you can't call _parse_ac_charge_settings() on a coroutine.
def read_ac_charge_times(self, settings_data=None):
    if settings_data is None:
        settings_data = self.detail()       # coroutine in async!
    return self._parse_ac_charge_settings(settings_data)
```

These methods need explicit `async def` overrides:

```python
class AsyncSph(Sph):
    async def read_ac_charge_times(self, settings_data=None):
        if settings_data is None:
            settings_data = await self.detail()  # await the coroutine
        return self._parse_ac_charge_settings(settings_data)
```

### Methods Requiring Async Overrides

| Layer | Class | Method | Reason |
|:------|:------|:-------|:-------|
| Base API | `AsyncGrowattApi` | `login` | Post-processes response dict |
| Base API | `AsyncGrowattApi` | `device_list` | Chains `plant_info()` then `_get_all_devices()` |
| Base API | `AsyncGrowattApi` | `update_plant_settings` | Conditionally calls `plant_settings()` |
| Device | `AsyncMin` | `read_time_segments` | Conditionally calls `self.settings()` |
| Device | `AsyncSph` | `read_ac_charge_times` | Conditionally calls `self.detail()` |
| Device | `AsyncSph` | `read_ac_discharge_times` | Conditionally calls `self.detail()` |

All other methods (~60) are shared via base classes with zero duplication.

## Usage

```python
# Sync
from growattServer import OpenApiV1

api = OpenApiV1(token="...")
plants = api.plant_list()

# Async
from growattServer import AsyncOpenApiV1

async def main():
    async with AsyncOpenApiV1(token="...", session=my_httpx_client) as api:
        plants = await api.plant_list()
```
