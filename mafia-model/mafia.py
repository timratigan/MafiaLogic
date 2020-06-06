from load_data import *
from generate_players import *
from simulate_game import *

random.seed(0)
np.random.seed(0)
# Game Logic Counts (i.e. unique roles)
known_counts = {"Jailer":1,"Spy":1,"Veteran":1,"Mayor":1,"Medium":1,"Godfather":1,"Mafioso":1,"Coven_Leader":1,"Puppeteer":1,"Plaguebearer":1,"Juggernaut":1,"Eros":1,"Eldest_Vampire":1,"Pestilence":0}
# Personally known counts
known_counts.update({"Siren":2,"Medusa":2,"Poisoner":1,"Hex_Master":1,"Necromancer":1,"Potion_Master":1,"Mirage":1})

GOD_RANDOMNESS = 0.4 # Assume that each role appears with \pm GOD_RANDOMNESS*100 %. 
MAX_ROLE_COUNT = 3 # Maximum number of a given role

for t in range(0):
    role_counts = generate_role_counts(GOD_RANDOMNESS,MAX_ROLE_COUNT,known_counts)
    anomalies = {}
    for role_index in range(num_roles):
        if role_counts[role_index] != 1:
            anomalies.update({role_names[role_index]:role_counts[role_index]})
    print(anomalies)

role_counts = generate_role_counts(GOD_RANDOMNESS,MAX_ROLE_COUNT,known_counts)

# Start with flat sus_matrix
sus_matrix = np.ones((num_players,num_roles))/num_roles + 0*np.random.rand(num_players,num_roles) # Matrix containing suspicions, sus_matrix[player,role] is % chance player is role 

"""
# Hint sus_matrix with known roles
for known_name, known_role in known_assignments.items():
    sus_matrix[players.index(known_name),role_names.index(known_role)]*=2
"""

# Load in sus_matrix
sus_matrix = np.array(known_game_state["Suspicions"])

# Normalize
for player_index in range(num_players):
    sus_matrix[player_index,] /= np.sum(sus_matrix[player_index,])

player_assignment = generate_simple_assignment(sus_matrix, role_counts)
print(player_assignment)
# Game Simulation: Given your suspicions, what is the chance of various events occuring?
# Updating Priors: Given what has played out, here are the computer's suspicions (Targeted Monte-Carlo from beginning)

# Simulate (a stupid) game forward from the known game state, given a role assignment
simulate_game(player_assignment, known_game_state)

