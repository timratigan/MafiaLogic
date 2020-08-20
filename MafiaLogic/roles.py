from typing import Union, List, Tuple

import numpy as np

from MafiaLogic.common import Player, Team, INVEST_RESULTS, Priority

# TOWN
class Investigator(Player):
    TEAM = Team.Town

    def at_night(self, action ,*args, **kwargs):
        if action == 'investigate':
            self.game.add_action(self, self.investigate, Priority.Investigate, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def investigate(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        result = INVEST_RESULTS[player.role]
        self.submit(f'target is one of {result}')

class Tracker(Player):
    """
    On non-full moon nights: choose a person to watch. You see all who visit them in turn order.
    On full moon nights: choose a person to watch. You see the people they visit that night.
    """
    TEAM = Team.Town
    
    def at_night(self, action ,*args, **kwargs):
        if action == 'track':
            assert not self.game.full_moon
            self.game.add_action(self, self.start_track, Priority.Controlling, args, kwargs)
            self.game.add_action(self, self.end_track, Priority.StartDay, args, kwargs)
        elif action == 'full_track':
            assert self.game.full_moon
            self.game.add_action(self, self.start_full_track, Priority.Controlling, args, kwargs)
            self.game.add_action(self, self.end_full_track, Priority.StartDay, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def start_track(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
    
    def end_track(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        if len(player.visited) == 0:
            self.submit(f'{player.name} was visited by noone')
        else:
            self.submit(f'{player.name} was visited by {player.visited}')
    
    def start_full_track(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
    
    def end_full_track(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        if len(player.visits) == 0:
            self.submit(f'{player.name} visited noone')
        else:
            self.submit(f'{player.name} visited {player.visits}')

class Psychic(Player):
    """
    On non-full moon nights: get three random names, at least one of which is evil. 
    On full moon nights: get two random names, at least one of which is good.
    """
    TEAM = Team.Town

    def at_night(self, action, *args, **kwargs):
        if action == 'full_commune':
            assert self.game.full_moon
            self.game.add_action(self, self.full_commune, Priority.Investigate, args, kwargs)
        elif action == 'commune':
            assert not self.game.full_moon
            self.game.add_action(self, self.commune, Priority.Investigate, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def commune(self) -> None:
        player_list = list(self.game.players.values())
        perm = np.random.permutation(player_list)
        results = set()
        # On non-full moon night: get three random names, at least one of which is evil.
        for player in perm:
            if not player.is_good:
                results.add(player)
        results.add(frozenset(np.random.choice(player_list, 2)))
        self.submit(f'one of players {results} is bad')

    def full_commune(self) -> None:
        player_list = list(self.game.players.values())
        perm = np.random.permutation(player_list)
        results = set()
        # On full moon nights: get two random names, at least one of which is good.
        for player in perm:
            if player.is_good:
                results.add(player)
        results.add(np.random.choice(player_list))
        self.submit(f'one of players {results} is good')

class Sheriff(Player):
    """
    Choose one person to investigate. You see whether they are suspicious or not.  (BINARY ANSWER)
    """
    TEAM = Team.Town

    def at_night(self, action ,*args, **kwargs):
        if action == 'investigate':
            self.game.add_action(self, self.investigate, Priority.Investigate, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def investigate(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        suspicious = False
        if player.TEAM in [Team.Vampire, Team.Mafia, Team.Werewolves] or player.hexed: # Unclear what counts as suspicious
            suspicious = True
        if player.detection_immunity: # Assuming this overrides hexes
            suspicious = False
        if suspicious:
            self.submit(f'{player.name} is suspicious')
        else:
            self.submit(f'{player.name} is not suspicious')

class Spy(Player):
    """
    Choose to spy on Mafia, Coven, or Werewolves. Receive bits of their conversation in the morning
    """
    TEAM = Team.Town

    def at_night(self, action ,*args, **kwargs):
        if action == 'spy':
            self.game.add_action(self, self.spy, Priority.StartDay, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def spy(self, team: Team) -> None:
        assert team in [Team.Mafia, Team.Coven, Team.Werewolves]
        self.submit(f'you recieve whispers from team {team}')

class Jailor(Player):
    """
    Speak to the jailed player. May execute your prisoner (max 4 times). If you kill an innocent role, you lose the ability to execute.  Cannot execute on the first night.
    If role-blocked or controlled, they jail but do not execute.	Unique role. If on any night but N0 you fail to execute a SK or WW (full moon only), they attack you.
    """
    TEAM = Team.Town
    attack_power = 3

    def at_night(self, action,*args, **kwargs):
        if action == 'jail':
            self.game.add_action(self, self.jail, Priority.PrevDay, args, kwargs)
        elif action == 'execute':
            self.game.add_action(self, self.execute, Priority.Kill, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def jail(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        self.submit(f'You talk to {player.name}')
        player.submit(f'You were jailed')
        player.jailed = True

    def execute(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        if not self.roleblocked and not self.controlled:
            if self.attack(player):
                bad_kill = False
                if player.TEAM in [Team.Town]: # Unclear
                    bad_kill = True
                if bad_kill:
                    self.attack_power = 0
                    self.submit(f'For killing a good role, your ability to execute is gone')
        else:
            self.submit(f'Failed to execute since roleblocked/controlled')
        
class Werewolf_Hunter(Player):
    """
    Choose a person to investigate. If they are a werewolf, you attack them. 
    If all werewolves are dead, you become a vigilante with one bullet. Werewolves that try to bite you die instantly.	
    Can listen in on the werewolf chat	2	0	Bite immune and kills werewolf		Werewolf Hunter, Basilisk, Seer, Polyjuice Potioneer
    """
    TEAM = Team.Town
    
    def at_night(self, action ,*args, **kwargs):
        if action == 'investigate':
            self.game.add_action(self, self.investigate, Priority.Investigate, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def investigate(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        result = INVEST_RESULTS[player.role]
        self.submit(f'target is one of {result}')




# MAFIA
class Consigliere(Player):
    TEAM = Team.Mafia

    def at_night(self, action, *args, **kwargs):
        if action == 'investigate':
            self.game.add_action(self, self.investigate, Priority.Investigate, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def investigate(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        self.submit(f'target\'s role is {player.role}')
