from MafiaLogic.game import MafiaGame
from MafiaLogic.common import Team

test = MafiaGame([[1,'Investigator'],[1,'Psychic']\
    ,[1,'Consigliere'],[1,'Tracker'],[1,'Sheriff'],[1,'Spy']\
        ,[1,'Jailor'],[1,'Werewolf_Hunter'],[1,'Chosen_One']\
            ,[1,'Veteran'],[1,'Chef'],[1,'Bodyguard'],[1,'Doctor']\
                ,[1,'Crusader'],[1,'Trapper'],[1,'Priest'],[1,'Retributionist'],[1,'Transporter'],[1,'Moosehead'],[1,'Escort']\
                    ],\
    ['Ivan','Peter','Cory','Troy','Susan','Sera','Julie',\
        'Wassem','Chet','Victor','Clyde','Boris','Daryl','Carrie',\
            'Trevor','Perry','Roy','Tiffany','Mark','Edd'])
# Max: Invest, Seth: Psychic, Tim: Consig, Emma: Tracker, Bob: Sheriff, etc...

#N0 Actions
test.get_player(0).at_night('investigate',3) #p0 Investigates p1
test.get_player(1).at_night('full_commune')  #p1 full_commune
test.get_player(2).at_night('investigate',1) #p2 consig p1
test.get_player(3).at_night('watch',0) #p3 watch p2
test.get_player(4).at_night('investigate',0) #p4 invest p0
test.get_player(5).at_night('spy',Team.Mafia) # Spy
test.get_player(6).at_night('jail',0) # Jailor
test.get_player(7).at_night('investigate',2) # Werewolf Hunter
test.get_player(8).at_night('attack',3) # Chosen One
test.get_player(9).at_night('vest') # Veteran
test.get_player(10).at_night('poison', 5) # Chef
test.get_player(11).at_night('protect',3) # Bodyguard
test.get_player(11).at_night('vest') # Bodyguard
test.get_player(12).at_night('heal', 8) # Doctor
test.get_player(13).at_night('protect', 3) # Crusader
test.get_player(14).at_night('trap', 3) # Trapper
test.get_player(15).at_night('heal', 0) # Priest
test.get_player(16).at_night('vest') # Retributionist
test.get_player(17).at_night('swap',1,12) # Transporter
test.get_player(18).at_night('disorient',2) # Moosehead
test.get_player(19).at_night('roleblock',10) # Escort

test._advance()
test.print_status()
"""
action 0 2
action 1
action 2 0
advance
advance
vote 0 1
vote 1 2
vote 2 1
advance
vote 0 Guilty
vote 1 Innocent
vote 2 Guilty
advance

"""