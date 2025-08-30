# Plant Settings

This is part of the [ShinePhone/Legacy doc](../shinephone.md).

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