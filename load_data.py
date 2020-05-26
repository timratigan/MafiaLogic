import numpy as np
import re
import matplotlib.pyplot as plt
from time import time
from bisect import bisect_right
import numpy as np
import random
import json
from extra_functions import *

# loading in data and packages and configuring game information
# defined as groups of players which may share information
teams = ["T", "M", "C", "V", "S", "W"] # Town, Mafia, Coven, Vampires, Serial Killers, Werewolvs

roles = [] # full role information
role_names = [] # names of roles
role_teams = [] # number denoting the affiliation of each role

with open("files/roles.txt","r") as role_reader:
    for role in role_reader:
        current_role = role.split()
        if current_role[0] != "Name":
            roles.append([str(current_role[0]),str(current_role[1]),int(current_role[2]),int(current_role[3]),str(current_role[4]),float(current_role[5]), int(current_role[6])])
            role_names.append(str(current_role[0]))

investigation_groups = [["Investigator", "Consigliere", "Mayor", "Survivor", "Plaguebearer", "Pestilence"],["Bookie", "Priest", "Vampire", "Eldest_Vampire","Jester"],\
    ["Lookout", "Escort", "Siren", "Consort", "Serial_Killer"],["Vampire_Hunter", "Amnesiac", "Medusa", "Psychic", "Disguiser"],\
        ["Sheriff", "Executioner", "Werewolf", "Janitor", "Moosehead"],["Doctor", "Spy", "Lawyer", "Potion_Master", "Hex_Master"],\
            ["Puppeteer", "Hacker", "Eros", "Tracker", "Hypnotist"],["Jailer", "Chef", "Poisoner", "Guardian_Angel", "Coven_Leader"],\
                ["Vigilante", "Veteran", "Pirate", "Mafioso", "Ambusher"],["Bodyguard", "Godfather", "Medium", "Crusader", "Thug"],["Juggernaut"],\
                    ["Arsonist", "Retributionist", "Necromancer", "Trapper", "Bomber"],["Transporter", "House_Painter", "Therapist", "Mirage", "Apprentice"]]

players = []
with open("files/players.txt","r") as player_reader:
    for player in player_reader:
        players.append(player[:-1])

num_players = len(players)
num_roles = len(roles)

# Randomly assign roles:
print("Number of roles:", num_roles, "Number of players:", num_players)
unique_roles = ["Jailer","Spy","Veteran","Mayor","Medium","Godfather","Mafioso","Coven_Leader","Puppeteer","Plaguebearer","Juggernaut","Eros","Eldest_Vampire"]
none_roles = ["Pestilence"] 

# Check the total number of averages:
total_expected = 0
for role in roles:
    total_expected += float(role[5])
if total_expected != num_players:
    print("Warning: # of players unequal to God expectations:", num_players, "!=",total_expected)

known_game_state = json.loads('files/known_game_state.json')

epsilon = 10**(-14)