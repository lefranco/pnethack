#!/usr/bin/env python3


"""
File : mapping.py

In charge of displaying to screen what is seen of a dungeon level.

The algorithm used is "recursive shadowcasting FOV" from Bjorn Bergstrom.
source : roguebasin
It is not symetric and has the best indoor performances.
"""

import typing
import curses
import random
import fractions
import math
import sys

import constants
import mycurses
import places
import alignment
import abstractlevel

LOS_FULLY_SYMETRICAL = False


class Mapping:
    """ This class does the mapping, it calculates what the hero sees of the level to display on the screen """

    def __init__(self, level: abstractlevel.AbstractLevel) -> None:

        self._level = level

        # says if place is currently seen
        self._sees: typing.Dict[typing.Tuple[int, int], bool] = dict()

        # says if place is currently remembered (has been seen once)
        self._has_seen: typing.Dict[typing.Tuple[int, int], bool] = dict()

        # says if place is currently lit
        self._lit: typing.Dict[typing.Tuple[int, int], places.LightLevelEnum] = dict()

        # will be updated later
        self._hero_pos: typing.Optional[typing.Tuple[int, int]] = None
        self._hero_prev_pos: typing.Optional[typing.Tuple[int, int]] = None
        self._knows_all = False  # for debug
        for x_pos in range(self._level.level_width):
            for y_pos in range(self._level.level_height):
                self._sees[(x_pos, y_pos)] = False
                self._has_seen[(x_pos, y_pos)] = False

    def _blocks_vision(self, x_pos: int, y_pos: int) -> bool:
        if x_pos < 0 or y_pos < 0 or x_pos >= self._level.level_width or y_pos >= self._level.level_height:
            return True
        return self._level.data[(x_pos, y_pos)].blocks_vision()

    def _lit_now(self, x_pos: int, y_pos: int) -> places.LightLevelEnum:
        if x_pos < 0 or y_pos < 0 or x_pos >= self._level.level_width or y_pos >= self._level.level_height:
            return places.LightLevelEnum.NORMAL
        return self._lit[(x_pos, y_pos)]

    def _sees_now(self, x_pos: int, y_pos: int) -> bool:
        return self._sees[(x_pos, y_pos)]

    def _reinit_light(self) -> None:
        for x_pos in range(self._level.level_width):
            for y_pos in range(self._level.level_height):
                self._lit[(x_pos, y_pos)] = places.LightLevelEnum.NORMAL

    def _reinit_sees(self) -> None:
        for x_pos in range(self._level.level_width):
            for y_pos in range(self._level.level_height):
                self._sees[(x_pos, y_pos)] = False

    def _set_lit(self, x_pos: int, y_pos: int, light_level: places.LightLevelEnum) -> None:
        if 0 <= x_pos < self._level.level_width and 0 <= y_pos < self._level.level_height:
            self._lit[(x_pos, y_pos)] = light_level

    def _set_seeing(self, x_pos: int, y_pos: int) -> None:
        if 0 <= x_pos < self._level.level_width and 0 <= y_pos < self._level.level_height:
            self._sees[(x_pos, y_pos)] = True

    def _has_already_seen(self, x_pos: int, y_pos: int) -> bool:
        return self._has_seen[(x_pos, y_pos)]

    def _set_has_seen(self, x_pos: int, y_pos: int) -> None:
        if 0 <= x_pos < self._level.level_width and 0 <= y_pos < self._level.level_height:
            self._has_seen[(x_pos, y_pos)] = True

    def _cast_light_rec(self, octant: int, origin: typing.Tuple[int, int], range_limit: typing.Optional[int], x_start: int, top: fractions.Fraction, bottom: fractions.Fraction, result: typing.Set[typing.Tuple[int, int]]) -> None:
        """ Recursive part of lightcasting function """

        def _get_distance(x_val: int, y_val: int) -> float:
            """ get_distance """
            return math.sqrt(x_val ** 2 + y_val ** 2)

        def _translate_octant(x_val: int, y_val: int, octant: int, origin: typing.Tuple[int, int]) -> typing.Tuple[int, int]:
            """ translate_octant """
            new_x, new_y = origin
            if octant == 0:
                new_x += x_val
                new_y -= y_val
            elif octant == 1:
                new_x += y_val
                new_y -= x_val
            elif octant == 2:
                new_x -= y_val
                new_y -= x_val
            elif octant == 3:
                new_x -= x_val
                new_y -= y_val
            elif octant == 4:
                new_x -= x_val
                new_y += y_val
            elif octant == 5:
                new_x -= y_val
                new_y += x_val
            elif octant == 6:
                new_x += y_val
                new_y += x_val
            elif octant == 7:
                new_x += x_val
                new_y += y_val
            return new_x, new_y

        def _blocks_light(x_val: int, y_val: int, octant: int, origin: typing.Tuple[int, int]) -> bool:
            """ blocksLight """
            new_x, new_y = _translate_octant(x_val, y_val, octant, origin)
            return self._blocks_vision(new_x, new_y)

        def _set_visible(x_val: int, y_val: int, octant: int, origin: typing.Tuple[int, int]) -> None:
            """ setVisible """
            viewed = _translate_octant(x_val, y_val, octant, origin)
            result.add(viewed)

        # start of _cast_light_rec method

        for x_val in range(x_start, range_limit + 1 if range_limit else sys.maxsize):

            top_y = 0
            if top.denominator == 1:
                top_y = x_val
            else:
                top_y = int(((x_val * 2 - 1) * top.numerator + top.denominator) / (top.denominator * 2))
                if _blocks_light(x_val, top_y, octant, origin):
                    if top >= fractions.Fraction(top_y * 2 + 1, x_val * 2) and not _blocks_light(x_val, top_y + 1, octant, origin):
                        top_y += 1
                else:
                    a_for_x = x_val * 2
                    if _blocks_light(x_val + 1, top_y + 1, octant, origin):
                        a_for_x += 1
                    if top > fractions.Fraction(top_y * 2 + 1, a_for_x):
                        top_y += 1

            bottom_y = 0
            if bottom.numerator == 0:
                bottom_y = 0
            else:
                bottom_y = int(((x_val * 2 - 1) * bottom.numerator + bottom.denominator) / (bottom.denominator * 2))
                if bottom >= fractions.Fraction(bottom_y * 2 + 1, x_val * 2) and _blocks_light(x_val, bottom_y, octant, origin) and not _blocks_light(x_val, bottom_y + 1, octant, origin):
                    bottom_y += 1

            was_opaque: typing.Optional[bool] = None

            for y_val in range(top_y, bottom_y - 1, -1):
                if range_limit is None or _get_distance(x_val, y_val) <= range_limit:
                    is_opaque = _blocks_light(x_val, y_val, octant, origin)

                    is_visible = False
                    if not LOS_FULLY_SYMETRICAL:
                        is_visible = is_opaque or ((y_val != top_y or top > fractions.Fraction(y_val * 4 - 1, x_val * 4 + 1)) and (y_val != bottom_y or bottom < fractions.Fraction(y_val * 4 + 1, x_val * 4 - 1)))
                    else:
                        is_visible = (y_val != top_y or top >= fractions.Fraction(y_val, x_val)) and (y_val != bottom_y or bottom <= fractions.Fraction(y_val, x_val))

                    if is_visible:
                        _set_visible(x_val, y_val, octant, origin)
                    if x_val != range_limit:
                        if is_opaque:
                            if was_opaque is not None and not was_opaque:
                                new_x, new_y = x_val * 2, y_val * 2 + 1

                                if not LOS_FULLY_SYMETRICAL:
                                    if _blocks_light(x_val, y_val + 1, octant, origin):
                                        new_x -= 1

                                if top > fractions.Fraction(new_y, new_x):
                                    if y_val == bottom_y:
                                        bottom = fractions.Fraction(new_y, new_x)
                                        break
                                    else:
                                        self._cast_light_rec(octant, origin, range_limit, x_val + 1, top, fractions.Fraction(new_y, new_x), result)
                                else:
                                    if y_val == bottom_y:
                                        return
                            was_opaque = True
                        else:  # isOpaque
                            if was_opaque is not None and was_opaque:
                                new_x, new_y = x_val * 2, y_val * 2 + 1
                                if _blocks_light(x_val + 1, y_val + 1, octant, origin):
                                    new_x += 1
                                if bottom >= fractions.Fraction(new_y, new_x):
                                    return
                                top = fractions.Fraction(new_y, new_x)
                            was_opaque = False

            if was_opaque is None or was_opaque:
                break

    def _cast_light(self, x_origin: int, y_origin: int, range_limit: typing.Optional[int]) -> typing.Set[typing.Tuple[int, int]]:
        """
        Adam Milazzo's algorith for line of sight

        http://www.adammil.net/blog/v125_Roguelike_Vision_Algorithms.html
        On his site he compares :
         - Ray casting
         - Shadow casting
         - Diamond walls
         - Permissive field of view
        - "My algorithm"

        Algorithm below is a Python strict translation of the C Sharp code implementing "My algorithm".

        It can be made fully symmetrical using LOS_FULLY_SYMETRICAL
        """

        result: typing.Set[typing.Tuple[int, int]] = set()
        origin = (x_origin, y_origin)
        result.add(origin)
        for octant in range(8):
            self._cast_light_rec(octant, origin, range_limit, 1, fractions.Fraction(1, 1), fractions.Fraction(0, 1), result)
        return result

    # now the methods visible from outside the module

    def knows(self, x_pos: int, y_pos: int) -> bool:
        """ need to know if players know about that tile """
        return self._has_seen[(x_pos, y_pos)]

    def set_knows_all(self) -> None:
        """ sets that hero know all (debug)  """
        self._knows_all = not self._knows_all

    def do_light_effects(self) -> None:
        """ Do the light effects """

        self._reinit_light()

        for light_source in self._level.level_light_sources:
            # calculates places that are lit/darkened
            x_pos, y_pos = light_source.level_pos
            result = self._cast_light(x_pos, y_pos, light_source.light_radius)
            # the light source is seen, too
            result.add(light_source.level_pos)
            # lit them
            for (x_pos, y_pos) in result:
                self._set_lit(x_pos, y_pos, light_source.light_level)

    def do_place_observer(self, obs_pos: typing.Tuple[int, int]) -> None:
        """ Place observer """
        self._hero_prev_pos = self._hero_pos
        self._hero_pos = obs_pos

    def do_update_fov(self) -> None:
        """ Calculate seen squares from the given location and radius """

        self._reinit_sees()

        assert self._hero_pos, "Unknown hero position for do_update_fov()"
        x_hero, y_hero = self._hero_pos

        # places next to observer are always seen (and observer)
        result = set()
        for delta_x in [-1, 0, 1]:
            for delta_y in [-1, 0, 1]:
                result.add((x_hero + delta_x, y_hero + delta_y))
        for (x_pos, y_pos) in result:
            self._set_seeing(x_pos, y_pos)

        # places at vision radius are seen unless dark
        result = self._cast_light(x_hero, y_hero, constants.FOV_RADIUS)
        for (x_pos, y_pos) in result:
            if self._lit_now(x_pos, y_pos) != places.LightLevelEnum.DARK:
                self._set_seeing(x_pos, y_pos)

        # places at infinite radius are seen if lit
        infinite = constants.DUNGEON_WIDTH + constants.DUNGEON_HEIGHT
        result = self._cast_light(x_hero, y_hero, infinite)
        for (x_pos, y_pos) in result:
            if self._lit_now(x_pos, y_pos) == places.LightLevelEnum.LIT:
                self._set_seeing(x_pos, y_pos)

    def do_update_has_seen(self) -> None:
        """ Remembers what was seen """

        # what is seen will be remembered
        for x_pos in range(self._level.level_width):
            for y_pos in range(self._level.level_height):
                if self._sees_now(x_pos, y_pos):
                    self._set_has_seen(x_pos, y_pos)

        # for debug
        if self._knows_all:
            for x_pos in range(self._level.level_width):
                for y_pos in range(self._level.level_height):
                    self._set_has_seen(x_pos, y_pos)

    def enter_level(self) -> typing.List[str]:
        """ When hero enters level """
        messages: typing.List[str] = list()
        for special_room in self.level.level_special_rooms:
            some_messages = special_room.mytype.messages_entering_level()
            if some_messages:
                messages.append(random.choice(some_messages))
        for feature in self.level.level_features:
            some_messages = feature.messages_entering_level()
            if some_messages:
                messages.append(random.choice(some_messages))
        # remove dublins
        messages = sorted(set(messages))
        # sort randomly
        random.shuffle(messages)
        return messages

    def check_special_rooms(self, hero_alignment: alignment.AlignmentEnum) -> typing.List[str]:
        """ When hero walks on level : checks for messages """
        messages: typing.List[str] = list()
        for special_room in self.level.level_special_rooms:
            if special_room.is_inside(self._hero_pos) and not special_room.is_inside(self._hero_prev_pos):
                some_messages = special_room.mytype.messages_entering_room()
                if some_messages:
                    messages.append(random.choice(some_messages))
                if special_room.altar_alignment:
                    if hero_alignment != special_room.altar_alignment:
                        messages.append("You have a forbidding feeling.")
                    else:
                        messages.append("You experience a sense of peace")

        return messages

    def check_engravings(self) -> typing.List[str]:
        """ When hero walks on level : checks for graffitis (headstone or floor) """
        if self._hero_pos is None:
            return list()
        if self._hero_pos == self._hero_prev_pos:
            return list()
        place = self.level.data[self._hero_pos]
        return place.engraving_messages()

    def display(self, window: typing.Any) -> None:
        """ Displays the map on the given curses screen (utterly unoptimized) """

        assert self._hero_pos, "Unknown hero position for display()"
        hero_x_pos, hero_y_pos = self._hero_pos

        for x_pos in range(self._level.level_width):
            for y_pos in range(self._level.level_height):

                # attr
                if x_pos == hero_x_pos and y_pos == hero_y_pos:
                    attr = mycurses.color(curses.COLOR_WHITE, curses.COLOR_BLACK)
                elif self._sees_now(x_pos, y_pos):
                    attr = mycurses.color(curses.COLOR_WHITE, curses.COLOR_BLACK) | curses.A_BOLD
                elif self._has_already_seen(x_pos, y_pos):
                    attr = mycurses.color(curses.COLOR_WHITE, curses.COLOR_BLACK) | curses.A_DIM
                else:
                    attr = mycurses.color(curses.COLOR_BLACK, curses.COLOR_BLACK)

                place = self._level.data[(x_pos, y_pos)]
                char = place.display_glyph()

                window.addstr(constants.MESSAGES_BUFFER_SIZE + constants.PROMPT_BUFFER_SIZE + y_pos, x_pos, char, attr)

    @property
    def level(self) -> abstractlevel.AbstractLevel:
        """ property """
        return self._level

    @property
    def has_seen(self) -> typing.Dict[typing.Tuple[int, int], bool]:
        """ property """
        return self._has_seen

    @has_seen.setter
    def has_seen(self, has_seen: typing.Dict[typing.Tuple[int, int], bool]) -> None:
        """ setter """
        self._has_seen = has_seen


if __name__ == '__main__':
    assert False, "Do not run this script"
