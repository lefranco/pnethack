#!/usr/bin/env python3


"""
File : monsters.py

Handle stuff related to all living creatures of the game. Even the undead.
Hero is a monster too.
"""

import typing
import collections
import enum

import myrandom
import mylogger
import display
import pickables

# how long monster position stays in monster's memory
MAX_MEMORY_FRESHNESS = 20


class Backsack:
    """ Purse object """
    name = "Backsack"

    def __init__(self) -> None:
        self._content: typing.Set[pickables.Pickable] = set()

    def add_something(self, item: pickables.Pickable) -> None:
        """ picking up something """
        self._content.add(item)

    def remove_something(self, item: pickables.Pickable) -> None:
        """ drop something """
        self._content.remove(item)

    def list_content(self) -> typing.List[pickables.Pickable]:
        """ yields the list """
        return sorted(self._content)

    def __str__(self) -> str:
        res = "    Inventory : "
        for pick_class in pickables.Pickable.__subclasses__():
            items_class = [i.whatis() for i in self._content if isinstance(i, pick_class)]
            if items_class:
                res += f"\n {pick_class.__name__}  {pick_class.class_glyph}:\n"
                res += "\n".join(items_class)
        return res


class Purse:
    """ Purse object """
    name = "Purse"
    short_name = "$"

    def __init__(self, value: int) -> None:
        self._value = value

    def __str__(self) -> str:
        return f"{type(self).short_name}:{self._value}"


class Points:
    """ Generic point engine """

    # will be superseded
    short_name = "à"

    def __init__(self, value: int) -> None:
        self._value = value
        self._value_max = value

    def credit(self, more: int) -> None:
        """ get some more or some less """
        self._value += more
        if self._value < 0:
            self._value = 0
        if self._value > self._value_max:
            self._value = self._value_max

    def __str__(self) -> str:
        return f"{type(self).short_name}:{self._value}({self._value_max})"


class HitPoints(Points):
    """ Hit points engine """

    name = "HitPoints"
    short_name = "HP"


class PowerPoints(Points):
    """ Power points engine """

    name = "Power"
    short_name = "Pw"


class ExperienceLevel:
    """ Experience Level engine """
    name = "Experience Level"
    short_name = "XL"

    def __init__(self, value: int) -> None:
        self._value = value

    def gain_one(self) -> None:
        """ Gain a level """
        self._value += 1

    def loose_one(self) -> None:
        """ Loose a level """
        self._value -= 1

    def __str__(self) -> str:
        return f"{type(self).short_name}:{self._value}"


class ArmourClass:
    """ Armour class engine """

    name = "Armour Class"
    short_name = "AC"

    def __init__(self, value: int) -> None:
        self._value = value

    def __str__(self) -> str:
        return f"{type(self).short_name}:{self._value}"


class MemoryPosition:
    """ class part of an AI to remember position of other monsters """

    def __init__(self) -> None:
        # actually it is not a monster, it is an occupant (that includes the heavyrock too)
        self._where_is_monster: typing.Dict[Occupant, typing.Tuple[int, int]] = dict()
        self._what_monster_there: typing.Dict[typing.Tuple[int, int], Occupant] = dict()
        self._freshness: typing.Dict[Occupant, int] = dict()

    def note_position(self, occupant: 'Occupant') -> None:
        """ Store in memory the occupant that is seen """

        occupant_pos = occupant.position

        # clean false information in self._what_monster_there
        if occupant in self._where_is_monster:
            prev_occupant_pos = self._where_is_monster[occupant]
            if prev_occupant_pos in self._what_monster_there and self._what_monster_there[prev_occupant_pos] is occupant:
                del self._what_monster_there[prev_occupant_pos]

        # clean false information in self._where_is_monster
        if occupant_pos in self._what_monster_there:
            prev_monster = self._what_monster_there[occupant_pos]
            if prev_monster in self._where_is_monster and self._where_is_monster[prev_monster] == occupant_pos:
                del self._where_is_monster[prev_monster]

        # put monster in
        self._where_is_monster[occupant] = occupant_pos
        self._what_monster_there[occupant_pos] = occupant
        self._freshness[occupant] = MAX_MEMORY_FRESHNESS

    def recall_position(self, monster: 'Occupant') -> typing.Optional[typing.Tuple[int, int]]:
        """ Using one's memory recall where is monster """

        if monster not in self._where_is_monster:
            return None

        monster_pos = self._where_is_monster[monster]
        return monster_pos

    def recall_monster(self, position: typing.Tuple[int, int]) -> typing.Optional['Occupant']:
        """ Using one's memory recall whate is somewhere """

        if position not in self._what_monster_there:
            return None

        monster = self._what_monster_there[position]
        return monster

    def rot_memory(self) -> None:
        """ Memory fades away """

        for occupant in self._freshness.copy():
            self._freshness[occupant] -= 1
            if self._freshness[occupant] == 0:
                # rotten : forget about occupant
                occupant_pos = self._where_is_monster[occupant]
                del self._where_is_monster[occupant]
                del self._what_monster_there[occupant_pos]
                del self._freshness[occupant]


