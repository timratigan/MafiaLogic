import numpy as np
import random
from load_data import *
import matplotlib.pyplot as plt 
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
        roles[role_names.index(role_name)][5] = role_count # We rewrite the mean so that the next step cannot mess with the known information

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

def temperature(t): # Choose the appropriate temperature for interation step t
    return 1 + 10000*np.exp(-t/1000)

def assignment_energy(assignment, sus_square): # Calculate the "energy" (- log of culmulative probability) of a given arrangement
    probability = 1
    chance_sum = 0
    for player_index in range(num_players):
        probability *= sus_square[player_index, assignment[player_index]]
        chance_sum += sus_square[player_index, assignment[player_index]]
    return -np.log(probability + 0*chance_sum) 

def check_assignment(assignment, role_indices_extended):
    known_roles = ["Coven_Leader", "Siren", "Siren", "Medusa", "Medusa", "Poisoner", "Puppeteer", "Hex_Master", "Necromancer", "Potion_Master", "Mirage"]
    correct = 0
    for player_index in range(54,65):
        if known_roles[player_index - 54] == role_names[role_indices_extended[assignment[player_index]]]:
            correct += 1
    return correct

def generate_player_assignment(sus_matrix, role_counts):
    # Question: Given a suspicion matrix of priors, i.e. likelihood that each player is each role, pull a player distribution
    # Answer? For each possible combination, can compute the probability given the matrix, and then sample
    # But this is prohibitively expensive (65! options), so we instead adopt a thermalization strategy, where the energy is (-log of) the culmulative probability

    # Extending sus_matrix to a square
    sus_square = np.zeros((num_players,num_players))
    role_indices_extended = []
    for role_index in range(num_roles):
        for i in range(role_counts[role_index]):
            role_indices_extended.append(role_index)

    for player_index in range(num_players):
        for extended_role_index in range(num_players):
            sus_square[player_index,extended_role_index] = sus_matrix[player_index,role_indices_extended[extended_role_index]]
    
    # Thermalization 
    # Generate Random Starting Point 
    assignment = np.random.permutation(range(num_players))
    current_energy = assignment_energy(assignment,sus_square)
    positions = []
    for t in range(10000):
        random_index = np.random.randint(num_players,size=2) # Random index permutation
        candidate_assignment = assignment.copy()
        candidate_assignment[random_index[0]] = assignment[random_index[1]]
        candidate_assignment[random_index[1]] = assignment[random_index[0]]
        new_energy = assignment_energy(candidate_assignment,sus_square)
        energy_difference = new_energy - current_energy
        if np.random.random() < np.exp(-temperature(t)*energy_difference):
            assignment = candidate_assignment
            current_energy = new_energy
            positions.append([t,current_energy,check_assignment(assignment,role_indices_extended)])
    positions = np.array(positions)
    plt.plot(positions[:,0],(positions[:,1]-250)*5)
    plt.plot(positions[:,0],positions[:,2]*10)
    plt.savefig("graph.png")
    print(check_assignment(assignment,role_indices_extended))
    # Match result with player assignment
    player_assignment = {}
    for player_index in range(num_players):
        player_assignment.update({players[player_index]:role_names[role_indices_extended[assignment[player_index]]]})
    
    return player_assignment


