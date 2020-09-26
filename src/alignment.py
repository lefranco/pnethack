#!/usr/bin/env python3


"""
File : alignment.py

Stuff related to alignment
"""

import enum


@enum.unique
class AlignmentEnum(enum.Enum):
    """ Possible alignments """
    UNALIGNED = enum.auto()
    LAWFUL = enum.auto()
    NEUTRAL = enum.auto()
    CHAOTIC = enum.auto()

    def description(self) -> str:
        """ for what is """
        if self is AlignmentEnum.UNALIGNED:
            return "unaligned"
        if self is AlignmentEnum.LAWFUL:
            return "lawful"
        if self is AlignmentEnum.NEUTRAL:
            return "neutral"
        if self is AlignmentEnum.CHAOTIC:
            return "chaotic"
        assert False, "Description of alignement issue"
        return ""

    def player_allowed(self) -> bool:
        """ as it says """
        return self in [AlignmentEnum.LAWFUL, AlignmentEnum.NEUTRAL, AlignmentEnum.CHAOTIC]


class Alignment:
    """ Alignment object """

    def __init__(self, value: AlignmentEnum) -> None:
        self._value = value

    @property
    def value(self) -> AlignmentEnum:
        """ property """
        return self._value

    def __str__(self) -> str:
        return self._value.name.title()[:3]


if __name__ == '__main__':
    assert False, "Do not run this script"
