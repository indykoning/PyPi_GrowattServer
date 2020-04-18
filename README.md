# Growatt Server
Package to retrieve PV information form the growatt server.

## Usage
```
import growattServer

api = growattServer.GrowattApi()
login_response = api.login(<username>, <password>)
#Get a list of growatt plants.
print(api.plant_list(login_response['userId']))
```
## Methods and Variables
### Methods
Any methods that may be useful.

`api.login(username, password)` Log into the growatt api. This must be done before making any request. after this you will be logged in. you will want to capture the response to get the `userId` variable.

`api.plant_list(user_id)` Get a list of plants registered to your account.

`api.plant_info(plant_id)` Get info for specified plant.

`api.plant_detail(plant_id, timespan<1=day, 2=month>, date)` Get details of a specific plant.

`api.inverter_list(plant_id)` Get a list of inverters in specified plant. (May be deprecated in the future, since it gets all devices. Use device_list instead)

`api.device_list(plant_id)` Get a list of devices in specified plant.

`api.inverter_data(inverter_id, date)` Get some basic data of a specific date for the inverter.

`api.inverter_detail(inverter_id)` Get detailed data on inverter.

`api.storage_detail(storage_id)` Get detailed data on storage (battery).

`api.storage_params(storage_id)` Get a ton of info on storage (More info, more convoluted).

`api.storage_energy_overview(plant_id, storage_id)` Get the information you see in the "Generation overview".

### Variables
Some variables you may want to set.

`api.server_url` The growatt server url, default: 'http://server.growatt.com/'
## Note
This is based on the endpoints used on the mobile app and could be changed without notice.
