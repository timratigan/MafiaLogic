from load_data import *

def simulate_game(player_assignment,known_game_state):
    # Initalize Game State:
    game_state = known_game_state.copy()
    print(game_state["Player States"]["Max Jerdee"])
    for player_name, player_role in player_assignment.items():
        game_state["Player States"][player_name]["Role"] = player_role
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