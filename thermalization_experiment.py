import numpy as np
import matplotlib.pyplot as plt
from itertools import permutations
# In this file, we test correlation lengths for the problem (and earlier that we in fact recover the correct probability distribution)
# and find that about 6N step are needed, N being the number of steps, are needed to reach thermal equilibrium, at least for a random sus_matrix
# it is possible that for a more specific sus_matrix the thermalization time could be affected, but we assume that if we start near a probability 
# maximum (and so energy minimum), we may rely on a similar thermalization time. Experiments are carried out for T = 1. 
# np.random.seed(0)
# N = 8 -> 50 thermal
# N = 6 -> 30 thermal
# N = 10 -> 60
# N = 15 -> 100, Conjecture: ~ N*6 steps are needed
# N = 25 -> 150 
# N = 50 -> ~300
# N = 65 -> ~400

N = 65
thermalization = 1000
trials = 15000
test = 700
corr_lengths = range(test)
curr_length = np.zeros(test)

def assignment_probability(assignment,sus_square):
    probability = 1
    for player_index in range(N):
        probability *= sus_square[player_index, assignment[player_index]]
    return probability

def assignment_energy(assignment,sus_square):
    return -np.log(assignment_probability(assignment,sus_square))

def diff(assignment1,assignment2):
    res = 0
    for i in range(N):
        if assignment1[i] == assignment2[i]:
            res += 1
    return res

sus_square = np.random.rand(N,N)
# Include known submatrix
for i in range(N):
    sus_square[i,N-i-1] *= 1

assignment = np.array(range(N))
current_energy = assignment_energy(assignment,sus_square)
times = []
lengths = []
assignments = np.zeros((thermalization,N))
for t in range(thermalization + trials):
    assignments[t % thermalization] = assignment.copy()
    random_index = np.random.randint(N,size=2) # Random index permutation
    candidate_assignment = assignment.copy()
    candidate_assignment[random_index[0]] = assignment[random_index[1]]
    candidate_assignment[random_index[1]] = assignment[random_index[0]]
    new_energy = assignment_energy(candidate_assignment,sus_square)
    energy_difference = new_energy - current_energy
    if np.random.random() < np.exp(-1*energy_difference):
        assignment = candidate_assignment
        current_energy = new_energy
    if t > thermalization:
        for length_index in range(len(corr_lengths)):
            curr_length[length_index] = diff(assignments[t % thermalization],assignments[(t - corr_lengths[length_index]) % thermalization])
        lengths.append(curr_length.copy())
lengths = np.array(lengths)
averages = np.sum(lengths,axis=0)/trials
plt.plot(averages)
plt.savefig("graph.png")
