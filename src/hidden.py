#!/usr/bin/env python3


"""
File : hidden.py

Handles possibly hidden features in the dungeoon (doors and corridors)
"""

import typing
import enum

import display


class Secret:
    """ A feature that can be secret """

    def __init__(self, position: typing.Tuple[int, int], secret: bool) -> None:
        self._position = position
        self._secret = secret

    def reveal_secret(self) -> None:
        """ Tile modifier - door is revealed """
        self._secret = False

    @property
    def position(self) -> typing.Tuple[int, int]:
        """ property """
        return self._position

    @property
    def secret(self) -> bool:
        """ property """
        return self._secret


class Corridor(display.Displayable, Secret):
    """ A corridor object """

    def __init__(self, position: typing.Tuple[int, int], secret: bool) -> None:
        Secret.__init__(self, position, secret)

    def glyph(self) -> str:
        """ glyph """
        if self._secret:
            return ' '
        return "▒"

    def whatis(self) -> str:
        """ whatis """
        if self._secret:
            return "some matter"
        return f"a corridor"

    def may_access(self) -> bool:
        """ may access """
        if self._secret:
            return False
        return True

    def blocks_vision(self) -> bool:
        """ blocks_vision """
        if self._secret:
            return True
        return False


@enum.unique
class DoorContextEnum(enum.Enum):
    """ All possible tiles types """
    ROOM = enum.auto()
    MAZE = enum.auto()


@enum.unique
class DoorStatusEnum(enum.Enum):
    """ All possible door statuses """

    OPENED = enum.auto()
    CLOSED = enum.auto()
    LOCKED = enum.auto()
    DESTROYED = enum.auto()

    def desc(self) -> str:
        """ desc """
        if self is DoorStatusEnum.OPENED:
            return "opened"
        if self is DoorStatusEnum.CLOSED:
            return "closed"
        if self is DoorStatusEnum.LOCKED:
            return "locked"
        if self is DoorStatusEnum.DESTROYED:
            return "destroyed"
        assert False, "Missing desc for DoorStatusEnum"
        return ""

    def glyph(self) -> str:
        """ what to display """
        if self in [DoorStatusEnum.OPENED, DoorStatusEnum.DESTROYED]:
            return "▯"
        return "▮"


# door comes here. It is a very special feature
class Door(display.Displayable, Secret):
    """ A door object """

    def __init__(self, position: typing.Tuple[int, int], status: DoorStatusEnum, secret: bool, context: DoorContextEnum) -> None:
        Secret.__init__(self, position, secret)
        self._vertical = False
        self._context = context
        self._status = status

    def glyph(self) -> str:
        """ what to display """
        if self._secret:
            if self._context == DoorContextEnum.ROOM:
                if self._vertical:
                    return "║"
                return "═"
            if self._context == DoorContextEnum.MAZE:
                if self._vertical:
                    return "│"
                return "─"
        return self._status.glyph()

    def whatis(self) -> str:
        """ whatis """
        if self._secret:
            return "a wall"
        desc = self._status.desc()
        return f"a door [{desc}]"

    def open_door(self) -> bool:
        """ Opening the door """
        if self._status is not DoorStatusEnum.CLOSED:
            return False
        self._status = DoorStatusEnum.OPENED
        return True

    def close_door(self) -> bool:
        """ Closing the door """
        if self._status is not DoorStatusEnum.OPENED:
            return False
        self._status = DoorStatusEnum.CLOSED
        return True

    def kick_door(self) -> bool:
        """ Kicking the door """
        if self._status not in [DoorStatusEnum.CLOSED, DoorStatusEnum.LOCKED]:
            return False
        self._status = DoorStatusEnum.DESTROYED
        return True

    def may_access(self) -> bool:
        """ may access """
        if self._secret:
            return False
        return self._status in [DoorStatusEnum.OPENED, DoorStatusEnum.DESTROYED]

    def blocks_vision(self) -> bool:
        """ blocks_vision """
        if self._secret:
            return True
        return self._status in [DoorStatusEnum.CLOSED, DoorStatusEnum.LOCKED]

    @property
    def vertical(self) -> bool:
        """ property """
        return self._vertical

    @vertical.setter
    def vertical(self, vertical: bool) -> None:
        """ setter """
        self._vertical = vertical

    @property
    def status(self) -> DoorStatusEnum:
        """ property """
        return self._status

    @property
    def secret(self) -> bool:
        """ property """
        return self._secret


if __name__ == '__main__':
    assert False, "Do not run this script"
