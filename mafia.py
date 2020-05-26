
# Loading in  and configuring game information
teams = ["Mafia", "Coven", "Vampires", "Plaguebearer", "Pestilence", "Arsonist", "Serial Killers", "Werewolves", "Juggernaut", "Eros"]

roles = []
with open("roles.txt","r") as role_reader:
    for role in role_reader:
        roles.append(role[:-1])

players = []
with open("players.txt","r") as player_reader:
    for player in player_reader:
        players.append(player[:-1])

player_count = len(players)
role_count = len(roles)

print(role_count, player_count)