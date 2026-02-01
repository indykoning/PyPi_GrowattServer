import getpass
import pprint

import growattServer

"""
This is a very trivial script that logs into a user's account and prints out useful data for a "NOAH" system.
This has been tested against my personal system (NOAH2000) which is a 2kW Balcony Storage system.

Throughout the script there are points where 'pp.pprint' has been commented out. If you wish to see all the data that is returned from those
specific library calls, just uncomment them and they will appear as part of the output.
"""

pp = pprint.PrettyPrinter(indent=4)

"""
A really hacky function to allow me to print out things with an indent in-front
"""
def indent_print(to_output, indent) -> None:
  indent_string = ""
  for _x in range(indent):
    indent_string += " "
  print(indent_string + to_output)

#Prompt user for username
username=input("Enter username:")

#Prompt user to input password
user_pass=getpass.getpass("Enter password:")

api = growattServer.GrowattApi()
login_response = api.login(username, user_pass)

plant_list = api.plant_list(login_response["user"]["id"])
#pp.pprint(plant_list)

print("***Totals for all plants***")
pp.pprint(plant_list["totalData"])
print()

print("***List of plants***")
for plant in plant_list["data"]:
  indent_print("ID: {}, Name: {}".format(plant["plantId"], plant["plantName"]), 2)
print()

for plant in plant_list["data"]:
  plant_id = plant["plantId"]
  plant_name = plant["plantName"]
  plant_info=api.plant_info(plant_id)
  #pp.pprint(plant_info)
  print(f"***Info for Plant {plant_id} - {plant_name}***")
  #There are more values in plant_info, but these are some of the useful/interesting ones
  indent_print("CO2 Reducion: {}".format(plant_info["Co2Reduction"]),2)
  indent_print("Nominal Power (w): {}".format(plant_info["nominal_Power"]),2)
  indent_print("Solar Energy Today (kw): {}".format(plant_info["todayEnergy"]),2)
  indent_print("Solar Energy Total (kw): {}".format(plant_info["totalEnergy"]),2)
  print()
  indent_print("Devices in plant:",2)
  for device in plant_info["deviceList"]:
    device_sn = device["deviceSn"]
    device_type = device["deviceType"]
    indent_print(f"- Device - SN: {device_sn}, Type: {device_type}",4)

  is_noah = api.is_plant_noah_system(plant["plantId"])
  if is_noah["result"] == 1 and (is_noah["obj"]["isPlantNoahSystem"] or is_noah["obj"]["isPlantHaveNoah"]):
    device_sn = is_noah["obj"]["deviceSn"]
    indent_print(f"**NOAH - SN: {device_sn}**",2)

    noah_system = api.noah_system_status(is_noah["obj"]["deviceSn"])
    pp.pprint(noah_system["obj"])
    print()

    noah_infos = api.noah_info(is_noah["obj"]["deviceSn"])
    pp.pprint(noah_infos["obj"]["noah"])
    print()
    indent_print("Remaining battery (" + "%" + "): {}".format(noah_system["obj"]["soc"]),2)
    indent_print("Solar Power (w): {}".format(noah_system["obj"]["ppv"]),2)
    indent_print("Charge Power (w): {}".format(noah_system["obj"]["chargePower"]),2)
    indent_print("Discharge Power (w): {}".format(noah_system["obj"]["disChargePower"]),2)
    indent_print("Output Power (w): {}".format(noah_system["obj"]["pac"]),2)
