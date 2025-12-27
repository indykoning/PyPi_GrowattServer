# Inverter Settings

This is part of the [ShinePhone/Legacy doc](../shinephone.md).

NOTE: The inverter settings function appears to only work with 'mix' and 'tlx' systems based on the API call that it makes being specific to those inverter types

The inverter settings function(s) allow you to change individual values on your inverter e.g. time, charging period etc.
From what has been reverse engineered from the api, each setting has a `setting_type` and a set of `parameters` that are relevant to it.

Known working settings & parameters are as follows (all parameter values are strings):

* **Time/Date**
  * type: `pf_sys_year`
  * params:
    * `param1`: datetime in format: `YYYY-MM-DD HH:MM:SS`
* **Hybrid inverter AC charge times**
  * function: `api.update_mix_inverter_setting`
  * setting type: `mix_ac_charge_time_period`
  * params:
    * `param1`: Charging power % (value between 0 and 100)
    * `param2`: Stop charging Statement of Charge % (value between 0 and 100)
    * `param3`: Allow AC charging (0 = Disabled, 1 = Enabled)
    * `param4`: Schedule 1 - Start time - Hour e.g. "01" (1am)
    * `param5`: Schedule 1 - Start time - Minute e.g. "00" (0 minutes)
    * `param6`: Schedule 1 - End time - Hour e.g. "02" (2am)
    * `param7`: Schedule 1 - End time - Minute e.g. "00" (0 minutes)
    * `param8`: Schedule 1 - Enabled/Disabled (0 = Disabled, 1 = Enabled)
    * `param9`: Schedule 2 - Start time - Hour e.g. "01" (1am)
    * `param10`: Schedule 2 - Start time - Minute e.g. "00" (0 minutes)
    * `param11`: Schedule 2 - End time - Hour e.g. "02" (2am)
    * `param12`: Schedule 2 - End time - Minute e.g. "00" (0 minutes)
    * `param13`: Schedule 2 - Enabled/Disabled (0 = Disabled, 1 = Enabled)
    * `param14`: Schedule 3 - Start time - Hour e.g. "01" (1am)
    * `param15`: Schedule 3 - Start time - Minute e.g. "00" (0 minutes)
    * `param16`: Schedule 3 - End time - Hour e.g. "02" (2am)
    * `param17`: Schedule 3 - End time - Minute e.g. "00" (0 minutes)
    * `param18`: Schedule 3 - Enabled/Disabled (0 = Disabled, 1 = Enabled)
* **AC-coupled inverter AC charge times**
  * function: `api.update_ac_inverter_setting`
  * setting type: `spa_ac_charge_time_period`
  * params:
    * `param1`: Charging power % (value between 0 and 100)
    * `param2`: Stop charging Statement of Charge % (value between 0 and 100)
    * `param3`: Schedule 1 - Start time - Hour e.g. "01" (1am)
    * `param4`: Schedule 1 - Start time - Minute e.g. "00" (0 minutes)
    * `param5`: Schedule 1 - End time - Hour e.g. "02" (2am)
    * `param6`: Schedule 1 - End time - Minute e.g. "00" (0 minutes)
    * `param7`: Schedule 1 - Enabled/Disabled (0 = Disabled, 1 = Enabled)
    * `param8`: Schedule 2 - Start time - Hour e.g. "01" (1am)
    * `param9`: Schedule 2 - Start time - Minute e.g. "00" (0 minutes)
    * `param10`: Schedule 2 - End time - Hour e.g. "02" (2am)
    * `param11`: Schedule 2 - End time - Minute e.g. "00" (0 minutes)
    * `param12`: Schedule 2 - Enabled/Disabled (0 = Disabled, 1 = Enabled)
    * `param13`: Schedule 3 - Start time - Hour e.g. "01" (1am)
    * `param14`: Schedule 3 - Start time - Minute e.g. "00" (0 minutes)
    * `param15`: Schedule 3 - End time - Hour e.g. "02" (2am)
    * `param16`: Schedule 3 - End time - Minute e.g. "00" (0 minutes)
    * `param17`: Schedule 3 - Enabled/Disabled (0 = Disabled, 1 = Enabled)
* **TLX inverter settings**
  * function: `api.update_tlx_inverter_setting`
  * type: `charge_power`
   *   param1: Charging power % (value between 0 and 100)
  * type: `charge_stop_soc`
   *   param1: Charge Stop SOC
  * type: `discharge_power`
   *   param1: Discharging power % (value between 0 and 100)
  * type: `on_grid_discharge_stop_soc`
   *   param1: On-grid discharge Stop SOC
  * type: `discharge_stop_soc`
   *   param1: Off-grid discharge Stop SOC
  * type: `ac_charge`
   *   param1: Allow AC (grid) charging (0 = Disabled, 1 = Enabled)
  * type: `pf_sys_year` 
   *   param1: datetime in format: `YYYY-MM-DD HH:MM:SS`
  * function: `api.update_tlx_inverter_time_segment`
   *   segment_id: The segment to update (1-9)
   *   batt_mode: Battery Mode for the segment: 0=Load First(Self-Consumption), 1=Battery First, 2=Grid First  
   *   start_time: timedate object with start time of segment with format HH:MM
   *   end_time: timedate object with end time of segment with format HH:MM
   *   enabled: time segment enabled, boolean: True (Enabled), False (Disabled)
* **Classic inverter settings**
  * function: `api.update_classic_inverter_setting`
  * description: Applies settings for specified system based on serial number. This function is only going to work for classic inverters.
  * params:
    * `param1`: First parameter (specific to the setting type)
    * `param2`: Second parameter (specific to the setting type)
    * Additional parameters can be passed as needed.

The four functions `update_tlx_inverter_setting`, `update_mix_inverter_setting`, `update_ac_inverter_setting`, and `update_inverter_setting` take either a dictionary or an array. If an array is passed it will automatically generate the `paramN` key based on array index since all params for settings seem to used the same numbering scheme.

Only the settings described above have been tested with `update_tlx_inverter_setting` and they all take only one single parameter. It is very likely that the function works with all settings returned by `tlx_get_enabled_settings`, but this has not been tested. A helper function `update_tlx_inverter_time_segment` is provided for the settings that require more than one parameter.

The `api.get_mix_inverter_settings` method can be used to get the current inverter settings for the specified serial number including charge/discharge schedule for hybrid systems.