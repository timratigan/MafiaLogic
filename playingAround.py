from MafiaLogic.game import MafiaGame
from MafiaLogic.common import Team

test = MafiaGame([[1,'Investigator'],[1,'Psychic']\
    ,[1,'Consigliere'],[1,'Tracker'],[1,'Sheriff'],[1,'Spy']\
        ,[1,'Jailor']],\
    ['Max','Seth','Tim','Emma','Bob','Bert','Bertha'])
# Max: Invest, Seth: Psychic, Tim: Consig, Emma: Tracker, Bob: Sheriff
test.print_status()
#N0 Actions
test.get_player(0).at_night('investigate',3) #p0 Investigates p1
test.get_player(1).at_night('full_commune')  #p1 full_commune
test.get_player(2).at_night('investigate',1) #p2 consig p1
test.get_player(3).at_night('full_track',0) #p3 track p2
test.get_player(4).at_night('investigate',0) #p4 invest p0
test.get_player(5).at_night('spy',Team.Mafia) 
test.get_player(6).at_night('jail',0) 
test.get_player(6).at_night('execute',0) 
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