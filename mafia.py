import numpy as np
import re
from extra_functions import *
from load_data import *
from generate_players import *
import matplotlib.pyplot as plt
from time import time

random.seed(0)
np.random.seed(0)
# Known information
known_assignments = {"Seth Lovelace":"Coven_Leader", "Irene Hsu":"Siren","AJ Kawczynski":"Siren","Emerson Thomas":"Medusa", "Conor Rachlin":"Medusa", "Lucas Salvador":"Poisoner", "Max Jerdee":"Puppeteer", "Natalia Miller":"Hex_Master", "Cassidy Crone":"Necromancer", "Ed Horan":"Potion_Master", "Emma Moriarty":"Mirage"} 
known_counts = {"Siren":2,"Medusa":2,"Poisoner":1,"Hex_Master":1,"Necromancer":1,"Potion_Master":1,"Mirage":1}

GOD_RANDOMNESS = 0.5 # Assume that each role appears with \pm GOD_RANDOMNESS*100 %. 
MIN_ROLE = 0 # Option to force a minimum number of players in each role
MAX_ROLE = 5 # Option to force a maximum number of players in each role
MAX_ROLE_MULT = 2 # Option to force a maximum number of players in each role as a multiple of the average for the role

""" Testing Role Count Generation
for t in range(10):
    role_counts = generate_role_counts(GOD_RANDOMNESS,MIN_ROLE,MAX_ROLE,MAX_ROLE_MULT,known_counts)
    anomalies = {}
    for role_index in range(num_roles):
        if role_counts[role_index] != 1:
            anomalies.update({role_names[role_index]:role_counts[role_index]})
    print(anomalies)
"""
role_counts = generate_role_counts(GOD_RANDOMNESS,MIN_ROLE,MAX_ROLE,MAX_ROLE_MULT,known_counts)

# Start with flat sus_matrix
sus_matrix = np.ones((num_players,num_roles))/num_roles + 0.01*np.random.rand(num_players,num_roles) # Matrix containing suspicions, sus_matrix[player,role] is % chance player is role 

"""
# Hint sus_matrix with known roles
for known_name, known_role in known_assignments.items():
    sus_matrix[players.index(known_name),role_names.index(known_role)]*=2
"""

# Update sus_matrix with known roles
for known_name, known_role in known_assignments.items():
    sus_matrix[players.index(known_name),]=np.zeros(num_roles)
    sus_matrix[players.index(known_name),role_names.index(known_role)]=1

# Normalize
for player_index in range(num_players):
    sus_matrix[player_index,] /= np.sum(sus_matrix[player_index,])

player_assignment = generate_player_assignment(sus_matrix, role_counts)
print(player_assignment)

# Notes from Seth:
# Suspicion Matrix for each faction 
# Player State: Role, Alive/Dead, AP, Base DP, Extra DP, Poisoned, Infected, Doused, Target, 
# Visit_History, Jailed, RBed, Love, Trapped, Hexxed, Bombed-1=no bomb: ticker otherwise, Vested 
# Spy suspicions approach reality slowly 
# ^ store as array of dictionaries? 

# Game State: Player States + Suspicion Matrices, Moon/Full Moon 

# Check victory conditions 
