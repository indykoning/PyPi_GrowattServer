# MIN/TLX Inverter Settings

This is part of the [OpenAPI V1 doc](../openapiv1.md).

For MIN/TLX systems, the public V1 API provides a more robust way to read and write inverter settings:

* **Read Parameter**
  * function: `api.min_read_parameter`
  * parameters:
    * `device_sn`: The device serial number
    * `parameter_id`: Parameter ID to read (e.g., "discharge_power")
    * `start_address`, `end_address`: Optional, for reading registers by address

* **Write Parameter**
  * function: `api.min_write_parameter`
  * parameters:
    * `device_sn`: The device serial number
    * `parameter_id`: Parameter ID to write (e.g., "ac_charge")
    * `parameter_values`: Value to set (single value, list, or dictionary)

* **Time Segments**
  * function: `api.min_write_time_segment`
  * parameters:
    * `device_sn`: The device serial number
    * `segment_id`: Segment number (1-9)
    * `batt_mode`: Battery mode (0=Load First, 1=Battery First, 2=Grid First)
    * `start_time`: Datetime.time object for segment start
    * `end_time`: Datetime.time object for segment end
    * `enabled`: Boolean to enable/disable segment

* **Read Time Segments**
  * function: `api.min_read_time_segments`
  * parameters:
    * `device_sn`: The device serial number
    * `settings_data`: Optional settings data to avoid redundant API calls