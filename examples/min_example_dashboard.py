import growattServer
import json

"""
Example script fetching key power and today+total energy metrics from a Growatt MID-30KTL3-XH (TLX) + APX battery hybrid system
using the V1 API with token-based authentication.
"""

# Get the API token from user input or environment variable
# api_token = os.environ.get("GROWATT_API_TOKEN") or input("Enter your Growatt API token: ")

# test token from official API docs https://www.showdoc.com.cn/262556420217021/1494053950115877
api_token = "6eb6f069523055a339d71e5b1f6c88cc"  # gitleaks:allow

# Initialize the API with token
api = growattServer.GrowattApiV1(token=api_token)

# Get plant list using V1 API
plant_response = api.plant_list_v1()
if plant_response['error_code'] != 0:
    print(f"Failed to get plants, error: {plant_response['error_msg']}")
    exit()

plant_id = plant_response['data']['plants'][0]['plant_id']

# Get devices in plant using V1 API
devices_response = api.device_list_v1(plant_id)
if devices_response['error_code'] != 0:
    print(f"Failed to get devices, error: {devices_response['error_msg']}")
    exit()

# Iterate over all devices
energy_data = None
for device in devices_response['data']['devices']:
    if device['type'] == 7:  # (MIN/TLX)
        inverter_sn = device['device_sn']

        # Get energy data using new API
        energy_response = api.min_energy(device_sn=inverter_sn)
        if energy_response['error_code'] != 0:
            print(
                f"Failed to get energy data, error: {energy_response['error_msg']}")
            exit()

        energy_data = energy_response['data']
        with open('energy_data.json', 'w') as f:
            json.dump(energy_data, f, indent=4, sort_keys=True)

# energy data does not contain epvToday for some reason, so we need to calculate it
epv_today = energy_data["epv1Today"] + energy_data["epv2Today"]

solar_production = f'{float(epv_today):.1f}/{float(energy_data["epvTotal"]):.1f}'
solar_production_pv1 = f'{float(energy_data["epv1Today"]):.1f}/{float(energy_data["epv1Total"]):.1f}'
solar_production_pv2 = f'{float(energy_data["epv2Today"]):.1f}/{float(energy_data["epv2Total"]):.1f}'
energy_output = f'{float(energy_data["eacToday"]):.1f}/{float(energy_data["eacTotal"]):.1f}'
system_production = f'{float(energy_data["esystemToday"]):.1f}/{float(energy_data["esystemTotal"]):.1f}'
battery_charged = f'{float(energy_data["echargeToday"]):.1f}/{float(energy_data["echargeTotal"]):.1f}'
battery_grid_charge = f'{float(energy_data["eacChargeToday"]):.1f}/{float(energy_data["eacChargeTotal"]):.1f}'
battery_discharged = f'{float(energy_data["edischargeToday"]):.1f}/{float(energy_data["edischargeTotal"]):.1f}'
exported_to_grid = f'{float(energy_data["etoGridToday"]):.1f}/{float(energy_data["etoGridTotal"]):.1f}'
imported_from_grid = f'{float(energy_data["etoUserToday"]):.1f}/{float(energy_data["etoUserTotal"]):.1f}'
load_consumption = f'{float(energy_data["elocalLoadToday"]):.1f}/{float(energy_data["elocalLoadTotal"]):.1f}'
self_consumption = f'{float(energy_data["eselfToday"]):.1f}/{float(energy_data["eselfTotal"]):.1f}'
battery_charged = f'{float(energy_data["echargeToday"]):.1f}/{float(energy_data["echargeTotal"]):.1f}'

# Output the dashboard
print("\nGeneration overview             Today/Total(kWh)")
print(f'Solar production          {solar_production:>22}')
print(f' Solar production, PV1    {solar_production_pv1:>22}')
print(f' Solar production, PV2    {solar_production_pv2:>22}')
print(f'Energy Output             {energy_output:>22}')
print(f'System production         {system_production:>22}')
print(f'Self consumption          {self_consumption:>22}')
print(f'Load consumption          {load_consumption:>22}')
print(f'Battery Charged           {battery_charged:>22}')
print(f' Charged from grid        {battery_grid_charge:>22}')
print(f'Battery Discharged        {battery_discharged:>22}')
print(f'Import from grid          {imported_from_grid:>22}')
print(f'Export to grid            {exported_to_grid:>22}')

print("\nPower overview                          (Watts)")
print(f'AC Power                 {float(energy_data["pac"]):>22.1f}')
print(f'Self power               {float(energy_data["pself"]):>22.1f}')
print(
    f'Export power             {float(energy_data["pacToGridTotal"]):>22.1f}')
print(
    f'Import power             {float(energy_data["pacToUserTotal"]):>22.1f}')
print(
    f'Local load power         {float(energy_data["pacToLocalLoad"]):>22.1f}')
print(f'PV power                 {float(energy_data["ppv"]):>22.1f}')
print(f'PV #1 power              {float(energy_data["ppv1"]):>22.1f}')
print(f'PV #2 power              {float(energy_data["ppv2"]):>22.1f}')
print(
    f'Battery charge power     {float(energy_data["bdc1ChargePower"]):>22.1f}')
print(
    f'Battery discharge power  {float(energy_data["bdc1DischargePower"]):>22.1f}')
print(f'Battery SOC              {int(energy_data["bdc1Soc"]):>21}%')
