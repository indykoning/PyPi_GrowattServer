import growattServer
import datetime
import json

"""
# Example script controlling a MID/TLX Growatt (MID-30KTL3-XH + APX battery) system using the public growatt API 
# You can obtain an API token from the Growatt API documentation or developer portal.
"""

# Get the API token from user input or environment variable
# api_token = os.environ.get("GROWATT_API_TOKEN") or input("Enter your Growatt API token: ")

# test token from official API docs https://www.showdoc.com.cn/262556420217021/1494053950115877
api_token = "6eb6f069523055a339d71e5b1f6c88cc"  # gitleaks:allow

# Initialize the API with token instead of using login
api = growattServer.OpenApiV1(token=api_token)

# Plant info
plant_list = api.plant_list()  # Use V1 endpoint
if plant_list['error_code'] != 0:
    print(f"Failed to get plant list, error: {plant_list['error_msg']}")
    exit()

print(f"Plants: Found {plant_list['data']['count']} plants")
plant_id = plant_list['data']['plants'][0]['plant_id']

# Devices
devices_response = api.device_list(plant_id)
if devices_response['error_code'] != 0:
    print(f"Failed to get devices, error: {plant_list['error_msg']}")
    exit()

for device in devices_response['data']['devices']:
    if device['type'] == 7:  # (MIN/TLX)
        inverter_sn = device['device_sn']

        # Get device details using v1 API
        inverter_detail_response = api.min_detail(inverter_sn)
        if inverter_detail_response['error_code'] == 0:
            inverter_data = inverter_detail_response['data']
            print("Saving inverter data to inverter_data.json")
            with open('inverter_data.json', 'w') as f:
                json.dump(inverter_data, f, indent=4, sort_keys=True)

        # Get energy data using v1 API
        energy_response = api.min_energy(device_sn=inverter_sn)
        if energy_response['error_code'] == 0:
            energy_data = energy_response['data']
            print("Saving energy data to energy_data.json")
            with open('energy_data.json', 'w') as f:
                json.dump(energy_data, f, indent=4, sort_keys=True)

        # Get energy details from v1 API
        energy_history_response = api.min_energy_history(inverter_sn)
        if energy_history_response['error_code'] == 0:
            energy_history_data = energy_history_response['data']['datas']
            print("Saving energy history data to energy_history.json")
            with open('energy_history.json', 'w') as f:
                json.dump(energy_history_data, f, indent=4, sort_keys=True)

        # Get settings using v1 API
        settings_response = api.min_settings(device_sn=inverter_sn)
        if settings_response['error_code'] == 0:
            print("Saving settings data to settings_data.json")
            settings_data = settings_response['data']
            with open('settings_data.json', 'w') as f:
                json.dump(settings_data, f, indent=4, sort_keys=True)

        tou = api.min_read_time_segments(inverter_sn, settings_response)
        print(json.dumps(tou, indent=4))

        # Example of reading individual parameter
        res = api.min_read_parameter(inverter_sn, 'discharge_power')
        if res['error_code'] != 0:
            print(f"Failed to read parameters, error: {res['error_msg']}")
            exit()
        print("Current discharge power:", res['data'], "%")

        # Settings parameters. Uncomment to test

        # Turn on AC charging
#        res = api.min_write_parameter(inverter_sn, 'ac_charge', 1)
#        print("AC charging enabled: ", res)

        # Enable Load First between 00:00 and 11:59 using time segment 1
#        res = api.min_write_time_segment(
#            device_sn=inverter_sn,
#            segment_id=1,
#            batt_mode=growattServer.BATT_MODE_LOAD_FIRST,
#            start_time=datetime.time(0, 0),
#            end_time=datetime.time(00, 59),
#            enabled=True
#        )
#        print(res)
