import growattServer
import getpass
import pprint

"""
This script demonstrates how to interface with the configuration settings of a plant and its classic inverters.
It uses the `update_classic_inverter_setting` function to apply settings to a classic inverter.
"""
pp = pprint.PrettyPrinter(indent=4)

# Prompt user for username
username = input("Enter username:")

# Prompt user to input password
user_pass = getpass.getpass("Enter password:")

api = growattServer.GrowattApi(True, username)
login_response = api.login(username, user_pass)

plant_list = api.plant_list(login_response['user']['id'])

# Simple logic to just get the first inverter from the first plant
# Expand this using a for-loop to perform for more systems
plant = plant_list['data'][0]  # This is an array - we just take the first - would need a for-loop for more systems
plant_id = plant['plantId']
plant_name = plant['plantName']
plant_info = api.plant_info(plant_id)

devices = api.device_list(plant_id)
device = devices[0]  # This is an array - we just take the first - would need a for-loop for more systems
device_sn = device['deviceSn']
device_type = device['deviceType']

# Turn inverter on
print("Turning on inverter: %s" % (device_sn))

# Set up the default parameters
default_parameters = {
    "action": "inverterSet",
    "serialNum": device_sn,
}

parameters = {
    "paramId": "pv_on_off",
    "command_1": "0001", # 0001 to turn on, 0000 to turn off
    "command_2": "",  # Empty string for command_2 as not used
}
response = api.update_classic_inverter_setting(default_parameters, parameters)
print(response)