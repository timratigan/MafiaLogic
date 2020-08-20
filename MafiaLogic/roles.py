from typing import Union, List, Tuple, Callable, Dict

import numpy as np
import sys

from MafiaLogic.common import Player, Team, INVEST_RESULTS, Priority, Game, noop, TimeOfDay


class Investigator(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Investigate

    def night_action(self, player_name: Player.PLAYER_NAME) -> None:
        player = self._game.get_player(player_name)
        if self.visit(player):
            return
        result = INVEST_RESULTS[player.role]
        self.submit(f'target is one of {result}')


class Lookout(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Investigate

    def night_action(self, player_name: Player.PLAYER_NAME) -> None:
        player = self._game.get_player(player_name)
        if self.visit(player):
            return

        player.on_visited_by(self.visit_action, TimeOfDay.Morning)

    def visit_action(self, visitor: Player, visitee: Player, attacking: bool) -> bool:
        self.submit(f'Your target was visited by {visitor.name}')
        return False


class Psychic(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Investigate

    def night_action(self) -> None:
        perm = np.random.permutation(self._game.players.values())
        if self._game.night % 2 == 0:
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

    def night_action(self, player_name: Player.PLAYER_NAME) -> None:
        player = self._game.get_player(player_name)
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

    def night_action(self, player_name: Player.PLAYER_NAME) -> None:
        player = self._game.get_player(player_name)
        if self.visit(player):
            return

        player.on_visit(self.visit_action, TimeOfDay.Morning)

    def visit_action(self, visitor: Player, visitee: Player, attacking: bool) -> bool:
        self.submit(f'Your target visited {visitee}')
        return False


class Jailor(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Antecedent
    UNIQUE = True

    def __init__(self, game: Game, player_id):
        super().__init__(game, player_id)
        self._jailed_player: Union[Player, None] = None
        self._jailed_defense = 0
        self._kills = 4

    def day_action(self, player_name: Player.PLAYER_NAME) -> None:
        player = self._game.get_player(player_name)
        self._reset(_jailed_player=player)

    def night_action(self, kill: bool) -> None:
        if not self._game.night:
            kill = False

        self._jailed_player.reset_action()
        self._jailed_player._reset(DEFENSE=max(self._jailed_player.DEFENSE, 3))
        self._jailed_player.on_visited_by(self.visit_action)

        jail_class = self._jailed_player.__class__.__name__
        if kill and self._kills:
            self.add_action(self, self.kill, Priority.Kill)
        elif jail_class in ['SerialKiller', 'Werewolf'] and self._game.night:
            strength = 1 + jail_class == 'Werewolf'
            self._game.add_action(self._jailed_player, self._jailed_player.attack, Priority.Kill, self, strength)

    def kill(self):
        self._jailed_player.DEFENSE = self._jailed_defense
        self.attack(self._jailed_player, 3)
        self._kills -= 1
        if self._jailed_player.is_dead and self._jailed_player.__class__.TEAM == Team.Town:
            self._kills = 0
            self.submit('You killed an innocent player')
        self.submit(f'You have {self._kills} more kills')

    def visit_action(self, visitor: Player, visitee: Player, attacking: bool) -> bool:
        visitor.submit('Your target was in jail')
        return True


class VampireHunter(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Kill
    BITE_IMMUNITY = True

    def __init__(self, game: Game, player_id):
        super().__init__(game, player_id)
        self.on_visited_by(self.visit_action)

    def night_action(self, player_name: Player.PLAYER_NAME) -> None:
        player = self._game.get_player(player_name)
        if player.__class__.TEAM == Team.Vampire:
            self.attack(player, 2)

    def visit_action(self, visitor: Player, visitee: Player, attacking: bool) -> bool:
        if visitor.__class__.TEAM == Team.Vampire:
            self.attack(visitor, 2)
        return False


class Vigilante(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Kill

    def __init__(self, game: Game, player_id):
        super().__init__(game, player_id)
        self._bullets = 4
        self._guilty = False

    def night_action(self, player_name: Player.PLAYER_NAME) -> None:
        if self._guilty:
            self._game.kill(self)
            print(f'Player {self.name} has died of guilt')
            return
        if not self._bullets:
            return
        player = self._game.get_player(player_name)
        self.attack(player, 1)
        self._bullets -= 1
        self.submit(f'{self._bullets} bullets left')
        if player.__class__.TEAM == Team.Town and player.is_dead:
            self._guilty = True


class Veteran(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Antecedent
    ROLEBLOCK_IMMUNITY = True
    CONTROL_IMMUNITY = True
    UNIQUE = True

    def __init__(self, game: Game, player_id):
        super().__init__(game, player_id)
        self._alerts = 4

    def night_action(self, alert: bool):
        if alert and self._alerts:
            self._alerts -= 1
            self._reset(DEFENSE=max(self.DEFENSE, 2), BITE_IMMUNITY=True)
            self.on_visited_by(self.visit_action, TimeOfDay.Morning)

    def visit_action(self, visitor: Player, visitee: Player, attacking: bool) -> bool:
        self.attack(visitor, 2)
        return False


class Chef(Player):
    TEAM = Team.Town

    def add_action(self, *args, **kwargs):
        cb, priority = (self.day_action, Priority.Antecedent) if not self._game.time_of_day == TimeOfDay.Night else (
            self.moonless_action, Priority.Heal) if self._game.night % 2 else (self.full_moon_action, Priority.Kill)
        self._game.add_action(self, cb, priority, *args, **kwargs)

    def moonless_action(self, player_name: Player.PLAYER_NAME) -> None:
        player = self._game.get_player(player_name)
        if player is self:
            self.submit('The Chef cannot act on themselves')
            return
        if self.visit(player):
            return
        player.heal()

    def full_moon_action(self, player_name: Player.PLAYER_NAME) -> None:
        player = self._game.get_player(player_name)
        if player is self:
            self.submit('The Chef cannot act on themselves')
            return
        if self.visit(player):
            return
        player.poison()


class Bodyguard(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Antecedent

    def __init__(self, game: Game, player_id):
        super().__init__(game, player_id)
        self._vests = 2

    def night_action(self, player_name: Player.PLAYER_NAME) -> None:
        player = self._game.get_player(player_name)
        if player is self and self._vests:
            self._vests -= 1
            self._reset(DEFENSE=max(self.DEFENSE, 1), BITE_IMMUNITY=True)
        elif player is not self:
            self._game.add_action(self, self.night_protect, Priority.KillProtect, player_name)

    def night_protect(self, player_name: Player.PLAYER_NAME):
        player = self._game.get_player(player_name)
        if self.visit(player):
            return

        player.on_visited_by(self.visit_action, TimeOfDay.Morning)

    def visit_action(self, visitor: Player, visitee: Player, attacking: bool) -> bool:
        if not attacking:
            return False
        self.attack(visitor, 2, visit=False)
        if np.random.randint(2):
            self.submit('You died protecting your target')
            self._game.kill(self)
        if visitor.is_dead:
            visitee.submit('You were attacked but someone protected you')
            return True
        return False


class Doctor(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Protect

    def night_action(self, player_name: Player.PLAYER_NAME) -> None:
        player = self._game.get_player(player_name)
        if self.visit(player):
            return

        player.heal()


class Crusader(Player):
    TEAM = Team.Town
    PRIORITY = Priority.KillProtect

    def __init__(self, game: Game, player_id):
        super().__init__(game, player_id)
        self._targets = []

    def night_action(self, player_name: Player.PLAYER_NAME) -> None:
        player = self._game.get_player(player_name)
        if self.visit(player):
            return

        self._reset('_targets')
        self._game.add_action(self, self.crusade, Priority.Kill)
        player._reset(DEFENSE=max(player.DEFENSE, 2))
        player.on_visited_by(self.visit_action, TimeOfDay.Morning)

    def crusade(self):
        if not self._targets:
            return
        self.attack(np.random.choice(self._targets), 1, visit=False)

    def visit_action(self, visitor: 'Player', visitee: 'Player', attacking: bool) -> bool:
        self._targets.append(visitor)
        return False


class Trapper(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Controlling

    def __init__(self, game: Game, player_id):
        super().__init__(game, player_id)
        self._trap: Union[Player, None] = None

    def night_action(self, player_name: Player.PLAYER_NAME) -> None:
        player = self._game.get_player(player_name)
        if self.visit(player):
            return

        if self._trap is not None:
            self._trap._on_visited_by.remove(self.visit_action)
        self._trap = player
        self._game.queue(player.on_visited_by, TimeOfDay.Trial, self.visit_action)

    def visit_action(self, visitor: 'Player', visitee: 'Player', attacking: bool) -> bool:
        if attacking:
            self.attack(visitor, 2, visit=False)
        else:
            self.submit(f'You trapped someone and learned their role is {visitor.role}')
        visitee._on_visited_by.remove(self.visit_action)
        self._trap = None
        return True


class Priest(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Protect

    def __init__(self, game: Game, player_id):
        super().__init__(game, player_id)
        self._last_heal = -2

    def night_action(self, player_name: Player.PLAYER_NAME, option: str) -> None:
        player = self._game.get_player(player_name)
        option = option.lower()
        if option == 'heal' and self._game.night - self._last_heal > 1:
            if player.poisoned:
                player.submit('You were healed of poison')
            player.poisoned = 0
            self._last_heal = self._game.night
        elif option == 'cleanse':
            player.doused = player.framed = player.hexed = False  # TODO: this
        elif option == 'purify':
            player.infected = False  # TODO: also this
        else:
            self.submit('Night action must be one of heal, cleanse, or purify')


class Hacker(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Antecedent
    ROLEBLOCK_IMMUNITY = True

    def __init__(self, game: Game, player_id):
        super().__init__(game, player_id)
        self._team_sizes: Dict[Team, int] = {}
        self._bits = 1
        self._game.queue(self._init, TimeOfDay.Night)

    def _init(self):
        self._team_sizes = {team: len(self._game.players_by_team[team]) for team in Team}

    def night_action(self, team: str, attack=0) -> None:
        team = Team[team]  # TODO: restrict team choices
        if self._bits <= attack:
            self.submit('Not enough bits to attack, hacked instead')
            attack = 0
        if attack not in [0, 2, 4, 8]:
            self.submit('Attack must be 2, 4, or 8, hacked instead')
            attack = 0
        if attack == 2:
            players = [player for player in self._game.players_by_team[team] if player.get_targets()]
            if players:
                player = np.random.choice(players)
                idx, name = player.get_targets(True)[0]
                _, cb, args, kwargs = player._queued_action
                if len(args) > idx:
                    val, loc = args, idx
                else:
                    val, loc = kwargs, name
                if isinstance(val[loc], int):
                    ids = list(self._game.players.keys())
                    val[loc] = ids[(ids.index(val[loc]) + 1) % len(ids)]
                else:
                    names = self._game.players_by_name
                    val[loc] = names.peekitem((names.index(val[loc]) + 1) % len(names))
            else:
                self.submit('No valid targets')
                attack = 0
        elif attack == 4:
            pass  # TODO: roleblock last submitted night action from team
        elif attack == 8:
            for player in self._game.players_by_team[team]:
                player.on_visit(self.visit_action)
        else:
            self._game.add_action(self, self.hack, Priority.StartDay, team)
        self._bits -= attack

    def hack(self, team: Team):
        if np.random.rand() > len(self._game.players_by_team[team]) / self._team_sizes[team]:
            self.submit(f'Unsuccessful hack.  You have {self._bits} bits')
            return
        self._bits *= 2
        self.submit(f'Successful hack.  You have {self._bits} bits')

    # TODO: make this work on e.g. ambusher
    def visit_action(self, visitor: Player, visitee: Player, attacking: bool) -> bool:
        if visitee.__class__.TEAM == Team.Town and attacking:
            visitee._reset(DEFENSE=visitee.DEFENSE + 2)
            for player in self._game.players_by_team[visitor.__class__.TEAM]:
                player._on_visit.remove(self.visit_action)
        return False


class Therapist(Player):
    TEAM = Team.Town
    PRIORITY = Priority.Immediate

    def night_action(self, player_name: Player.PLAYER_NAME, therapy: str):
        player = self._game.get_player(player_name)
        if self.visit(player):
            return

        therapy = therapy.lower()
        if therapy in ['a', 'alternative']:
            if player._queued_action is None:
                return
            for priority, action_list in self._game._action_queue.items():
                if player._queued_action in priority:
                    new_priority = Priority(min(priority.value + 2, Priority.Haunt.value))
                    self._game._action_queue[priority].remove(player._queued_action)
                    self._game._action_queue[new_priority].append(player._queued_action)
                    break
        elif therapy in ['b', 'behavioral']:
            if not player.ROLEBLOCK_IMMUNITY:
                player.reset_action()
                player.submit('You were roleblocked')
            else:
                player.submit('Someone tried to roleblock you but you were immune')
                self.submit('Your target was roleblock immune')
        elif therapy in ['c', 'cognitive']:
            for target in player.get_targets():
                self.submit(f'Your target wanted to target {self._game.get_player(target).name}')
        else:
            self.submit('Not a valid therapy')


class Consigliere(Player):
    TEAM = Team.Mafia

    def night_action(self, player_name: Player.PLAYER_NAME) -> None:
        player = self._game.get_player(player_name)
        if self.visit(player):
            return
        self.submit(f'target\'s role is {player.role}')
