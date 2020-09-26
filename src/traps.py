#!/usr/bin/env python3


"""
File : traps.py

Handle stuff related to all traps.
"""

import enum

import display


@enum.unique
class TrapTypeEnum(display.SomethingSeen, enum.Enum):
    """ Trap types """

    DART = ("a dart trap")
    ARROW = ("an arrow trap")


class Trap(display.Displayable):
    """ A trap object """

    class_glyph = '^'

    def __init__(self, mytype: TrapTypeEnum) -> None:
        self._mytype = mytype

    def glyph(self) -> str:
        """ property """
        return self.class_glyph

    def whatis(self) -> str:
        """ for whatis() """
        return self._mytype.desc


if __name__ == '__main__':
    assert False, "Do not run this script"
