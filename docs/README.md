# Growatt Server Docs

Welcome to the docs for the [GrowattServer Python package](https://pypi.org/project/growattServer/)
Package to retrieve PV information from the growatt server.

This package uses the Growatt Cloud in order to retrieve information from your "Power Plant"/home, Inverters, Battery banks and more!
It can also be used to update Settings on your Plant, Inverters and Battery banks made by Growatt.

### Legacy API

This is the original way this package has started, at the time of writing it is still the most used.
Please refer to the docs for [ShinePhone/legacy](./shinephone.md) for it's usage and available methods.

### V1 API

This follows Growatt's OpenAPI V1.
Please refer to the docs for [OpenAPI V1](./openapiv1.md) for it's usage and available methods.

### Breaking Change: `requests` -> `httpx`

This version replaces the `requests` library with `httpx` for both sync and async HTTP.
If your code catches `requests.exceptions.RequestException`, update it to catch
`httpx.HTTPError` instead. See the [exceptions module](../growattServer/exceptions.py)
for details on exception handling.

### Sync/Async Support

The library supports both synchronous and asynchronous usage. Every API class has an async
counterpart — use whichever fits your application:

| Sync | Async |
|:-----|:------|
| `GrowattApi` | `AsyncGrowattApi` |
| `OpenApiV1` | `AsyncOpenApiV1` |

The async classes accept an optional `session` parameter (an `httpx.AsyncClient`) so you can
share a session across your application (useful in frameworks like Home Assistant).

For details on how the sync/async class hierarchy works internally, see
[Architecture: Sync/Async Design](./architecture.md).

## Examples

The `examples` directory contains example usage for the library. You are required to have the library installed to use them `pip install growattServer`. However, if you are contributing to the library and want to use the latest version from the git repository, simply create a symlink to the growattServer directory inside the `examples` directory.

## Disclaimer

The developers & maintainers of this library accept no responsibility for any damage, problems or issues that arise with your Growatt systems as a result of its use.

The library contains functions that allow you to modify the configuration of your plant & inverter which carries the ability to set values outside of normal operating parameters, therefore, settings should only be modified if you understand the consequences.

To the best of our knowledge only the `settings` functions perform modifications to your system and all other operations are read only. Regardless of the operation:

***The library is used entirely at your own risk.***