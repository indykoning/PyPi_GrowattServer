# ShinePhone reverse engineered api (legacy)

This is where the project was born, when no consumer facing api was available. We reverse-engineered the ShinePhone app.

Currently Growatt does seem to support consumers using their [OpenApi](./openapiv1.md).
At the time of writing this "Legacy API" is still the most used method.

## Getting started

Using username/password basic authentication

```python
import growattServer

api = growattServer.GrowattApi()
login_response = api.login(<username>, <password>)
# Get a list of growatt plants.
print(api.plant_list(login_response['user']['id']))
```

## Methods and Variables

### Methods

Any methods that may be useful.

|method|arguments|description|
|:---|:---:|:---|
| `api.login(username, password)` | username: String, password: String | Log into the growatt API. This must be done beforemaking any request. After this you will be logged in. You will want to capture the response to get the `userId` variable. Should not be used for public v1 APIs. |
| `api.plant_list(user_id)` | user_id: String | Get a list of plants registered to your account. |
| `api.plant_info(plant_id)` | plant_id: String | Get info for specified plant. |
| `api.plant_settings(plant_id)` | plant_id: String | Get the current settings for the specified plant. see: [details](./shinephone/plant_settings.md) |
| `api.plant_detail(plant_id, timespan, date)` | plant_id: String, timespan: Int (1=day, 2=month), date: String | Get details of a specific plant. |
| `api.plant_energy_data(plant_id)` | plant_id: String | Get energy data for the specified plant. |
| `api.device_list(plant_id)` | plant_id: String | Get a list of devices in specified plant. |
| `api.dashboard_data(plant_id, timespan, date)` | plant_id: String, timespan: Int (0=hour, 1=day, 2=month), date: String | Get dashboard values for a timespan. NOTE: Many values are incorrect for 'Mix' systems but still provide some accurate data unavailable elsewhere. |
| `api.inverter_list(plant_id)` | plant_id: String | Get a list of inverters in specified plant. (May be deprecated in the future, use `device_list` instead). |
| `api.inverter_data(inverter_id, date)` | inverter_id: String, date: String | Get some basic data of a specific date for the inverter. |
| `api.inverter_detail(inverter_id)` | inverter_id: String | Get detailed data on inverter. |
| `api.tlx_system_status(plant_id, tlx_id)` | plant_id: String, tlx_id: String | Get system status. |
| `api.tlx_energy_overview(plant_id, tlx_id)` | plant_id: String, tlx_id: String | Get energy overview of the system. |
| `api.tlx_energy_prod_cons(plant_id, tlx_id)` | plant_id: String, tlx_id: String | Get energy production and consumption for the system. |
| `api.tlx_data(tlx_id, date)` | tlx_id: String, date: String | Get some basic data of a specific date for the tlx type inverter. |
| `api.tlx_detail(tlx_id)` | tlx_id: String | Get detailed data on a tlx type inverter. |
| `api.tlx_params(tlx_id)` | tlx_id: String | Get parameters for the tlx type inverter. |
| `api.tlx_get_all_settings(tlx_id)` | tlx_id: String | Get all possible settings for the tlx type inverter. |
| `api.tlx_get_enabled_settings(tlx_id)` | tlx_id: String | Get all enabled settings for the tlx type inverter. |
| `api.tlx_battery_info(serial_num)` | serial_num: String | Get battery info for tlx systems. |
| `api.tlx_battery_info_detailed(serial_num)` | serial_num: String | Get detailed battery info. |
| `api.mix_info(mix_id, plant_id=None)` | mix_id: String, plant_id: String (optional) | Get high-level information about the Mix system, including daily and overall totals. |
| `api.mix_totals(mix_id, plant_id)` | mix_id: String, plant_id: String | Get daily and overall total information for the Mix system (duplicates some of the information from `mix_info`). |
| `api.mix_system_status(mix_id, plant_id)` | mix_id: String, plant_id: String | Get instantaneous values for Mix system, e.g., current import/export, generation, charging rates, etc. |
| `api.mix_detail(mix_id, plant_id, timespan, date)` | mix_id: String, plant_id: String, timespan: Int <0=hour, 1=day, 2=month>, date: String | Get detailed values for a timespan. The API call also returns totals data for the same values in this time window. |
| `api.storage_detail(storage_id)` | storage_id: String | Get detailed data on storage (battery). |
| `api.storage_params(storage_id)` | storage_id: String | Get extensive information on storage (more info, more convoluted). |
| `api.storage_energy_overview(plant_id, storage_id)` | plant_id: String, storage_id: String | Get the information you see in the "Generation overview". |
| `api.is_plant_noah_system(plant_id)` | plant_id: String | Get information if Noah devices are configured for the specified plant. |
| `api.noah_system_status(serial_number)` | serial_number: String | Get the current status for the specified Noah device, e.g., workMode, soc, chargePower, disChargePower, current import/export, etc. |
| `api.noah_info(serial_number)` | serial_number: String | Get all information for the specified Noah device, e.g., configured operation modes, battery management settings, firmware version, etc. |
| `api.update_plant_settings(plant_id, changed_settings, current_settings)` | plant_id: String, changed_settings: Dict, current_settings: Dict (optional) | Update the settings for a plant to the values specified in the dictionary. If `current_settings` are not provided, it will look them up automatically using the `get_plant_settings` function. |
| `api.update_tlx_inverter_setting(serial_number, setting_type, parameter)` | serial_number: String, setting_type: String, parameter: Any | Apply the provided parameter for the specified setting on the specified tlx inverter. see: [details](./shinephone/inverter_settings.md) |
| `api.update_tlx_inverter_time_segment(serial_number, segment_id, batt_mode, start_time, end_time, enabled)` | serial_number: String, segment_id: Int, batt_mode: String, start_time: String, end_time: String, enabled: Bool | Update one of the 9 time segments with the specified battery mode (load, battery, grid first). see: [details](./shinephone/inverter_settings.md) |
| `api.update_mix_inverter_setting(serial_number, setting_type, parameters)` | serial_number: String, setting_type: String, parameters: Dict/Array | Apply the provided parameters for the specified setting on the specified Mix inverter. see: [details](./shinephone/inverter_settings.md) |
| `api.update_ac_inverter_setting(serial_number, setting_type, parameters)` | serial_number: String, setting_type: String, parameters: Dict/Array | Apply the provided parameters for the specified setting on the specified AC-coupled inverter. see: [details](./shinephone/inverter_settings.md) |
| `api.update_noah_settings(serial_number, setting_type, parameters)` | serial_number: String, setting_type: String, parameters: Dict/Array | Apply the provided parameters for the specified setting on the specified Noah device. see: [details](./shinephone/noah_settings.md) |
| `api.update_classic_inverter_setting(default_parameters, parameters)` | default_parameters: Dict, parameters: Dict/Array | Applies settings for specified system based on serial number. This function is only going to work for classic inverters. |

