from typing import Union, List, Tuple

import numpy as np

from MafiaLogic.common import Player, Team, INVEST_RESULTS, Priority


class Investigator(Player):
    TEAM = Team.Town

    def at_night(self, *args, **kwargs):
        self.game.add_action(self.investigate, Priority.Investigate, args, kwargs)

    def investigate(self, player: Player) -> List[List[Player, str]]:
        result = INVEST_RESULTS[player.role]
        return [[self, f'target is one of {result}']]


class Psychic(Player):
    TEAM = Team.Town

    def at_night(self, *args, **kwargs):
        self.game.add_action(self.commune, Priority.Investigate, args, kwargs)

    def commune(self) -> List[List[Player, str]]:
        perm = np.random.permutation(self.game.players.values())
        results = set()
        if self.game.night % 2 == 0:
            for player in perm:
                if player.is_good:
                    results.add(player)
            results.add(np.random.choice(self.game.players.values()))
            return [[self, f'one of players {results} is good']]
        else:
            for player in perm:
                if not player.is_good:
                    results.add(player)
            results.add(set(np.random.choice(self.game.players.values(), 2)))
            return [[self, f'one of players {results} is bad']]


class Consigliere(Player):
    TEAM = Team.Mafia

    def at_night(self, *args, **kwargs):
        self.game.add_action(self.investigate, Priority.Investigate, args, kwargs)

    def investigate(self, player: Player) -> List[List[Player, str]]:
        return [[self, f'target\'s role is {player.role}']]
