from typing import Union, List, Tuple

import numpy as np

from MafiaLogic.common import Player, Game, Team, INVEST_RESULTS, Priority

########################
#         TOWN         #
########################
class Investigator(Player):
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)

    def at_night(self, action ,*args, **kwargs):
        if action == 'investigate':
            self.game.add_action(self, self.investigate, Priority.Investigate, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def investigate(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        if not self.roleblocked:
            result = INVEST_RESULTS[player.role]
            self.submit(f'target is one of {result}')
        else:
            self.submit(f'You were roleblocked')

class Tracker(Player):
    """
    On non-full moon nights: choose a person to watch. You see all who visit them in turn order.
    On full moon nights: choose a person to watch. You see the people they visit that night.
    """
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)
    
    def at_night(self, action ,*args, **kwargs):
        if action == 'track':
            assert not self.game.full_moon
            self.game.add_action(self, self.start_track, Priority.Controlling, args, kwargs)
            self.game.add_action(self, self.end_track, Priority.StartDay, args, kwargs)
        elif action == 'watch':
            assert self.game.full_moon
            self.game.add_action(self, self.start_watch, Priority.Controlling, args, kwargs)
            self.game.add_action(self, self.end_watch, Priority.StartDay, args, kwargs)
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
    
    def start_watch(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
    
    def end_watch(self, player_name: Union[int, str]) -> None:
        if not self.roleblocked:
            player = self.game.get_player(player_name)
            if len(player.visits) == 0:
                self.submit(f'{player.name} visited noone')
            else:
                self.submit(f'{player.name} visited {player.visits}')
        else:
            self.submit(f'You were roleblocked')

class Psychic(Player):
    """
    On non-full moon nights: get three random names, at least one of which is evil. 
    On full moon nights: get two random names, at least one of which is good.
    """
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)

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
                break
        results.add(np.random.choice(player_list))
        self.submit(f'one of players {results} is good')

class Sheriff(Player):
    """
    Choose one person to investigate. You see whether they are suspicious or not.  (BINARY ANSWER)
    """
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)

    def at_night(self, action ,*args, **kwargs):
        if action == 'investigate':
            self.game.add_action(self, self.investigate, Priority.Investigate, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def investigate(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        if not self.roleblocked:
            suspicious = False
            if player.TEAM in [Team.Vampire, Team.Mafia, Team.Werewolves] or player.hexed: # AMB: Unclear what counts as suspicious
                suspicious = True
            if player.detection_immunity: # Assuming this overrides hexes
                suspicious = False
            if suspicious:
                self.submit(f'{player.name} is suspicious')
            else:
                self.submit(f'{player.name} is not suspicious')
        else:
            self.submit(f'You were roleblocked')

class Spy(Player):
    """
    Choose to spy on Mafia, Coven, or Werewolves. Receive bits of their conversation in the morning
    """
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)

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
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)
        self.attack_power = 3

    def at_night(self, action,*args, **kwargs):
        if action == 'jail':
            self.game.add_action(self, self.jail, Priority.PrevDay, args, kwargs)
        elif action == 'execute':
            assert self.game.night > 0
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