### Variables

Some variables you may want to set.

`api.server_url` The growatt server URL, default: 'https://openapi.growatt.com/'

You may need a different URL depending on where your account is registered:

'https://openapi-cn.growatt.com/' (Chinese server)
'https://openapi-us.growatt.com/' (North American server)
'https://openapi.growatt.com/' (Other regional server: e.g. Europe)

## Initialisation

The library can be initialised to introduce randomness into the User Agent field that is used when communicating with the servers.

This has been added since the Growatt servers started checking for the presence of a `User-Agent` field in the headers that are sent.

By default the library will use a pre-set `User-Agent` value which identifies this library while also appearing like an Android device. However, it is also possible to pass in parameters to the intialisation of the library to override this entirely, or just add a random ID to the value. e.g.

```python
api = growattServer.GrowattApi() # The default way to initialise

api = growattServer.GrowattApi(True) # Adds a randomly generated User ID to the default User-Agent

api = growattServer.GrowattApi(False, "my_user_agent_value") # Overrides the default and uses "my_user_agent_value" in the User-Agent header
```

## Note

This is based on the endpoints used on the mobile app and could be changed without notice.

## Settings Discovery

The settings for the Plant and Inverter have been reverse engineered by using the ShinePhone Android App and the NetCapture SSL application together to inspect the API calls that are made by the application and the parameters that are provided with it.

See: [Reverse Engineered](./shinephone/reverse_engineering.md)