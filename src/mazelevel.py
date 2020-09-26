#!/usr/bin/env python3


"""
File : mazelevel.py

Random creation of a maze level.
"""

import typing
import random
import enum
import abc

import myrandom
import mylogger
import places
import abstractlevel
import features


@enum.unique
class DirectionEnum(enum.Enum):
    """ Possible direction from corner of wall """
    EAST = enum.auto()
    SOUTH = enum.auto()
    WEST = enum.auto()
    NORTH = enum.auto()


class AbstractCase(abc.ABC):
    """ A generic case """

    def __init__(self, position: typing.Tuple[int, int]) -> None:
        self._position = position

    @abc.abstractmethod
    def tile_type(self) -> places.TileTypeEnum:
        """ Should provide tile type to display """

    @property
    def position(self) -> typing.Tuple[int, int]:
        """ property """
        return self._position


class Empty(AbstractCase):
    """ A cell that will never be filled in """

    # no init since init of parent class is used

    def tile_type(self) -> places.TileTypeEnum:
        return places.TileTypeEnum.GROUND_TILE


class PossWall(AbstractCase):
    """ Can be a wall or not, separates cells """

    def __init__(self, position: typing.Tuple[int, int], vertical: bool) -> None:
        AbstractCase.__init__(self, position)
        self._vertical = vertical
        self._cancelled = False
        self._connects: typing.List[Empty] = list()

    def add_connects(self, empty: Empty) -> None:
        """ add a connection to posswall """
        self._connects.append(empty)

    def cancel(self) -> None:
        """ cancel posswall (no wall there) """
        self._cancelled = True

    def tile_type(self) -> places.TileTypeEnum:
        if self._cancelled:
            return places.TileTypeEnum.GROUND_TILE
        if self._vertical:
            return places.TileTypeEnum.MAZE_V_WALL
        return places.TileTypeEnum.MAZE_H_WALL

    def __lt__(self, other: 'PossWall') -> bool:
        """ need to sort posswals for determinism """
        return self.position < other.position

    @property
    def vertical(self) -> bool:
        """ property """
        return self._vertical

    @property
    def connects(self) -> typing.List[Empty]:
        """ property """
        return self._connects

    @property
    def cancelled(self) -> bool:
        """ property """
        return self._cancelled


class Corner(AbstractCase):
    """ Separates cells too, but always present """

    def __init__(self, position: typing.Tuple[int, int]) -> None:
        AbstractCase.__init__(self, position)
        self._connects: typing.Dict[DirectionEnum, PossWall] = dict()

    def add_connects(self, direction: DirectionEnum, posswall: PossWall) -> None:
        """ add a connection to corner """
        self._connects[direction] = posswall

    def tile_type(self) -> places.TileTypeEnum:

        alive_connects = {d for (d, pw) in self._connects.items() if not pw.cancelled}

        if len(alive_connects) == 4:
            assert alive_connects == set([DirectionEnum.EAST, DirectionEnum.WEST, DirectionEnum.NORTH, DirectionEnum.SOUTH]), "Maze : corner four connects but different"
            return places.TileTypeEnum.MAZE_X_CORNER

        if len(alive_connects) == 3:
            if alive_connects == set([DirectionEnum.EAST, DirectionEnum.WEST, DirectionEnum.SOUTH]):
                return places.TileTypeEnum.MAZE_T_0_CORNER
            if alive_connects == set([DirectionEnum.WEST, DirectionEnum.NORTH, DirectionEnum.SOUTH]):
                return places.TileTypeEnum.MAZE_T_90_CORNER
            if alive_connects == set([DirectionEnum.EAST, DirectionEnum.WEST, DirectionEnum.NORTH]):
                return places.TileTypeEnum.MAZE_T_180_CORNER
            if alive_connects == set([DirectionEnum.EAST, DirectionEnum.NORTH, DirectionEnum.SOUTH]):
                return places.TileTypeEnum.MAZE_T_270_CORNER

        if len(alive_connects) == 2:

            if alive_connects == set([DirectionEnum.EAST, DirectionEnum.NORTH]):
                return places.TileTypeEnum.MAZE_L_0_CORNER
            if alive_connects == set([DirectionEnum.EAST, DirectionEnum.SOUTH]):
                return places.TileTypeEnum.MAZE_L_90_CORNER
            if alive_connects == set([DirectionEnum.WEST, DirectionEnum.SOUTH]):
                return places.TileTypeEnum.MAZE_L_180_CORNER
            if alive_connects == set([DirectionEnum.WEST, DirectionEnum.NORTH]):
                return places.TileTypeEnum.MAZE_L_270_CORNER

            if alive_connects == set([DirectionEnum.EAST, DirectionEnum.WEST]):
                return places.TileTypeEnum.MAZE_H_WALL
            if alive_connects == set([DirectionEnum.NORTH, DirectionEnum.SOUTH]):
                return places.TileTypeEnum.MAZE_V_WALL

        if len(alive_connects) == 1:
            if alive_connects == set([DirectionEnum.NORTH]):
                return places.TileTypeEnum.MAZE_I_0_CORNER
            if alive_connects == set([DirectionEnum.EAST]):
                return places.TileTypeEnum.MAZE_I_90_CORNER
            if alive_connects == set([DirectionEnum.SOUTH]):
                return places.TileTypeEnum.MAZE_I_180_CORNER
            if alive_connects == set([DirectionEnum.WEST]):
                return places.TileTypeEnum.MAZE_I_270_CORNER

        assert False, "Maze : corner connects unexpected situation"
        return None

    @property
    def connects(self) -> typing.Dict[DirectionEnum, PossWall]:
        """ property """
        return self._connects


