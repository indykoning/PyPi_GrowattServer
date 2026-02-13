# OpenAPI V1 - Devices

Devices offer a generic way to interact with your device using the V1 API without needing to provide your S/N every time. And can be used instead of the more specific device functions in the API class.

```python
import growattServer
from growattServer.open_api_v1.devices import Sph, Min

api = growattServer.OpenApiV1(token="YOUR_API_TOKEN")

device = Sph(api, 'YOUR_DEVICE_SERIAL_NUMBER') # or Min(api, 'YOUR_DEVICE_SERIAL_NUMBER')
device.detail()
device.energy()
device.energy_history()
device.read_parameter()
device.write_parameter()
```

If you do not know your devices type, but do have their type id this method will provide you with the correct device class to use

```
import growattServer

api = growattServer.OpenApiV1(token="YOUR_API_TOKEN")
device = api.get_device(device_sn, device_type)
if device is not None:
    device.detail()
    device.energy()
    device.energy_history()
    device.read_parameter()
    device.write_parameter()
```

The basic methods are described here

| Method | Arguments | Description |
|:---|:---|:---|
| `device.energy()` | None | Get current energy data for any inverter, including power and energy values. |
| `device.detail()` | None | Get detailed data for any inverter. |
| `device.energy_history(start_date=None, end_date=None, timezone=None, page=None, limit=None)` | start_date: Date, end_date: Date, timezone: String, page: Int, limit: Int | Get energy history data for any inverter (7-day max range). |
| `device.read_parameter(parameter_id, start_address=None, end_address=None)` | parameter_id: String, start_address: Int, end_address: Int | Read a specific setting for any inverter. |
| `device.write_parameter(parameter_id, parameter_values)` | parameter_id: String, parameter_values: Dict/Array | Set parameters on any inverter. Parameter values can be a single value, a list, or a dictionary. |

However some device classes harbor more methods, which will be described in their respective readmes:
- [SPH/MIX](./devices/sph.md)
- [Min/TLX](./devices/min.md)