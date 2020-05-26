import numpy as np
import re
from extra_functions import *

# loading in  and configuring game information
# defined as groups of players which may share information
teams = ["T", "M", "C", "V", "S", "W"] # Town, Mafia, Coven, Vampires, Serial Killers, Werewolvs

roles = [] # full role information
role_names = [] # names of roles
role_teams = [] # number denoting the affiliation of each role
with open("roles.txt","r") as role_reader:
    for role in role_reader:
        roles.append(role.split())
        role_names.append(roles[-1][0])

investigation_groups = [["Investigator", "Consigliere", "Mayor", "Survivor", "Plaguebearer", "Pestilence"],["Bookie", "Priest", "Vampire", "Eldest_Vampire","Jester"],\
    ["Lookout", "Escort", "Siren", "Consort", "Serial_Killer"],["Vampire_Hunter", "Amnesiac", "Medusa", "Psychic", "Disguiser"],\
        ["Sheriff", "Executioner", "Werewolf", "Janitor", "Moosehead"],["Doctor", "Spy", "Lawyer", "Potion_Master", "Hex_Master"],\
            ["Puppeteer", "Hacker", "Eros", "Tracker", "Hypnotist"],["Jailer", "Chef", "Poisoner", "Guardian_Angel", "Coven_Leader"],\
                ["Vigilante", "Veteran", "Pirate", "Mafioso", "Ambusher"],["Bodyguard", "Godfather", "Medium", "Crusader", "Thug"],["Juggernaut"],\
                    ["Arsonist", "Retributionist", "Necromancer", "Trapper", "Bomber"],["Transporter", "House_Painter", "Therapist", "Mirage", "Apprentice"]]

players = []
with open("players.txt","r") as player_reader:
    for player in player_reader:
        players.append(player[:-1])

player_count = len(players)
role_count = len(roles)

# Initialize game state
# Randomly assign roles:
print(role_count, player_count)

