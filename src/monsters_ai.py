#!/usr/bin/env python3


"""
AI for monsters
"""


import typing
import random
import enum

import mylogger
import myrandom
import monsters
import monsters_ai_tools
import actions

DEBUG_TRACKING = True

# square where to expect dissapearing target to be
RANGE_SEARCH = 10

# probability to wake up
PROBA_WAKEUP = 3


@enum.unique
class StateEnum(enum.Enum):
    """ state machine """

    SLEEPING = enum.auto()
    FOLLOWING = enum.auto()
    TRACKING = enum.auto()
    SEARCHING = enum.auto()
    WANDERING = enum.auto()


class MonsterAIData:
    """ Data relative to an monster with an AI """

    def __init__(self, monster: monsters.Monster, tools: monsters_ai_tools.MonstersAITools, hero: typing.Any) -> None:

        # from init
        self._monster = monster
        self._tools = tools
        self._hero = hero

        # engine data
        self._state = StateEnum.SLEEPING
        self._target: typing.Optional[typing.Tuple[int, int]] = None
        self._seen_not_there: typing.Set[typing.Tuple[int, int]] = set()

    def give_action(self) -> actions.Action:
        """ This is THE A.I. here for a monster """

        def keep_note() -> None:
            """ Take a good note of what monster sees """

            # restrict to a square around monster pos (optimisation)
            x_monster, y_monster = self._monster.position
            for x_pos in range(x_monster - RANGE_SEARCH, x_monster + RANGE_SEARCH + 1):
                for y_pos in range(y_monster - RANGE_SEARCH, y_monster + RANGE_SEARCH + 1):
                    pos = x_pos, y_pos
                    if pos not in level.data:
                        continue
                    place = level.data[pos]
                    if not place.may_access():
                        continue
                    if pos == self._monster.position:
                        continue
                    success, _ = self._tools.can_see(self._monster, pos)
                    if not success:
                        continue
                    if not place.occupant:
                        self._seen_not_there.add(pos)
                        continue
                    self._monster.memory_position.note_position(place.occupant)
                    if place.occupant != self._hero:
                        self._seen_not_there.add(pos)

        def make_guess() -> typing.List[typing.Tuple[int, int]]:
            """ Intelligent part of tracking : target dissapeared, what do I do ?
                Returns list of possible positions for target
            """

            possible_positions: typing.Dict[typing.Tuple[int, int], int] = dict()

            # restrict to a square around monster pos (optimisation)
            x_monster, y_monster = self._monster.position
            for x_pos in range(x_monster - RANGE_SEARCH, x_monster + RANGE_SEARCH + 1):
                for y_pos in range(y_monster - RANGE_SEARCH, y_monster + RANGE_SEARCH + 1):
                    # we have a raw place
                    pos = x_pos, y_pos
                    if pos not in level.data:
                        continue
                    place = level.data[pos]
                    if not place.may_access():
                        continue
                    if pos == self._monster.position:
                        continue
                    # now we have a plausible place
                    # I (monster) have seen target not there : eliminated
                    if pos in self._seen_not_there:
                        continue
                    # must not be seen
                    success, _ = self._tools.can_see(self._monster, pos)
                    if success:
                        continue
                    # must be accessible
                    success, _, path = self._tools.path_towards(self._monster, pos)
                    if not success:
                        continue
                    # special
                    # TODO : avoid going back
                    possible_positions[pos] = len(path)

            if not possible_positions:
                return list()
            closest_pos_dist = min(possible_positions.values())
            closest_positions = [p for p in possible_positions if possible_positions[p] == closest_pos_dist]
            return closest_positions

        # method starts here

        # store dungeon level
        level = self._monster.dungeon_level

        # take a note of all occupants (monsters and heavyboulders) I see
        keep_note()

        # start with something simple : track the hero

        # can I reach the hero ?
        success, _ = self._tools.can_reach(self._monster, self._hero.position)
        if success:
            # TODO :  put a message on screen !
            if DEBUG_TRACKING:
                mylogger.LOGGER.debug("monster on %s can reach hero", self._monster.position)
            return actions.Action(actions.ActionEnum.REST, the_monster=self._monster)

        if self._state == StateEnum.SLEEPING:

            success, _ = self._tools.can_see(self._monster, self._hero.position)
            if success:
                self._seen_not_there = set()
                self._target = self._hero.position
                self._state = StateEnum.FOLLOWING
                if DEBUG_TRACKING:
                    mylogger.LOGGER.debug("monster on %s set target %s wakes up and start following", self._monster.position, self._target)

            elif myrandom.percent_chance(PROBA_WAKEUP):
                self._target = self._monster.dungeon_level.random_position()
                self._state = StateEnum.WANDERING
                if DEBUG_TRACKING:
                    mylogger.LOGGER.debug("monster on %s wakes up naturally and starts wandering towards %s", self._monster.position, self._target)

        elif self._state == StateEnum.FOLLOWING:

            success, _ = self._tools.can_see(self._monster, self._hero.position)
            if success:
                self._seen_not_there = set()
                self._target = self._hero.position
                if DEBUG_TRACKING:
                    mylogger.LOGGER.debug("monster on %s still following", self._monster.position)
            else:
                last_known_hero_pos = self._monster.memory_position.recall_position(self._hero)
                if not last_known_hero_pos:
                    self._target = None
                    self._target = self._monster.dungeon_level.random_position()
                    self._state = StateEnum.WANDERING
                    if DEBUG_TRACKING:
                        mylogger.LOGGER.debug("(this is strange) monster on %s give up no last known position starts wandering", self._monster.position)
                else:
                    self._target = last_known_hero_pos
                    self._state = StateEnum.TRACKING
                    if DEBUG_TRACKING:
                        mylogger.LOGGER.debug("monster on %s set target %s starts tracking to last known position", self._monster.position, self._target)

        elif self._state == StateEnum.TRACKING:

            success, _ = self._tools.can_see(self._monster, self._hero.position)
            if success:
                self._seen_not_there = set()
                self._target = self._hero.position
                self._state = StateEnum.FOLLOWING
                if DEBUG_TRACKING:
                    mylogger.LOGGER.debug("monster on %s sees hero so follows", self._monster.position)

            elif self._monster.position == self._target:

                # now seek the closest reachable unseen pos
                closest_positions = make_guess()

                if not closest_positions:
                    self._target = self._monster.dungeon_level.random_position()
                    self._state = StateEnum.WANDERING
                    if DEBUG_TRACKING:
                        mylogger.LOGGER.debug("monster on %s give up no unseen position starts wandering towards %s", self._monster.position, self._target)
                else:
                    chosen_pos = random.choice(closest_positions)
                    self._target = chosen_pos
                    self._state = StateEnum.SEARCHING
                    if DEBUG_TRACKING:
                        mylogger.LOGGER.debug("monster on %s set target %s by guessing and starts searching", self._monster.position, self._target)

        elif self._state == StateEnum.SEARCHING:

            success, _ = self._tools.can_see(self._monster, self._hero.position)
            if success:
                self._seen_not_there = set()
                self._target = self._hero.position
                self._state = StateEnum.FOLLOWING
                if DEBUG_TRACKING:
                    mylogger.LOGGER.debug("monster on %s sees hero so follows", self._monster.position)

            elif self._monster.position == self._target:

                # now seek the closest reachable unseen pos not visited
                mylogger.LOGGER.debug("monster on %s make guesss %d not there places", self._monster.position, len(self._seen_not_there))
                closest_positions = make_guess()

                if not closest_positions:
                    self._target = self._monster.dungeon_level.random_position()
                    self._state = StateEnum.WANDERING
                    if DEBUG_TRACKING:
                        mylogger.LOGGER.debug("monster on %s give up no unseen position starts wandering towards %s", self._monster.position, self._target)
                else:
                    chosen_pos = random.choice(closest_positions)
                    self._target = chosen_pos
                    if DEBUG_TRACKING:
                        mylogger.LOGGER.debug("monster on %s searching reached target assigns new target %s", self._monster.position, self._target)

        elif self._state == StateEnum.WANDERING:
            success, _ = self._tools.can_see(self._monster, self._hero.position)
            if success:
                self._seen_not_there = set()
                self._target = self._hero.position
                self._state = StateEnum.FOLLOWING
                if DEBUG_TRACKING:
                    mylogger.LOGGER.debug("monster on %s sees hero so follows", self._monster.position)
            elif self._monster.position == self._target:
                self._target = None
                self._state = StateEnum.SLEEPING
                if DEBUG_TRACKING:
                    mylogger.LOGGER.debug("monster on %s reached target and stops wandering falls asleep", self._monster.position)
            else:
                assert self._target, "Wandering but no target"
                success, _, _ = self._tools.path_towards(self._monster, self._target)
                if not success:
                    self._target = self._monster.dungeon_level.random_position()
                    if DEBUG_TRACKING:
                        mylogger.LOGGER.debug("monster on %s wandering but target not reachable, change...", self._monster.position)

        if not self._target:
            if DEBUG_TRACKING:
                mylogger.LOGGER.debug("monster on %s has no target", self._monster.position)
            return actions.Action(actions.ActionEnum.REST, the_monster=self._monster)

        assert self._target != self._monster.position

        # now apply target
        success, direction, _ = self._tools.path_towards(self._monster, self._target)
        if not success:
            if DEBUG_TRACKING:
                mylogger.LOGGER.debug("monster %s cannot reach target", self._monster.position)
            return actions.Action(actions.ActionEnum.REST, the_monster=self._monster)

        if DEBUG_TRACKING:
            mylogger.LOGGER.debug("monster on %s aims target %s", self._monster.position, self._target)
        return actions.Action(actions.ActionEnum.MOVE, the_monster=self._monster, the_direction=direction)


class MonstersAI:
    """ Provides an AI for every monster """

    def __init__(self, hero: typing.Any) -> None:
        self._hero = hero
        self._actor_table: typing.Dict[monsters.Monster, MonsterAIData] = dict()
        self._tools = monsters_ai_tools.MonstersAITools()

    def give_action(self, monster: monsters.Monster) -> actions.Action:
        """ provide action for a monster  """
        ai_data = self._actor_table[monster]
        return ai_data.give_action()

    def register(self, monster: monsters.Monster) -> None:
        """ register a monster """
        ai_data = MonsterAIData(monster, self._tools, self._hero)
        self._actor_table[monster] = ai_data

    def unregister(self, monster: monsters.Monster) -> None:
        """ unregister a monster  """
        del self._actor_table[monster]

    @property
    def tools(self) -> monsters_ai_tools.MonstersAITools:
        """ property """
        return self._tools


if __name__ == '__main__':
    assert False, "Do not run this script"