class MazeLevel(abstractlevel.AbstractLevel):
    """ A maze level object """

    def __init__(self, level_name: str, depth: int, branch: str, already_special_rooms: typing.Set[abstractlevel.SpecialRoomEnum], nb_down_stairs: int = 1, nb_up_stairs: int = 1, entry_level: bool = False) -> None:  # pylint: disable=unused-argument

        def outside_maze(pos: typing.Tuple[int, int]) -> bool:
            """ detects outside positions """

            x_pos, y_pos = pos
            if x_pos < 0 or x_pos > self._maze_width - 1:
                return True
            if y_pos < 0 or y_pos > self._maze_height - 1:
                return True
            return False

        #  start of init here

        abstractlevel.AbstractLevel.__init__(self, level_name, depth, branch, nb_down_stairs, nb_up_stairs, entry_level)

        self._empty_tiles: typing.Set[Empty] = set()
        self._posswall_tiles: typing.Set[PossWall] = set()
        self._corner_tiles: typing.Set[Corner] = set()

        # resized to make sure we have walls on every edge of level
        self._maze_width = (self._level_width // 4) * 4 - 1
        self._maze_height = (self._level_height // 4) * 4 - 1

        # create maze items
        empty_table = dict()
        posswall_table = dict()
        for x_pos in range(self._maze_width):
            for y_pos in range(self._maze_height):
                pos = (x_pos, y_pos)

                if x_pos % 2 == 0 and y_pos % 2 == 0:
                    corner = Corner(pos)
                    self._corner_tiles.add(corner)
                    continue

                if x_pos % 2 == 0 or y_pos % 2 == 0:
                    vertical = x_pos % 2 == 0
                    posswall = PossWall(pos, vertical)
                    self._posswall_tiles.add(posswall)
                    posswall_table[pos] = posswall
                    continue

                empty = Empty(pos)
                self._empty_tiles.add(empty)
                empty_table[pos] = empty

        # connect maze walls to empties
        for posswall in self._posswall_tiles:
            x_pos, y_pos = posswall.position
            delta_table = [(-1, 0), (1, 0)] if posswall.vertical else [(0, -1), (0, 1)]
            for delta_x, delta_y in delta_table:
                neigh_x = x_pos + delta_x
                neigh_y = y_pos + delta_y
                neigh = (neigh_x, neigh_y)
                if outside_maze(neigh):
                    continue
                empty = empty_table[neigh]
                posswall.add_connects(empty)

        # connect maze corners to walls
        delta_direction_table = {DirectionEnum.WEST: (-1, 0), DirectionEnum.EAST: (1, 0), DirectionEnum.NORTH: (0, -1), DirectionEnum.SOUTH: (0, 1)}
        for corner in self._corner_tiles:
            x_pos, y_pos = corner.position
            for direction, (delta_x, delta_y) in delta_direction_table.items():
                neigh_x = x_pos + delta_x
                neigh_y = y_pos + delta_y
                neigh = (neigh_x, neigh_y)
                if outside_maze(neigh):
                    continue
                posswall = posswall_table[neigh]
                corner.add_connects(direction, posswall)

        # make sets of empties
        group = dict()
        for empty in self._empty_tiles:
            group[empty] = empty

        # sort once for all to make it determinist
        sorted_posswall_tiles = sorted(self._posswall_tiles)

        while True:

            selectable_posswalls = [pw for pw in sorted_posswall_tiles if len(pw.connects) == 2 and group[pw.connects[0]] != group[pw.connects[1]]]

            if not selectable_posswalls:
                mylogger.LOGGER.debug("mazelevel : no wall with different groups")
                break

            posswall_selected = random.choice(sorted(selectable_posswalls))

            # merge groups
            group_from = group[posswall_selected.connects[0]]
            group_to = group[posswall_selected.connects[1]]
            for empty in self._empty_tiles:
                if group[empty] == group_to:
                    group[empty] = group_from

            # remove wall
            posswall_selected.cancel()

        mylogger.LOGGER.debug("mazelevel : made level")

        selectable_tiles = {e.position for e in self._empty_tiles}

        # put stairs in places where they go down
        for _ in range(nb_down_stairs):
            staircase = random.choice(sorted(selectable_tiles))
            self._downstairs.add(staircase)
            selectable_tiles.remove(staircase)

        # put stairs in places where they go up
        for _ in range(nb_up_stairs):
            staircase = random.choice(sorted(selectable_tiles))
            self._upstairs.add(staircase)
            selectable_tiles.remove(staircase)

            # could be the dungeon entry point
            if entry_level:
                self._entry_position = staircase

        # add features
        nb_features = 2 + myrandom.dice("d2")
        for _ in range(nb_features):
            feature_pos_choice = random.choice(sorted(selectable_tiles))
            selectable_tiles.remove(feature_pos_choice)
            features_selection = [features.Fountain]
            features_selection_table = [features.PROBA_FEATURES[features.POSSIBLE_FEATURES.index(f)] for f in features_selection]
            feature_class_choices = random.choices(features_selection, features_selection_table)
            feature_class_choice = feature_class_choices[0]
            abstractlevel.put_feature(feature_pos_choice, feature_class_choice, self._level_features)

        # add engravings
        nb_engravings = 1 + myrandom.dice("d1")
        for _ in range(nb_engravings):
            engraving_pos_choice = random.choice(sorted(selectable_tiles))
            selectable_tiles.remove(engraving_pos_choice)
            abstractlevel.put_engraving(engraving_pos_choice, self._level_engravings)

        # add heavyrocks
        # No heavy rocks in mazes

        self._free_downstairs = self._downstairs.copy()
        self._free_upstairs = self._upstairs.copy()

    def convert_to_places(self) -> None:
        """ Converts logical just created level to table of tiles the game will use """

        for empty in self._empty_tiles:
            tile_type = empty.tile_type()
            tile = places.Tile(tile_type)
            place = places.Place(tile)
            empty_pos = empty.position
            self._data[empty_pos] = place

        for posswall in self._posswall_tiles:
            tile_type = posswall.tile_type()
            tile = places.Tile(tile_type)
            place = places.Place(tile)
            posswall_pos = posswall.position
            self._data[posswall_pos] = place

        for corner in self._corner_tiles:
            tile_type = corner.tile_type()
            tile = places.Tile(tile_type)
            place = places.Place(tile)
            corner_pos = corner.position
            self._data[corner_pos] = place

        # export features
        for feature in self._level_features:
            feature_level_pos = feature.position
            feature_place = self._data[feature_level_pos]
            assert feature_place.tile.mytype is places.TileTypeEnum.GROUND_TILE, "feature not on ground tile"
            feature_place.feature = feature

        # export engravings
        for engraving in self._level_engravings:
            engraving_level_pos = engraving.position
            engraving_place = self._data[engraving_level_pos]
            assert engraving_place.tile.mytype is places.TileTypeEnum.GROUND_TILE, "engraving not on ground tile"
            engraving_place.inscription = engraving.inscription

        # export engravings
        # no heavyrock for mazes

        # light sources are not exported

        # export stairs
        self.export_stairs()


if __name__ == '__main__':
    abstractlevel.test(MazeLevel)
