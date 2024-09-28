import growattServer
import datetime
import getpass
import json

"""
# Example script controlling a Growatt MID-30KTL3-XH + APX battery hybrid system by emulating the ShinePhone iOS app. 
# The same API calls are used by the ShinePhone Android app as well. Traffic intercepted using HTTP Toolkit. 
# 
# The plant / energy / device APIs seem to be generic for all Growatt systems, while the inverter and battery APIs use the TLX APIs.
#
# The available settings under the 'Control' tab in ShinePhone are created by combining the results from two function calls:
# tlx_get_all_settings() seem to returns the sum of all settings for all systems while tlx_get_enabled_settings() tells 
# which of these settings are valid for the TLX system.
# 
# Settings that takes a single parameter can be set using update_tlx_inverter_setting(). A helper function, update_tlx_inverter_time_segment()
# is provided for updating time segments which take several parameters. The inverter is picky and time intervals can't be overlapping,
# even if they are disabled. 
# 
# The set functions are commented out in the example, uncomment to test, and use at your own risk. Most likely all settings returned in 
# tlx_get_enabled_settings() can be set using update_tlx_inverter_setting(), but has not been tested.
#  
"""

#Prompt user for username
username=input("Enter username:")

#Prompt user to input password
user_pass=getpass.getpass("Enter password:")

user_agent = 'ShinePhone/8.1.17 (iPhone; iOS 15.6.1; Scale/2.00)'
api = growattServer.GrowattApi(agent_identifier=user_agent)

login_response = api.login(username, user_pass)
user_id = login_response['user']['id']
print("Login successful, user_id:", user_id)

# Plant info
plant_list = api.plant_list_two()
plant_id = plant_list[0]['id']
plant_info = api.plant_info(plant_id)
print("Plant info:", json.dumps(plant_info, indent=4, sort_keys=True))

# Energy data
energy_data = api.get_energy_data(plant_id)
print("Energy data", json.dumps(energy_data, indent=4, sort_keys=True))

# Devices
devices = api.get_all_devices(plant_id)
print("Devices:", json.dumps(devices, indent=4, sort_keys=True))

for device in devices['deviceList']:
    if device['deviceType'] == 'tlx':
        # Inverter info
        inverter_sn = device['deviceSn']
        inverter_info = api.tlx_params(inverter_sn)
        print("TLX inverter info:", json.dumps(inverter_info, indent=4, sort_keys=True))

        # Data
        data = api.tlx_data(inverter_sn, datetime.datetime.now())
        print("TLX data:", json.dumps(data, indent=4, sort_keys=True))

        # Settings
        all_settings = api.tlx_get_all_settings(inverter_sn)
        enabled_settings = api.tlx_get_enabled_settings(inverter_sn)
        enabled_keys = enabled_settings['enable'].keys()
        available_settings = {k: v for k, v in all_settings.items() if k in enabled_keys}
        print("Settings:", json.dumps(available_settings, indent=4, sort_keys=True))

    elif device['deviceType'] == 'bat':
        # Battery info
        batt_info = api.get_battery_info(device['deviceSn'])
        print("Battery info:", json.dumps(batt_info, indent=4, sort_keys=True))
        batt_info_detailed = api.get_battery_info_detailed(plant_id, device['deviceSn'])
        print("Battery info: detailed", json.dumps(batt_info_detailed, indent=4, sort_keys=True))


# Examples of updating settings, uncomment to use

# Set charging power to 95%
#res = api.update_tlx_inverter_setting(inverter_sn, 'charge_power', 96)
#print(res)

# Turn on AC charging
#res = api.update_tlx_inverter_setting(inverter_sn, 'ac_charge', 1)
#print(res)

# Enable Load First between 00:01 and 11:59 using time segment 1
#res = api.update_tlx_inverter_time_segment(serial_number = inverter_sn,
#                                           segment_id = 1,
#                                           batt_mode = growattServer.BATT_MODE_LOAD_FIRST,
#                                           start_time = datetime.time(00, 1),
#                                           end_time = datetime.time(11, 59),
#                                           enabled=True)
#print(res)