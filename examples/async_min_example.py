"""
Async example script for MIN/TLX devices using the OpenAPI V1.

This is the async equivalent of min_example.py. All API calls use await
and the client is used as an async context manager.

You can obtain an API token from the Growatt API documentation or developer portal.
"""

import asyncio
import json

import growattServer

# test token from official API docs https://www.showdoc.com.cn/262556420217021/1494053950115877
api_token = "6eb6f069523055a339d71e5b1f6c88cc"  # gitleaks:allow


async def main():
    try:
        async with growattServer.AsyncOpenApiV1(token=api_token) as api:
            # Plant info
            plants = await api.plant_list()
            print(f"Plants: Found {plants['count']} plants")
            plant_id = plants["plants"][0]["plant_id"]

            # Devices
            devices = await api.device_list(plant_id)

            for device in devices["devices"]:
                if device["type"] == 7:  # (MIN/TLX)
                    inverter_sn = device["device_sn"]
                    print(f"Processing inverter: {inverter_sn}")

                    # Get device details
                    inverter_data = await api.min_detail(inverter_sn)
                    print(json.dumps(inverter_data, indent=4, sort_keys=True))

                    # Get energy data
                    energy_data = await api.min_energy(device_sn=inverter_sn)
                    print(json.dumps(energy_data, indent=4, sort_keys=True))

                    # Get settings
                    settings_data = await api.min_settings(device_sn=inverter_sn)
                    print(json.dumps(settings_data, indent=4, sort_keys=True))

                    # Read time segments
                    tou = await api.min_read_time_segments(inverter_sn, settings_data)
                    print(json.dumps(tou, indent=4))

    except growattServer.GrowattV1ApiError as e:
        print(f"API Error: {e} (Code: {e.error_code}, Message: {e.error_msg})")
    except growattServer.GrowattParameterError as e:
        print(f"Parameter Error: {e}")
    except growattServer.GrowattApiError as e:
        print(f"Network Error: {e}")


asyncio.run(main())
