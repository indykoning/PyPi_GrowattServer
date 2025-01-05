import growattServer
import datetime
import getpass
import pprint

"""
This is a very trivial script to show how to interface with the configuration settings of a plant and it's inverters
This has been tested against my personal system (muppet3000) which is a hybrid (aka 'mix') inverter system.

Throughout the script there are points where 'pp.pprint' has been commented out. If you wish to see all the data that is returned from those
specific library calls, just uncomment them and they will appear as part of the output.
"""
pp = pprint.PrettyPrinter(indent=4)

#Prompt user for username
username=input("Enter username:")

#Prompt user to input password
user_pass=getpass.getpass("Enter password:")

api = growattServer.GrowattApi()
login_response = api.login(username, user_pass)

plant_list = api.plant_list(login_response['user']['id'])

#Simple logic to just get the first inverter from the first plant
#Expand this using a for-loop to perform for more systems (see mix_example for more detail)
plant = plant_list['data'][0] #This is an array - we just take the first - would need a for-loop for more systems
plant_id = plant['plantId']
plant_name = plant['plantName']
plant_info=api.plant_info(plant_id)


device = plant_info['deviceList'][0] #This is an array - we just take the first - would need a for-loop for more systems
device_sn = device['deviceSn']
device_type = device['deviceType']


#Get plant settings - This is performed for us inside 'update_plant_settings' but you can get ALL of the settings using this
current_settings = api.get_plant_settings(plant_id)
#pp.pprint(current_settings)

#Get mix inverter settings
inverter_settings = api.get_mix_inverter_settings(device_sn)
pp.pprint(inverter_settings)

#Change the timezone of the plant
plant_settings_changes = {
  'plantTimezone': '0'
}
print("Changing the following plant setting(s):")
pp.pprint(plant_settings_changes)
response = api.update_plant_settings(plant_id, plant_settings_changes)
print(response)
print("")




#Set inverter time
now = datetime.datetime.now()
dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
time_settings={
  'param1': dt_string
}
print("Setting inverter time to: %s" %(dt_string))
response = api.update_mix_inverter_setting(device_sn, 'pf_sys_year', time_settings)
print(response)
print("")



#Set inverter schedule (Uses the 'array' method which assumes all parameters are named param1....paramN)
schedule_settings = ["100", #Charging power %
                     "100", #Stop charging SoC %
                     "1",   #Allow AC charging (1 = Enabled)
                     "00", "40", #Schedule 1 - Start time
                     "04", "20", #Schedule 1 - End time
                     "1",        #Schedule 1 - Enabled/Disabled (1 = Enabled)
                     "00", "00", #Schedule 2 - Start time
                     "00", "00", #Schedule 2 - End time
                     "0",        #Schedule 2 - Enabled/Disabled (0 = Disabled)
                     "00", "00", #Schedule 3 - Start time
                     "00", "00", #Schedule 3 - End time
                     "0"]        #Schedule 3 - Enabled/Disabled (0 = Disabled)
print("Setting the inverter charging schedule to:")
pp.pprint(schedule_settings)
response = api.update_mix_inverter_setting(device_sn, 'mix_ac_charge_time_period', schedule_settings)
print(response)
