#!/usr/bin/env python3


"""
File : actions.py

Handle stuff related to all living creatures of the game. Even the undead.
"""

import typing
import enum
import random
import math
import curses

import myrandom
import gui
import pickables
import hidden
import monsters
import heavyrocks


@enum.unique
class DirectionEnum(enum.Enum):
    """ Direction for a move command  """

    # Id = desc, diagonal
    DOWN = ("down", False)
    UP = ("up", False)
    LEFT = ("left", False)
    RIGHT = ("right", False)
    UPLEFT = ("up left", True)
    UPRIGHT = ("up right", True)
    DOWNLEFT = ("down left", True)
    DOWNRIGHT = ("down right", True)
    CLIMB_UP = ("climb up", False)
    CLIMB_DOWN = ("climb down", False)

    def __init__(self, desc: str, diagonal: bool) -> None:
        self._desc = desc
        self._diagonal = diagonal

    @property
    def diagonal(self) -> bool:
        """ property """
        return self._diagonal


DIRECTION_2_DELTA = {
    # orthogonal
    DirectionEnum.DOWN: (0, 1),
    DirectionEnum.UP: (0, -1),
    DirectionEnum.LEFT: (-1, 0),
    DirectionEnum.RIGHT: (1, 0),
    # diagonal
    DirectionEnum.UPLEFT: (-1, -1),
    DirectionEnum.UPRIGHT: (1, -1),
    DirectionEnum.DOWNLEFT: (-1, 1),
    DirectionEnum.DOWNRIGHT: (1, 1),
}


@enum.unique
class ActionEnum(enum.Enum):
    """ ActionEnum """

    # Id = (name, cost)

    MOVE = ("move", 0)

    CLIMB = ("attack", 24)
    ATTACK = ("attack", 12)
    PUSH = ("push", 24)
    OPEN_DOOR = ("open", 6)
    CLOSE_DOOR = ("close", 6)
    KICK = ("kick", 6)
    PICK_UP = ("pick", 6)
    DROP = ("drop", 6)
    THROW = ("throw", 6)
    REST = ("rest", 12)
    SEARCH = ("search", 36)

    def __init__(self, name: str, cost: int) -> None:

        # actually not used
        self._name = name

        # cost in time segments of action
        self._cost = cost

    def is_move(self) -> bool:
        """ to treat differently move action """
        return self is ActionEnum.MOVE

    @property
    def cost(self) -> int:
        """ property """
        return self._cost


