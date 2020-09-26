#!/usr/bin/env python3


"""
File : cavelevel.py

Random creation of a cave level.
"""

import typing
import random
import collections
import heapq
import itertools

import myrandom
import mylogger
import places
import features
import abstractlevel


class CaveLevel(abstractlevel.AbstractLevel):
    """ A cave level object """

    def __init__(self, level_name: str, depth: int, branch: str, already_special_rooms: typing.Set[abstractlevel.SpecialRoomEnum], nb_down_stairs: int = 1, nb_up_stairs: int = 1, entry_level: bool = False) -> None:  # pylint: disable=unused-argument

        def outside_cave(pos: typing.Tuple[int, int]) -> bool:
            """ detects outside positions """

            x_pos, y_pos = pos
            if x_pos < 1 or x_pos > self._level_width - 2:
                return True
            if y_pos < 1 or y_pos > self._level_height - 2:
                return True
            return False

        def range_cells(pos: typing.Tuple[int, int], dist: int) -> int:
            """ live cells at distance dist """

            x_pos, y_pos = pos
            neigh_sum = 0
            for (delta_x, delta_y) in itertools.product(range(- dist, dist + 1), range(- dist, dist + 1)):
                if (delta_x, delta_y) == (0, 0):
                    continue
                neigh_x = x_pos + delta_x
                neigh_y = y_pos + delta_y
                neigh = (neigh_x, neigh_y)
                if outside_cave(neigh):
                    continue
                neigh_sum += cave_table[neigh]
            return neigh_sum

        def join_groups() -> None:
            """ add cells to join grooups """

            def all_reachable(position: typing.Tuple[int, int]) -> typing.Set[typing.Tuple[int, int]]:
                """ yield cave cells reachable from this one """

                reachable_from_there: typing.Set[typing.Tuple[int, int]] = set()
                queue: typing.List[typing.Tuple[int, int]] = list()
                heapq.heappush(queue, position)
                while queue:

                    new_pos = heapq.heappop(queue)
                    if new_pos in reachable_from_there:
                        continue

                    reachable_from_there.add(new_pos)
                    x_pos, y_pos = new_pos

                    for (delta_x, delta_y) in itertools.product(range(- 1, 2), range(- 1, 2)):
                        if (delta_x, delta_y) == (0, 0):
                            continue
                        neigh_x = x_pos + delta_x
                        neigh_y = y_pos + delta_y
                        neigh = (neigh_x, neigh_y)
                        if outside_cave(neigh):
                            continue
                        if not cave_table[neigh]:
                            continue
                        heapq.heappush(queue, neigh)

                return reachable_from_there

            # build a static table once for all
            touched_table: typing.Dict[typing.Tuple[int, int], typing.Set[typing.Tuple[int, int]]] = collections.defaultdict(set)
            for pos in itertools.product(range(1, self._level_width - 1), range(1, self._level_height - 1)):
                (x_pos, y_pos) = pos
                # put the futher ones
                for (delta_x, delta_y) in itertools.product(range(- 2, 3), range(- 2, 3)):
                    neigh_x = x_pos + delta_x
                    neigh_y = y_pos + delta_y
                    neigh = (neigh_x, neigh_y)
                    if outside_cave(neigh):
                        continue
                    touched_table[pos].add(neigh)
                # remove the closer ones
                for (delta_x, delta_y) in itertools.product(range(- 1, 2), range(- 1, 2)):
                    neigh_x = x_pos + delta_x
                    neigh_y = y_pos + delta_y
                    neigh = (neigh_x, neigh_y)
                    if outside_cave(neigh):
                        continue
                    touched_table[pos].remove(neigh)

            while True:

                mylogger.LOGGER.debug("cavelevel : joining groups")

                # group cells by leader (first found)
                group_of: typing.Dict[typing.Tuple[int, int], typing.Tuple[int, int]] = dict()
                for pos in itertools.product(range(1, self._level_width - 1), range(1, self._level_height - 1)):
                    if not cave_table[pos]:
                        continue
                    if pos in group_of:
                        continue
                    reachable = all_reachable(pos)
                    for reach_pos in reachable:
                        group_of[reach_pos] = pos

                # find the actual groups by reversing
                group_r: typing.Dict[typing.Tuple[int, int], typing.Set[typing.Tuple[int, int]]] = collections.defaultdict(set)
                for key, val in group_of.items():
                    group_r[val].add(key)
                groups_unsorted = group_r.values()
                groups = sorted(groups_unsorted, key=lambda g: len(g), reverse=True)  # pylint: disable=unnecessary-lambda

                mylogger.LOGGER.debug("cavelevel : groups lengths are %s", " ".join([str(len(g)) for g in groups]))

                if len(groups) == 1:
                    mylogger.LOGGER.debug("cavelevel : network is compact")
                    break

                second_group = sorted(groups)[1]
                if len(second_group) < 5:
                    mylogger.LOGGER.debug("cavelevel : second biggest group is too small : ignored, all done")
                    break

                # find the possible joiners
                possible_joiners = {(x, y) for (x, y) in itertools.product(range(1, self._level_width - 1), range(1, self._level_height - 1)) if not cave_table[(x, y)]}

                # calculate the frozens once for all
                fgroups = {frozenset(g) for g in groups}

                # find the actual joiners that touch a group
                joins: typing.Dict[typing.Tuple[int, int], typing.Set[typing.FrozenSet[typing.Tuple[int, int]]]] = collections.defaultdict(set)
                for joiner in possible_joiners:
                    for neigh in touched_table[joiner]:
                        for fgroup in fgroups:
                            if neigh in fgroup:
                                joins[joiner].add(fgroup)

                # keep the real joiners (that join at least two)
                for j in joins.copy():
                    if len(joins[j]) < 2:
                        del joins[j]

                # exit loop if no join possible
                if not joins:
                    mylogger.LOGGER.debug("cavelevel : no joiner so done - cancelling minority groups ")
                    sorted_groups = sorted(groups, key=len, reverse=True)
                    kept_group = sorted_groups[0]
                    nb_cancelled = 0
                    for group in groups:
                        if group == kept_group:
                            continue
                        for pos in group:
                            nb_cancelled += 1
                            cave_table[pos] = False
                    mylogger.LOGGER.debug("cavelevel : cancelled %d cave cells", nb_cancelled)
                    break

                # select amongst the best joiners
                perf_joiner = {j: sum([len(g) for g in joins[j]]) for j in joins}
                best_join = max(perf_joiner.values())
                selectable_joiners = [j for j in perf_joiner if perf_joiner[j] == best_join]
                selected_joiner = random.choice(sorted(selectable_joiners))

                mylogger.LOGGER.debug("cavelevel : joined groups of %s", " ".join([str(len(g)) for g in joins[selected_joiner]]))

                # make the join
                x_pos, y_pos = selected_joiner
                for (delta_x, delta_y) in itertools.product(range(- 2, 3), range(- 2, 3)):
                    neigh_x = x_pos + delta_x
                    neigh_y = y_pos + delta_y
                    neigh = (neigh_x, neigh_y)
                    if outside_cave(neigh):
                        continue
                    cave_table[neigh] = True

        #  start of init here

        abstractlevel.AbstractLevel.__init__(self, level_name, depth, branch, nb_down_stairs, nb_up_stairs, entry_level)

        cave_table: typing.Dict[typing.Tuple[int, int], bool] = dict()

        for (x_pos, y_pos) in itertools.product(range(1, self._level_width - 1), range(1, self._level_height - 1)):
            cave_table[(x_pos, y_pos)] = myrandom.percent_chance(45)

        for _ in range(4):
            future_cave_table = dict()
            for pos in itertools.product(range(1, self._level_width - 1), range(1, self._level_height - 1)):
                future_cave_table[pos] = False
                if range_cells(pos, 1) >= 5:
                    future_cave_table[pos] = True
                    continue
                if range_cells(pos, 1) <= 2:
                    future_cave_table[pos] = True
                    continue
            cave_table = future_cave_table.copy()

        for _ in range(3):
            future_cave_table = dict()
            for pos in itertools.product(range(1, self._level_width - 1), range(1, self._level_height - 1)):
                future_cave_table[pos] = False
                if range_cells(pos, 1) >= 5:
                    future_cave_table[pos] = True
                    continue
            cave_table = future_cave_table.copy()

        mylogger.LOGGER.debug("cavelevel : made initial cave")

        # every cave tile must be reachable
        join_groups()

        mylogger.LOGGER.debug("cavelevel : joined groups")

        # make a set of tiles
        self._cave_tiles = [tile_pos for tile_pos in itertools.product(range(1, self._level_width - 1), range(1, self._level_height - 1)) if cave_table[tile_pos]]

        ratio = len(self._cave_tiles) * 100 / ((self._level_width - 2) * (self._level_height - 2))
        mylogger.LOGGER.debug("cavelevel : %% of accessible = %f", ratio)

        selectable_tiles = [p for p in self._cave_tiles if range_cells(p, 1) == 8]

        # put stairs in level from room in places where they go down
        for _ in range(nb_down_stairs):
            staircase_position = random.choice(sorted(selectable_tiles))
            selectable_tiles.remove(staircase_position)
            self._downstairs.add(staircase_position)

        # put stairs in level from room in places where they go up
        for _ in range(nb_up_stairs):
            staircase_position = random.choice(sorted(selectable_tiles))
            selectable_tiles.remove(staircase_position)
            self._upstairs.add(staircase_position)

            # could be the dungeon entry point
            if entry_level:
                self._entry_position = staircase_position

        # add features - must be in room coordinates
        nb_features = 4 + myrandom.dice("d4")
        for _ in range(nb_features):
            feature_pos_choice = random.choice(sorted(selectable_tiles))
            selectable_tiles.remove(feature_pos_choice)
            features_selection = [features.Sink, features.Fountain, features.HeadStone]
            features_selection_table = [features.PROBA_FEATURES[features.POSSIBLE_FEATURES.index(f)] for f in features_selection]  # type: ignore
            feature_class_choices = random.choices(features_selection, features_selection_table)
            feature_class_choice = feature_class_choices[0]
            abstractlevel.put_feature(feature_pos_choice, feature_class_choice, self._level_features)

        # add engravings
        nb_engravings = 2 + myrandom.dice("d2")
        for _ in range(nb_engravings):
            engraving_pos_choice = random.choice(sorted(selectable_tiles))
            selectable_tiles.remove(engraving_pos_choice)
            abstractlevel.put_engraving(engraving_pos_choice, self._level_engravings)

        # add heavyrocks
        # No heavy rocks in caves (perhaps : some boulders...)

        # add source light
        nb_light_sources = 3 + myrandom.dice("d4")
        for _ in range(nb_light_sources):
            if myrandom.toss_coin():
                light_level = places.LightLevelEnum.DARK
            else:
                light_level = places.LightLevelEnum.LIT
            pos_light_source = random.choice(sorted(selectable_tiles))
            radius = 4 + myrandom.dice("d4")
            selectable_tiles.remove(pos_light_source)
            light_source = places.LightSourceRecord(level_pos=pos_light_source, light_level=light_level, light_radius=radius)
            self._level_light_sources.append(light_source)

        self._free_downstairs = self._downstairs.copy()
        self._free_upstairs = self._upstairs.copy()

    def convert_to_places(self) -> None:
        """ Converts logical just created level to table of tiles the game will use """

        # export cave tiles
        for position in self._cave_tiles:
            tile = places.Tile(places.TileTypeEnum.GROUND_TILE)
            place = places.Place(tile)
            self._data[position] = place

        # export features
        for feature in self._level_features:
            feature_pos = feature.position
            feature_place = self._data[feature_pos]
            assert feature_place.tile.mytype is places.TileTypeEnum.GROUND_TILE, "feature not on ground tile"
            feature_place.feature = feature

        # export engravings
        for engraving in self._level_engravings:
            engraving_pos = engraving.position
            engraving_place = self._data[engraving_pos]
            assert engraving_place.tile.mytype is places.TileTypeEnum.GROUND_TILE, "engraving not on ground tile"
            engraving_place.inscription = engraving.inscription

        # export engravings
        # no heavyrock for mazes

        # light sources are not exported

        # export stairs
        self.export_stairs()


if __name__ == '__main__':
    abstractlevel.test(CaveLevel)
