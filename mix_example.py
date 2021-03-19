import growattServer
import datetime
import getpass
import pprint

"""
This is a very trivial script that logs into a user's account and prints out useful data for a "Mix" system (Hybrid).
The first half of the logic is applicable to all types of system. There is a clear point (marked in the script) where we specifically
make calls to the "mix" WebAPI calls, at this point other types of systems will no longer work.
This has been tested against my personal system (muppet3000) which is a hybrid inverter system.

Throughout the script there are points where 'pp.pprint' has been commented out. If you wish to see all the data that is returned from those
specific library calls, just uncomment them and they will appear as part of the output.

NOTE - For some reason (not sure if this is just specific to my system or not) the "export to grid" daily total and overall total values don't seem to be populating. As such they are untested.
This has been causing problems on my WebUI and mobile app too, it is not a bug in this library, the output from this script has been updated to reflect it's inaccuracy.
"""

pp = pprint.PrettyPrinter(indent=4)

"""
A really hacky function to allow me to print out things with an indent in-front
"""
def indent_print(to_output, indent):
  indent_string = ""
  for x in range(indent):
    indent_string += " "
  print(indent_string + to_output)

#Prompt user for username
username=input("Enter username:")

#Prompt user to input password
user_pass=getpass.getpass("Enter password:")

api = growattServer.GrowattApi()
login_response = api.login(username, user_pass)

plant_list = api.plant_list(login_response['userId'])
#pp.pprint(plant_list)

print("***Totals for all plants***")
pp.pprint(plant_list['totalData'])
print("")

print("***List of plants***")
for plant in plant_list['data']:
  indent_print("ID: %s, Name: %s"%(plant['plantId'], plant['plantName']), 2)
print("")