# Role-swap to vigi needed        
class Werewolf_Hunter(Player):
    """
    Choose a person to investigate. If they are a werewolf, you attack them. 
    If all werewolves are dead, you become a vigilante with one bullet. Werewolves that try to bite you die instantly.	
    Can listen in on the werewolf chat	2	0	Bite immune and kills werewolf		Werewolf Hunter, Basilisk, Seer, Polyjuice Potioneer
    """
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)
        self.attack_power = 2

    def at_night(self, action ,*args, **kwargs):
        if action == 'investigate':
            self.game.add_action(self, self.investigate, Priority.Investigate, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def investigate(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        if not self.roleblocked:
            if player.TEAM == Team.Werewolves:
                self.attack(player)
                self.submit(f'{player.name} was a werewolf')
            else:
                self.submit(f'{player.name} is not a werewolf')
        else:
            self.submit(f'You were roleblocked')
        
# Needs to be implemented (check previous bibles)
class Vigilante(Player):
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)
        
    def at_night(self, action ,*args, **kwargs):
        if action == 'investigate':
            self.game.add_action(self, self.investigate, Priority.Investigate, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def investigate(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        if not self.roleblocked:
            result = INVEST_RESULTS[player.role]
            self.submit(f'target is one of {result}')
        else:
            self.submit(f'You were roleblocked')

class Chosen_One(Player):
    """
    Chosen One (modified vigilante)	Choose one person to attack (max 4 times). If you kill a legitimately innocent role, you commit suicide the next night.	None	1	0	
    Immune to Dark Lord and Curse Master's attacks.	
    Immunity to Dark Lord's killing power also means immunity to Head Death Eater attacks IF the Head Death Eater is acting on the orders of the Dark Lord.	Chosen One, Veteran, Dueler, Head Death Eater, Inferius
    """
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)
        self.attack_power = 1

    def at_night(self, action ,*args, **kwargs):
        if self.will_suicide:
            self.game.add_action(self, self.suicide, Priority.Immetiate, args, kwargs)
            self.will_suicide = False
        if action == 'attack':
            self.game.add_action(self, self.attack_wrapper, Priority.Kill, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def attack_wrapper(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        if self.attack(player):
            if player.TEAM == Team.Town:
                self.submit(f'since {player.name} was town, you will kill yourself the next night')
                self.will_suicide = True
    
    def suicide(self) -> None:
        self.submit(f'You commited suicide after killing a town role the last night')
        self.alive = False

class Veteran(Player):
    """
    Veteran	4 times per game, you can choose to go on alert. If so, you gain 2 defense and attack all who visit you REGARDLESS OF AFFINITY	
    None	2	2 if on alert	
    Role-block immune, control immune, bite immune on alert	Unique role	
    Chosen One, Veteran, Dueler, Head Death Eater, Inferius
    """
    TEAM = Team.Town

    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)
        self.defended = False
        self.attack_power = 2
        self.vests = 4

    def at_night(self, action ,*args, **kwargs):
        if action == 'vest':
            self.game.add_action(self, self.vest, Priority.Immediate, args, kwargs)
            self.game.add_action(self, self.end_vest, Priority.CleanUp, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def vest(self) -> None:
        assert self.vests > 0
        self.vests -= 1
        defense_power = 2
        roleblock_immunity = True
        control_immunity = True
        bite_immunity = True
        self.protectors.append(self)
    
    def end_vest(self) -> None:
        if not self.defended:
            self.submit(f'Noone visited you last night')
        defense_power = 0
        roleblock_immunity = False
        control_immunity = False
        bite_immunity = False
        self.defended = False

    # All Protectors must have a protect_from method
    def protect_from(self, attacking_player) -> None:
        self.submit(f'You attempt to protect yourself')
        self.attack(attacking_player)
        self.defended = True

# TODO: Go back and implement poison after doing poisoner
class Chef(Player):
    """
    Moonless Night: Visit and heal target (see Doctor)
    Full Moon Night: Visit and poison target (see poisoner)"	
    None	3	0		You cannot act on yourself. Healing prevents death by poison	
    Chief Warlock, Herbologist, Poisoner, Guardian Angel, Curse Master
    """
    TEAM = Team.Town

    def at_night(self, action ,*args, **kwargs):
        if action == 'heal':
            assert not self.game.full_moon
            self.game.add_action(self, self.heal, Priority.Protect, args, kwargs)
        elif action == 'poison':
            assert self.game.full_moon
            self.game.add_action(self, self.poison, Priority.Kill, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def heal(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        if not self.roleblocked:
            player.defense_power = 2
            self.submit(f'you heal {player.name}')
        else:
            self.submit(f'You were roleblocked')

    def poison(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        if not self.roleblocked:
            pass
        else:
            self.submit(f'You were roleblocked')

class Bodyguard(Player):
    """
    Select a player. That player gains a defense of 2. If another player tries to attack your target, 
    you attack the visitor with probability 50% that you die in the attack. You also have 2 vest which you can use to grant yourself a defense of 1.
    None	2	1 if vested	Bite immune when vested	Does not attack non-killing visitors like the dementor or the Obscurus.	Patronus, Dark Lord, Crusader, Protego Diabolicus
    """
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)
        self.attack_power = 2
        self.vests = 2

    def at_night(self, action ,*args, **kwargs):
        if action == 'protect':
            self.game.add_action(self, self.protect, Priority.Investigate, args, kwargs)
            self.game.add_action(self, self.end_protect, Priority.CleanUp, args, kwargs)
        elif action == 'vest': # Additional Action
            assert self.vests > 0
            self.vests -= 1
            self.game.add_action(self, self.vest, Priority.Investigate, args, kwargs) #AMB: vest go on TT 0?
            self.game.add_action(self, self.end_vest, Priority.CleanUp, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def protect(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player) #AMB: Do they visit or protect first?
        if not self.roleblocked:
            player.defense_power += 2
            player.protectors.append(self)  

    def end_protect(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        player.defense_power -= 2

    def protect_from(self, attacking_player) -> None:
        self.attack(attacking_player)
        if self.game.random() > 0.5:
            self.alive = False
            self.submit(f'You Died while defending')
        
    def vest(self) -> None:
        self.defense_power = 1
        self.bite_immunity = True

    def end_vest(self) -> None:
        self.defense_power = 0
        self.bite_immunity = False

class Doctor(Player): # AMB: Does healing get rid of poison or anything else?
    """
    Select one player. That player has defense of 2 for the turn. You can heal yourself once per game. 	
    None	0	0			Phoenix, Animagus, Official, Potion Master, Hex Master
    """
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)

    def at_night(self, action ,*args, **kwargs):
        if action == 'heal':
            self.game.add_action(self, self.heal, Priority.Protect, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def heal(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        if not self.roleblocked:
            player.defense_power = 2
            self.submit(f'you heal {player.name}')

class Crusader(Player):
    """
    Grants a defense of 2 to whoever you visit. Randomly attacks one visitor regardless of which side they are on. 
    Cannot protect yourself.	None	1	0			Patronus, Dark Lord, Seer, Crusader, Dementor
    """
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)
        self.attack_power = 1

    def at_night(self, action ,*args, **kwargs):
        if action == 'protect':
            self.game.add_action(self, self.protect, Priority.KillProtect, args, kwargs)
            self.game.add_action(self, self.random_attack, Priority.Kill, args, kwargs) #AMB: Random attacks occur during Kill time?
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    # Unusual in that we don't trigger on each attack, but at the end
    def protect(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        if not self.roleblocked:
            player.defense_power = 2

    def random_attack(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        visited_sans = player.visited.copy()
        visited_sans.remove(self)
        print(player, player.visited, visited_sans)
        if visited_sans is not None:
            self.attack(np.random.choice(visited_sans))
        else:
            self.submit(f'Noone visited {player.name}')
# TODO: Test multi-turn trapping
class Trapper(Player):
    """
    Select one player and place a trap outside their house. The first visitor to that house is trapped and prevented from doing their action. 
    If the visitor was attacking, they get attacked instead. Otherwise, the trapper learns their ROLE (but not their name). 
    Only one trap may be active at a time, placing a new trap disables the old one. It takes a full night to build a trap (basically there's a delay of 1 night)	
    None	2	0		Does not attack non-killing visitors like the dementor or the Obscurus.	Sorcerer, Necromancer, Cursebreaker, Magic Bomber
    """
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)
        self.attack_power = 2

    # Extra local vaciables
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)
        self.trapped_player = None

    def at_night(self, action ,*args, **kwargs):
        if action == 'trap': 
            self.game.add_action(self, self.trap, Priority.Controlling, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def trap(self, player_name: Union[int, str]) -> None: #AMB: does trap dissapear on death?
        player = self.game.get_player(player_name)
        self.visit(player)
        if not self.roleblocked:
            if self.trapped_player is not None:
                del player.trappers[trapped_player]
            trapped_player = player
            player.trappers[trapped_player] = False
            self.submit(f'You set a trap at {player.name}')
        else:
            self.submit(f'You were roleblocked')
   
class Priest(Player):
    """
    Choose a player. You can choose to either
    (1) heal them from poison,
    (2) remove the effect of dousing, hexing, framing, and bribery, or 
    (3) cure them of plague. Must wait one day between poison cures.	
    None	0	0			Time Turner, Professor, poltergeist
    """
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)
        self.last_heal = 0

    def at_night(self, action ,*args, **kwargs):
        if action == 'heal':
            assert self.last_heal == 0
            self.game.add_action(self, self.heal, Priority.Protect, args, kwargs)
            self.last_heal = 1
        elif action == 'clean':
            self.last_heal = 0
            self.game.add_action(self, self.clean, Priority.Protect, args, kwargs)
        elif action == 'cure':
            self.last_heal = 0
            self.game.add_action(self, self.cure, Priority.Protect, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def heal(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        if not self.roleblocked: #AMB: do they know if the person was poisoned?
            player.poisoned = False
            self.submit(f'You healed {player.name} of poison')
        else:
            self.submit(f'You were roleblocked')

    def clean(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        if not self.roleblocked:
            self.doused = False
            self.hexed = False
            self.framed = False
            self.bribed = False
            self.submit(f'You cleaned {player.name}')
        else:
            self.submit(f'You were roleblocked')
    
    def cure(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        if not self.roleblocked:
            self.infected = False
            self.submit(f'You cured {player.name} of the plague')
        else:
            self.submit(f'You were roleblocked')

class Retributionist(Player):
    """
    Once a game, on or after Night 3, select a dead player to bring back to life. 
    You have THREE vests, which you can choose to use on yourself or donate to the revived player. 	None	0	2 (if vested)	
    Bite immune if vested	cannot revive a Polyjuice Potioneer	Sorcerer, Necromancer, Cursebreaker, Magic Bomber
    """
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)
        self.can_ressurrect = True
        self.vests = 3

    def at_night(self, action ,*args, **kwargs):
        if action == 'ressurrect':
            bad_ressurrects = ['Disguiser', 'Priest', 'Necromancer', 'Trapper', 'Bomber']
            assert self.can_ressurrect and not args[0].alive and args[0].role not in bad_ressurrects and self.game.night >= 3
            self.can_ressurrect = False
            self.game.add_action(self, self.ressurrect, Priority.Ressurrect, args, kwargs)
        elif action == 'vest':
            assert self.vests > 0
            self.vests -= 1
            self.game.add_action(self, self.vest, Priority.Immediate, args, kwargs)
            self.game.add_action(self, self.end_vest, Priority.CleanUp, args, kwargs) #AMB: TT not specified
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def ressurrect(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        player.alive = True
    
    def vest(self) -> None:
        self.defense_power = 2
        self.bite_immunity = True
    
    def end_vest(self) -> None:
        self.defense_power = 0
        self.bite_immunity = False

class Transporter(Player):
    """
    Select two people. Any action affecting the first will affect the second, and vice-versa.  
    Order of multiple is determined randomly.	None	0	0	Role-block immune, control immune	
    If you transport an active Veteran/Basilisk/WW, you will die, but transport will still occur. 
    If you transport a converting Werewolf, the transport will occur and you will be converted.	Quidditch Captain, Knight Bus Driver, Mirage, Moosehead
    """
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)
        self.roleblock_immunity = True
        self.control_immunity = True

    def at_night(self, action ,*args, **kwargs):
        if action == 'swap':
            self.game.add_action(self, self.swap, Priority.Transport, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def swap(self, player_name: Union[int, str], player_name2: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        player2 = self.game.get_player(player_name2)
        self.visit(player)
        self.visit(player2)
        if not self.roleblocked:
            self.game.swaps.append([player.id,player2.id])
            self.submit(f'You tried to swap {player.name} and {player2.name}')
        else:
            self.submit(f'You were roleblocked')

class Moosehead(Player):
    """
    Moosehead	"Select one person. Find out if they go out, and if they do, you take them out 
    to a party and they overindulge.... and they become disoriented and perform 
    their chosen action on a random target."	None	0	0	Role-block immune, control immune		Auror, Executioner, Werewolf, Caretaker
    """
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)
        self.roleblock_immunity = True
        self.control_immunity = True

    def at_night(self, action ,*args, **kwargs):
        if action == 'disorient':
            self.game.add_action(self, self.disorient, Priority.Controlling, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def disorient(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        if not self.roleblocked:
            alive_players = [] #maybe should keep track of this
            for a_player in self.game.players:
                if self.game.get_player(a_player).alive:
                    alive_players.append(a_player)
            player.control_id = np.random.choice(alive_players)
            self.submit(f'You disoriented {player.name} so that they acted on {self.game.get_player(player.control_id).name}') #AMB: Is the disoriented player informed of the control?
        else:
            self.submit(f'You were roleblocked')

class Escort(Player):
    """
    Sphinx (Escort)	Select one person to role-block. The player cannot perform an action that night. 
    (Same as dementor.) Removes any links/vows this person has with another player caused by Unbreakable Vow Enforcer, regardless of whether or not the role-blocking occurs.	
    None	0	0	Role-block immune	Some roles are role-block immune, and others (SK, active Werewolf) will kill or convert you	Sphinx, Veela, Dementor, Grim
    """
    TEAM = Team.Town
    def __init__(self, game: Game, player_id, name=None):
        super().__init__(game, player_id, name)
        self.roleblock_immunity = True

    def at_night(self, action ,*args, **kwargs):
        if action == 'roleblock':
            self.game.add_action(self, self.roleblock, Priority.RoleBlock, args, kwargs)
        else:
            print('Action', action,'not found for',self.__class__.__name__)

    def roleblock(self, player_name: Union[int, str]) -> None:
        player = self.game.get_player(player_name)
        self.visit(player)
        if not self.roleblocked:
            if player.check_roleblocked():
                self.submit(f'{player.name} successfully roleblocked')
            else:
                self.submit(f'{player.name} roleblock failed')
            # Unlink player Enforcer links
            for player2 in player.links.keys():
                del player.links[player2]
                if player in player2.links.keys():
                    del player2.links[player]
        else:
            self.submit(f'You were roleblocked')

########################
#         MAFIA        #
########################

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
        if not self.roleblocked:
            self.submit(f'target\'s role is {player.role}')
        else:
            self.submit(f'You were roleblocked')

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
        if not self.roleblocked:
            self.submit(f'target\'s role is {player.role}')
        else:
            self.submit(f'You were roleblocked')
