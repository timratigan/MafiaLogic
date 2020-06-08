from abc import ABCMeta, abstractmethod
from collections import defaultdict
from enum import Enum
from typing import List, Dict, Union, Callable

INVEST_SETS = frozenset({
    frozenset({'Investigator', 'Psychic', 'Consigliere', 'Mayor', 'Survivor', 'Plaguebearer'}),
    frozenset({'Escort', 'Consort', 'Siren', 'Lookout', 'SerialKiller'}),
    frozenset({'VampireHunter', 'Amnesiac', 'Medusa', 'Psychic', 'Disguiser'}),
    frozenset({'Sheriff', 'Executioner', 'Werewolf', 'Janitor', 'Moosehead'}),
    frozenset({'Doctor', 'Spy', 'Lawyer', 'PotionMaster', 'HexMaster'}),
    frozenset({'Puppeteer', 'Hacker', 'Eros', 'Tracker', 'Hypnotist'}),
    frozenset({'Jailor', 'Chef', 'Poisoner', 'GuardianAngel', 'CovenLeader'}),
    frozenset({'Vigilante', 'Veteran', 'Pirate', 'Mafioso', 'Ambusher'}),
    frozenset({'Bodyguard', 'Godfather', 'Medium', 'Crusader', 'Thug'}),
    frozenset({'Arsonist', 'Retributionist', 'Necromancer', 'Trapper', 'Bomber'}),
    frozenset({'Bookie', 'Priest', 'Vampire', 'Jester'}),
    frozenset({'Transporter', 'HousePainter', 'Therapist', 'Mirage', 'Apprentice'})
})


INVEST_RESULTS = {key: value for value in INVEST_SETS for key in value}


class Team(Enum):
    NeutralBenign = 0
    Town = 1
    Mafia = 2
    Coven = 3
    Pirate = 4
    NeutralChaos = 5
    NeutralEvil = 6
    Hate = 7
    Vampire = 8


class Priority(Enum):
    Antecedent = -1
    Immediate = 0
    Controlling = 1
    Duel = 2
    RoleBlock = 3
    Transport = 3
    Resurrect = 4
    Protect = 5
    KillProtect = 6
    Deceive = 7
    Investigate = 8
    Kill = 9
    Heal = 10
    Transform = 10
    Haunt = 11
    StartDay = 256


class TimeOfDay(Enum):
    Morning = 0
    Nomination = 1
    Trial = 2
    Night = 3


def noop(*args, **kwargs):
    return


class Game(object, metaclass=ABCMeta):
    def __init__(self):
        self.players: Dict[int, Player] = {}
        self.dead_players: Dict[int, Player] = {}
        self.players_by_team: Dict[Team, List[Player]] = defaultdict(list)
        self.players_by_name: Dict[Union[int, str], Player] = {}
        self.players_by_role: Dict[str, List[Player]] = defaultdict(list)
        self.dead_players_by_name: Dict[Union[int, str], Player] = {}
        self.night: int = 0
        self.time_of_day: TimeOfDay = TimeOfDay.Night

    @abstractmethod
    def add_action(self, player: 'Player', cb: Callable, priority: Priority, *args, **kwargs) -> None:
        pass

    def queue(self, cb: Callable, tod: TimeOfDay, *args, **kwargs):
        pass

    @abstractmethod
    def get_player(self, player_id) -> 'Player':
        pass

    @abstractmethod
    def attack(self, attacker: 'Player', attackee: 'Player', strength: int):
        pass

    @abstractmethod
    def kill(self, player: 'Player'):
        pass

    def change_roles(self, player: 'Player', role: str):
        pass


class Player(object):
    # attributes that should be modified by the subclass
    TEAM: Team = Team.NeutralBenign
    PRIORITY: Priority = Priority.StartDay
    DETECTION_IMMUNITY = False
    ROLEBLOCK_IMMUNITY = False
    BITE_IMMUNITY = False
    CONTROL_IMMUNITY = False
    DEFENSE = 0
    UNIQUE = False

    def __init__(self, game: Game, player_id, name=None):
        self.game: Game = game
        self.role: str = self.__class__.__name__
        self.id: Union[int, str] = player_id
        self.name: Union[int, str] = self.id if name is None else name
        self.lover: Union[Player, None] = None
        self.framed: bool = False
        self.hexed: bool = False
        self.infected: bool = False
        self.doused: bool = False
        self.poisoned = 0
        self.healed = False

        self._queued_action = None
        self._messages = defaultdict(list)

        self._visited_by = []
        self._visited = []

    def add_action(self, *args, **kwargs):
        cb = self.night_action if self.game.time_of_day == TimeOfDay.Night else self.day_action
        self.game.add_action(self, cb, self.PRIORITY, *args, **kwargs)

    @property
    def is_good(self):
        return self.TEAM in [Team.Town, Team.NeutralBenign, Team.Hate] and \
               self.role not in ['Anarchist', 'HexMaster', 'Arsonist']

    def submit(self, message):
        self._messages[self.game.night].append(message)

    def reset_action(self):
        if self._queued_action:
            self._queued_action[1] = noop
        self._queued_action = None

    def visit(self, player: 'Player') -> bool:
        self._visited.append(player)
        plaguebearers = self.game.players_by_role['Plaguebearer']
        if self.infected and not player.infected:
            player.infected = True
            for plaguebearer in plaguebearers:
                plaguebearer.submit(f'{player.name} infected')
        elif player.infected and not self.infected:
            self.infected = True
            for plaguebearer in plaguebearers:
                plaguebearer.submit(f'{self.name} infected')
        return player.visited_by(self)

    def visited_by(self, player: 'Player') -> bool:  # return whether visiting should end the action
        self._visited_by.append(player)
        return False

    def attack(self, player: 'Player', strength: int):
        self.game.attack(self, player, strength)

    def rampage(self, player: 'Player', strength: int):
        self.attack(player, strength)
        for visitor in player._visited_by:
            if visitor.__class__.__name__ != 'Tracker':
                self.attack(visitor, strength)

    def heal(self, defense=2):
        self.DEFENSE = max(defense, self.DEFENSE)
        self.healed = True
        if self.poisoned:
            self.submit('You were healed of poison')
            self.poisoned = 0
        self.game.queue(self._reset_def, TimeOfDay.Morning)

    def _reset_def(self):
        self.DEFENSE = self.__class__.DEFENSE
        self.healed = False

    def poison(self):
        self.submit('You were poisoned')
        self.poisoned = max(self.poisoned, 1)
        self.game.queue(self._poison, TimeOfDay.Morning)

    def _poison(self):
        if not self.poisoned:
            return
        if self.poisoned > 1:
            self.game.kill(self)
            return
        self.poisoned += 1
        self.game.queue(self._poison, TimeOfDay.Morning)

    night_action = noop

    day_action = noop

    def __repr__(self):
        return str(self.name)
