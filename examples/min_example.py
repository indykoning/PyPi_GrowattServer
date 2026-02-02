import json

import requests

import growattServer

"""
# Example script controlling a MID/TLX Growatt (MID-30KTL3-XH + APX battery) system using the public growatt API
# You can obtain an API token from the Growatt API documentation or developer portal.
"""

# Get the API token from user input or environment variable
# api_token = os.environ.get("GROWATT_API_TOKEN") or input("Enter your Growatt API token: ")

# test token from official API docs https://www.showdoc.com.cn/262556420217021/1494053950115877
api_token = "6eb6f069523055a339d71e5b1f6c88cc"  # gitleaks:allow

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
        if device["type"] == 7:  # (MIN/TLX)
            inverter_sn = device["device_sn"]
            print(f"Processing inverter: {inverter_sn}")

            # Get device details
            inverter_data = api.min_detail(inverter_sn)
            print("Saving inverter data to inverter_data.json")
            with open("inverter_data.json", "w") as f:
                json.dump(inverter_data, f, indent=4, sort_keys=True)

            # Get energy data
            energy_data = api.min_energy(device_sn=inverter_sn)
            print("Saving energy data to energy_data.json")
            with open("energy_data.json", "w") as f:
                json.dump(energy_data, f, indent=4, sort_keys=True)

            # Get energy history
            energy_history_data = api.min_energy_history(inverter_sn)
            print("Saving energy history data to energy_history.json")
            with open("energy_history.json", "w") as f:
                json.dump(energy_history_data["datas"],
                          f, indent=4, sort_keys=True)

            # Get settings
            settings_data = api.min_settings(device_sn=inverter_sn)
            print("Saving settings data to settings_data.json")
            with open("settings_data.json", "w") as f:
                json.dump(settings_data, f, indent=4, sort_keys=True)

            # Read time segments
            tou = api.min_read_time_segments(inverter_sn, settings_data)
            print(json.dumps(tou, indent=4))

            # Read discharge power
            discharge_power = api.min_read_parameter(
                inverter_sn, "discharge_power")
            print("Current discharge power:", discharge_power, "%")

            # Settings parameters - Uncomment to test

            # Turn on AC charging
#            api.min_write_parameter(inverter_sn, 'ac_charge', 1)
#            print("AC charging enabled successfully")

            # Enable Load First between 00:00 and 11:59 using time segment 1
#            api.min_write_time_segment(
#                device_sn=inverter_sn,
#                segment_id=1,
#                batt_mode=growattServer.BATT_MODE_BATTERY_FIRST,
#                start_time=datetime.time(0, 0),
#                end_time=datetime.time(00, 59),
#                enabled=True
#            )
#            print("Time segment updated successfully")


except growattServer.GrowattV1ApiError as e:
    print(f"API Error: {e} (Code: {e.error_code}, Message: {e.error_msg})")
except growattServer.GrowattParameterError as e:
    print(f"Parameter Error: {e}")
except requests.exceptions.RequestException as e:
    print(f"Network Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
