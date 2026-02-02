import getpass

import growattServer

"""
This is a simple script that demonstrates the various ways to initialise the library to set a User Agent
"""

#Prompt user for username
username=input("Enter username:")

#Prompt user to input password
user_pass=getpass.getpass("Enter password:")



api = growattServer.GrowattApi()
login_response = api.login(username, user_pass)
print("Default initialisation")
print("User-Agent: {}\nLogged in User id: {}".format(api.agent_identifier, login_response["userId"]))
print()

api = growattServer.GrowattApi(True)
login_response = api.login(username, user_pass)
print("Add random ID to default User-Agent")
print("User-Agent: {}\nLogged in User id: {}".format(api.agent_identifier, login_response["userId"]))
print()

api = growattServer.GrowattApi(False, "my-user-id")
login_response = api.login(username, user_pass)
print("Override default User-Agent")
print("User-Agent: {}\nLogged in User id: {}".format(api.agent_identifier, login_response["userId"]))
print()

api = growattServer.GrowattApi(True, "my-user-id")
login_response = api.login(username, user_pass)
print("Override default User-Agent and add random ID")
print("User-Agent: {}\nLogged in User id: {}".format(api.agent_identifier, login_response["userId"]))
print()

api = growattServer.GrowattApi(False, growattServer.GrowattApi.agent_identifier + " - my-user-id")
login_response = api.login(username, user_pass)
print("Extend default User-Agent")
print("User-Agent: {}\nLogged in User id: {}".format(api.agent_identifier, login_response["userId"]))
print()

api = growattServer.GrowattApi(True, growattServer.GrowattApi.agent_identifier + " - my-user-id")
login_response = api.login(username, user_pass)
print("Extend default User-Agent and add random ID")
print("User-Agent: {}\nLogged in User id: {}".format(api.agent_identifier, login_response["userId"]))
print()

