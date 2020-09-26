#!/usr/bin/env python3


"""
File : dungeon.py

Overall creation of the dungeon. Means creating levels and linking them with stairs.
"""

import typing
import time
import enum

import myjson
import mylogger
import myrandom
import constants
import mazelevel
import cavelevel
import roomlevel
import mappedlevel
import abstractlevel


NB_TEST = 10


@enum.unique
class LevelTypeEnum(enum.Enum):
    """ Possible types of level """
    MAPPED_LEVEL = enum.auto()
    ROOM_LEVEL = enum.auto()
    MAZE_LEVEL = enum.auto()
    CAVE_LEVEL = enum.auto()


def find_level_type(name: str) -> LevelTypeEnum:
    """ find level type fom name """
    type_level_name = name.upper() + "_LEVEL"
    try:
        type_level = LevelTypeEnum[type_level_name]
    except KeyError:
        assert False, f"Sorry, I do not know this type of level '{name}', try 'MAPPED', 'ROOM', 'MAZE' or 'CAVE'"
    return type_level


class Dungeon:
    """
    Creates the whole dungeon
    """

    def __init__(self) -> None:

        def read_dungeon(loaded_content: typing.Dict[str, typing.Any]) -> None:
            """ reads a dungeon from json file """

            level_by_name_table: typing.Dict[str, abstractlevel.AbstractLevel] = dict()
            junction_list: typing.List[typing.Tuple[str, str]] = list()

            for item_name in loaded_content:

                item_data = loaded_content[item_name]
                item_type = item_data["type"]

                if item_type == "level":
                    level_name = item_data["name"]
                    level_type_name = item_data["level_type"]
                    level_type = find_level_type(level_type_name)
                    depth = item_data["depth"] if "depth" in item_data else 1
                    branch = item_data["branch"]
                    level_identifier = f"{depth}{branch}"
                    assert level_identifier not in self._level_table, f"Duplicated depth/branch identifier {level_identifier}"
                    nb_up_stairs = item_data["nb_up_stairs"] if "nb_up_stairs" in item_data else 1
                    nb_down_stairs = item_data["nb_down_stairs"] if "nb_down_stairs" in item_data else 1
                    entry_level = item_data["entry_level"] if "entry_level" in item_data else False
                    level = make_level(level_name, level_type, depth, branch, nb_down_stairs, nb_up_stairs, entry_level)
                    if entry_level:
                        self._entrance_level = level
                    level_by_name_table[level_name] = level
                    self._level_table[level_identifier] = level

                elif item_type == "junction":
                    upl_name = item_data["up"]
                    down_name = item_data["down"]
                    junction_list.append((upl_name, down_name))

                else:
                    assert False, "Unknown item type"

            for (up_level_name, down_level_name) in junction_list:
                if up_level_name is not None:
                    assert up_level_name in level_by_name_table, f"There is no level 'up' to join for {up_level_name}"
                    up_level = level_by_name_table[up_level_name]
                else:
                    up_level = None
                if down_level_name is not None:
                    assert down_level_name in level_by_name_table, f"There is no level 'down' to join for {down_level_name}"
                    down_level = level_by_name_table[down_level_name]
                else:
                    down_level = None
                join_levels(up_level, down_level, False)

        def make_level(level_name: str, level_type: LevelTypeEnum, depth: int, branch: str, nb_down_stairs: int, nb_up_stairs: int, entry_level: bool) -> abstractlevel.AbstractLevel:
            """ Build a single level in the dungeon """

            if entry_level:
                assert not self._entry_point_defined, "Entry point defined twice for dungeon"
                self._entry_point_defined = True

            if level_type == LevelTypeEnum.MAPPED_LEVEL:
                t_before = time.perf_counter()
                attempt_mapped_level = mappedlevel.MappedLevel(level_name, depth, branch, self._already_special_rooms, nb_down_stairs, nb_up_stairs, entry_level)
                attempt_mapped_level.convert_to_places()
                t_after = time.perf_counter()
                elapsed = t_after - t_before
                mylogger.LOGGER.info("mapped level %s took %f seconds to build", level_name, elapsed)
                return attempt_mapped_level
            if level_type == LevelTypeEnum.ROOM_LEVEL:
                t_before = time.perf_counter()
                attempt_room_level = roomlevel.RoomLevel(level_name, depth, branch, self._already_special_rooms, nb_down_stairs, nb_up_stairs, entry_level)
                attempt_room_level.convert_to_places()
                attempt_room_level.scatter_items()
                attempt_room_level.populate_monsters()
                t_after = time.perf_counter()
                elapsed = t_after - t_before
                mylogger.LOGGER.info("room level %s took %f seconds to build", level_name, elapsed)
                return attempt_room_level
            if level_type == LevelTypeEnum.MAZE_LEVEL:
                t_before = time.perf_counter()
                attempt_maze_level = mazelevel.MazeLevel(level_name, depth, branch, self._already_special_rooms, nb_down_stairs, nb_up_stairs, entry_level)
                attempt_maze_level.convert_to_places()
                attempt_maze_level.scatter_items()
                attempt_maze_level.populate_monsters()
                t_after = time.perf_counter()
                elapsed = t_after - t_before
                mylogger.LOGGER.info("maze level %s took %f seconds to build", level_name, elapsed)
                return attempt_maze_level
            if level_type == LevelTypeEnum.CAVE_LEVEL:
                t_before = time.perf_counter()
                attempt_cave_level = cavelevel.CaveLevel(level_name, depth, branch, self._already_special_rooms, nb_down_stairs, nb_up_stairs, entry_level)
                attempt_cave_level.convert_to_places()
                attempt_cave_level.scatter_items()
                attempt_cave_level.populate_monsters()
                t_after = time.perf_counter()
                elapsed = t_after - t_before
                mylogger.LOGGER.info("cave level %s took %f seconds to build", level_name, elapsed)
                return attempt_cave_level
            assert False, f"What is this type of level '{level_type}' ?"
            return None

        def join_levels(upper_level: typing.Optional[abstractlevel.AbstractLevel], lower_level: typing.Optional[abstractlevel.AbstractLevel], debug_context: bool) -> None:
            """ Join two levels in the dungeon (insert stairs etc...) """

            # Obvious checks
            assert upper_level or lower_level, "Cannot join None and None"
            if upper_level and lower_level:
                assert upper_level.depth.value < lower_level.depth.value, f"Joining levels '{upper_level.name}' and '{lower_level.name}' : check their depth"

            up_staircase = None
            if upper_level:
                up_staircase = upper_level.pop_downstairs()
                assert up_staircase, f"There are no staircase down in level '{upper_level.name}'"

            down_staircase = None
            if lower_level:
                down_staircase = lower_level.pop_upstairs()
                if not debug_context:
                    assert down_staircase, f"There are no staircase up in level '{lower_level.name}'"

            if up_staircase and down_staircase:
                assert upper_level, "No upper level"
                upper_level.junction_table[up_staircase] = (lower_level, down_staircase)
                assert lower_level, "No lower level"
                lower_level.junction_table[down_staircase] = (upper_level, up_staircase)
            elif up_staircase and not down_staircase:
                assert upper_level, "No upper level"
                upper_level.junction_table[up_staircase] = None, (0, 0)  # void !
            elif down_staircase and not up_staircase:
                assert lower_level, "No lower level"
                lower_level.junction_table[down_staircase] = None, (0, 0)  # void !

        #  == start of init here ==
        t_before_dungeon = time.perf_counter()

        self._entry_point_defined = False
        self._level_table: typing.Dict[str, abstractlevel.AbstractLevel] = dict()
        self._already_special_rooms: typing.Set[abstractlevel.SpecialRoomEnum] = set()

        if constants.GENERATE_LEVEL:
            type_level = find_level_type(constants.GENERATE_LEVEL)
            branch = ""
            if constants.GENERATE_LEVEL == "ROOM":
                branch = "D"  # doom
            elif constants.GENERATE_LEVEL == "MAZE":
                branch = "G"  # gehennom
            elif constants.GENERATE_LEVEL == "CAVE":
                branch = "M"  # mines
            else:
                assert False, "Cannot generate this type of level."
            self._entrance_level = make_level(f"Testing {constants.GENERATE_LEVEL} type", type_level, constants.GENERATE_LEVEL_DEPTH, branch, 1, 1, True)
            join_levels(None, self._entrance_level, True)
            return

        if constants.LOAD_LEVEL:
            self._entrance_level = make_level(constants.LOAD_LEVEL, LevelTypeEnum.MAPPED_LEVEL, 1, "X", 1, 1, True)
            join_levels(None, self._entrance_level, True)
            return

        # json machinery
        json_reader = myjson.JsonReader("DUNGEON")
        loaded_content = json_reader.extract()
        read_dungeon(loaded_content)

        t_after_dungeon = time.perf_counter()
        elapsed = t_after_dungeon - t_before_dungeon
        mylogger.LOGGER.info("*** dungeon took %f seconds to build ***", elapsed)

        assert self._entry_point_defined, "No entry point defined for dungeon"

    def start_position(self) -> typing.Tuple[abstractlevel.AbstractLevel, typing.Tuple[int, int]]:
        """ Dungeon start position """
        assert self._entrance_level.entry_position, "Start position not defined"
        return self._entrance_level, self._entrance_level.entry_position

    def get_level(self, identifier: str) -> typing.Optional[abstractlevel.AbstractLevel]:
        """ Get level from identifier """
        if identifier not in self._level_table:
            return None
        return self._level_table[identifier]


def test() -> None:
    """ test """
    mylogger.start_logger(True)
    constants.load_config()

    for num in range(NB_TEST):
        myrandom.restart_random()
        print(f"{num} ", end='', flush=True)
        Dungeon()


if __name__ == '__main__':
    test()
