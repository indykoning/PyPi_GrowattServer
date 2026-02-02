"""
Example script for SPH devices using the OpenAPI V1.

This script demonstrates controlling SPH interface devices (device type 5)
such as hybrid inverter systems.
You can obtain an API token from the Growatt API documentation or developer portal.
"""

import json
import os

import requests

import growattServer

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
        print(device)
        if device["type"] == growattServer.DeviceType.SPH.value:
            inverter_sn = device["device_sn"]
            print(f"Processing SPH device: {inverter_sn}")

            # Get energy data
            energy_data = api.sph_energy(
                device_sn=inverter_sn,
            )
            print("Saving energy data to energy_data.json")
            with open("energy_data.json", "w") as f:
                json.dump(energy_data, f, indent=4, sort_keys=True)

            # Get energy history
            energy_history_data = api.sph_energy_history(
                device_sn=inverter_sn,
            )
            print("Saving energy history data to energy_history.json")
            with open("energy_history.json", "w") as f:
                json.dump(
                    energy_history_data.get("datas", []),
                    f,
                    indent=4,
                    sort_keys=True,
                )

            # Get device details
            inverter_data = api.sph_detail(
                device_sn=inverter_sn,
            )
            print("Saving inverter data to inverter_data.json")
            with open("inverter_data.json", "w") as f:
                json.dump(inverter_data, f, indent=4, sort_keys=True)

            # Read some settings directly from inverter_data (from sph_detail)
            # See docs/openapiv1/sph_settings.md for all available fields
            print("Device Settings:")
            print(f"  Device status: {inverter_data.get('status', 'N/A')}")
            print(f"  Battery type: {inverter_data.get('batteryType', 'N/A')}")
            print(f"  EPS enabled: {inverter_data.get('epsFunEn', 'N/A')}")
            print(f"  Export limit: {inverter_data.get('exportLimitPowerRate', 'N/A')}%")

            # Read AC charge time periods using helper function and inverter_data to avoid rate limiting
            charge_config = api.sph_read_ac_charge_times(
                settings_data=inverter_data,
            )
            print("AC Charge Configuration:")
            print(f"  Charge Power: {charge_config['charge_power']}%")
            print(f"  Stop SOC: {charge_config['charge_stop_soc']}%")
            print(f"  Mains Enabled: {charge_config['mains_enabled']}")
            print(f"  Periods: {json.dumps(charge_config['periods'], indent=4)}")

            # Read AC discharge time periods using helper function and inverter_data to avoid rate limiting
            discharge_config = api.sph_read_ac_discharge_times(
                settings_data=inverter_data,
            )
            print("AC Discharge Configuration:")
            print(f"  Discharge Power: {discharge_config['discharge_power']}%")
            print(f"  Stop SOC: {discharge_config['discharge_stop_soc']}%")
            print(f"  Periods: {json.dumps(discharge_config['periods'], indent=4)}")

            # Write examples - Uncomment to test

            # Example 1: Set AC charge time periods
            # Charge at 50% power, stop at 95% SOC, grid charging enabled
            # api.sph_write_ac_charge_times(
            #     device_sn=inverter_sn,
            #     charge_power=50,
            #     charge_stop_soc=95,
            #     mains_enabled=True,
            #     periods=[
            #         {"start_time": datetime.time(0, 0), "end_time": datetime.time(6, 0), "enabled": True},
            #         {"start_time": datetime.time(0, 0), "end_time": datetime.time(0, 0), "enabled": False},
            #         {"start_time": datetime.time(0, 0), "end_time": datetime.time(0, 0), "enabled": False},
            #     ]
            # )
            # print("AC charge periods updated successfully")

            # Example 2: Set AC discharge time periods
            # Discharge at 100% power, stop at 20% SOC
            # api.sph_write_ac_discharge_times(
            #     device_sn=inverter_sn,
            #     discharge_power=100,
            #     discharge_stop_soc=20,
            #     periods=[
            #         {"start_time": datetime.time(17, 0), "end_time": datetime.time(22, 0), "enabled": True},
            #         {"start_time": datetime.time(0, 0), "end_time": datetime.time(0, 0), "enabled": False},
            #         {"start_time": datetime.time(0, 0), "end_time": datetime.time(0, 0), "enabled": False},
            #     ]
            # )
            # print("AC discharge periods updated successfully")

            # Example 3: Turn device on/off
            # api.sph_write_parameter(inverter_sn, "pv_on_off", "1")  # Turn on
            # api.sph_write_parameter(inverter_sn, "pv_on_off", "0")  # Turn off

            # Example 4: Set grid voltage limits
            # api.sph_write_parameter(inverter_sn, "pv_grid_voltage_high", "270")
            # api.sph_write_parameter(inverter_sn, "pv_grid_voltage_low", "180")

            # Example 5: Configure off-grid/EPS settings
            # api.sph_write_parameter(inverter_sn, "mix_off_grid_enable", "1")  # Enable
            # api.sph_write_parameter(inverter_sn, "mix_ac_discharge_frequency", "0")  # 50Hz
            # api.sph_write_parameter(inverter_sn, "mix_ac_discharge_voltage", "0")  # 230V

            # Example 6: Set anti-backflow (export limit)
            # api.sph_write_parameter(inverter_sn, "backflow_setting", ["1", "50"])  # On, 50%

except growattServer.GrowattV1ApiError as e:
    print(f"API Error: {e} (Code: {e.error_code}, Message: {e.error_msg})")
except growattServer.GrowattParameterError as e:
    print(f"Parameter Error: {e}")
except requests.exceptions.RequestException as e:
    print(f"Network Error: {e}")
except Exception as e:  # noqa: BLE001
    print(f"Unexpected error: {e}")
