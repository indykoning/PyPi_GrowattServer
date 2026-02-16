# OpenAPI V1 - Min/TLX Device (device type 7)

The Min device offers the following methods

| Method | Arguments | Description |
|:---|:---|:---|
| `device.energy()` | None | Get current energy data for a min inverter, including power and energy values. |
| `device.detail()` | None | Get detailed data for a min inverter. |
| `device.energy_history(start_date=None, end_date=None, timezone=None, page=None, limit=None)` | start_date: Date, end_date: Date, timezone: String, page: Int, limit: Int | Get energy history data for a min inverter (7-day max range). |
| `device.settings()` | None | Get all settings for a min inverter. |
| `device.read_parameter(parameter_id, start_address=None, end_address=None)` | parameter_id: String, start_address: Int, end_address: Int | Read a specific setting for a min inverter. see: [details](../min_tlx_settings.md) |
| `device.write_parameter(parameter_id, parameter_values)` | parameter_id: String, parameter_values: Dict/Array | Set parameters on a min inverter. Parameter values can be a single value, a list, or a dictionary. see: [details](../min_tlx_settings.md) |
| `device.write_time_segment(segment_id, batt_mode, start_time, end_time, enabled=True)` | segment_id: Int, batt_mode: Int <0=load priority, 1=battery priority, 2=grid priority>, start_time: datetime.time, end_time: datetime.time, enabled: Bool | Update a specific time segment for a min inverter. see: [details](../min_tlx_settings.md) |
| `device.read_time_segments(settings_data=None)` | settings_data: Dict | Read all time segments from a MIN inverter. Optionally pass settings_data to avoid redundant API calls. see: [details](../min_tlx_settings.md) |