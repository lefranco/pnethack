#!/usr/bin/env python3


"""
File : display.py

Abstract class for all stuff that can appear on the screen.
"""

import abc


class Displayable(abc.ABC):
    """ All displayable objects must derive from this class """

    @abc.abstractmethod
    def glyph(self) -> str:
        """ character to display on screen """

    @abc.abstractmethod
    def whatis(self) -> str:
        """ explanation to put in messages """


class SomethingSeen:
    """ Parent class for enums that have a desc """

    def __init__(self, desc: str) -> None:
        self._desc = desc

    @property
    def desc(self) -> str:
        """ property """
        return self._desc


if __name__ == '__main__':
    assert False, "Do not run this script"
