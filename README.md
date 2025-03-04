# Growatt Server

Package to retrieve PV information from the growatt server.

Special thanks to [Sjoerd Langkemper](https://github.com/Sjord) who has provided a strong base to start off from https://github.com/Sjord/growatt_api_client
These projects may merge in the future since they are simmilar in code and function.

## Usage

```python
import growattServer

api = growattServer.GrowattApi()
login_response = api.login(<username>, <password>)
#Get a list of growatt plants.
print(api.plant_list(login_response['user']['id']))
```

## Methods and Variables

### Methods

Any methods that may be useful.

`api.login(username, password)` Log into the growatt API. This must be done before making any request. After this you will be logged in. You will want to capture the response to get the `userId` variable.

`api.plant_list(user_id)` Get a list of plants registered to your account.

`api.plant_info(plant_id)` Get info for specified plant.

`api.plant_settings(plant_id)` Get the current settings for the specified plant

`api.plant_detail(plant_id, timespan<1=day, 2=month>, date)` Get details of a specific plant.

`api.plant_energy_data(plant_id)` Get energy data for the specified plant.

`api.inverter_list(plant_id)` Get a list of inverters in specified plant. (Maybe deprecated in the future, since it gets all devices. Use `device_list` instead).

`api.device_list(plant_id)` Get a list of devices in specified plant.

`api.inverter_data(inverter_id, date)` Get some basic data of a specific date for the inverter.

`api.inverter_detail(inverter_id)` Get detailed data on inverter.

`api.tlx_system_status(plant_id, tlx_id)` Get system status.

`api.tlx_energy_overview(plant_id, tlx_id)` Get energy overview of the system.

`api.tlx_energy_prod_cons(plant_id, tlx_id)` Get energy production and consumption for the system.

`api.tlx_data(tlx_id, date)` Get some basic data of a specific date for the tlx type inverter.

`api.tlx_detail(tlx_id)` Get detailed data on a tlx type inverter.

`api.tlx_params(tlx_id)` Get parameters for the tlx type inverter.

`api.tlx_get_all_settings(tlx_id)` Get all possible settings for the tlx type inverter.

`api.tlx_get_enabled_settings(tlx_id)` Get all enabled settings for the tlx type inverter. 

`api.tlx_battery_info(serial_num)` Get battery info for tlx systems.

`api.tlx_battery_info_detailed(serial_num)` Get detailed battery info.

`api.mix_info(mix_id, plant_id=None)` Get high level information about the Mix system including daily and overall totals. NOTE: `plant_id` is an optional parameter, it does not appear to be used by the remote API, but is used by the mobile app these calls were reverse-engineered from.

`api.mix_totals(mix_id, plant_id)` Get daily and overall total information for the Mix system (duplicates some of the information from `mix_info`).

`api.mix_system_status(mix_id, plant_id)` Get instantaneous values for Mix system e.g. current import/export, generation, charging rates etc.

`api.mix_detail(mix_id, plant_id, timespan=<0=hour, 1=day, 2=month>, date)` Get detailed values for a timespan, the API call also returns totals data for the same values in this time window

`api.dashboard_data(plant_id, timespan=<0=hour, 1=day, 2=month>, date)` Get dashboard values for a timespan, the API call also returns totals data for the same values in this time window. NOTE: Many of the values on this API call are incorrect for 'Mix' systems, however it still provides some accurate values that are unavailable on other API calls.

`api.storage_detail(storage_id)` Get detailed data on storage (battery).

`api.storage_params(storage_id)` Get a ton of info on storage (More info, more convoluted).

`api.storage_energy_overview(plant_id, storage_id)` Get the information you see in the "Generation overview".

`api.is_plant_noah_system(plant_id)` Get the Information if noah devices are configured for the specified plant

`api.noah_system_status(serial_number)` Get the current status for the specified noah device e.g. workMode, soc, chargePower, disChargePower, current import/export etc.

`api.noah_info(serial_number)` Get all information for the specified noah device e.g. configured Operation Modes, configured Battery Management charging upper & lower limit, configured System Default Output Power, Firmware Version

`api.update_plant_settings(plant_id, changed_settings, current_settings)` Update the settings for a plant to the values specified in the dictionary, if the `current_settings` are not provided it will look them up automatically using the `get_plant_settings` function - See 'Plant settings' below for more information

`api.update_tlx_inverter_setting(serial_number, setting_type, parameter)` Applies the provided parameter for the specified setting on the specified tlx inverter; see 'Inverter settings' below for more information.

`api.update_tlx_inverter_time_segment(serial_number, segment_id, batt_mode, start_time, end_time, enabled)` Updates one of the 9 time segments with the specified battery mode (load, battery, grid first); see 'Inverter settings' below for more information.

`api.update_mix_inverter_setting(serial_number, setting_type, parameters)` Applies the provided parameters (dictionary or array) for the specified setting on the specified mix inverter; see 'Inverter settings' below for more information

`api.update_ac_inverter_setting(serial_number, setting_type, parameters)` Applies the provided parameters (dictionary or array) for the specified setting on the specified AC-coupled inverter; see 'Inverter settings' below for more information

`api.update_noah_settings(serial_number, setting_type, parameters)` Applies the provided parameters (dictionary or array) for the specified setting on the specified noah device; see 'Noah settings' below for more information

#### Power/Energy chart data

Methods returning power/energy metrics by time/day/month/year. Depending on your inverter, some endpoints might return invalid/inaccurate data.

* `api.dashboard_data(plant_id, timespan, date)`
  * power (pAC, pPV, (dis)charge) by time for single day
  * energy (eAC, (dis)charge) by day/month/year
* `api.plant_power_chart(plant_id, timespan, date)`
  * power (pAC) by time for single day
  * energy (eAC) by day/month/year
* `api.plant_energy_chart(timespan, date)`
  * energy (eAC) by day/month/year
* `api.plant_energy_chart_comparison(timespan, date)`
  * energy (eAC) by month/quarter - compare multiple years
* `api.inverter_energy_chart(plant_id, inverter_id, date, timespan)`
  * power (pAC, pPV1/2/3/4, vPV1/2/3/4, iPV1/2/3/4, vAC, iAC, fAC, Temp) by time for single day
  * energy (eAC, ePV1/2/3/4) by day/month/year
* `api.tlx_data(tlx_id, date, tlx_data_type)`
  * power (pAC, pPV) by time for single day
  * panel voltage/current by time for single day
* `api.tlx_energy_chart(tlx_id, date, timespan)`
  * energy (eAC) by day/month/year
* `api.tlx_energy_prod_cons(plant_id, tlx_id, timespan, date)`
  * power (pAC, pPV, (dis)charge) by time for single day
  * energy (eAC, (dis)charge) by day/month/year
* `api.mix_detail(mix_id, plant_id, timespan, date)`
  * power (pAC, pPV, (dis)charge) by time for single day
  * energy (eAC, (dis)charge) by day/month/year

### Variables

Some variables you may want to set.

`api.server_url` The growatt server URL, default: 'https://openapi.growatt.com/'

You may need a different URL depending on where your account is registered:

'https://openapi-cn.growatt.com/' (Chinese server)
'https://openapi-us.growatt.com/' (North American server)
'https://openapi.growatt.com/' (Other regional server: e.g. Europe)

## Note

This is based on the endpoints used on the mobile app and could be changed without notice.

## Initialisation

The library can be initialised to introduce randomness into the User Agent field that is used when communicating with the servers.

This has been added since the Growatt servers started checking for the presence of a `User-Agent` field in the headers that are sent.

By default the library will use a pre-set `User-Agent` value which identifies this library while also appearing like an Android device. However, it is also possible to pass in parameters to the intialisation of the library to override this entirely, or just add a random ID to the value. e.g.

```python
api = growattServer.GrowattApi() # The default way to initialise

api = growattServer.GrowattApi(True) # Adds a randomly generated User ID to the default User-Agent

api = growattServer.GrowattApi(False, "my_user_agent_value") # Overrides the default and uses "my_user_agent_value" in the User-Agent header
```

Please see the `user_agent_options.py` example in the `examples` directory if you wish to investigate further.

## Examples

The `examples` directory contains example usage for the library. You are required to have the library installed to use them `pip install growattServer`. However, if you are contributing to the library and want to use the latest version from the git repository, simply create a symlink to the growattServer directory inside the `examples` directory.

## Plant Settings

The plant settings function(s) allow you to re-configure the settings for a specified plant. The following settings are required (and are therefore pre-populated based on the existing values for these settings)
* `plantCoal` - The formula used to calculate equivalent coal usage
* `plantSo2` - The formula used to calculate So2 generation/saving
* `accountName` - The username that the system is assigned to
* `plantID` - The ID of the plant
* `plantFirm` - The 'firm' of the plant (unknown what this relates to - hardcoded to '0')
* `plantCountry` - The Country that the plant resides in
* `plantType` - The 'type' of plant (numerical value - mapped to an Enum)
* `plantIncome` - The formula used to calculate money per kwh
* `plantAddress` - The address of the plant
* `plantTimezone` - The timezone of the plant (relative to UTC)
* `plantLng` - The longitude of the plant's location
* `plantCity` - The city that the plant is located in
* `plantCo2` - The formula used to calculate Co2 saving/reduction
* `plantMoney` - The local currency e.g. gbp
* `plantPower` - The capacity/size of the plant in W e.g. 6400 (6.4kw)
* `plantLat` - The latitude of the plant's location
* `plantDate` - The date that the plant was installed
* `plantName` - The name of the plant

The function `update_plant_settings` allows you to provide a python dictionary of any/all of the above settings and change their value.

## Inverter Settings
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

The four functions `update_tlx_inverter_setting`, `update_mix_inverter_setting`, `update_ac_inverter_setting`, and `update_inverter_setting` take either a dictionary or an array. If an array is passed it will automatically generate the `paramN` key based on array index since all params for settings seem to used the same numbering scheme.

Only the settings described above have been tested with `update_tlx_inverter_setting` and they all take only one single parameter. It is very likely that the function works with all settings returned by `tlx_get_enabled_settings`, but this has not been tested. A helper function `update_tlx_inverter_time_segment` is provided for the settings that require more than one parameter.

## Noah Settings
The noah settings function allow you to change individual values on your noah system e.g. system default output power, battery management, operation mode and currency
From what has been reverse engineered from the api, each setting has a `setting_type` and a set of `parameters` that are relevant to it.

Known working settings & parameters are as follows (all parameter values are strings):
* **Change "System Default Output Power"**
  * function: `api.update_noah_settings`
  * setting type: `default_power`
  * params:
    * `param1`: System default output power in watt
* **Change "Battery Management"**
  * function: `api.update_noah_settings`
  * setting type: `charging_soc`
  * params:
    * `param1`: Charge upper limit in %
    * `param2`: Charge lower limit in %
* **Change "Operation Mode" Time Segment**
  * function: `api.update_noah_settings`
  * setting type: `time_segment` key from `api.noah_info(serial_number)`, for new `time_segment` count the ending number up
  * params:
    * `param1`: Workingmode (0 = Load First, 1 = Battery First)
    * `param2`: Start time - Hour e.g. "01" (1am)
    * `param3`: Start time - Minute e.g. "00" (0 minutes)
    * `param4`: End time - Hour e.g. "02" (2am)
    * `param5`: End time - Minute e.g. "00" (0 minutes)
    * `param6`: Output power in watt (For Workingmode "Battery First" always "0")
    * `param7`: Enabled/Disabled (0 = Disabled, 1 = Enabled)
* **Change "Currency"**
  * function: `api.update_noah_settings`
  * setting type: `updatePlantMoney`
  * params:
    * `param1`: Plant Id
    * `param2`: Cost per kWh e.g. "0.22"
    * `param3`: Unit value from `api.noah_info(serial_number)` - `unitList`

## Settings Discovery

The settings for the Plant and Inverter have been reverse engineered by using the ShinePhone Android App and the NetCapture SSL application together to inspect the API calls that are made by the application and the parameters that are provided with it.

## Disclaimer

The developers & maintainers of this library accept no responsibility for any damage, problems or issues that arise with your Growatt systems as a result of its use.

The library contains functions that allow you to modify the configuration of your plant & inverter which carries the ability to set values outside of normal operating parameters, therefore, settings should only be modified if you understand the consequences.

To the best of our knowledge only the `settings` functions perform modifications to your system and all other operations are read only. Regardless of the operation:

***The library is used entirely at your own risk.***
