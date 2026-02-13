# OpenAPI V1 - SPH/MIX Device (device type 5)

The SPH device offers the following methods

| Method | Arguments | Description |
|:---|:---|:---|
| `device.detail()` | None | Get detailed data and settings for an SPH hybrid inverter. see: [details](../sph_settings.md) |
| `device.energy()` | None | Get current energy data for an SPH inverter, including power and energy values. |
| `device.energy_history(start_date=None, end_date=None, timezone=None, page=None, limit=None)` | start_date: Date, end_date: Date, timezone: String, page: Int, limit: Int | Get energy history data for an SPH inverter (7-day max range). |
| `device.read_parameter(parameter_id=None, start_address=None, end_address=None)` | parameter_id: String (optional), start_address: Int (optional), end_address: Int (optional) | Read a specific parameter (only pv_on_off supported). see: [details](../sph_settings.md) |
| `device.write_parameter(parameter_id, parameter_values)` | parameter_id: String, parameter_values: Dict/Array | Set parameters on an SPH inverter. see: [details](../sph_settings.md) |

#### SPH Helper Methods

Convenience methods that wrap the core SPH methods above for common use cases.

| Method | Arguments | Description |
|:---|:---|:---|
| `device.write_ac_charge_times(...)` | device_sn, charge_power, charge_stop_soc, mains_enabled, periods | Helper: wraps `sph_write_parameter()` with type `mix_ac_charge_time_period`. see: [details](../sph_settings.md) |
| `device.write_ac_discharge_times(...)` | device_sn, discharge_power, discharge_stop_soc, periods | Helper: wraps `sph_write_parameter()` with type `mix_ac_discharge_time_period`. see: [details](../sph_settings.md) |
| `device.read_ac_charge_times(...)` | device_sn (optional), settings_data (optional) | Helper: parses charge config from `sph_detail()` response. see: [details](../sph_settings.md) |
| `device.read_ac_discharge_times(...)` | device_sn (optional), settings_data (optional) | Helper: parses discharge config from `sph_detail()` response. see: [details](../sph_settings.md) |