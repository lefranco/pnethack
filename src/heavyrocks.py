#!/usr/bin/env python3


"""
File : features.py

Handles a heavy rock (statue or boulder)
"""

import typing

import monsters


class HeavyRock(monsters.Occupant):
    """ generic feature """

    # will be superseded
    class_glyph = "à"

    def __init__(self, dungeon_level: typing.Any, position: typing.Tuple[int, int]) -> None:
        monsters.Occupant.__init__(self, dungeon_level, position)

    def glyph(self) -> str:
        """ glyph """
        return self.class_glyph

    def whatis(self) -> str:
        """ whatis """
        assert False, "Missing whatis for HeavyRock"
        return ""

    def blocks_vision(self) -> bool:
        """ blocks_vision """
        return True

    def move_me_to(self, position: typing.Tuple[int, int]) -> None:
        """ move (passive) """
        self._position = position

    @property
    def position(self) -> typing.Tuple[int, int]:
        """ property """
        return self._position


class Boulder(HeavyRock):
    """ A boulder """

    class_glyph = "0"

    def __init__(self, dungeon_level: typing.Any, position: typing.Tuple[int, int]) -> None:
        HeavyRock.__init__(self, dungeon_level, position)

    def whatis(self) -> str:
        """ whatis """
        return "a boulder"


class Statue(HeavyRock):
    """ A statue """

    class_glyph = "¥"

    def __init__(self, dungeon_level: typing.Any, position: typing.Tuple[int, int], statue_of: monsters.MonsterTypeEnum) -> None:
        HeavyRock.__init__(self, dungeon_level, position)
        self.monster_type = statue_of

    def whatis(self) -> str:
        """ whatis """
        return f"a statue of {self.monster_type.desc}"


# Probability of different heavyrock
POSSIBLE_HEAVYROCKS = list(HeavyRock.__subclasses__())

# Boulder Statue
PROBA_HEAVYROCKS = [66, 34]
assert len(PROBA_HEAVYROCKS) == len(POSSIBLE_HEAVYROCKS), "Mismatch in heavyrock probability table"
assert sum(PROBA_HEAVYROCKS) == 100, f"Sum of proba tiles is {sum(PROBA_HEAVYROCKS)} not 100"


if __name__ == '__main__':
    assert False, "Do not run this script"
