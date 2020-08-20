import abc
from collections import defaultdict
from enum import Enum
from typing import List, Dict, Union

INVEST_SETS = frozenset({
    frozenset({'Investigator', 'Psychic', 'Consigliere', 'Navigator'}),
    frozenset({'Lookout', 'Scientist', 'CovenLeader', 'Cupid'}),
    frozenset({'Sheriff', 'Executioner', 'Werewolf'}),
    frozenset({'Tracker', 'Mayor', 'Plaguebearer', 'Amnesiac'}),
    frozenset({'Spy', 'Blackmailer', 'Puppeteer'}),
    frozenset({'Archivist', 'Medusa', 'Janitor', 'CabinBoy'}),
    frozenset({'Jailor', 'QuarterMaster', 'GuardianAngel'}),
    frozenset({'Vigilante', 'Ambusher', 'Captain'}),
    frozenset({'Veteran', 'Bomber', 'Survivor'}),
    frozenset({'Chef', 'Poisoner', 'Juggernaut'}),
    frozenset({'Bodyguard', 'Crusader', 'Godfather', 'Arsonist'}),
    frozenset({'Doctor', 'PotionMaster', 'Quack'}),
    frozenset({'Transporter', 'Trapper', 'Hypnotist', 'Smuggler'}),
    frozenset({'Escort', 'Consort', 'Siren', 'Thief'}),
    frozenset({'Medium', 'Retributionist', 'Necromancer'}),
    frozenset({'Lawyer', 'HexMaster', 'Vampire', 'Jester'}),
    frozenset({'Spy', 'Blackmailer', 'Puppeteer'}),
    frozenset({'Anarchist', 'Bishop', 'Deputy', 'Admiral'})
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
    Werewolves = 7
    Vampire = 8


class Priority(Enum):
    PrevDay = -1
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
    CleanUp = 512


class TimeOfDay(Enum):
    Morning = 0
    Nomination = 1
    Trial = 2
    Night = 3


def noop(*args, **kwargs):
    return


class Game(object, metaclass=abc.ABCMeta):
    def __init__(self):
        self.players: Dict[int, Player] = {}
        self.dead_players: Dict[int, Player] = {}
        self.players_by_team: Dict[Team, List[Player]] = defaultdict(list)
        self.players_by_name: Dict[Union[int, str], Player] = {}
        self.dead_players_by_name: Dict[Union[int, str], Player] = {}
        self.night: int = 0
        self.full_moon: bool = True
        self.time_of_day: TimeOfDay = TimeOfDay.Night

    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def add_action(self, player, cb, priority, args=None, kwargs=None) -> None:
        pass

    @abc.abstractmethod
    def get_player(self, player_id) -> 'Player':
        pass


class Player(object):
    # attributes that should be modified by the subclass
    TEAM = Team.NeutralBenign
    IS_UNIQUE = False
    default_defense = defense_power = 0
    attack_power = 0
    detection_immunity = False
    bite_immunity = False
    control_immunity = False
    roleblock_immunity = False

    def __init__(self, game: Game, player_id, name=None):
        self.game: Game = game
        self.role: str = self.__class__.__name__
        self.id: Union[int, str] = player_id
        self.name: Union[int, str] = self.id if name is None else name
        self.alive: bool = True
        self.lover: Union[Player, None] = None
        self.doused: bool = False
        self.hexed: bool = False
        self.framed: bool = False
        self.bribed: bool = False
        self.poisoned: bool = False
        self.infected: bool = False
        self.will_suicide: bool = False
        # Dict of Player:active, where active is a bool
        self.trappers = {}
        # Variables which reset every night
        self.jailed: bool = False
        self.protectors: List[Player] = []
        self.visits: List[Player] = []
        self.visited: List[Player] = []
        self.roleblocked: bool = False
        self.controlled: bool = False

        self._queued_action = None
        self._messages = defaultdict(list)

    def day_action(self, *args, **kwargs) -> None:
        pass

    def at_night(self, *args, **kwargs) -> None:
        pass
    
    def __str__(self):
        return self.name + '-' + self.role

    def __repr__(self):
        return self.name + '-' + self.role

    @property
    def is_good(self):
        return self.TEAM in [Team.Town, Team.NeutralBenign, Team.Werewolves] and \
               self.role not in ['Anarchist', 'HexMaster', 'Arsonist']

    def submit(self, message):
        self._messages[self.game.night].append(message)

    def visit(self, visited_player, hostile=False):
        for trapper, active in visited_player.trappers.items():
            if active:
                self.roleblocked()
                if hostile:
                    trapper.attack(self)
                else:
                    trapper.submit(f'A {self.role} visited your trap at {visited_player.name}')
        self.visits.append(visited_player)
        visited_player.visited.append(self)

    def attack(self, attacked_player) -> bool:
        self.visit(attacked_player, True)
        for protector in attacked_player.protectors:
            protector.protect_from(self)
        killed = self.attack_power > attacked_player.defense_power
        if killed:
            attacked_player.alive = False
            attacked_player.submit(f'You were killed by the {self.role}')
            self.submit(f'You killed {attacked_player.name}, the {attacked_player.role}')
        else:
            attacked_player.submit(f'You defended yourself from {self.role}')
            self.submit(f'You failed to kill {attacked_player.name}')
        return killed

    def roleblocked(self):
        if not self.roleblock_immunity:
            self.roleblocked = True

    def reset_action(self):
        if self._queued_action:
            self._queued_action[1] = noop

    def reset_status(self):
        self.protectors = []
        self.visits = []
        self.visited = []
        self.jailed = False
        self.roleblocked = False
        self.controlled = False
        self.defense_power = self.default_defense
        for k in self.trappers.keys():
            self.trappers[k] = True
