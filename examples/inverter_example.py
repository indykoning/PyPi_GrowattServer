import json
import os

import requests

import growattServer

"""
# Example script controlling a classic Growatt inverter system using the public growatt API
# You can obtain an API token from the Growatt API documentation or developer portal.
"""

# Get the API token from environment variable or use test token
api_token = os.environ.get("GROWATT_API_TOKEN")
if not api_token:
    # test token from official API docs https://www.showdoc.com.cn/262556420217021/1494053950115877
    api_token = "6eb6f069523055a339d71e5b1f6c88cc"  # noqa: S105

try:
    # Initialize the API with token instead of using login
    api = growattServer.OpenApiV1(token=api_token)

    # Plant info
    plants = api.plant_list()
    print(f"Plants: Found {plants['count']} plants")
    plant_id = plants["plants"][0]["plant_id"]

    # Devices
    devices = api.device_list(plant_id)

    for device in devices["devices"]:
        if device["type"] == growattServer.DeviceType.INVERTER.value:
            inverter_sn = device["device_sn"]
            print(f"Processing inverter: {inverter_sn}")
            device_class = api.get_device(inverter_sn, device["type"])

            # Get device details
            inverter_data = device_class.detail()
            print("Saving inverter data to inverter_data.json")
            with open("inverter_data.json", "w") as f:
                json.dump(inverter_data, f, indent=4, sort_keys=True)

            # Get energy data
            energy_data = device_class.energy()
            print("Saving energy data to energy_data.json")
            with open("energy_data.json", "w") as f:
                json.dump(energy_data, f, indent=4, sort_keys=True)

            # Get energy history
            energy_history_data = device_class.energy_history()
            print("Saving energy history data to energy_history.json")
            with open("energy_history.json", "w") as f:
                json.dump(energy_history_data["datas"],
                          f, indent=4, sort_keys=True)

            # Read power rate
            active_p_rate = device_class.read_parameter("pv_active_p_rate")
            print("Current power rate:", active_p_rate, "%")

            # Settings parameters - Uncomment to test

            # Set active power rate
#            device_class.write_parameter('pv_active_p_rate', 100)
#            print("set active power rate to 100%")

except growattServer.GrowattV1ApiError as e:
    print(f"API Error: {e} (Code: {e.error_code}, Message: {e.error_msg})")
except growattServer.GrowattParameterError as e:
    print(f"Parameter Error: {e}")
except requests.exceptions.RequestException as e:
    print(f"Network Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
