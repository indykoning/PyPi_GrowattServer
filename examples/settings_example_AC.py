import growattServer
import sys
import json
'''
Sample script to set AC battery charging
Takes commandline arguments for terminal SOC, start time, end time, 
    and whether to run, with default arguments if none are given
Tested on an SPA3000
'''

# check for SOC percent and whether to run 
if len(sys.argv) != 7:
    SOC = '40'
    startH = '0'
    startM = '40'
    endH = '04'
    endM = '30'
    run = '1'
else:
    SOC = str(sys.argv[1])
    startH = '{:02.0f}'.format(int(sys.argv[2]))
    startM = '{:02.0f}'.format(int(sys.argv[3]))
    endH = '{:02.0f}'.format(int(sys.argv[4]))
    endM = '{:02.0f}'.format(int(sys.argv[5]))
    run = str(sys.argv[6])

api = growattServer.GrowattApi()

# This part needs to be adapted by the user
login_response = api.login('USERNAME_AS_STRING',
                           'PASSWORD_AS_STRING')

if login_response['success']:
    # Get a list of growatt plants.
    plant_list = api.plant_list(login_response['user']['id'])
    plant = plant_list['data'][0]
    plant_id = plant['plantId']
    plant_info = api.plant_info(plant_id)
    device = plant_info['deviceList'][0]
    device_sn = device['deviceSn']

    # All parameters need to be given, including zeros
    # All parameters must be strings
    schedule_settings = ['100',          # Charging power %
                         SOC,            # Stop charging at SoC %
                         startH, startM, # Schedule 1 - Start time
                         endH, endM,     # Schedule 1 - End time
                         run,            # Schedule 1 - Enabled/Disabled (1 = Enabled)
                         '00','00',      # Schedule 2 - Start time
                         '00','00',      # Schedule 2 - End time
                         '0',            # Schedule 2 - Enabled/Disabled (1 = Enabled)
                         '00','00',      # Schedule 3 - Start time
                         '00','00',      # Schedule 3 - End time
                         '0']            # Schedule 3 - Enabled/Disabled (1 = Enabled)

    response = api.update_ac_inverter_setting(device_sn,
                                              'spa_ac_charge_time_period',
                                              schedule_settings)
else:
    response = login_response
print(json.dumps(response))