for plant in plant_list['data']:
  plant_id = plant['plantId']
  plant_name = plant['plantName']
  plant_info=api.plant_info(plant_id)
  #pp.pprint(plant_info)
  print("***Info for Plant %s - %s***"%(plant_id, plant_name))
  #There are more values in plant_info, but these are some of the useful/interesting ones
  indent_print("CO2 Reducion: %s"%(plant_info['Co2Reduction']),2)
  indent_print("Nominal Power (w): %s"%(plant_info['nominal_Power']),2)
  indent_print("Solar Energy Today (kw): %s"%(plant_info['todayEnergy']),2)
  indent_print("Solar Energy Total (kw): %s"%(plant_info['totalEnergy']),2)
  print("")
  indent_print("Devices in plant:",2)
  for device in plant_info['deviceList']:
    device_sn = device['deviceSn']
    device_type = device['deviceType']
    indent_print("- Device - SN: %s, Type: %s"%(device_sn, device_type),4)

  print("")
  for device in plant_info['deviceList']:
    device_sn = device['deviceSn']
    device_type = device['deviceType']
    indent_print("**Device - SN: %s, Type: %s**"%(device_sn, device_type),2)
    #NOTE - This is the bit where we specifically only handle information on Mix devices - this won't work for non-mix devices

    #These two API calls return lots of duplicated information, but each also holds unique information as well
    mix_info = api.mix_info(device_sn, plant_id)
    pp.pprint(mix_info)
    mix_totals = api.mix_totals(device_sn, plant_id)
    #pp.pprint(mix_totals)
    indent_print("*TOTAL VALUES*", 4)
    indent_print("==Today Totals==", 4)
    indent_print("Battery Charge (kwh): %s"%(mix_info['eBatChargeToday']),6)
    indent_print("Battery Discharge (kwh): %s"%(mix_info['eBatDisChargeToday']),6)
    indent_print("Solar Generation (kwh): %s"%(mix_info['epvToday']),6)
    indent_print("Local Load (kwh): %s"%(mix_totals['elocalLoadToday']),6)
    indent_print("Export to Grid (kwh): %s"%(mix_totals['etoGridToday']),6)
    indent_print("==Overall Totals==",4)
    indent_print("Battery Charge: %s"%(mix_info['eBatChargeTotal']),6)
    indent_print("Battery Discharge (kwh): %s"%(mix_info['eBatDisChargeTotal']),6)
    indent_print("Solar Generation (kwh): %s"%(mix_info['epvTotal']),6)
    indent_print("Local Load (kwh): %s"%(mix_totals['elocalLoadTotal']),6)
    indent_print("Export to Grid (kwh): %s"%(mix_totals['etogridTotal']),6)
    print("")

    mix_detail = api.mix_detail(device_sn, plant_id)
    #pp.pprint(mix_detail)

    #Some of the 'totals' values that are returned by this function do not align to what we would expect, however the graph data always seems to be accurate.
    #Therefore, here we take a moment to calculate the same values provided elsewhere but based on the graph data instead
    #The particular stats that we question are 'load consumption' (elocalLoad)  and 'import from grid' (etouser) which seem to be calculated from one-another
    #It would appear that 'etouser' is calculated on the backend incorrectly for systems that use AC battery charged (e.g. during cheap nighttime rates)
    pacToGridToday = 0.0
    pacToUserToday = 0.0
    pdischargeToday = 0.0
    ppvToday = 0.0
    sysOutToday = 0.0

    chartData = mix_detail['chartData']
    for time_entry, data_points in chartData.items():
      #For each time entry convert it's wattage into kWh, this assumes that the wattage value is
      #the same for the whole 5 minute window (it's the only assumption we can make)
      #We Multiply the wattage by 5/60 (the number of minutes of the time window divided by the number of minutes in an hour)
      #to give us the equivalent kWh reading for that 5 minute window
      pacToGridToday += float(data_points['pacToGrid']) * (5/60)
      pacToUserToday += float(data_points['pacToUser']) * (5/60)
      pdischargeToday += float(data_points['pdischarge']) * (5/60)
      ppvToday += float(data_points['ppv']) * (5/60)
      sysOutToday += float(data_points['sysOut']) * (5/60)

    mix_detail['calculatedPacToGridTodayKwh'] = round(pacToGridToday,2)
    mix_detail['calculatedPacToUserTodayKwh'] = round(pacToUserToday,2)
    mix_detail['calculatedPdischargeTodayKwh'] = round(pdischargeToday,2)
    mix_detail['calculatedPpvTodayKwh'] = round(ppvToday,2)
    mix_detail['calculatedSysOutTodayKwh'] = round(sysOutToday,2)

    #Option to print mix_detail again now we've made the additions
    #pp.pprint(mix_detail)

    dashboard_data = api.dashboard_data(plant_id)
    #pp.pprint(dashboard_data)

    indent_print("*TODAY TOTALS BREAKDOWN*", 4)
    indent_print("Self generation total (batteries & solar - from API) (kwh): %s"%(mix_detail['eCharge']),6)
    indent_print("Load consumed from solar (kwh): %s"%(mix_detail['eChargeToday']),6)
    indent_print("Load consumed from batteries (kwh): %s"%(mix_detail['echarge1']),6)
    indent_print("Self consumption total (batteries & solar - from API) (kwh): %s"%(mix_detail['eChargeToday1']),6)
    indent_print("Load consumed from grid (kwh): %s"%(mix_detail['etouser']),6)
    indent_print("Total imported from grid (Load + AC charging) (kwh): %s"%(dashboard_data['etouser'].replace('kWh','')),6)
    calculated_consumption = float(mix_detail['eChargeToday']) + float(mix_detail['echarge1']) + float(mix_detail['etouser'])
    indent_print("Load consumption (calculated) (kwh): %s"%(round(calculated_consumption,2)),6)
    indent_print("Load consumption (API) (kwh): %s"%(mix_detail['elocalLoad']),6)

    indent_print("Exported (kwh): %s"%(mix_detail['eAcCharge']), 6)

    solar_to_battery = round(float(mix_info['epvToday']) - float(mix_detail['eAcCharge']) - float(mix_detail['eChargeToday']),2)
    indent_print("Solar battery charge (calculated) (kwh): %s"%(solar_to_battery), 6)
    ac_to_battery = round(float(mix_info['eBatChargeToday']) - solar_to_battery,2)
    indent_print("AC battery charge (calculated) (kwh): %s"%(ac_to_battery), 6)
    print("")

    indent_print("*TODAY TOTALS COMPARISONS*", 4)

    indent_print("Export to Grid (kwh) - TRUSTED:", 6)
    indent_print("mix_totals['etoGridToday']: %s"%(mix_totals['etoGridToday']), 8)
    indent_print("mix_detail['eAcCharge']: %s"%(mix_detail['eAcCharge']), 8)
    indent_print("mix_detail['calculatedPacToGridTodayKwh']: %s"%(mix_detail['calculatedPacToGridTodayKwh']), 8)
    print("")

    indent_print("Imported from Grid (kwh) - TRUSTED:", 6)
    indent_print("dashboard_data['etouser']: %s"%(dashboard_data['etouser'].replace('kWh','')), 8)
    indent_print("mix_detail['calculatedPacToUserTodayKwh']: %s"%(mix_detail['calculatedPacToUserTodayKwh']), 8)
    print("")

    indent_print("Battery discharge (kwh) - TRUSTED:", 6)
    indent_print("mix_info['eBatDisChargeToday']: %s"%(mix_info['eBatDisChargeToday']), 8)
    indent_print("mix_totals['edischarge1Today']: %s"%(mix_totals['edischarge1Today']), 8)
    indent_print("mix_detail['echarge1']: %s"%(mix_detail['echarge1']), 8)
    indent_print("mix_detail['calculatedPdischargeTodayKwh']: %s"%(mix_detail['calculatedPdischargeTodayKwh']), 8)
    print("")

    indent_print("Solar generation (kwh) - TRUSTED:", 6)
    indent_print("mix_info['epvToday']: %s"%(mix_info['epvToday']), 8)
    indent_print("mix_totals['epvToday']: %s"%(mix_totals['epvToday']), 8)
    indent_print("mix_detail['calculatedPpvTodayKwh']: %s"%(mix_detail['calculatedPpvTodayKwh']), 8)
    print("")

    indent_print("Load Consumption (kwh) - TRUSTED:", 6)
    indent_print("mix_totals['elocalLoadToday']: %s"%(mix_totals['elocalLoadToday'],), 8)
    indent_print("mix_detail['elocalLoad']: %s"%(mix_detail['elocalLoad']), 8)
    indent_print("mix_detail['calculatedSysOutTodayKwh']: %s"%(mix_detail['calculatedSysOutTodayKwh']), 8)
    print("")


    #This call gets all of the instantaneous values from the system e.g. current load, generation etc.
    mix_status = api.mix_system_status(device_sn, plant_id)
    #pp.pprint(mix_status)
    #NOTE - There are some other values available in mix_status, however these are the most useful ones
    indent_print("*CURRENT VALUES*",4)
    indent_print("==Batteries==",4)
    indent_print("Charging Batteries at (kw): %s"%(mix_status['chargePower']),6)
    indent_print("Discharging Batteries at (kw): %s"%(mix_status['pdisCharge1']),6)
    indent_print("Batteries %%: %s"%(mix_status['SOC']),6)

    indent_print("==PVs==",4)
    indent_print("PV1 wattage: %s"%(mix_status['pPv1']),6)
    indent_print("PV2 wattage: %s"%(mix_status['pPv2']),6)
    calc_pv_total = (float(mix_status['pPv1']) + float(mix_status['pPv2']))/1000
    indent_print("PV total wattage (calculated) - KW: %s"%(round(calc_pv_total,2)),6)
    indent_print("PV total wattage (API) - KW: %s"%(mix_status['ppv']),6)

    indent_print("==Consumption==",4)
    indent_print("Local load/consumption - KW: %s"%(mix_status['pLocalLoad']),6)

    indent_print("==Import/Export==",4)
    indent_print("Importing from Grid - KW: %s"%(mix_status['pactouser']),6)
    indent_print("Exporting to Grid - KW: %s"%(mix_status['pactogrid']),6)

