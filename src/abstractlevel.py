#!/usr/bin/env python3


"""
File : abstractlevel.py

All classes building levels herit from this class and abide this class' interface
"""

import abc
import typing
import itertools
import enum
import random

import constants
import mylogger
import myrandom
import features
import heavyrocks
import pickables
import alignment
import places
import monsters

NB_TEST = 10


# Probability of presence of item on a tile
PROBA_PRESENCE_ITEM = 4

# types A -> G
# Probability of different types of items depending on branch
PROBA_CATEGORIES_ITEM = {
    "M": (10, 10, 10, 10, 40, 10, 10),  # mine - mine levels
    "G": (10, 20, 30, 20, 10, 5, 5),  # gehenon - maze level
    "D": (30, 20, 10, 10, 10, 10, 10)  # doom - room level
}
# add for a new branch here
for b, p in PROBA_CATEGORIES_ITEM.items():
    assert len(p) == len(pickables.PROBA_ITEMS), f"Mismatch in types items probability table for branch {b}"
    assert sum(p) == 100, f"Sum of proba tiles is {sum(p)} not 100  for branch {b}"


@enum.unique
class SpecialRoomEnum(enum.Enum):
    """ Possible special rooms type """

    # Id = (difficulty, frequency,
    #   messages_entering_level,
    #   messages_entering_room)

    # Type A
    SHOP = (0, 0, ["You hear someone cursing shoplifters.", "You hear the chime of a cash register"], ["Welcome to <shopkeeper>'s <merchandise> store!"])

    # Type B
    THRONE_ROOM = (1, 3, ["You hear the tones of courtly conversation.", "You hear a sceptre pounded in judgment"], ["You enter an opulent throne room!"])
    TREASURE_ZOO = (2, 1, ["You hear a sound reminiscent of an elephant stepping on a peanut.", "You hear a sound reminiscent of a seal barking."], ["Welcome to David's treasure zoo!"])
    TEMPLE = (3, 4, ["You hear a strident plea for donations."], ["You enter a temple"])
    GRAVEYARD = (4, 2, ["You suddenly realize it is unnaturally quiet."], ["You have an uncanny feeling..."])
    BARRACKS = (5, 5, ["You hear blades being honed.", "You hear dices being thrown"], ["You enter a military barracks!"])
    # Oracle should not be generated
    ORACLE = (0, 0, ["You hear convulsive ravings."], ["You enter Delphi...(tbd)"])

    # Type C
    FUNGUS_FARM = (1, 4, ["You hear you are on a fungus farm level (tbd)"], ["You enter a room full of fungi!"])
    LEPRECHAUN_HALL = (2, 5, ["You hear you are on a leprechaun level (tbd)"], ["You enter leprechaun hall!"])
    BEEHIVE = (3, 3, ["You hear a low buzzing."], ["You enter a giant beehive!"])
    NYMPH_GARDEN = (4, 3, ["You hear you are on a nymph garden level (tbd)"], ["You enter nymph garden"])
    ANTHOLE = (5, 5, ["You hear you are on a anthole level (tbd)"], ["You enter anthole"])
    COCKATRICE_NEST = (6, 4, ["You hear you are on a cockatrice nest level (tbd)"], ["You enter a disgusting nest!"])
    GIANT_COURT = (7, 2, ["You hear you are on a giant court level (tbd)"], ["You enter a giant throne room"])
    DRAGON_LAIR = (8, 1, ["You hear you are on a dragon's lair level (tbd)"], ["You enter dragon lair"])

    def __init__(self, difficulty: int, frequency: int, messages_entering_level: typing.List[str], messages_entering_room: typing.List[str]) -> None:

        # how frequent in generation
        self._difficulty = difficulty
        # towards which level more generated
        self._frequency = frequency
        # some special rooms produce a message when entering level
        self._messages_entering_level = messages_entering_level
        # some special rooms produce a message when entering room itself
        self._messages_entering_room = messages_entering_room

    def messages_entering_level(self) -> typing.List[str]:
        """ not a property """
        return self._messages_entering_level

    def messages_entering_room(self) -> typing.List[str]:
        """ not a property """
        return self._messages_entering_room

    @property
    def difficulty(self) -> int:
        """ property """
        return self._difficulty

    @property
    def frequency(self) -> int:
        """ property """
        return self._frequency


