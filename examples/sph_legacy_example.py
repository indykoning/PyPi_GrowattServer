"""
Read live data and totals from an SPH/SPM hybrid inverter via the regional
mobile API (the surface ShinePhone uses).

This is the *legacy* (mobile) path, distinct from the V1 OpenAPI flow shown
in sph_example.py. Use this when V1 isn't an option — most notably for
newer SPH/SPM models like SPM-10000TL-HU which are not registered in V1's
device_list and whose data is null/zero on the legacy mix_*/tlx_* endpoints
of openapi.growatt.com.

The mobile API exposes SPH endpoints under newTwoSphAPI.do on regional
hosts (server-{region}-api.growatt.com). Set `api.server_url` to your
regional host before calling `login()`. Common regions:
    server-au-api.growatt.com   (Australia / Oceania)
    server-cn-api.growatt.com   (China)
    server-us-api.growatt.com   (North America)
    server-api.growatt.com      (Europe / other)
"""

import getpass
import pprint

import growattServer

pp = pprint.PrettyPrinter(indent=4)


def indent_print(message: str, indent: int) -> None:
    print(" " * indent + message)


# Prompt for credentials and region.
username = input("Enter username: ")
user_pass = getpass.getpass("Enter password: ")
region = input(
    "Enter regional host (e.g. server-au-api.growatt.com) "
    "[server-api.growatt.com]: "
).strip() or "server-api.growatt.com"

# The mobile API expects a ShinePhone-style User-Agent. The default
# identifier works too, but matching the mobile app is the most compatible.
api = growattServer.GrowattApi(
    agent_identifier="ShinePhone/8.4.7 (iPhone; iOS 26.4; Scale/3.00)",
)
api.server_url = f"https://{region}/"

login_response = api.login(username, user_pass)
if not login_response.get("success"):
    raise SystemExit(f"Login failed: {login_response}")

user_id = login_response["user"]["id"]
plant_list = api.plant_list(user_id)

print("\n***List of plants***")
for plant in plant_list["data"]:
    indent_print(f"ID: {plant['plantId']}, Name: {plant['plantName']}", 2)

for plant in plant_list["data"]:
    plant_id = plant["plantId"]
    plant_name = plant["plantName"]
    plant_info = api.plant_info(plant_id)

    print(f"\n***Plant {plant_id} - {plant_name}***")
    indent_print(f"Solar Energy Today (kWh): {plant_info['todayEnergy']}", 2)
    indent_print(f"Solar Energy Total (kWh): {plant_info['totalEnergy']}", 2)

    # SPH devices live in plant_info["sphList"], not "deviceList" (which
    # only contains classic-class inverters). plant_info also has lists for
    # other device classes — invList, mixList (in some accounts),
    # storageList, witList, etc.
    sph_devices = plant_info.get("sphList", [])
    if not sph_devices:
        indent_print("No SPH devices in this plant — skipping.", 2)
        continue

    for device in sph_devices:
        sph_sn = device["deviceSn"]
        print(f"\n  ** SPH Device {sph_sn} (sphType={device['sphType']}) **")

        # 1. Live system status — instantaneous values.
        status = api.sph_system_status(plant_id, sph_sn)
        # pp.pprint(status)
        indent_print("== Batteries ==", 4)
        indent_print(f"SOC: {status['SOC']} %", 6)
        indent_print(f"Battery voltage: {status['vBat']} V", 6)
        indent_print(f"Charging at: {status['pCharge1']} kW", 6)
        indent_print(f"Discharging at: {status['pDisCharge1']} kW", 6)

        indent_print("== PV ==", 4)
        indent_print(f"Total PV power: {status['ppv']} kW", 6)
        indent_print(
            f"PV1: {status['ppv1']} W ({status['vpv1']} V), "
            f"PV2: {status['ppv2']} W ({status['vpv2']} V), "
            f"PV3: {status['ppv3']} W ({status['vpv3']} V)",
            6,
        )

        indent_print("== Grid / Load ==", 4)
        indent_print(f"Importing from grid: {status['pacToUser']} kW", 6)
        indent_print(f"Exporting to grid: {status['pacToGrid']} kW", 6)
        indent_print(f"Local load: {status['pLocalLoad']} kW", 6)
        indent_print(
            f"Grid: {status['vAc1']} V @ {status['fAc']} Hz "
            f"(status={status['status']})",
            6,
        )

        # 2. Daily / lifetime energy totals.
        totals = api.sph_energy_overview(plant_id, sph_sn)
        # pp.pprint(totals)
        indent_print("== Energy today ==", 4)
        indent_print(f"PV: {totals['epvToday']} kWh", 6)
        indent_print(f"Battery charged: {totals['eChargeToday']} kWh", 6)
        indent_print(f"Battery discharged: {totals['eDisChargeToday']} kWh", 6)
        indent_print(f"Local load: {totals['elocalLoadToday']} kWh", 6)
        indent_print(f"Exported to grid: {totals['eToGridToday']} kWh", 6)

        indent_print("== Energy lifetime ==", 4)
        indent_print(f"PV: {totals['epvTotal']} kWh", 6)
        indent_print(f"Battery charged: {totals['eChargeTotal']} kWh", 6)
        indent_print(f"Battery discharged: {totals['eDisChargeTotal']} kWh", 6)
        indent_print(f"Local load: {totals['elocalLoadTotal']} kWh", 6)
        indent_print(f"Exported to grid: {totals['eToGridTotal']} kWh", 6)

        # 3. Per-day chart series (5-minute resolution). Other chart_type
        # values: 1=month, 2=year, 3=total (lifetime, 5 yearly buckets).
        day_chart = api.sph_energy_prod_and_cons(plant_id, sph_sn, chart_type=0)
        ppv_series = day_chart["chartData"]["ppv"]
        # Each value is a 5-minute average in kW; sum × (5/60) ≈ kWh.
        ppv_today_kwh = round(sum(float(v or 0) for v in ppv_series) * (5 / 60), 2)
        indent_print("== Today's chart (calculated from 5-min samples) ==", 4)
        indent_print(f"PV (calculated from chart): {ppv_today_kwh} kWh", 6)
        indent_print(f"Self-consumption (API): {day_chart['eChargeToday1']} kWh", 6)
        indent_print(f"Grid import (API): {day_chart['etouser']} kWh", 6)

        # 4. Settings — full bean of every adjustable parameter.
        settings = api.sph_settings(sph_sn)
        # pp.pprint(settings)
        indent_print(f"== Settings ({len(settings)} keys) ==", 4)
        for key in (
            "sys_work_mode",
            "pv_on_off",
            "cutoff_soc",
            "cuton_soc",
            "bat_max_charge_current",
            "bat_max_discharge_current",
            "zero_ct_sell",
            "zero_load_sell",
        ):
            if key in settings:
                indent_print(f"{key}: {settings[key]}", 6)

        # 5. Writing a setting (commented out — uncomment to enable).
        #
        # On this device, sys_work_mode=1 enables On Grid mode (PV
        # sell-back). Use sph_settings() to discover the supported setting
        # types and read the current value before writing.
        #
        # api.update_sph_inverter_setting(sph_sn, "sys_work_mode", 1)
