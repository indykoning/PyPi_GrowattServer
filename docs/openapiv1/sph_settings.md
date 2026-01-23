# SPH Inverter Settings

This is part of the [OpenAPI V1 doc](../openapiv1.md).

For SPH (hybrid inverter) systems, the public V1 API provides methods to read and write inverter settings.

**Source:** [Official Growatt API Documentation](https://www.showdoc.com.cn/262556420217021/6129763571291058)

## Read All Settings

* function: `api.sph_detail`
* parameters:
  * `device_sn`: The device serial number
* returns: Dict containing all device data and settings

**Return parameter description:**

| Field | Type | Description |
|-------|------|-------------|
| serialNum | String | Serial Number |
| portName | String | Communication port information Communication port type and address |
| dataLogSn | String | DataLog serial number |
| groupId | int | Inverter group |
| alias | String | Alias |
| location | String | Location |
| addr | int | Inverter address |
| fwVersion | String | Firmware version |
| model | long | Model |
| innerVersion | String | Internal version number |
| lost | boolean | Whether communication is lost |
| status | int | Mix Status 0: waiting mode, 1: self-check mode, 3: failure mode, 4: upgrading, 5, 6, 7, 8: normal mode |
| tcpServerIp | String | TCP server IP address |
| lastUpdateTime | Date | Last update time |
| sysTime | Calendar | System Time |
| deviceType | int | 0: Mix6k, 1: Mix4-10k |
| communicationVersion | String | Communication version number |
| onOff | int | Switch machine |
| pmax | int | Rated power |
| vnormal | float | Rated PV voltage |
| lcdLanguage | int | LCD language |
| countrySelected | int | Country selection |
| wselectBaudrate | int | Baud rate selection |
| comAddress | int | Mailing address |
| manufacturer | String | Manufacturer Code |
| dtc | int | Device code |
| modbusVersion | int | MODBUS version |
| floatChargeCurrentLimit | float | Float charge current limit |
| vbatWarning | float | Low battery voltage alarm point |
| vbatWarnClr | float | Low battery voltage recovery point |
| vbatStopForDischarge | float | Battery discharge stop voltage |
| vbatStopForCharge | float | Battery charging stop voltage |
| vbatStartForDischarge | float | Lower limit of battery discharge voltage |
| vbatStartforCharge | float | Battery charging upper limit voltage |
| batTempLowerLimitD | float | Lower limit of battery discharge temperature |
| batTempUpperLimitD | float | Upper limit of battery discharge temperature |
| batTempLowerLimitC | float | Lower limit of battery charging temperature |
| batTempUpperLimitC | float | Upper limit of battery charging temperature |
| forcedDischargeTimeStart1 | String | Discharge 1 start time |
| forcedDischargeTimeStart2 | String | Discharge 2 start time |
| forcedDischargeTimeStart3 | String | Discharge 3 start time |
| forcedDischargeTimeStop1 | String | Discharge 1 stop time |
| forcedDischargeTimeStop2 | String | Discharge 2 stop time |
| forcedDischargeTimeStop3 | String | Discharge 3 stop time |
| forcedChargeTimeStart1 | String | Charge 1 start time |
| forcedChargeTimeStart2 | String | Charge 2 start time |
| forcedChargeTimeStart3 | String | Charge 3 start time |
| forcedChargeTimeStop1 | String | Charge 1 stop time |
| forcedChargeTimeStop2 | String | Charge 2 stop time |
| forcedChargeTimeStop3 | String | Charge 3 stop time |
| bctMode | int | Sensor type (2:METER;1:cWirelessCT;0:cWiredCT) |
| bctAdjust | int | Sensor adjustment enable |
| wdisChargeSOCLowLimit1 | int | Discharge in load priority mode |
| wdisChargeSOCLowLimit2 | int | Grid priority mode discharge |
| wchargeSOCLowLimit1 | int | Load priority mode charging |
| wchargeSOCLowLimit2 | int | Battery priority mode charging |
| acChargeEnable | int | AC charging enable |
| priorityChoose | int | Energy priority selection |
| chargePowerCommand | int | Charging power setting |
| disChargePowerCommand | int | Discharge power setting |
| bagingTestStep | int | Battery self-test |
| batteryType | int | Battery type selection |
| epsFunEn | int | Emergency power enable |
| epsVoltSet | int | Emergency power supply voltage |
| epsFreqSet | int | Emergency power frequency |
| forcedDischargeStopSwitch1 | int | Discharge 1 enable bit |
| forcedDischargeStopSwitch2 | int | Discharge 2 enable bit |
| forcedDischargeStopSwitch3 | int | Discharge 3 enable bit |
| forcedChargeStopSwitch1 | int | Charge 1 enable bit |
| forcedChargeStopSwitch2 | int | Charge 2 enable bit |
| forcedChargeStopSwitch3 | int | Charge 3 enable bit |
| voltageHighLimit | float | Mains voltage upper limit |
| voltageLowLimit | float | Mains voltage lower limit |
| buckUpsFunEn | int | Off-grid enable |
| uspFreqSet | int | Off-grid frequency |
| buckUPSVoltSet | int | Off-grid voltage |
| pvPfCmdMemoryState | int | Does the inverter store the following commands |
| activeRate | int | Active power |
| reactiveRate | int | Reactive power |
| underExcited | int | Capacitive or Perceptual |
| exportLimit | int | Backflow prevention enable |
| exportLimitPowerRate | float | Backflow prevention |
| powerFactor | float | PF value |
| pv_on_off | String | Switch |
| pf_sys_year | String | Set time |
| pv_grid_voltage_high | String | Mains voltage upper limit |
| pv_grid_voltage_low | String | Mains voltage lower limit |
| mix_off_grid_enable | String | Off-grid enable |
| mix_ac_discharge_frequency | String | Off-grid frequency |
| mix_ac_discharge_voltage | String | Off-grid voltage |
| pv_pf_cmd_memory_state | String | Set whether to store the following PF commands |
| pv_active_p_rate | String | Set active power |
| pv_reactive_p_rate | String | Set reactive power |
| pv_reactive_p_rate_two | String | No power capacity/inductive |
| backflow_setting | String | Backflow prevention setting |
| pv_power_factor | String | Set PF value |
| batSeriesNum | int | Number of cells in series |
| batParallelNum | int | Number of parallel cells |
| error_code | string | 0: normal return, 10001: system error |
| error_msg | string | Error message prompt |

## Read Parameter

* function: `api.sph_read_parameter`
* parameters:
  * `device_sn`: The device serial number
  * `parameter_id`: Parameter ID to read (optional)
  * `start_address`, `end_address`: Optional, for reading registers by address

**Supported parameter types for reading:**

| parameter_id | Description | Return value |
|--------------|-------------|--------------|
| `pv_on_off` | Switch | 0 (off), 1 (on) |

## Write Parameter

* function: `api.sph_write_parameter`
* parameters:
  * `device_sn`: The device serial number
  * `parameter_id`: Parameter ID to write
  * `parameter_values`: Value to set (single value, list, or dictionary)

**Supported parameter types for writing:**

| parameter_id | Description | Values |
|--------------|-------------|--------|
| **Device Control** |||
| `pv_on_off` | Switch | "0" (off), "1" (on) |
| `pf_sys_year` | Set time | hour:min format |
| **Charge Settings** |||
| `mix_ac_charge_time_period` | Charge time periods | charge power, stop SOC, mains enable, time periods... |
| **Discharge Settings** |||
| `mix_ac_discharge_time_period` | Discharge time periods | discharge power, stop SOC, time periods... |
| **Grid Settings** |||
| `pv_grid_voltage_high` | Mains voltage upper limit | e.g. "270" |
| `pv_grid_voltage_low` | Mains voltage lower limit | e.g. "180" |
| `pv_active_p_rate` | Set active power | 0-100 |
| `pv_reactive_p_rate` | Set reactive power | value |
| `pv_reactive_p_rate_two` | No power capacity/inductive | value |
| `pv_pf_cmd_memory_state` | Set whether to store PF commands | "0" (no), "1" (yes) |
| `pv_power_factor` | Set PF value | 0-100 |
| `backflow_setting` | Backflow prevention setting | "1" (on), "0" (off), power % |
| **Off-Grid/EPS Settings** |||
| `mix_off_grid_enable` | Off-grid enable | "1" (enabled), "0" (disabled) |
| `mix_ac_discharge_frequency` | Off-grid frequency | "0" (50Hz), "1" (60Hz) |
| `mix_ac_discharge_voltage` | Off-grid voltage | "0" (230V), "1" (208V), "2" (240V) |

> **Note:** For time period settings, it's recommended to use the dedicated helper functions `sph_write_ac_charge_times()` and `sph_write_ac_discharge_times()` instead of calling `sph_write_parameter()` directly.

## AC Charge Time Periods

### Write: `api.sph_write_ac_charge_times`

* parameters:
  * `device_sn`: The device serial number
  * `charge_power`: Charging power percentage (0-100)
  * `charge_stop_soc`: Stop charging at this SOC percentage (0-100)
  * `mains_enabled`: Boolean to enable/disable grid charging
  * `periods`: List of 3 period dicts, each with:
    * `start_time`: datetime.time object for period start
    * `end_time`: datetime.time object for period end
    * `enabled`: Boolean to enable/disable period

### Read: `api.sph_read_ac_charge_times`

* parameters:
  * `device_sn`: The device serial number (not used if settings_data is provided)
  * `settings_data`: Settings data from sph_detail() (not used if device_sn is provided)
* note: Either `device_sn` or `settings_data` must be provided
* returns: Dict with `charge_power`, `charge_stop_soc`, `mains_enabled`, and `periods` list

## AC Discharge Time Periods

### Write: `api.sph_write_ac_discharge_times`

* parameters:
  * `device_sn`: The device serial number
  * `discharge_power`: Discharge power percentage (0-100)
  * `discharge_stop_soc`: Stop discharging at this SOC percentage (0-100)
  * `periods`: List of 3 period dicts, each with:
    * `start_time`: datetime.time object for period start
    * `end_time`: datetime.time object for period end
    * `enabled`: Boolean to enable/disable period

### Read: `api.sph_read_ac_discharge_times`

* parameters:
  * `device_sn`: The device serial number (not used if settings_data is provided)
  * `settings_data`: Settings data from sph_detail() (not used if device_sn is provided)
* note: Either `device_sn` or `settings_data` must be provided
* returns: Dict with `discharge_power`, `discharge_stop_soc`, and `periods` list