class Action:
    """ Stores an action that will be solved later """

    # these are defined once for all
    the_messages: typing.Optional[gui.Messages] = None

    def __init__(self, mytype: ActionEnum,
                 the_monster: typing.Optional[monsters.Monster] = None,
                 the_direction: typing.Optional[DirectionEnum] = None,
                 the_item: typing.Optional[pickables.Pickable] = None,
                 the_door: typing.Optional[hidden.Door] = None,
                 the_victim: typing.Optional[monsters.Monster] = None) -> None:
        self._mytype = mytype
        self._the_monster = the_monster
        self._the_direction = the_direction
        self._the_item = the_item
        self._the_door = the_door
        self._the_victim = the_victim

    def is_move(self) -> bool:
        """ to treat differently move action """
        return self._mytype.is_move()

    def move(self) -> None:
        """ move action """

        assert self._the_monster
        assert self._the_direction
        assert Action.the_messages

        cur_pos = self._the_monster.position
        cur_level = self._the_monster.dungeon_level

        # new pos
        x_pos, y_pos = cur_pos
        delta_x, delta_y = DIRECTION_2_DELTA[self._the_direction]
        new_pos = (x_pos + delta_x, y_pos + delta_y)

        if new_pos not in self._the_monster.dungeon_level.data:
            Action.the_messages.store("Move error!")
            return

        # cannot access because not walkable
        if not cur_level.data[new_pos].may_access():
            if self._the_monster.is_hero():
                curses.beep()  # does not work here ???
                curses.flash()
                obstacle = cur_level.data[new_pos].bumped_into()
                Action.the_messages.store(f"Ouch you bumped into {obstacle}")
            return

        # cannot access because door and diagonal
        if self._the_direction.diagonal:
            if not cur_level.data[new_pos].may_access_diagonally() or not cur_level.data[cur_pos].may_access_diagonally():
                if self._the_monster.is_hero():
                    Action.the_messages.store(f"You cannot go that way!")
                return

        # cannot access because monster or heavyrock there
        occupant = cur_level.data[new_pos].occupant
        if occupant:
            if self._the_monster.is_hero():
                Action.the_messages.store(f"There is already {occupant.whatis()} there")
            return

        self._the_monster.moves_to(cur_level, new_pos)

    def climb(self) -> None:
        """ climb action """

        assert self._the_monster
        assert self._the_direction
        assert Action.the_messages

        cur_pos = self._the_monster.position
        cur_level = self._the_monster.dungeon_level

        if self._the_direction == DirectionEnum.CLIMB_UP:
            if cur_pos not in cur_level.junction_table:
                Action.the_messages.store("Junction error!")
                return
            new_level, new_pos = cur_level.junction_table[cur_pos]
            self._the_monster.moves_to(new_level, new_pos)
            if self._the_monster.is_hero():
                Action.the_messages.store("You climb up the stairs...")
            return

        if self._the_direction == DirectionEnum.CLIMB_DOWN:
            if cur_pos not in cur_level.junction_table:
                Action.the_messages.store("Junction error!")
                return
            new_level, new_pos = cur_level.junction_table[cur_pos]
            self._the_monster.moves_to(new_level, new_pos)
            if self._the_monster.is_hero():
                Action.the_messages.store("You climb down the stairs...")
            return

    def attack(self) -> None:
        """ attack action """

        assert self._the_monster
        assert Action.the_messages
        assert self._the_victim

        if self._the_monster.is_hero():
            Action.the_messages.store("That is a monster :-)")
            Action.the_messages.store("Fight not implemented yet.")
            Action.the_messages.store("However we kill the monster")
            self._the_victim.die()

    def push(self) -> None:
        """ push action """

        assert self._the_monster
        assert self._the_direction
        assert Action.the_messages

        cur_pos = self._the_monster.position
        cur_level = self._the_monster.dungeon_level

        # new pos
        x_pos, y_pos = cur_pos
        delta_x, delta_y = DIRECTION_2_DELTA[self._the_direction]
        new_pos = (x_pos + delta_x, y_pos + delta_y)
        occupant = cur_level.data[new_pos].occupant

        if self._the_monster.is_hero():
            if isinstance(occupant, heavyrocks.Boulder):
                boulder = occupant
                boulder_pos = boulder.position
                boulder_pos_x, boulder_pos_y = boulder_pos
                boulder_dest_pos = (boulder_pos_x + delta_x, boulder_pos_y + delta_y)
                if self._the_direction.diagonal:
                    if not cur_level.data[boulder_dest_pos].may_access_diagonally() or not cur_level.data[boulder_pos].may_access_diagonally():
                        if self._the_monster.is_hero():
                            Action.the_messages.store(f"You cannot push the boulder that way!")
                        return
                occupant = cur_level.data[boulder_dest_pos].occupant
                if occupant:
                    if isinstance(occupant, monsters.Monster):
                        if self._the_monster.is_hero():
                            Action.the_messages.store(f"You hear a monster screaming behind the boulder!")
                    else:
                        if self._the_monster.is_hero():
                            Action.the_messages.store(f"There seems to be something behind the boulder!")
                    return
                if not cur_level.data[boulder_dest_pos].may_access() or cur_level.data[boulder_dest_pos].may_climb_up():
                    if self._the_monster.is_hero():
                        Action.the_messages.store(f"The boulder cannot go in this direction!")
                    return
                if cur_level.data[boulder_dest_pos].may_climb_down():
                    if self._the_monster.is_hero():
                        Action.the_messages.store(f"The boulder falls down the stairs!")
                    # no more boulder
                    cur_level.data[boulder_pos].occupant = None
                    # TODO : put boulder in level below
                    # move monster
                    self._the_monster.moves_to(cur_level, new_pos)
                    return
                # move boulder
                cur_level.data[boulder_pos].occupant = None
                cur_level.data[boulder_dest_pos].occupant = boulder
                boulder.move_me_to(boulder_dest_pos)
                # move monster
                self._the_monster.moves_to(cur_level, new_pos)

    def cost(self) -> int:
        """ cost of action """
        return self._mytype.cost

    def open_door(self) -> None:
        """ open door action """

        assert self._the_door
        assert self._the_monster
        assert Action.the_messages

        if self._the_door.status is hidden.DoorStatusEnum.OPENED:
            if self._the_monster.is_hero():
                Action.the_messages.store("Hey, it seems the door is already open!")
            return
        if self._the_door.status is hidden.DoorStatusEnum.DESTROYED:
            if self._the_monster.is_hero():
                Action.the_messages.store("Hey, it seems the door is broken!")
            return
        if self._the_door.status is hidden.DoorStatusEnum.LOCKED:
            if self._the_monster.is_hero():
                Action.the_messages.store("Mmm. The door appears to be locked...")
            return
        if self._the_door.open_door():
            if self._the_monster.is_hero():
                Action.the_messages.store("You succeeded in opening the door")
            return

    def close_door(self) -> None:
        """ close door action """

        assert Action.the_messages
        assert self._the_monster
        assert self._the_door

        if self._the_door.status in [hidden.DoorStatusEnum.CLOSED, hidden.DoorStatusEnum.LOCKED]:
            if self._the_monster.is_hero():
                Action.the_messages.store("Hey, it seems the door is already closed!")
            return

        door_pos = self._the_door.position
        if self._the_monster.dungeon_level.data[door_pos].items:
            if self._the_monster.is_hero():
                Action.the_messages.store("Hey, there are objects in the way!")
            return

        if self._the_door.close_door():
            if self._the_monster.is_hero():
                Action.the_messages.store("You succedded in closing the door")
            return

    def kick(self) -> None:
        """ kick action """

        assert Action.the_messages
        assert self._the_monster

        assert self._the_door or self._the_direction

        if self._the_door:

            if self._the_door.status is hidden.DoorStatusEnum.OPENED:
                if self._the_monster.is_hero():
                    Action.the_messages.store("Hey that door is open!")
                return
            if self._the_door.status is hidden.DoorStatusEnum.DESTROYED:
                if self._the_monster.is_hero():
                    Action.the_messages.store("Hey that door is already destroyed!")
                return
            proba = 3 * self._the_monster.strength_value()
            if not myrandom.percent_chance(proba):
                Action.the_messages.store("Ouch!")
                return
            if self._the_door.kick_door():
                if self._the_monster.is_hero():
                    Action.the_messages.store("As you kick the door, it crashed open!")
                return

        if self._the_direction:
            something_moved = False

            delta_x, delta_y = DIRECTION_2_DELTA[self._the_direction]
            x_pos, y_pos = self._the_monster.position
            start_pos = (x_pos + delta_x, y_pos + delta_y)

            for item in self._the_monster.dungeon_level.data[start_pos].items.copy():
                (new_x, new_y) = start_pos
                good_pos = start_pos
                dist_max = math.ceil(self._the_monster.strength_value() / 2 - item.mytype.weight / 40) + myrandom.randint(-1, 1)
                dist = 0
                while dist < dist_max:
                    (new_x, new_y) = (new_x + delta_x, new_y + delta_y)
                    new_pos = (new_x, new_y)
                    if new_pos not in self._the_monster.dungeon_level.data:
                        break
                    if not self._the_monster.dungeon_level.data[new_pos].may_access():
                        break
                    good_pos = new_pos
                    dist += 1
                if good_pos != start_pos:
                    something_moved = True
                    self._the_monster.dungeon_level.data[start_pos].items.remove(item)
                    self._the_monster.dungeon_level.data[good_pos].items.append(item)

            if not something_moved:
                Action.the_messages.store("Thump!")

            return

    def pickup(self) -> None:
        """ pickup action """

        assert Action.the_messages
        assert self._the_monster
        assert self._the_item

        hero_pos = self._the_monster.position
        place = self._the_monster.dungeon_level.data[hero_pos]
        local_items = place.items

        if self._the_item not in local_items:
            if self._the_monster.is_hero():
                Action.the_messages.store("Hey, the item to pick is no more there!")
            return

        local_items.remove(self._the_item)
        self._the_monster.backsack.add_something(self._the_item)
        Action.the_messages.store(f"{self._the_item.whatis()}")

    def drop(self) -> None:
        """ drop action """

        assert Action.the_messages
        assert self._the_monster
        assert self._the_item

        hero_pos = self._the_monster.position
        place = self._the_monster.dungeon_level.data[hero_pos]
        local_items = place.items

        if self._the_item not in self._the_monster.backsack.list_content():
            if self._the_monster.is_hero():
                Action.the_messages.store("Hey, the item to drop is no more there!")
            return

        self._the_monster.backsack.remove_something(self._the_item)
        local_items.append(self._the_item)
        if self._the_monster.is_hero():
            Action.the_messages.store(f"You dropped {self._the_item.whatis()}")

    def throw(self) -> None:
        """ throw action """

        assert Action.the_messages
        assert self._the_monster
        assert self._the_direction
        assert self._the_item

        delta_x, delta_y = DIRECTION_2_DELTA[self._the_direction]
        x_pos, y_pos = self._the_monster.position
        start_pos = (x_pos + delta_x, y_pos + delta_y)
        (new_x, new_y) = start_pos
        good_pos = start_pos
        dist_max = math.ceil(2 * self._the_monster.strength_value() / 3 - self._the_item.mytype.weight / 50) + myrandom.randint(-1, 1)
        dist = 0
        while dist < dist_max:
            (new_x, new_y) = (new_x + delta_x, new_y + delta_y)
            new_pos = (new_x, new_y)
            if new_pos not in self._the_monster.dungeon_level.data:
                break
            if not self._the_monster.dungeon_level.data[new_pos].may_access():
                break
            good_pos = new_pos
            dist += 1
        if good_pos != start_pos:

            if self._the_item not in self._the_monster.backsack.list_content():
                if self._the_monster.is_hero():
                    Action.the_messages.store("Hey, the item to throw is no more there!")
                return

            self._the_monster.backsack.remove_something(self._the_item)
            self._the_monster.dungeon_level.data[good_pos].items.append(self._the_item)
            return

        if self._the_monster.is_hero():
            Action.the_messages.store("Thump!")

    def rest(self) -> None:
        """ rest action """

        assert self._the_monster
        self._the_monster.rest_in_place()

    def search(self) -> None:
        """ search action """

        assert self._the_monster
        assert Action.the_messages

        x_pos, y_pos = self._the_monster.position
        actual_secrets = list()
        for delta in DIRECTION_2_DELTA.values():
            delta_x, delta_y = delta
            new_pos = (x_pos + delta_x, y_pos + delta_y)
            door = self._the_monster.dungeon_level.data[new_pos].door
            if door:
                if door.secret:
                    actual_secrets.append(new_pos)
            corridor = self._the_monster.dungeon_level.data[new_pos].corridor
            if corridor:
                if corridor.secret:
                    actual_secrets.append(new_pos)

        if not actual_secrets:
            return

        luck_value = self._the_monster.luck_value() if self._the_monster.is_hero() else 0
        success = myrandom.decide_success(int(self._the_monster.proba_secret_detection_value()), luck_value)
        if not success:
            return

        secret_pos = random.choice(actual_secrets)
        place = self._the_monster.dungeon_level.data[secret_pos]
        if place.door and place.door.secret:
            if self._the_monster.is_hero():
                Action.the_messages.store("You discovered a secret door...")
            place.door.reveal_secret()
            return
        if place.corridor and place.corridor.secret:
            if self._the_monster.is_hero():
                Action.the_messages.store("You discovered a secret passage...")
            place.corridor.reveal_secret()
            return

    def execute(self) -> None:
        """ execute action """
        if self._mytype == ActionEnum.MOVE:
            self.move()
        if self._mytype == ActionEnum.CLIMB:
            self.climb()
        if self._mytype == ActionEnum.ATTACK:
            self.attack()
        if self._mytype == ActionEnum.PUSH:
            self.push()
        if self._mytype == ActionEnum.OPEN_DOOR:
            self.open_door()
        if self._mytype == ActionEnum.CLOSE_DOOR:
            self.close_door()
        if self._mytype == ActionEnum.KICK:
            self.kick()
        if self._mytype == ActionEnum.PICK_UP:
            self.pickup()
        if self._mytype == ActionEnum.DROP:
            self.drop()
        if self._mytype == ActionEnum.THROW:
            self.throw()
        if self._mytype == ActionEnum.REST:
            self.rest()
        if self._mytype == ActionEnum.SEARCH:
            self.search()


if __name__ == '__main__':
    assert False, "Do not run this script"
