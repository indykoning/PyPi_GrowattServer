
import getpass
import sys

import growattServer

# Example script fetching key power and today+total energy metrics from a Growatt MID-30KTL3-XH (TLX) + APX battery hybrid system
#
# There is a lot of overlap in what the various Growatt APIs returns.
# tlx_detail() contains the bulk of the needed data, but some info is missing and is fetched from
# tlx_system_status(), tlx_energy_overview() and tlx_battery_info_detailed() instead


# Prompt user for username
username=input("Enter username:")

# Prompt user to input password
user_pass=getpass.getpass("Enter password:")

# Login, emulating the Growatt app
user_agent = "ShinePhone/8.1.17 (iPhone; iOS 15.6.1; Scale/2.00)"
api = growattServer.GrowattApi(agent_identifier=user_agent)
login_response = api.login(username, user_pass)
if not login_response["success"]:
    print(f"Failed to log in, msg: {login_response['msg']}, error: {login_response['error']}")
    sys.exit()

# Get plant(s)
plant_list = api.plant_list_two()
plant_id = plant_list[0]["id"]

# Get devices in plant
devices = api.device_list(plant_id)

# Iterate over all devices. Here we are interested in data from 'tlx' inverters and 'bat' devices
batteries_info = []
for device in devices:
    if device["deviceType"] == "tlx":
        inverter_sn = device["deviceSn"]

        # Inverter detail, contains the bulk of energy and power values
        inverter_detail = api.tlx_detail(inverter_sn).get("data")

        # Energy overview is used to retrieve "epvToday" which is not present in tlx_detail() for some reason
        energy_overview = api.tlx_energy_overview(plant_id, inverter_sn)

        # System status, contains power values, not available in inverter_detail()
        system_status = api.tlx_system_status(plant_id, inverter_sn)

    if device["deviceType"] == "bat":
        batt_info = api.tlx_battery_info(device["deviceSn"])
        if batt_info.get("lost"):
            # Disconnected batteries are listed with 'old' power/energy/SOC data
            # Therefore we check it it's 'lost' and skip it in that case.
            print("'Lost' battery found, skipping")
            continue

        # Battery info
        batt_info = api.tlx_battery_info_detailed(plant_id, device["deviceSn"]).get("data")

        if float(batt_info["chargeOrDisPower"]) > 0:
            bdcChargePower =  float(batt_info["chargeOrDisPower"])
            bdcDischargePower = 0
        else:
            bdcChargePower = 0
            bdcDischargePower =  float(batt_info["chargeOrDisPower"])
            bdcDischargePower = -bdcDischargePower

        battery_data = {
            "serialNum": device["deviceSn"],
            "bdcChargePower": bdcChargePower,
            "bdcDischargePower": bdcDischargePower,
            "dischargeTotal": batt_info["dischargeTotal"],
            "soc": batt_info["soc"]
        }
        batteries_info.append(battery_data)


solar_production     = f'{float(energy_overview["epvToday"]):.1f}/{float(energy_overview["epvTotal"]):.1f}'
solar_production_pv1 = f'{float(inverter_detail["epv1Today"]):.1f}/{float(inverter_detail["epv1Total"]):.1f}'
solar_production_pv2 = f'{float(inverter_detail["epv2Today"]):.1f}/{float(inverter_detail["epv2Total"]):.1f}'
energy_output        = f'{float(inverter_detail["eacToday"]):.1f}/{float(inverter_detail["eacTotal"]):.1f}'
system_production    = f'{float(inverter_detail["esystemToday"]):.1f}/{float(inverter_detail["esystemTotal"]):.1f}'
battery_charged      = f'{float(inverter_detail["echargeToday"]):.1f}/{float(inverter_detail["echargeTotal"]):.1f}'
battery_grid_charge  = f'{float(inverter_detail["eacChargeToday"]):.1f}/{float(inverter_detail["eacChargeTotal"]):.1f}'
battery_discharged   = f'{float(inverter_detail["edischargeToday"]):.1f}/{float(inverter_detail["edischargeTotal"]):.1f}'
exported_to_grid     = f'{float(inverter_detail["etoGridToday"]):.1f}/{float(inverter_detail["etoGridTotal"]):.1f}'
imported_from_grid   = f'{float(inverter_detail["etoUserToday"]):.1f}/{float(inverter_detail["etoUserTotal"]):.1f}'
load_consumption     = f'{float(inverter_detail["elocalLoadToday"]):.1f}/{float(inverter_detail["elocalLoadTotal"]):.1f}'
self_consumption     = f'{float(inverter_detail["eselfToday"]):.1f}/{float(inverter_detail["eselfTotal"]):.1f}'
battery_charged      = f'{float(inverter_detail["echargeToday"]):.1f}/{float(inverter_detail["echargeTotal"]):.1f}'

print("\nGeneration overview             Today/Total(kWh)")
print(f"Solar production          {solar_production:>22}")
print(f" Solar production, PV1    {solar_production_pv1:>22}")
print(f" Solar production, PV2    {solar_production_pv2:>22}")
print(f"Energy Output             {energy_output:>22}")
print(f"System production         {system_production:>22}")
print(f"Self consumption          {self_consumption:>22}")
print(f"Load consumption          {load_consumption:>22}")
print(f"Battery Charged           {battery_charged:>22}")
print(f" Charged from grid        {battery_grid_charge:>22}")
print(f"Battery Discharged        {battery_discharged:>22}")
print(f"Import from grid          {imported_from_grid:>22}")
print(f"Export to grid            {exported_to_grid:>22}")

print("\nPower overview                          (Watts)")
print(f'AC Power                 {float(inverter_detail["pac"]):>22.1f}')
print(f'Self power               {float(inverter_detail["pself"]):>22.1f}')
print(f'Export power             {float(inverter_detail["pacToGridTotal"]):>22.1f}')
print(f'Import power             {float(inverter_detail["pacToUserTotal"]):>22.1f}')
print(f'Local load power         {float(inverter_detail["pacToLocalLoad"]):>22.1f}')
print(f'PV power                 {float(inverter_detail["ppv"]):>22.1f}')
print(f'PV #1 power              {float(inverter_detail["ppv1"]):>22.1f}')
print(f'PV #2 power              {float(inverter_detail["ppv2"]):>22.1f}')
print(f'Battery charge power     {float(system_status["chargePower"])*1000:>22.1f}')
if len(batteries_info) > 0:
    print(f'Batt #1 charge power     {float(batteries_info[0]["bdcChargePower"]):>22.1f}')
if len(batteries_info) > 1:
    print(f'Batt #2 charge power     {float(batteries_info[1]["bdcChargePower"]):>22.1f}')
print(f'Battery discharge power      {float(system_status["pdisCharge"])*1000:>18.1f}')
if len(batteries_info) > 0:
    print(f'Batt #1 discharge power  {float(batteries_info[0]["bdcDischargePower"]):>22.1f}')
if len(batteries_info) > 1:
    print(f'Batt #2 discharge power  {float(batteries_info[1]["bdcDischargePower"]):>22.1f}')
if len(batteries_info) > 0:
    print(f'Batt #1 SOC              {int(batteries_info[0]["soc"]):>21}%')
if len(batteries_info) > 1:
    print(f'Batt #2 SOC              {int(batteries_info[1]["soc"]):>21}%')