class SpecialRoom:
    """ A special room object """

    def __init__(self, mytype: SpecialRoomEnum, upper_left: typing.Tuple[int, int], size: typing.Tuple[int, int], altar_alignment: typing.Optional[alignment.AlignmentEnum] = None) -> None:

        # the  size for the room
        size_width, size_height = size

        # the position for the room
        upper_left_x, upper_left_y = upper_left

        # cells include walls and walls include corners
        self._cells = {(x, y) for x in range(upper_left_x, upper_left_x + size_width + 1) for y in range(upper_left_y, upper_left_y + size_height + 1)}

        self._mytype = mytype

        # only relevant for altars
        self._altar_alignment = altar_alignment

    def is_inside(self, pos: typing.Optional[typing.Tuple[int, int]]) -> bool:
        """ Says if position is inside the spceial room """
        if pos is None:
            return False
        return pos in self._cells

    @property
    def mytype(self) -> SpecialRoomEnum:
        """ property """
        return self._mytype

    @property
    def altar_alignment(self) -> typing.Optional[alignment.AlignmentEnum]:
        """ property """
        return self._altar_alignment


class DungeonLevelDepth:
    """ Dungeon level name sort of """

    name = "Dungeon Level"
    short_name = "Dlvl"

    def __init__(self, value: int) -> None:
        self._value = value

    def __str__(self) -> str:
        return f"{type(self).short_name}:{self._value}"

    @property
    def value(self) -> int:
        """ property """
        return self._value


class Engraving:
    """ Engraving (just a string) """

    def __init__(self, position: typing.Tuple[int, int], inscription: str) -> None:
        self._position = position
        self._inscription = inscription

    @property
    def position(self) -> typing.Tuple[int, int]:
        """ property """
        return self._position

    @property
    def inscription(self) -> str:
        """ property """
        return self._inscription


def put_feature(position: typing.Tuple[int, int], feature_class_choice: typing.Any, container: typing.List[features.Feature]) -> None:
    """ a random feature """

    if feature_class_choice is features.Altar:
        altar_alignment = random.choice(list(alignment.AlignmentEnum))
        altar = features.Altar(position, altar_alignment)
        container.append(altar)
        return

    if feature_class_choice is features.HeadStone:
        with open("./data/headstones.dat") as file:
            lines = file.read().splitlines()
        inscription = random.choice(lines)
        headstone = features.HeadStone(position, inscription)
        container.append(headstone)
        return

    other_feature = feature_class_choice(position)
    container.append(other_feature)


def put_engraving(position: typing.Tuple[int, int], container: typing.List[Engraving]) -> None:
    """ a random engraving """

    with open("./data/graffitis.dat") as file:
        lines = file.read().splitlines()
    inscription = random.choice(lines)
    engraving = Engraving(position, inscription)
    container.append(engraving)


def put_heavyrock(dungeon_level: 'AbstractLevel', position: typing.Tuple[int, int], heavyrock_class_choice: typing.Any, container: typing.List[heavyrocks.HeavyRock]) -> None:
    """ a random heavyrock """

    if heavyrock_class_choice is heavyrocks.Statue:
        monster = random.choice([m for m in monsters.MonsterTypeEnum if m.statue_possible])
        statue = heavyrocks.Statue(dungeon_level, position, monster)
        container.append(statue)
        return

    if heavyrock_class_choice is heavyrocks.Boulder:
        boulder = heavyrocks.Boulder(dungeon_level, position)
        container.append(boulder)
        return

    assert False, "put_heavyrock() : what is this object ?"


