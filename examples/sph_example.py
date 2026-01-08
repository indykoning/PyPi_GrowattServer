"""
Example script for SPH devices using the OpenAPI V1.

This script demonstrates controlling SPH interface devices (device type 5)
such as hybrid inverter systems.
You can obtain an API token from the Growatt API documentation or developer portal.
"""

import datetime
import json
from pathlib import Path

import requests

from . import growattServer

# Get the API token from user input or environment variable
# api_token = os.environ.get("GROWATT_API_TOKEN") or input("Enter your Growatt API token: ")

# test token from official API docs https://www.showdoc.com.cn/262556420217021/1494053950115877
api_token = "6eb6f069523055a339d71e5b1f6c88cc"  # noqa: S105

try:
    # Initialize the API with token instead of using login
    api = growattServer.OpenApiV1(token=api_token)

    # Plant info
    plants = api.plant_list()
    print(f"Plants: Found {plants['count']} plants")  # noqa: T201
    plant_id = plants["plants"][0]["plant_id"]

    # Devices
    devices = api.device_list(plant_id)

    for device in devices["devices"]:
        print(device)  # noqa: T201
        if device["type"] == growattServer.DeviceType.SPH.value:
            inverter_sn = device["device_sn"]
            print(f"Processing SPH device: {inverter_sn}")  # noqa: T201

            # Get device details
            inverter_data = api.sph_detail(
                device_sn=inverter_sn,
            )
            print("Saving inverter data to inverter_data.json")  # noqa: T201
            with Path("inverter_data.json").open("w") as f:
                json.dump(inverter_data, f, indent=4, sort_keys=True)

            # Get energy data
            energy_data = api.sph_energy(
                device_sn=inverter_sn,
            )
            print("Saving energy data to energy_data.json")  # noqa: T201
            with Path("energy_data.json").open("w") as f:
                json.dump(energy_data, f, indent=4, sort_keys=True)

            # Get energy history
            energy_history_data = api.sph_energy_history(
                device_sn=inverter_sn,
            )
            print("Saving energy history data to energy_history.json")  # noqa: T201
            with Path("energy_history.json").open("w") as f:
                json.dump(
                    energy_history_data.get("datas", []),
                    f,
                    indent=4,
                    sort_keys=True,
                )

            # Get settings
            settings_data = api.sph_settings(
                device_sn=inverter_sn,
            )
            print("Saving settings data to settings_data.json")  # noqa: T201
            with Path("settings_data.json").open("w") as f:
                json.dump(settings_data, f, indent=4, sort_keys=True)

            # Read AC charge time periods
            charge_times = api.sph_read_ac_charge_times(
                device_sn=inverter_sn,
                settings_data=settings_data,
            )
            print("AC Charge Time Periods:")  # noqa: T201
            print(json.dumps(charge_times, indent=4))  # noqa: T201

            # Read AC discharge time periods
            discharge_times = api.sph_read_ac_discharge_times(
                device_sn=inverter_sn,
                settings_data=settings_data,
            )
            print("AC Discharge Time Periods:")  # noqa: T201
            print(json.dumps(discharge_times, indent=4))  # noqa: T201

            # Read discharge power
            discharge_power = api.sph_read_parameter(
                device_sn=inverter_sn,
                parameter_id="discharge_power",
            )
            print(f"Current discharge power: {discharge_power}%")  # noqa: T201

            # Write examples - Uncomment to test

            # Set AC charge time period 1: charge at 50% power to 95% SOC between 00:00-06:00
            # api.sph_write_ac_charge_time(
            #     device_sn=inverter_sn,
            #     period_id=1,
            #     charge_power=50,  # 50% charging power
            #     charge_stop_soc=95,  # Stop at 95% SOC
            #     start_time=datetime.time(0, 0),
            #     end_time=datetime.time(6, 0),
            #     mains_enabled=True,  # Enable grid charging
            #     enabled=True
            # )
            # print("AC charge period 1 updated successfully")

            # Set AC discharge time period 1: discharge at 100% power to 20% SOC between 17:00-22:00
            # api.sph_write_ac_discharge_time(
            #     device_sn=inverter_sn,
            #     period_id=1,
            #     discharge_power=100,  # 100% discharge power
            #     discharge_stop_soc=20,  # Stop at 20% SOC
            #     start_time=datetime.time(17, 0),
            #     end_time=datetime.time(22, 0),
            #     enabled=True
            # )
            # print("AC discharge period 1 updated successfully")

except growattServer.GrowattV1ApiError as e:
    print(f"API Error: {e} (Code: {e.error_code}, Message: {e.error_msg})")  # noqa: T201
except growattServer.GrowattParameterError as e:
    print(f"Parameter Error: {e}")  # noqa: T201
except requests.exceptions.RequestException as e:
    print(f"Network Error: {e}")  # noqa: T201
except Exception as e:  # noqa: BLE001
    print(f"Unexpected error: {e}")  # noqa: T201
