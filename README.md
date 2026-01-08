# Growatt Server
[![Version](https://img.shields.io/pypi/v/GrowattServer?style=flat-square)
](https://pypi.org/project/growattServer/)
[![Total Downloads](https://img.shields.io/pepy/dt/GrowattServer?style=flat-square)](https://pypi.org/project/growattServer/)

Package to retrieve PV information from the growatt server.

Special thanks to [Sjoerd Langkemper](https://github.com/Sjord) who has provided a strong base to start off from https://github.com/Sjord/growatt_api_client
That project has since ben archived.

This library now supports both the legacy password-based authentication and the V1 API with token-based authentication for MIN and SPH systems. MIN devices (type 7) correspond to MIN/MID series inverters, while SPH devices (type 5) are hybrid inverters. The V1 API is officially supported by Growatt and recommended over legacy authentication. Certain endpoints are not supported anymore by openapi.growatt.com. For example `api.min_write_parameter()` should be used instead of old `api.update_tlx_inverter_setting()`.

## Usage

### Legacy API

Please refer to the [docs](./docs/README.md) for [ShinePhone/legacy](./docs/shinephone.md) for it's usage and available methods.

### V1 API

Please refer to the [docs](./docs/README.md) for [OpenAPI V1](./docs/openapiv1.md) for it's usage and available methods.

## Examples

The `examples` directory contains example usage for the library. You are required to have the library installed to use them `pip install growattServer`. However, if you are contributing to the library and want to use the latest version from the git repository, simply create a symlink to the growattServer directory inside the `examples` directory.

## Disclaimer

The developers & maintainers of this library accept no responsibility for any damage, problems or issues that arise with your Growatt systems as a result of its use.

The library contains functions that allow you to modify the configuration of your plant & inverter which carries the ability to set values outside of normal operating parameters, therefore, settings should only be modified if you understand the consequences.

To the best of our knowledge only the `settings` functions perform modifications to your system and all other operations are read only. Regardless of the operation:

***The library is used entirely at your own risk.***