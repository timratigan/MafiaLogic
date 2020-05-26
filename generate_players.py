import numpy as np
import random
from load_data import *
def generate_role_counts(GOD_RANDOMNESS=0.4,MIN_ROLE=1,MAX_ROLE=5,MAX_ROLE_MULT=2,known_counts={},print_flag=False):
    # Use God expectations to produce role numbers:
    role_counts = np.zeros(num_roles,dtype=int)
    # Generate a random role_count from normal distributions:
    for role_index in range(num_roles):
        role = roles[role_index]
        role_counts[role_index] = np.minimum(np.round(random.gauss(role[5],role[5]*GOD_RANDOMNESS)),role[5]*MAX_ROLE_MULT)
    
    # Enforce minimum/maximum roles:
    role_counts = np.minimum(np.maximum(MIN_ROLE*np.ones(num_roles),role_counts),MAX_ROLE*np.ones(num_roles))
   
    # Enforce the unique/none roles and :
    for unique_role in unique_roles:
        role_counts[role_names.index(unique_role)] = 1
    for none_role in none_roles:
        role_counts[role_names.index(none_role)] = 0
    for (role_name, role_count) in known_counts.items():
        role_counts[role_names.index(role_name)]=role_count
    # We rewrite the mean so that the next step cannot mess with the known information

    # Produce the proper total number of players by adjusting the outliers back to the mean
    residues = {}
    for role_index in range(num_roles):
        role = roles[role_index]
        residues.update({role_index:role_counts[role_index] - role[5] + random.random()*epsilon}) #Tie-breaking
    excess = int(np.sum(role_counts) - num_players)
    
    sorted_residues = sorted(residues.items(), key=lambda x: x[1], reverse=(excess > 0))
    
    for role_pair in sorted_residues[:np.abs(excess)]:
        if excess > 0:
            role_counts[role_pair[0]] -= 1
        else:
            role_counts[role_pair[0]] += 1

    return role_counts.astype(int)

def generate_player_assignment():

    # Question: Given a suspicion matrix of priors, i.e. likelihood that each player is each role, pull a player distribution
    # Answer? For each possible combination, can compute the probability given the matrix, and then sample
    # Start with flat suspicion matrix, except for the known ones:
    suspicion_matrix = np.ones((num_players,num_roles))/num_roles
    player_assignment = {}
    return player_assignment
