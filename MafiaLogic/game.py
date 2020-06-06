from abc import ABC
from collections import defaultdict
from typing import List, Tuple

import numpy as np

from MafiaLogic.common import Game, TimeOfDay, Player, Team, Priority
import MafiaLogic.roles


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
        while not self._parse(input()):
            pass

    def add_action(self, player: Player, cb, priority: Priority, args=None, kwargs=None) -> None:
        player._queued_action = [player, cb, args, kwargs]
        self._action_queue[priority].append(player._queued_action)

    def get_player(self, player_id) -> Player:
        return self.players[player_id]

    def _advance(self):
        for x in self._message_buffer:
            print(x)
        self._message_buffer = []
        # noinspection PyTypeChecker
        self.time_of_day = TimeOfDay(
            (self.time_of_day.value + 1) % len(TimeOfDay))
        if self.time_of_day == TimeOfDay.Trial:
            self._votes = []
            self._nominee = max(self._vote_counts.items(), key=lambda t: t[1])[0]
            print(f'{self._nominee.name} is on trial!')
            self._vote_counts = defaultdict(int)
        elif self.time_of_day == TimeOfDay.Night:
            for voter, vote in self._votes:
                print(f'{voter.name} voted for {vote}')
            self._votes = []
            winner = max(self._vote_counts.items(), key=lambda t: t[1])[0]
            if winner:
                self._kill(self._nominee)
                print(f'{self._nominee.name} has been guillotined!')
            else:
                print(f'the town has decided not to guillotine {self._nominee.name}!')
            self._vote_counts = defaultdict(int)
        elif self.time_of_day == TimeOfDay.Morning:
            self.night += 1
            for priority in Priority:
                actions = self._action_queue[priority]
                for action in actions:
                    if not action:
                        continue
                    player, cb, args, kwargs = action
                    cb(*args, **kwargs)
                    player.reset_action()
            self._action_queue = defaultdict(list)

    def _kill(self, player: Player):
        del self.players[player.id]
        del self.players_by_name[player.name]
        self.players_by_team[player.TEAM].remove(player)
        self.dead_players[player.id] = player
        self.dead_players_by_name[player.name] = player
        player.reset_action()

    def _vote(self, voter, vote):
        self._votes.append([voter, vote])
        self._vote_counts[vote] += 1

    def _parse(self, args: str):
        args = list(filter(''.__ne__, args.split(' ')))
        if not args:
            return
        for i, arg in enumerate(args):
            try:
                args[i] = int(arg)
            except ValueError:
                pass

        if args[0] == 'action':
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
            player_id = args[1]
            voter = self.get_player(player_id)
            if self.time_of_day == TimeOfDay.Nomination:
                player_id = args[2]
                vote = self.get_player(player_id)
                self._vote(voter, vote)
                print(f'{voter.name} voted for {vote}')
            else:
                self._vote(voter, bool(args[2]))
