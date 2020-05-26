import numpy
# loading in  and configuring game information
# defined as groups of players which may share information
teams = ["Town", "Mafia", "Coven", "Serial Killers", "Werewolves"]

roles = []
role_teams = [] # number denoting the affiliation of each role
with open("roles.txt","r") as role_reader:
    for role in role_reader:
        roles.append(role[:-1])

investigation_groups = [["Investigator", "Consigliere", "Mayor", "Survivor", "Plaguebearer"],["Bookie", "Priest", "Vampire", "Jester"],["Lookout", "Escort", "Siren", "Consort", "Serial Killer"],["Vampire Hunter", "Amnesiac", "Medusa", "Psychic", "Disguise Master"],["Sheriff", "Executioner", "Werewolf", "Janitor", "Moosehead"],["Doctor", "Spy", "Lawyer", "Potion Master", "Hex Master"],["Puppeteer", "Hacker", "Eros", "Tracker", "Hypnotist"],["Jailor", "Chef", "Poisoner", "Guardian Angel", "Coven Leader"],["Vigilante", "Veteran", "Pirate", "Ambusher"],["Bodyguard", "Godfather", "Arsonist", "Crusader", "Thug"],["Transporter", "House Painter", "Therapist", "Mirage", "Apprentice"]]

players = []
with open("players.txt","r") as player_reader:
    for player in player_reader:
        players.append(player[:-1])

player_count = len(players)
role_count = len(roles)

print(role_count, player_count)

# Initialize game state
# Randomly assign roles:

