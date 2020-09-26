#!/usr/bin/python3


"""
File : sequencer.py

Sequencer.
"""

import typing

import myrandom
import actions
import monsters
import constants


class ActorData:
    """ Data relative to an actor of simulation """

    def __init__(self, segment_reference: int) -> None:
        self._move_credit = 0
        self._action_debt = 0
        self._segment_reference = segment_reference
        self._now_doing: typing.Optional[actions.Action] = None

    # move credit related methods

    def move_credit_full(self) -> bool:
        """ check if full """
        return self._move_credit >= constants.NB_SEGMENTS

    def give_move_credit(self, credit: int) -> None:
        """ more credit """
        self._move_credit += credit

    def consume_move_credit(self) -> None:
        """ more credit """
        self._move_credit -= constants.NB_SEGMENTS

    # action debt related methods

    def increase_action_debt(self, action_cost: int) -> None:
        """ increase debt """
        self._action_debt += action_cost

    def decrease_action_debt(self) -> None:
        """ decrease debt """
        if self._action_debt > 0:
            self._action_debt -= 1

    def no_action_debt(self) -> bool:
        """ no debt """
        return self._action_debt == 0

    # properties

    @property
    def segment_reference(self) -> int:
        """ property """
        return self._segment_reference

    @property
    def now_doing(self) -> typing.Optional[actions.Action]:
        """ property """
        return self._now_doing

    @now_doing.setter
    def now_doing(self, now_doing: actions.Action) -> None:
        """ setter """
        self._now_doing = now_doing


class Sequencer:
    """ Sequencer """

    def __init__(self) -> None:
        # we start a round 1
        self._round = 0
        self._segment = 0
        self._actor_table: typing.Dict[monsters.Monster, ActorData] = dict()

    def tick(self) -> None:
        """ tick """

        # give move credit to actors
        for actor, actor_data in self._actor_table.items():

            # no move credit if full already
            if actor_data.move_credit_full():
                continue

            # calculate move credit
            # the aim is to be as close as possible as ideal value
            # which is : actor.speed/constants.NB_SEGMENTS

            # step one : credit you get every time
            credit = actor.speed_value() // constants.NB_SEGMENTS
            first_reminder_max = actor.speed_value() % constants.NB_SEGMENTS
            # find biggest value that divides
            for first_reminder in range(first_reminder_max, 1, -1):
                if constants.NB_SEGMENTS % first_reminder == 0:
                    break
            else:
                first_reminder = 0

            # step two : credit you get once every n segments
            if first_reminder:
                divide = constants.NB_SEGMENTS // first_reminder
                assert constants.NB_SEGMENTS % first_reminder == 0
                delta_seg_now = actor_data.segment_reference - self._segment
                if delta_seg_now < 0:
                    delta_seg_now += constants.NB_SEGMENTS
                if delta_seg_now % divide == 0:
                    credit += 1
                second_reminder = first_reminder_max - first_reminder

                # step three : credit you get randomly
                if second_reminder:
                    if myrandom.randint(0, constants.NB_SEGMENTS - 1) < second_reminder:
                        credit += 1

            # give calculated move credit
            actor_data.give_move_credit(credit)

        # diminish actors' action debt (much simpler)
        for actor, actor_data in self._actor_table.items():
            actor_data.decrease_action_debt()
            if actor_data.no_action_debt():
                action = actor_data.now_doing
                # enclenches result of action  since finished doing it
                if action:
                    action.execute()
                    actor_data.now_doing = None

        # tick actors that are on "their" segment
        for actor, actor_data in self._actor_table.items():
            if actor_data.segment_reference == self._segment:
                actor.tick()

        # move clock time
        self._segment += 1
        if self._segment == constants.NB_SEGMENTS:
            self._segment = 0
            self._round += 1

    def can_do_something(self, actor: monsters.Monster) -> bool:
        """ not just moved nor doing anything """
        action_data = self._actor_table[actor]
        return action_data.move_credit_full() and action_data.no_action_debt()

    def starts_doing(self, actor: monsters.Monster, action: actions.Action) -> None:
        """ starts doing (move or action) """
        action_data = self._actor_table[actor]
        if action.is_move():
            action.execute()
            action_data.consume_move_credit()
        else:
            action_data.now_doing = action
            action_data.increase_action_debt(action.cost())

    def register(self, actor: monsters.Monster) -> None:
        """ register a monster or hero """
        action_data = ActorData(self._segment)
        self._actor_table[actor] = action_data

    def unregister(self, actor: monsters.Monster) -> None:
        """ unregister a monster or hero  """
        del self._actor_table[actor]

    def turn(self) -> str:
        """ turn to display on screen """
        return f"T:{self._round+1}.{self._segment+1}"


if __name__ == '__main__':
    assert False, "Do not run this script"
