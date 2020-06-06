from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from extra_functions import *
import numpy as np
import re
import matplotlib.pyplot as plt
from time import time
from bisect import bisect_right
import numpy as np
import random
import json

output = open('files/output.txt', 'w')
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1e3B3EkGI5qY_cn3XO-A2igWTVyWFTBx4lNdomTOYmgQ'
KNOWN_GAME_RANGE = 'Known!A2:E67'
ROLE_RANGE = 'Roles!A2:J63'

creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API
sheet = service.spreadsheets()
known_result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,range=KNOWN_GAME_RANGE).execute()
roles_result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,range=ROLE_RANGE).execute()
known_game_values = known_result.get('values', [])
roles_values = roles_result.get('values', [])
known_game_state = {"Environment Variables":{"Day":1,"Time":"Day","Moon":"Full"},"Player States":{},"Suspicions":[[]]}
role_info = {}
role_names = []
teams = {"Town":[], "Mafia":[], "Coven":[], "Vampires":[], "Serial_Killers":[], "Werewolves":[]}
valid_immunities = ["","Bite","Bite_Kill","Role_Block","Role_Block_Kill","Control","Control_Kill","Detection","Detection_Kill"]

if not roles_values:
    print('No roles data found')
else:
    for row in roles_values:
        role_name = row[0].strip()
        role_names.append(role_name)
        role_desc = {}
        role_desc["Team"] = row[1]
        if role_desc["Team"] != "Neutral":
            teams[role_desc["Team"]].append(role_name)
        role_desc["Attack_Power"] = int(row[2])
        role_desc["Defense_Power"] = int(row[3])
        role_desc["Immunities"] = []
        for immunity in row[4].split(","):
            imm = immunity.strip()
            if imm in valid_immunities:
                role_desc["Immunities"].append(imm)
            else:
                print(imm,"is an invalid immunitiy")
        role_desc["Average_Number"] = float(row[5])
        role_desc["Min_Number"] = int(row[6])
        # Interpret Syntax
        syntax = row[7]
        role_desc["Actions"] = []
        for action_syntax in syntax.split(","):
            action_syntax = action_syntax.strip()
            role_desc["Actions"].append(action_syntax)
        role_info.update({role_name:role_desc})

players = []
num_players = 66; num_roles = 62
sus_matrix = np.zeros((num_players,num_roles))

if not known_game_values:
    print('No known game data found.')
else:
    for row in known_game_values:
        player_name = row[0].strip()
        players.append(player_name)
        player_state = {}
        role_input = row[2]
        if role_input == '' or role_input == '?':
            for role_name in role_names:
                sus_matrix[players.index(player_name),role_names.index(role_name)] = role_info[role_name]["Average_Number"]
        elif role_input.replace(" ","_") in role_names:
            player_state["Role"] = role_input.replace(" ","_")
            sus_matrix[players.index(player_name),] = np.zeros(num_roles)
            sus_matrix[players.index(player_name),role_names.index(player_state["Role"])] = 1
        elif role_input[1:-1] in teams.keys():
            sus_matrix[players.index(player_name),] = np.zeros(num_roles)
            team_roles = teams[role_input[1:-1]]
            for team_role in team_roles:
                sus_matrix[players.index(player_name),role_names.index(team_role)] = role_info[team_role]["Average_Number"]
        elif '?' in role_input[-1]:
            sus_matrix[players.index(player_name),] = np.zeros(num_roles)
            for role_name in role_input.split('?'):
                if role_name != '':
                    role_name = role_name.strip().replace(" ","_")
                    sus_matrix[players.index(player_name),role_names.index(role_name)] = role_info[role_name]["Average_Number"]
        else:
            print("Warning: Role Input Error on", role_input)
        player_state["Alive"] = (row[3] == "Alive")
        known_game_state["Player States"].update({player_name:player_state})
        
# Normalize
for player_index in range(num_players):
    sus_matrix[player_index,] /= np.sum(sus_matrix[player_index,])
known_game_state["Suspicions"] = sus_matrix.tolist()

# loading in data and packages and configuring game information
# defined as groups of players which may share information

"""
# (optional) Load in everything we KNOW about the game
with open('files/known_game_state.json') as json_file:
    known_game_state = json.load(json_file)
    print("Game State Loaded")
"""

investigation_groups = [["Investigator", "Consigliere", "Mayor", "Survivor", "Plaguebearer", "Pestilence"],["Bookie", "Priest", "Vampire", "Eldest_Vampire","Jester"],\
    ["Lookout", "Escort", "Siren", "Consort", "Serial_Killer"],["Vampire_Hunter", "Amnesiac", "Medusa", "Psychic", "Disguiser"],\
        ["Sheriff", "Executioner", "Werewolf", "Janitor", "Moosehead"],["Doctor", "Spy", "Lawyer", "Potion_Master", "Hex_Master"],\
            ["Puppeteer", "Hacker", "Eros", "Tracker", "Hypnotist"],["Jailer", "Chef", "Poisoner", "Guardian_Angel", "Coven_Leader"],\
                ["Vigilante", "Veteran", "Pirate", "Mafioso", "Ambusher"],["Bodyguard", "Godfather", "Medium", "Crusader", "Thug"],["Juggernaut"],\
                    ["Arsonist", "Retributionist", "Necromancer", "Trapper", "Bomber"],["Transporter", "House_Painter", "Therapist", "Mirage", "Apprentice"]]

num_players = len(players)
num_roles = len(role_info)
role_names = list(role_info.keys())
role_stats_list = list(role_info.values())

# Check the total number of averages:
total_expected = 0
for role in role_info.values():
    total_expected += float(role["Average_Number"])
if total_expected != num_players:
    print("Warning: # of players unequal to God expectations:", num_players, "!=", total_expected)

epsilon = 10**(-14)