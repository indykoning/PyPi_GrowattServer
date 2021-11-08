import growattServer

api = growattServer.GrowattApi()
login_response = api.login(<username>, <password>)
#Get a list of growatt plants.
print(api.plant_list(login_response['user']['id']))