class AbstractLevel(abc.ABC):
    """ All level must derive from this class """

    _cur_identifier = itertools.count(0)

    def __init__(self, level_name: str, depth: int, branch: str, nb_down_stairs: int = 1, nb_up_stairs: int = 1, entry_level: bool = False) -> None:

        assert nb_up_stairs >= 0 and nb_down_stairs >= 0, "Creating a level with no stairs at all"
        assert not (entry_level and nb_up_stairs == 0), "Creating and entry level with no up stairs"

        # only relevant for entry level
        self._entry_position: typing.Optional[typing.Tuple[int, int]] = None

        # store dimensions
        self._level_height = constants.DUNGEON_HEIGHT
        self._level_width = constants.DUNGEON_WIDTH

        self._level_features: typing.List[features.Feature] = list()
        self._level_engravings: typing.List[Engraving] = list()
        self._level_heavyrocks: typing.List[heavyrocks.HeavyRock] = list()

        self._level_light_sources: typing.List[places.LightSourceRecord] = list()

        self._name = level_name
        self._depth = DungeonLevelDepth(depth)
        self._branch = branch
        self._junction_table: typing.Dict[typing.Tuple[int, int], typing.Tuple[typing.Optional['AbstractLevel'], typing.Optional[typing.Tuple[int, int]]]] = dict()  # will be filled later

        self._downstairs: typing.Set[typing.Tuple[int, int]] = set()
        self._upstairs: typing.Set[typing.Tuple[int, int]] = set()
        self._free_downstairs: typing.Set[typing.Tuple[int, int]] = set()
        self._free_upstairs: typing.Set[typing.Tuple[int, int]] = set()

        # every level need a different identiifier
        self._identifier = next(type(self)._cur_identifier)

        # special rooms of the level
        self._level_special_rooms: typing.List[SpecialRoom] = list()

        # actual data of the level
        self._data: typing.Dict[typing.Tuple[int, int], places.Place] = dict()

        # all tiles on level are matter until otherwise specified
        for x_pos in range(self._level_width):
            for y_pos in range(self._level_height):
                tile = places.Tile(places.TileTypeEnum.MATTER)
                place = places.Place(tile)
                self._data[(x_pos, y_pos)] = place

    def scatter_items(self) -> None:
        """ Put items on the level """

        mylogger.LOGGER.debug("abstractlevel : scatter_items()")
        for x_pos in range(self._level_width):
            for y_pos in range(self._level_height):
                place = self._data[(x_pos, y_pos)]
                # is place eligible ?
                if not place.may_access():
                    continue
                if place.door:
                    continue
                if place.may_climb_up() or place.may_climb_down():
                    continue
                if place.feature:
                    continue
                if myrandom.percent_chance(PROBA_PRESENCE_ITEM):

                    # first choice : choose item category (A, B etc...)
                    assert self._branch in PROBA_CATEGORIES_ITEM, "Either no item on this branch or add proba table for this branch"
                    proba_category_item_table = PROBA_CATEGORIES_ITEM[self._branch]
                    item_category_choices: typing.List[str] = random.choices(sorted(pickables.PROBA_ITEMS.keys()), proba_category_item_table)
                    item_category_choice: str = item_category_choices[0]

                    # second choice : choose item glyph (ring, spell book etc...)
                    # type first
                    possible_glyph_items, proba_glyph_item_table = pickables.PROBA_ITEMS[item_category_choice]
                    item_glyph_choices = random.choices(possible_glyph_items, proba_glyph_item_table)  # type: ignore
                    item_glyph_choice = item_glyph_choices[0]

                    # third choice : choose item type (a ring of searching etc...)
                    possible_types = item_glyph_choice.poss_type
                    item_type = random.choice(list(possible_types))
                    # make it to item
                    item = item_glyph_choice(item_type)
                    place.items.append(item)

    def populate_monsters(self) -> None:
        """ Put mosnsters on the level """
        # TODO
        pass

    def pop_downstairs(self) -> typing.Optional[typing.Tuple[int, int]]:
        """ Take a downstairs from level : common to all levels"""
        if not self._free_downstairs:
            return None
        staircase = random.choice(sorted(self._free_downstairs))
        self._free_downstairs.remove(staircase)
        return staircase

    def pop_upstairs(self) -> typing.Optional[typing.Tuple[int, int]]:
        """ Take a upstairs from level : common to all levels"""
        if not self._free_upstairs:
            return None
        staircase = random.choice(sorted(self._free_upstairs))
        self._free_upstairs.remove(staircase)
        return staircase

    def export_stairs(self) -> None:
        """ Export stairs : common to all levels """
        # export stairs down
        for staircase in self._downstairs:
            tile = places.Tile(places.TileTypeEnum.STAIRS_DOWN)
            place = places.Place(tile)
            self._data[staircase] = place
        # export stairs up
        for staircase in self._upstairs:
            tile = places.Tile(places.TileTypeEnum.STAIRS_UP)
            place = places.Place(tile)
            self._data[staircase] = place

    # monsters_ai is of class MonstersAITools but we cannot import it here (cycle)
    @staticmethod
    def show_path(monsters_ai: typing.Any, hero_position: typing.Tuple[int, int]) -> int:
        """ for debug purpose : put xans (x) on the path from some monster to hero """

        monster = monsters.Monster.ready_ones[0]
        success, _, path = monsters_ai.tools.path_towards(monster, hero_position)
        if not success:
            return 0
        for pos in path[:-1]:
            monsters.Monster(monsters.MonsterTypeEnum.XAN, monster.dungeon_level, pos, 0)
        return len(path)

    @staticmethod
    def show_los(monsters_ai: typing.Any, hero_position: typing.Tuple[int, int]) -> bool:
        """ for debug purpose : put xans (x) on the LOS (line of sight) from some monster to hero """

        monster = monsters.Monster.ready_ones[0]
        line: typing.List[typing.Tuple[int, int]] = list()
        success, line = monsters_ai.tools.can_see(monster, hero_position)
        for pos in line[:-1]:
            monsters.Monster(monsters.MonsterTypeEnum.XAN, monster.dungeon_level, pos, 0)
        return success  # type: ignore

    def reveal_secret(self) -> None:
        """ reveal secret stuff (debug)  """
        for place in self._data.values():
            if place.door:
                place.door.reveal_secret()
            if place.corridor:
                place.corridor.reveal_secret()

    def random_position(self) -> typing.Tuple[int, int]:
        """ Teleport level arrival on level position """
        possibilities = [pos for pos in self.data if self.data[pos].may_access() and not self.data[pos].occupant]
        return random.choice(possibilities)

    @abc.abstractmethod
    def convert_to_places(self) -> None:
        """ should convert logical level to physical level """

    @property
    def entry_position(self) -> typing.Optional[typing.Tuple[int, int]]:
        """ property """
        return self._entry_position

    @property
    def level_width(self) -> int:
        """ property """
        return self._level_width

    @property
    def level_height(self) -> int:
        """ property """
        return self._level_height

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier

    @property
    def data(self) -> typing.Dict[typing.Tuple[int, int], places.Place]:
        """ property """
        return self._data

    @property
    def junction_table(self) -> typing.Dict[typing.Tuple[int, int], typing.Tuple[typing.Optional['AbstractLevel'], typing.Optional[typing.Tuple[int, int]]]]:
        """ property """
        return self._junction_table

    @junction_table.setter
    def junction_table(self, junction_table: typing.Dict[typing.Tuple[int, int], typing.Tuple[typing.Optional['AbstractLevel'], typing.Optional[typing.Tuple[int, int]]]]) -> None:
        """ setter """
        self._junction_table = junction_table

    @property
    def level_special_rooms(self) -> typing.List[SpecialRoom]:
        """ property """
        return self._level_special_rooms

    @property
    def level_features(self) -> typing.List[features.Feature]:
        """ property """
        return self._level_features

    @property
    def level_engravings(self) -> typing.List[Engraving]:
        """ property """
        return self._level_engravings

    @property
    def level_heavyrocks(self) -> typing.List[heavyrocks.HeavyRock]:
        """ property """
        return self._level_heavyrocks

    @property
    def level_light_sources(self) -> typing.List[places.LightSourceRecord]:
        """ property """
        return self._level_light_sources

    @property
    def depth(self) -> DungeonLevelDepth:
        """ property """
        return self._depth

    @property
    def branch(self) -> str:
        """ property """
        return self._branch

    @property
    def name(self) -> str:
        """ property """
        return self._name


# will be called by the specific test function, not by "main"
def test(roomtype: typing.Type[typing.Any]) -> None:
    """ Just for testing making of levels """

    mylogger.start_logger(True)
    constants.load_config()

    for num in range(NB_TEST):
        myrandom.restart_random()
        print(f"{num} ", end='', flush=True)
        roomtype("dummy", 1, "X", set())


if __name__ == '__main__':
    assert False, "Do not run this script"
