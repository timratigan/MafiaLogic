from load_data import *

def simulate_game(player_assignment,known_player_states):
    # Initalize Game State:
    game_state = {"Environmental Variables":[0,"Night","Full"],"Player States":[]}
    for player, role in player_assignment.items():
        player_state = {"Name":player, "Role":role, "Alive":True}
        game_state["Player States"].append(player_state)
    print(game_state)
    # Phases: Day, Night
    for day in range(2):
        if day != 0:
            # Day
            print("Day", day)
            # Morning Email
            print("Morning Email, people update suspicions with new information")
            # Trial
            print("Trial Occurs, based upon suspicions and negotiation, an action is taken")
        # Night
        print("Night", day)
        print("Night actions occur, in the proper turn order")
    # Win Conditions:


# Notes from Seth:
# Suspicion Matrix for each faction 
# Player State: Role, Alive/Dead, AP, Base DP, Extra DP, Poisoned, Infected, Doused, Target, 
# Visit_History, Jailed, RBed, Love, Trapped, Hexxed, Bombed-1=no bomb: ticker otherwise, Vested 
# Spy suspicions approach reality slowly 
# ^ store as array of dictionaries? 

# Game State: Player States + Suspicion Matrices, Moon/Full Moon 

# Check victory conditions 