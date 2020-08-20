from abc import ABCMeta, abstractmethod
from collections import defaultdict, OrderedDict
from enum import Enum
from inspect import signature
from typing import List, Dict, Union, Callable

from sortedcontainers import SortedDict

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
        self.players: OrderedDict[int, Player] = OrderedDict()
        self.dead_players: Dict[int, Player] = {}
        self.players_by_team: Dict[Team, List[Player]] = defaultdict(list)
        self.players_by_name: SortedDict[Player.PLAYER_NAME, Player] = SortedDict()
        self.dead_players_by_name: Dict[Union[int, str], Player] = {}
        self.night: int = 0
        self.time_of_day: TimeOfDay = TimeOfDay.Trial

    @abstractmethod
    def add_action(self, player: 'Player', cb: Callable, priority: Priority, *args, **kwargs) -> None:
        pass

    def queue(self, cb: Callable, tod: TimeOfDay, *args, **kwargs):
        pass

    @abstractmethod
    def get_player(self, player_id) -> 'Player':
        pass

    @abstractmethod
    def attack(self, attacker: 'Player', attackee: 'Player', strength: int, visit=True):
        pass

    @abstractmethod
    def kill(self, player: 'Player'):
        pass

    def change_roles(self, player: 'Player', role: str):
        pass


class Player(object, metaclass=ABCMeta):
    # attributes that should be modified by the subclass
    TEAM: Team = Team.NeutralBenign
    PRIORITY: Priority = Priority.StartDay
    DETECTION_IMMUNITY = False
    ROLEBLOCK_IMMUNITY = False
    BITE_IMMUNITY = False
    CONTROL_IMMUNITY = False
    DEFENSE = 0
    UNIQUE = False
    PLAYER_NAME = Union[int, str]

    def __init__(self, game: Game, player_id, name=None):
        self._game: Game = game
        self.role: str = self.__class__.__name__
        self.id: Union[int, str] = player_id
        self.name: Union[int, str] = self.id if name is None else name
        self.lover: Union[Player, None] = None
        self.framed: bool = False
        self.hexed: bool = False
        self.infected: bool = False
        self.doused: bool = False
        self.poisoned: int = 0
        self.healed: bool = False

        self._queued_action = None
        self._messages = defaultdict(list)
        self._reset_vals = {}

        self._on_visit: List[Callable[[Player, Player, bool], bool]] = []
        self._on_visited_by: List[Callable[[Player, Player, bool], bool]] = []

    def add_action(self, *args, **kwargs):
        cb = self.night_action if self._game.time_of_day == TimeOfDay.Night else self.day_action
        self._game.add_action(self, cb, self.PRIORITY, *args, **kwargs)

    def get_targets(self, locations=False):
        if self._queued_action is None:
            return []
        player, cb, args, kwargs = self._queued_action
        params = signature(cb).parameters
        if locations:
            return [(i, k) for i, (k, v) in enumerate(params.items()) if v.annotation is self.PLAYER_NAME]
        return [args[i] if len(args) > i else kwargs[k] for i, (k, v) in enumerate(params.items()) if
                v.annotation is self.PLAYER_NAME]

    @property
    def is_good(self):
        return self.TEAM in [Team.Town, Team.NeutralBenign, Team.Hate] and \
               self.role not in ['Anarchist', 'HexMaster', 'Arsonist']

    @property
    def is_dead(self):
        return self.id in self._game.dead_players

    def submit(self, message):
        self._messages[self._game.night].append(message)

    def reset_action(self):
        if self._queued_action:
            self._queued_action[1] = noop
        self._queued_action = None

    def visit(self, player: 'Player', attacking=False) -> bool:
        result = False
        for cb in self._on_visit:
            result |= cb(self, player, attacking)
        for cb in player._on_visited_by:
            result |= cb(self, player, attacking)
        return result

    def on_visit(self, cb: Callable[['Player', 'Player', bool], bool], tod=None):
        self._on_visit.append(cb)
        if tod is not None:
            self._game.queue(lambda: self._on_visit.remove(cb), tod)

    def on_visited_by(self, cb: Callable[['Player', 'Player', bool], bool], tod=None):
        self._on_visited_by.append(cb)
        if tod is not None:
            self._game.queue(lambda: self._on_visited_by.remove(cb), tod)

    def attack(self, player: 'Player', strength: int, visit=True):
        self._game.attack(self, player, strength, visit)

    def heal(self, defense=2):
        self._reset(DEFENSE=max(defense, self.DEFENSE), healed=True)
        if self.poisoned:
            self.submit('You were healed of poison')
            self.poisoned = 0

    def visit_action(self, visitor: 'Player', visitee: 'Player', attacking: bool) -> bool:
        raise NotImplementedError

    def _reset(self, *args, queue=True, **kwargs):
        if queue:
            if not self._reset_vals:
                self._game.queue(self._reset, TimeOfDay.Morning, queue=False)
            for arg in args:
                if arg not in self._reset_vals:
                    self._reset_vals[arg] = getattr(self, arg)
            for k, v in kwargs.items():
                if k not in self._reset_vals:
                    self._reset_vals[k] = getattr(self, k)
                setattr(self, k, v)
        else:
            for k, v in self._reset_vals.items():
                setattr(self, k, v)
            self._reset_vals = {}

    def poison(self):
        self.submit('You were poisoned')
        self.poisoned = max(self.poisoned, 1)
        self._game.queue(self._poison, TimeOfDay.Morning)

    def _poison(self):
        if not self.poisoned:
            return
        if self.poisoned > 1:
            self._game.kill(self)
            return
        self.poisoned += 1
        self._game.queue(self._poison, TimeOfDay.Morning)

    night_action = noop

    day_action = noop

    def __repr__(self):
        return str(self.name)
