import growattServer

api = growattServer.GrowattApi()

username = input("Enter username:")
password = input("Enter password:")
login_response = api.login(username, password)

# Get a list of growatt plants.
print(api.plant_list(login_response['user']['id']))
