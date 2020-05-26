import numpy as np
import matplotlib.pyplot as plt
from itertools import permutations
from bisect import bisect_right
from extra_functions import *
# In this file, we test correlation lengths for the problem (and earlier that we in fact recover the correct probability distribution)
# and find that about 6N step are needed, N being the number of steps, are needed to reach thermal equilibrium, at least for a random sus_matrix
# it is possible that for a more specific sus_matrix the thermalization time could be affected, but we assume that if we start near a probability 
# maximum (and so energy minimum), we may rely on a similar thermalization time. Experiments are carried out for T = 1. 
np.random.seed(0)
# N = 8 -> 50 thermal
# N = 6 -> 30 thermal
# N = 10 -> 60
# N = 15 -> 100, Conjecture: ~ N*6 steps are needed
# N = 25 -> 150 
# N = 50 -> ~300
# N = 65 -> ~400

N = 8
thermalization = 10
trials = 10
runs = 2

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

float_formatter = "{:.5f}".format
np.set_printoptions(formatter={'float_kind':float_formatter})

def simple_sample(sus_square):
    assignment = list(range(N))
    square = sus_square.copy()
    polarization_order = sorted(range(N),key=lambda x: np.std(square[x,:]),reverse=True)
    for player_index in polarization_order:
        square[player_index,:] = np.cumsum(square[player_index,:])
        rand = np.random.random()*square[player_index,N-1]
        assignment[player_index] = min(bisect_right(square[player_index,:],rand),N-1)
        square[:,assignment[player_index]] = np.zeros(N)
    return assignment

sus_square = np.random.rand(N,N)
# Include known submatrix
for i in range(4,N):
    sus_square[i,] = np.zeros(N)
    sus_square[i,i] = 1

# compare encounters with expected encounters
expected_encounters = {}
simple_encounters = {}
prob_sum = 0
encounters = {}
for assignment in permutations(range(N)):
    expected_encounters[tuple(assignment)] = 1
    encounters[tuple(assignment)] = 0
    simple_encounters[tuple(assignment)] = 0
    for i in range(N):
        expected_encounters[tuple(assignment)] *= sus_square[i,assignment[i]]
    prob_sum += expected_encounters[tuple(assignment)]

# Normalize expected encounters
for k,v in expected_encounters.items():
    expected_encounters[k] = expected_encounters[k]/prob_sum*trials*runs

times = []
values = []
avg_value = np.zeros(trials)

for r in range(runs):
    times.append([])
    values.append([])
    assignment = simple_sample(sus_square) # Options for initial permutation
    #assignment = np.random.permutation(range(N))
    current_energy = assignment_energy(assignment,sus_square)
    for t in range(thermalization + trials):
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
                times[r].append(t)
                values[r].append(current_energy)
        if t > thermalization:
            encounters[tuple(assignment)] += 1
            avg_value[t-thermalization] += current_energy
    
for r in range(runs):
    plt.plot(times[r], values[r], color='b', alpha=0.25)
plt.plot(np.array(range(trials)) + thermalization, avg_value/runs, color='r')
plt.savefig("graph.png")

plt.clf()
plt.scatter(np.log(list(encounters.values())),np.log(list(expected_encounters.values())))
plt.plot(np.log(list(encounters.values())),np.log(list(encounters.values())), color='r')
plt.savefig("graph2.png")

for t in range(runs*trials):
    print(tuple(simple_sample(sus_square)))
    simple_encounters[tuple(simple_sample(sus_square))] += 1

plt.clf()
plt.scatter(np.log(list(simple_encounters.values())),np.log(list(expected_encounters.values())))
plt.plot(np.log(list(simple_encounters.values())),np.log(list(simple_encounters.values())), color='r')
plt.savefig("graph3.png")

""" Correlation lengths

test = 50
corr_lengths = range(test)
curr_length = np.zeros(test)

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
"""

    
