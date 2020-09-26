#!/usr/bin/env python3


"""
File : monsters_ai_tools.py

Useful tools for monster ia
"""

import typing
import heapq
import math

import constants
import actions
import monsters
import abstractlevel


class MonstersAITools:
    """ class providing Tools for monsters AI """

    @staticmethod
    def _blocks_vision(monster_level: abstractlevel.AbstractLevel, x_pos: int, y_pos: int) -> bool:
        """ function saying if a tile blocks vision """
        if x_pos < 0 or y_pos < 0 or x_pos >= monster_level.level_width or y_pos >= monster_level.level_height:
            return True
        return monster_level.data[(x_pos, y_pos)].blocks_vision()

    @staticmethod
    def can_reach(monster: monsters.Monster, reached_pos: typing.Tuple[int, int]) -> typing.Tuple[bool, actions.DirectionEnum]:
        """ Just an easy test if monster can reach (goto in one move) a position """

        reacher_pos = monster.position
        monster_level = monster.dungeon_level

        reacher_x, reacher_y = reacher_pos
        for direction, delta in actions.DIRECTION_2_DELTA.items():
            delta_x, delta_y = delta
            new_x, new_y = reacher_x + delta_x, reacher_y + delta_y
            new_pos = new_x, new_y
            if direction.diagonal:
                if not monster_level.data[new_pos].may_access_diagonally() or not monster_level.data[reacher_pos].may_access_diagonally():
                    continue
            if new_pos == reached_pos:
                return True, direction
        return False, actions.DirectionEnum.CLIMB_UP

    def can_see(self, monster: monsters.Monster, viewed_pos: typing.Tuple[int, int]) -> typing.Tuple[bool, typing.List[typing.Tuple[int, int]]]:
        """ Bresenham algorim for drawing a line between two points """

        def _get_distance2(from_pos: typing.Tuple[int, int], to_pos: typing.Tuple[int, int]) -> float:
            """ get_distance """
            x_from, y_from = from_pos
            x_to, y_to = to_pos
            return math.sqrt((x_to - x_from) ** 2 + (y_to - y_from) ** 2)

        def _sign(val: int) -> int:
            """ sign """
            if val < 0:
                return -1
            if val > 0:
                return 1
            return 0

        line: typing.List[typing.Tuple[int, int]] = list()
        viewer_pos = monster.position

        # Rules that out
        if _get_distance2(viewer_pos, viewed_pos) > constants.FOV_RADIUS:
            return False, list()

        x_orig, y_orig = viewer_pos
        x_dest, y_dest = viewed_pos

        width = x_dest - x_orig
        height = y_dest - y_orig

        delta_x1 = _sign(width)
        delta_y1 = _sign(height)

        longest = max(abs(width), abs(height))
        shortest = min(abs(width), abs(height))

        delta_x2 = _sign(width)
        delta_y2 = 0
        if not abs(width) > abs(height):
            delta_x2 = 0
            delta_y2 = _sign(height)

        numerator = longest // 2

        dist = 0
        x_cur, y_cur = x_orig, y_orig
        while True:
            if dist >= longest:
                break
            numerator += shortest
            if not numerator < longest:
                numerator -= longest
                x_cur += delta_x1
                y_cur += delta_y1
            else:
                x_cur += delta_x2
                y_cur += delta_y2
            if self._blocks_vision(monster.dungeon_level, x_cur, y_cur):
                return False, line
            line.append((x_cur, y_cur))
            dist += 1

        return True, line

    @staticmethod
    def path_towards(monster: monsters.Monster, target_pos: typing.Tuple[int, int]) -> typing.Tuple[bool, actions.DirectionEnum, typing.List[typing.Tuple[int, int]]]:
        """
        An "A-star"-like home made algorithm for reaching a target
        Returns :
          - is there a path ?
          - the direction to start using path
          - the path (just for information)
        """

        def _get_distance(from_pos: typing.Tuple[int, int], to_pos: typing.Tuple[int, int]) -> int:
            """ get_distance (diagonal distance) """
            x_from, y_from = from_pos
            x_to, y_to = to_pos
            return max(abs(x_to - x_from), abs(y_to - y_from))

        def _get_distance2(from_pos: typing.Tuple[int, int], to_pos: typing.Tuple[int, int]) -> float:
            """ get_distance (square of euclidian distance) """
            x_from, y_from = from_pos
            x_to, y_to = to_pos
            return math.sqrt((x_to - x_from)**2 + (y_to - y_from)**2)

        infinite = math.sqrt(constants.DUNGEON_WIDTH**2 + constants.DUNGEON_HEIGHT**2)

        mover_pos = monster.position
        monster_level = monster.dungeon_level

        # set to remember where we have been
        g_values: typing.Dict[typing.Tuple[int, int], int] = dict()

        # map to find element from heap
        reachable_map: typing.Dict[typing.Tuple[int, int], float] = dict()

        # heap to extract always closest to target element first
        reachables: typing.List[typing.Tuple[float, typing.Tuple[typing.Tuple[int, int], int]]] = list()
        empty_path: typing.List[typing.Tuple[int, int]] = list()
        g_value = 0
        h_value = _get_distance(mover_pos, target_pos) + _get_distance2(mover_pos, target_pos) / infinite
        f_value = g_value + h_value

        # push in fifo and update tables
        heapq.heappush(reachables, (f_value, (mover_pos, g_value)))
        reachable_map[mover_pos] = f_value
        g_values[mover_pos] = g_value

        predecessor = dict()

        while reachables:

            # extract new considered position
            _, (considered_pos, g_value) = heapq.heappop(reachables)

            # are we done
            if considered_pos == target_pos:
                break

            # consider neighbours
            considered_x, considered_y = considered_pos
            for direction, (delta_x, delta_y) in actions.DIRECTION_2_DELTA.items():

                # position
                new_pos = considered_x + delta_x, considered_y + delta_y

                # ignore if diagonally and not diagonally passable
                if direction.diagonal:
                    if not monster_level.data[new_pos].may_access_diagonally() or not monster_level.data[considered_pos].may_access_diagonally():
                        continue

                # ignore if not passable (or considered so) except for target
                if new_pos != target_pos and not monster.considers_passable(new_pos):
                    continue

                g_value2 = g_value + 1
                h_value = _get_distance(new_pos, target_pos) + _get_distance2(new_pos, target_pos) / infinite
                f_value = g_value2 + h_value

                # ignore is to be met later better
                if new_pos in reachable_map:
                    f_heap_value = reachable_map[new_pos]
                    if f_heap_value < f_value:
                        continue

                # ignore if met before better
                if new_pos in g_values and g_values[new_pos] <= g_value2:
                    continue

                # push in fifo and update tables
                heapq.heappush(reachables, (f_value, (new_pos, g_value2)))
                reachable_map[new_pos] = f_value
                g_values[new_pos] = g_value2
                predecessor[new_pos] = considered_pos

        # reached target
        if target_pos in g_values:
            # rebuild path from predecessor table
            rpath = list()
            pos = target_pos
            while pos in predecessor:
                rpath.append(pos)
                pos = predecessor[pos]
            path = list(reversed(rpath))
            # find direction
            first_in_path = path[0]
            start_x, start_y = mover_pos
            for direction, delta in actions.DIRECTION_2_DELTA.items():
                delta_x, delta_y = delta
                neighbour_pos = start_x + delta_x, start_y + delta_y
                if neighbour_pos == first_in_path:
                    return True, direction, path
            assert False, "Internal error in path_towards"

        return False, actions.DirectionEnum.CLIMB_UP, empty_path


if __name__ == '__main__':
    assert False, "Do not run this script"