class Occupant(display.Displayable):
    """ Monster of HeavyRock (statue/boulder) that may occupy a place """

    # Note : dungeon_level is of type abstractlevel.AbstractLevel but we do not want to
    #        import abstractlevel here because we would get an import chain such as:
    #        monster -> abstractlevel -> places -> monster
    def __init__(self, dungeon_level: typing.Any, position: typing.Tuple[int, int]) -> None:
        self._dungeon_level = dungeon_level
        self._position = position

    # will be superseded
    def glyph(self) -> str:
        """ glyph """
        assert False, "Missing glyph for Occupant"
        return ""

    # will be superseded
    def whatis(self) -> str:
        """ whatis """
        assert False, "Missing whatis for Occupant"
        return ""

    # will be superseded
    def blocks_vision(self) -> bool:  # pylint: disable=no-self-use
        """ blocks_vision """
        assert False, "Missing blocks_vision for Occupant"
        return False

    # Note: should return abstractlevel.AbstractLevel (see init)
    @property
    def dungeon_level(self) -> typing.Any:
        """ property """
        return self._dungeon_level

    @property
    def position(self) -> typing.Tuple[int, int]:
        """ property """
        return self._position


@enum.unique
class MonsterTypeEnum(display.SomethingSeen, enum.Enum):
    """ All possible tiles types """
    # Id = (desc, glyph, base_speed, is_strong, is_big, statue_possible)

    HERO = ("the hero", "@", 12, False, False, False)
    ORC = ("an orc", "o", 9, True, False, True)
    HUMAN = ("a human", "H", 12, False, False, True)
    CENTAUR = ("a centaur", "C", 18, True, False, True)
    XAN = ("a xan", "x", 18, False, False, True)

    def __init__(self, desc: str, monster_glyph: str, base_speed: int, is_strong: bool, is_big: bool, statue_possible: bool) -> None:
        display.SomethingSeen.__init__(self, desc)
        self._monster_glyph = monster_glyph
        self._base_speed = base_speed
        self._is_strong = is_strong
        self._is_big = is_big
        self._statue_possible = statue_possible

    @staticmethod
    def find(monster_name: str) -> 'MonsterTypeEnum':
        """ find monster by name """
        for monster_type in MonsterTypeEnum:
            if monster_type.desc.endswith(monster_name):
                return monster_type
        assert False, "Unknown monster type"
        return MonsterTypeEnum.HERO

    @property
    def monster_glyph(self) -> str:
        """ property """
        return self._monster_glyph

    @property
    def base_speed(self) -> int:
        """ property """
        return self._base_speed

    @property
    def is_strong(self) -> bool:
        """ property """
        return self._is_strong

    @property
    def is_big(self) -> bool:
        """ property """
        return self._is_big

    @property
    def statue_possible(self) -> bool:
        """ property """
        return self._statue_possible


