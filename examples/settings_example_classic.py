import getpass
import pprint

import growattServer

"""
This script demonstrates how to interface with the configuration settings of a plant and its classic inverters.
It uses the `update_classic_inverter_setting` function to apply settings to a classic inverter.
It also demonstrates how to get the current inverter status using `classic_inverter_info`.
"""
pp = pprint.PrettyPrinter(indent=4)

# Prompt user for username
username = input("Enter username:")

# Prompt user to input password
user_pass = getpass.getpass("Enter password:")

api = growattServer.GrowattApi(True, username)
login_response = api.login(username, user_pass)

plant_list = api.plant_list(login_response["user"]["id"])

# Display available plants and let user choose
print("\n=== Available Plants ===")
plants = plant_list["data"]
for i, p in enumerate(plants, 1):
    print(f"{i}. {p['plantName']} (ID: {p['plantId']})")

while True:
    try:
        plant_choice = int(input(f"\nSelect a plant (1-{len(plants)}): "))
        if 1 <= plant_choice <= len(plants):
            plant = plants[plant_choice - 1]
            break
        else:
            print(f"Please enter a number between 1 and {len(plants)}")
    except ValueError:
        print("Please enter a valid number")

plant_id = plant["plantId"]
plant_name = plant["plantName"]
plant_info = api.plant_info(plant_id)

# Display available devices and let user choose
devices = api.device_list(plant_id)
print(f"\n=== Available Devices for '{plant_name}' ===")
for i, d in enumerate(devices, 1):
    print(f"{i}. {d.get('deviceName', 'N/A')} (SN: {d['deviceSn']}, Type: {d['deviceType']})")

while True:
    try:
        device_choice = int(input(f"\nSelect a device (1-{len(devices)}): "))
        if 1 <= device_choice <= len(devices):
            device = devices[device_choice - 1]
            break
        else:
            print(f"Please enter a number between 1 and {len(devices)}")
    except ValueError:
        print("Please enter a valid number")

device_sn = device["deviceSn"]
device_type = device["deviceType"]

# Get inverter info (includes on/off status, firmware version, model, etc.)
print(f"\nGetting info for inverter: {device_sn}")
inverter_info = api.classic_inverter_info(device_sn)
pp.pprint(inverter_info)

on_off = inverter_info["onOff"]
print(f"Inverter on/off status: {'on' if on_off == '1' else 'off'}")

# Turn inverter on using the convenience method
print(f"Turning on inverter: {device_sn}")
response = api.set_classic_inverter_on_off(device_sn, enabled=True)
print(response)

# Turn inverter off
print(f"Turning off inverter: {device_sn}")
response = api.set_classic_inverter_on_off(device_sn, enabled=False)
print(response)

# Set active power rate to 50% (limits output power to 50% of rated capacity)
print(f"Setting active power rate to 50% for inverter: {device_sn}")
response = api.set_classic_inverter_active_power_rate(device_sn, power_rate=50)
print(response)

# Set active power rate back to 100% (full power output)
print(f"Setting active power rate to 100% for inverter: {device_sn}")
response = api.set_classic_inverter_active_power_rate(device_sn, power_rate=100)
print(response)
