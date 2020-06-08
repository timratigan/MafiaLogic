from typing import Union, List, Tuple, Callable

import numpy as np
import sys

from MafiaLogic.common import Player, Team, INVEST_RESULTS, Priority, Game, noop, TimeOfDay


class Investigator(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Investigate

    def night_action(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        if self.visit(player):
            return
        result = INVEST_RESULTS[player.role]
        self.submit(f'target is one of {result}')


class Lookout(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Investigate

    def night_action(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        if self.visit(player):
            return
        self.game.queue(self.queued_action, TimeOfDay.Morning, player)

    def queued_action(self, player: Player) -> None:
        self.submit(f'target was visited by {", ".join(visitor.name for visitor in player._visited_by)}')


class Psychic(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Investigate

    def night_action(self) -> None:
        perm = np.random.permutation(self.game.players.values())
        if self.game.night % 2 == 0:
            results = [player.name for player in perm[:1]]
            for player in perm:
                if player.is_good:
                    results.append(player.name)
                    break
            results = np.random.permutation(results)
            self.submit(f'at least one of players {", ".join(results)} is good')
        else:
            results = [player.name for player in perm[:2]]
            for player in perm:
                if not player.is_good:
                    results.append(player.name)
                    break
            results = np.random.permutation(results)
            self.submit(f'at least one of players {", ".join(results)} is bad')


class Sheriff(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Investigate

    def night_action(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        if self.visit(player):
            return
        if player.DETECTION_IMMUNITY:
            result = 'not suspicious'
        else:
            team = getattr(sys.modules[__name__], player.role).TEAM
            if team in [Team.Mafia, Team.Coven, Team.Pirate]:
                result = team.name
            elif team in [Team.NeutralBenign, Team.NeutralChaos, Team.NeutralEvil, Team.Hate]:
                result = 'Neutral'
            else:
                result = 'not suspicious'
        self.submit(f'your target is {result}')


class Spy(Player):
    Team = Team.Town
    ROLEBLOCK_IMMUNITY = True
    BITE_IMMUNITY = True

    # leaving night action empty, it'll have to be god's responsibility to send chats


class Tracker(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Controlling

    def night_action(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        if self.visit(player):
            return
        self.game.queue(self.queued_action, TimeOfDay.Morning, player)

    def queued_action(self, player: Player) -> None:
        self.submit(f'target visited {", ".join(visit.name for visit in player._visited)}')


class Jailor(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Antecedent
    UNIQUE = True

    def __init__(self, game: Game, player_id):
        super().__init__(game, player_id)
        self._jailed_player: Union[Player, None] = None
        self._jailed_visit = None
        self._jailed_defense = 0
        self._kills = 4

    def day_action(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self._jailed_player = player

    def night_action(self, kill: bool) -> None:
        if not self.game.night:
            kill = False

        if self._jailed_player._queued_action:
            self._jailed_player._queued_action[1] = noop
            self._jailed_player.reset_action()
        self._jailed_visit = self._jailed_player.visited_by
        self._jailed_defense = self._jailed_player.DEFENSE
        self._jailed_player.visited_by = self.jail_visited_by()
        self._jailed_player.DEFENSE = 3

        jail_class = self._jailed_player.__class__.__name__
        if kill and self._kills:
            self.add_action(self, self.kill, Priority.Kill)
        elif jail_class in ['SerialKiller', 'Werewolf'] and self.game.night:
            strength = 1 + jail_class == 'Werewolf'
            self.game.add_action(self._jailed_player, self._jailed_player.attack, Priority.Kill, self, strength)

        self.game.queue(self.reset_jail, TimeOfDay.Morning)

    def kill(self):
        self._jailed_player.DEFENSE = self._jailed_defense
        self.attack(self._jailed_player, 3)
        self._kills -= 1
        if self._jailed_player.id in self.game.dead_players and self._jailed_player.__class__.TEAM == Team.Town:
            self._kills = 0
            self.submit('You killed an innocent player')
        self.submit(f'You have {self._kills} more kills')

    def reset_jail(self):
        self._jailed_player.visited_by = self._jailed_visit
        self._jailed_player.defense = self._jailed_defense
        self._jailed_player = self._jailed_visit = None
        self._jailed_defense = 0

    def jail_visited_by(self) -> Callable:
        def func(player: Player) -> bool:
            self._jailed_player._visited_by.append(player)
            player.submit('Your target was in jail')
            return True

        return func


class VampireHunter(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Kill
    BITE_IMMUNITY = True

    def night_action(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        if player.__class__.TEAM == Team.Vampire:
            self.attack(player, 2)

    def visited_by(self, player: Player) -> bool:
        self._visited_by.append(player)
        if player.__class__.TEAM == Team.Vampire:
            self.attack(player, 2)
            return True
        return False


class Vigilante(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Kill

    def __init__(self, game: Game, player_id):
        super().__init__(game, player_id)
        self._bullets = 4
        self._guilty = False

    def night_action(self, player_name: Union[int, str]) -> None:
        if self._guilty:
            self.game.kill(self)
            print(f'Player {self.name} has died of guilt')
            return
        if not self._bullets:
            return
        player = self.game.get_player(player_name)
        self.attack(player, 1)
        self._bullets -= 1
        self.submit(f'{self._bullets} bullets left')
        if player.__class__.TEAM == Team.Town and player.id in self.game.dead_players:
            self._guilty = True


class Veteran(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Antecedent
    ROLEBLOCK_IMMUNITY = True
    CONTROL_IMMUNITY = True
    UNIQUE = True

    def __init__(self, game: Game, player_id):
        super().__init__(game, player_id)
        self._alert = False
        self._na_visited_by = self.visited_by

    def day_action(self, alert: bool):
        self._alert = alert

    def night_action(self):
        if self._alert:
            self.defense = 2
            self.visited_by = self.alert_visited_by
            self.BITE_IMMUNITY = True
            self.game.queue(self.reset_alert, TimeOfDay.Morning)

    def reset_alert(self):
        self._alert = False
        self.defense = 0
        self.visited_by = self._na_visited_by
        self.BITE_IMMUNITY = False

    def alert_visited_by(self, player: Player) -> bool:
        self._visited_by.append(player)
        self.attack(player, 2)
        return False


class Chef(Player):
    TEAM = Team.Town

    def add_action(self, *args, **kwargs):
        cb, priority = (self.day_action, Priority.Antecedent) if not self.game.time_of_day == TimeOfDay.Night else (
            self.moonless_action, Priority.Heal) if self.game.night % 2 else (self.full_moon_action, Priority.Kill)
        self.game.add_action(self, cb, priority, *args, **kwargs)

    def moonless_action(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        if player is self:
            self.submit('The Chef cannot act on themselves')
            return
        if self.visit(player):
            return
        player.heal()

    def full_moon_action(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        if player is self:
            self.submit('The Chef cannot act on themselves')
            return
        if self.visit(player):
            return
        player.poison()


class Bodyguard(Player):
    TEAM = Team.Town
    PRIORITY = Priority.KillProtect

    def night_action(self, player_name: Union[int, str]) -> None:




class Consigliere(Player):
    TEAM = Team.Mafia

    def night_action(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.submit(f'target\'s role is {player.role}')
