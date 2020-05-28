from load_data import *

def check_win(game_state):
    for player, player_state in game_state["Player States"]:
        if player_state["Alive"]:
            print(player)

# Notes from Seth:
# Suspicion Matrix for each faction 
# Player Name: Role, Team, Alive/Dead, AP, Base DP, Extra DP, Poisoned, Infected, Doused, Target, 
# Visit_History, Jailed, RBed, Love, Trapped, Hexxed, Bombed-1=no bomb: ticker otherwise, Vested 
# Spy suspicions approach reality slowly 
# ^ store as array of dictionaries? 
# Attributes of every player, and their default values if not specified
default_attributes = {"Team": None, "Alive": False, "Attack_Power": 0, "Defense_Power": 0, \
        "Poisoned": False, "Infected": False, "Doused": False, "Target": None, "Visit_History": None, \
            "Jailed": False, "Roleblocked": False, "Love": False, "Trapped": -1, "Hexxed": False, "Bombed": -1,\
                "Vested": False} 

# Special attributes of roles, along with defaults
role_attributes = {"Investigator":{"Taken":0}}

def simulate_game(player_assignment,known_game_state):
    # Initalize Game State:
    game_state = known_game_state.copy()
    
    for player_name, player_role in player_assignment.items():
        game_state["Player States"][player_name]["Role"] = player_role
    json.dump(game_state, output)

    # Storing Game History: 
    # Space of things which can happen 
    # Actions: 2 players, 1 action (Game State) 

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



# Game State: Player States + Suspicion Matrices, Moon/Full Moon 

# Check victory conditions 