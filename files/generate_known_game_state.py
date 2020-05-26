import json 

known_game_state = {"Environment Variables":[],"Player States":[]}

with open('files/known_game_state.json', 'w') as json_file:
  json.dump(known_game_state, json_file)
