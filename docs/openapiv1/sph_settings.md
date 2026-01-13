# SPH Inverter Settings

This is part of the [OpenAPI V1 doc](../openapiv1.md).

For SPH (hybrid inverter) systems, the public V1 API provides methods to read and write inverter settings. SPH inverters have different time period configurations compared to MIN inverters:

* **Read Parameter**
  * function: `api.sph_read_parameter`
  * parameters:
    * `device_sn`: The device serial number
    * `parameter_id`: Parameter ID to read (e.g., "discharge_power")
    * `start_address`, `end_address`: Optional, for reading registers by address

* **Write Parameter**
  * function: `api.sph_write_parameter`
  * parameters:
    * `device_sn`: The device serial number
    * `parameter_id`: Parameter ID to write (e.g., "ac_charge")
    * `parameter_values`: Value to set (single value, list, or dictionary)

* **AC Charge Time Periods**
  * function: `api.sph_write_ac_charge_times`
  * parameters:
    * `device_sn`: The device serial number
    * `charge_power`: Charging power percentage (0-100)
    * `charge_stop_soc`: Stop charging at this SOC percentage (0-100)
    * `mains_enabled`: Boolean to enable/disable grid charging
    * `periods`: List of 3 period dicts, each with:
      * `start_time`: datetime.time object for period start
      * `end_time`: datetime.time object for period end
      * `enabled`: Boolean to enable/disable period

* **AC Discharge Time Periods**
  * function: `api.sph_write_ac_discharge_times`
  * parameters:
    * `device_sn`: The device serial number
    * `discharge_power`: Discharge power percentage (0-100)
    * `discharge_stop_soc`: Stop discharging at this SOC percentage (0-100)
    * `periods`: List of 3 period dicts, each with:
      * `start_time`: datetime.time object for period start
      * `end_time`: datetime.time object for period end
      * `enabled`: Boolean to enable/disable period

* **Read AC Charge Time Periods**
  * function: `api.sph_read_ac_charge_times`
  * parameters:
    * `device_sn`: The device serial number
    * `settings_data`: Optional settings data to avoid redundant API calls

* **Read AC Discharge Time Periods**
  * function: `api.sph_read_ac_discharge_times`
  * parameters:
    * `device_sn`: The device serial number
    * `settings_data`: Optional settings data to avoid redundant API calls