class Monster(Occupant):
    """ A monster """

    rising_ones: typing.Deque['Monster'] = collections.deque([])
    ready_ones: typing.Deque['Monster'] = collections.deque([])
    standby_ones: typing.Deque['Monster'] = collections.deque([])
    sleeping_ones: typing.Deque['Monster'] = collections.deque([])
    dead_ones: typing.Deque['Monster'] = collections.deque([])

    def __init__(self, mytype: MonsterTypeEnum, dungeon_level: typing.Any, position: typing.Tuple[int, int], money_given: int) -> None:

        Occupant.__init__(self, dungeon_level, position)
        self._mytype = mytype

        experience_level = 1
        self._experience_level = ExperienceLevel(experience_level)

        hit_points = 1
        power_points = 1
        for _ in range(experience_level):
            hit_points += myrandom.dice("d8")
            power_points += myrandom.dice("d4")
        self._hit_points = HitPoints(hit_points)
        self._power_points = PowerPoints(power_points)

        self._armourclass = ArmourClass(10)
        self._backsack = Backsack()
        self._purse = Purse(money_given)

        # what monster remembers of other monsters (and heavyrocks)
        self._memory_position = MemoryPosition()

        # put it in map if provided
        if self._dungeon_level is not None:
            self._dungeon_level.data[self._position].occupant = self

        # that will make it "live"
        Monster.rising_ones.append(self)

    def glyph(self) -> str:
        """ glyph """
        return self._mytype.monster_glyph

    def whatis(self) -> str:
        """ whatis """
        return self._mytype.desc

    def is_hero(self) -> bool:
        """ need to know because more than often behaviour is different """
        return self._mytype is MonsterTypeEnum.HERO

    def die(self) -> None:
        """ All lives come to an end !"""

        # that will make it "die"
        mylogger.LOGGER.debug("death of monster %s", self)

        # remove from map
        # TODO : make a corpse...
        old_level = self._dungeon_level
        old_pos = self._position
        old_level.data[old_pos].occupant = None

        # make it inactive and put it list to handle as dead
        if self in Monster.ready_ones:
            Monster.ready_ones.remove(self)
            Monster.dead_ones.append(self)
        elif self in Monster.standby_ones:
            Monster.standby_ones.remove(self)
            Monster.dead_ones.append(self)
        elif self in Monster.rising_ones:
            # special case : does not die, just birth is cancelled
            Monster.rising_ones.remove(self)
        else:
            assert False, "Dying monster un strange state"

    def blocks_vision(self) -> bool:
        """ blocks_vision """
        return self._mytype.is_big

    def speed_value(self) -> int:
        """ speed """
        return self._mytype.base_speed

    def strength_value(self) -> int:
        """ strength """
        if self._mytype.is_strong:
            return 23  # "18/**" value
        return 10

    def proba_secret_detection_value(self) -> float:  # pylint: disable=no-self-use
        """ proba secret detection """
        return 15.0

    def luck_value(self) -> int:   # pylint: disable=no-self-use
        """ should not be called """
        assert False, "Monster do not have luck !"
        return 0

    # Note: parameter dungeon_level should have type abstractlevel.AbstractLevel (see init of parent Occupant class)
    def moves_to(self, dungeon_level: typing.Any, position: typing.Tuple[int, int]) -> None:
        """ Moves the monster (including the hero)  """

        old_level = self._dungeon_level
        old_pos = self._position

        # update monster data
        self._dungeon_level = dungeon_level
        self._position = position

        # update level data
        old_level.data[old_pos].occupant = None
        # test necessary when hero quitting dungeon
        if self._dungeon_level is not None:
            self._dungeon_level.data[self._position].occupant = self

    def rest_in_place(self) -> None:
        """ The monster takes a break """
        if myrandom.toss_coin():
            self.hit_points.credit(1)

    def considers_passable(self, position: typing.Tuple[int, int]) -> bool:
        """ function saying if monsters thinks a tile is passable """

        if not self._dungeon_level.data[position].may_access():
            return False

        # Occupant is extracted from the monsters' memory
        occupant_remembered = self._memory_position.recall_monster(position)
        if not occupant_remembered:
            return True

        # Pessimistic : we do not hope the monster there will move by the time we get there
        # TODO : could be a bit more clever about this, like finding an other way...
        if isinstance(occupant_remembered, Monster):
            return False

        # There is a boulder or a statue on the way
        return False

    def tick(self) -> None:
        """ tick """
        # TODO : pass it to everything that fades in this monster
        pass

    def __str__(self) -> str:
        return self.whatis()

    @property
    def mytype(self) -> MonsterTypeEnum:
        """ property """
        return self._mytype

    @property
    def hit_points(self) -> HitPoints:
        """ property """
        return self._hit_points

    @property
    def power_points(self) -> PowerPoints:
        """ property """
        return self._power_points

    @property
    def backsack(self) -> Backsack:
        """ property """
        return self._backsack

    @property
    def memory_position(self) -> MemoryPosition:
        """ property """
        return self._memory_position


if __name__ == '__main__':
    assert False, "Do not run this script"
