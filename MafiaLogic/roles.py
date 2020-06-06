from typing import Union, List, Tuple

import numpy as np

from MafiaLogic.common import Player, Team, INVEST_RESULTS, Priority


class Investigator(Player):
    TEAM = Team.Town

    def at_night(self, *args, **kwargs):
        self.game.add_action(self, self.investigate, Priority.Investigate, args, kwargs)

    def investigate(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        result = INVEST_RESULTS[player.role]
        self.submit(f'target is one of {result}')


class Psychic(Player):
    TEAM = Team.Town

    def at_night(self, *args, **kwargs):
        self.game.add_action(self, self.commune, Priority.Investigate, args, kwargs)

    def commune(self) -> None:
        perm = np.random.permutation(self.game.players.values())
        results = set()
        if self.game.night % 2 == 0:
            for player in perm:
                if player.is_good:
                    results.add(player)
            results.add(np.random.choice(self.game.players.values()))
            self.submit(f'one of players {results} is good')
        else:
            for player in perm:
                if not player.is_good:
                    results.add(player)
            results.add(set(np.random.choice(self.game.players.values(), 2)))
            self.submit(f'one of players {results} is bad')


class Consigliere(Player):
    TEAM = Team.Mafia

    def at_night(self, *args, **kwargs):
        self.game.add_action(self, self.investigate, Priority.Investigate, args, kwargs)

    def investigate(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.submit(f'target\'s role is {player.role}')
