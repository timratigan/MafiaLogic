from abc import ABC
from collections import defaultdict
from sortedcontainers import SortedList
from typing import Union, List, Tuple

import numpy as np

from MafiaLogic.common import Game, TimeOfDay, Player, Team, Priority
import MafiaLogic


class MafiaGame(Game, ABC):
    def __init__(self,
                 roles: List[Tuple[int, str]] = None,
                 names: List[str] = None
                 ):
        super().__init__()
        self._action_queue = defaultdict(list)
        self._message_buffer = []
        self._votes = []
        self._vote_counts = defaultdict(int)

        if names:
            names = np.random.permutation(names)

        i = 0
        if roles:
            for count, role in roles:
                for _ in range(count):
                    name = names[i] if names else None
                    player = getattr(MafiaLogic.roles, role)(
                        game=self,
                        player_id=i,
                        name=name)
                    if player.IS_UNIQUE:
                        assert count == 1
                    self.players[i] = player
                    self.players_by_team[player.TEAM].append(player)
                    self.players_by_name[player.name] = player
                    i += 1

    def start(self):
        while not self._parse(input('')):
            pass

    def add_action(self, cb, priority, args=None, kwargs=None) -> None:
        self._action_queue[priority.value].append([cb, args, kwargs])

    def _advance(self):
        for x in self._message_buffer:
            print(x)
        self._message_buffer = []
        # noinspection PyTypeChecker
        self.time_of_day = TimeOfDay(
            (self.time_of_day.value + 1) % len(TimeOfDay))
        if self.time_of_day == TimeOfDay.Trial:
            for voter, vote in self._votes:
                print(f'{voter.name} voted for {vote}')
            self._votes = []
            winner = max(self._vote_counts.items(), key=lambda t: t[1])[0]
            self._nominee = self.get_player(winner)
            print(f'{self._nominee.name} is on trial!')
            self._vote_counts = defaultdict(int)
        elif self.time_of_day == TimeOfDay.Night:
            for voter, vote in self._votes:
                print(f'{voter.name} voted for {vote}')
            self._votes = []
            winner = max(self._vote_counts.items(), key=lambda t: t[1])[0]
            if winner:
                self._kill(self._nominee)
                print(f'{self._nominee} has been guillotined!')
            else:
                print(f'the town has decided not to guillotine {self._nominee}!')
            self._vote_counts = defaultdict(int)
        elif self.time_of_day == TimeOfDay.Morning:
            for priority in Priority:
                actions = self._action_queue[priority]
                for cb, args, kwargs in actions:
                    cb(*args, **kwargs)
            self._action_queue = defaultdict(list)

        team = None
        for player in self.players.values():
            if team is None:
                team = player.TEAM
            else:
                if team != player.TEAM or team in [Team.NeutralBenign,
                                                   Team.NeutralChaos,
                                                   Team.NeutralEvil]:
                    break

    def _kill(self, player: Player):
        del self.players[player.id]
        del self.players_by_name[player.name]
        self.players_by_team[player.TEAM].remove(player)
        self.dead_players[player.id] = player
        self.dead_players_by_name[player.name] = player

    def _vote(self, voter, vote):
        self._votes.append([voter, vote])
        self._vote_counts[vote] += 1

    def _parse(self, args: str):
        args = list(filter(''.__ne__, args.split(' ')))
        if not args:
            return

        if args[0] == 'action':
            try:
                player_id = int(args[1])
            except ValueError:
                player_id = args[1]
            player = self.get_player(player_id)
            action_args = args[2:]
            if self.time_of_day != TimeOfDay.Night:
                player.day_action(*action_args)
            else:
                player.at_night(*action_args)
        elif args[0] == 'advance':
            self._advance()
        elif args[0] == 'vote':
            assert self.time_of_day in [TimeOfDay.Nomination, TimeOfDay.Trial]
            try:
                player_id = int(args[1])
            except ValueError:
                player_id = args[1]
            voter = self.get_player(player_id)
            if self.time_of_day == TimeOfDay.Nomination:
                try:
                    player_id = int(args[2])
                except ValueError:
                    player_id = args[2]
                vote = self.get_player(player_id)
                self._vote(voter, vote)
