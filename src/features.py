#!/usr/bin/env python3


"""
File : features.py

Handles features in the dungeoon
"""

import typing

import display
import alignment


class Feature(display.Displayable):
    """ generic feature """

    class_glyph = "à"

    def __init__(self, position: typing.Tuple[int, int]) -> None:
        self._position = position

    def glyph(self) -> str:
        """ glyph """
        return self.class_glyph

    # will be superseded
    def whatis(self) -> str:
        """ whatis """
        assert False, "Missing whatis for Feature"
        return ""

    # will be superseded
    def messages_entering_level(self) -> typing.List[str]:  # pylint: disable=no-self-use
        """ When such a feature is on level """
        return list()

    @property
    def position(self) -> typing.Tuple[int, int]:
        """ property """
        return self._position


class Altar(Feature):
    """ An altar """

    class_glyph = "_"

    def whatis(self) -> str:
        """ whatis """
        desc = self._alignment.description()
        return f"an altar [{desc}]"

    def __init__(self, position: typing.Tuple[int, int], altar_alignment: alignment.AlignmentEnum) -> None:
        Feature.__init__(self, position)
        self._alignment = altar_alignment


class Sink(Feature):
    """ A sink """

    class_glyph = "#"

    def whatis(self) -> str:
        """ whatis """
        return "a sink"

    def messages_entering_level(self) -> typing.List[str]:
        """ When such a feature is on level """
        return ["You hear a slow drip."]


class Fountain(Feature):
    """ A fountain """

    class_glyph = "{"

    def whatis(self) -> str:
        """ whatis """
        return "a fountain"

    def messages_entering_level(self) -> typing.List[str]:
        """ When such a feature is on level """
        return ["You hear bubbling water"]


class Throne(Feature):
    """ An throne """

    class_glyph = "|"

    def whatis(self) -> str:
        """ whatis """
        return "a throne"


class HeadStone(Feature):
    """ a headstone """

    class_glyph = "±"

    def __init__(self, position: typing.Tuple[int, int], inscription: str) -> None:
        Feature.__init__(self, position)
        self._inscription = inscription

    def whatis(self) -> str:
        """ whatis """
        return "a headstone"

    @property
    def inscription(self) -> str:
        """ property """
        return self._inscription


# Probability of different features
POSSIBLE_FEATURES = list(Feature.__subclasses__())


# Altar Sink Fountain Throne HeadStone
PROBA_FEATURES = [20, 15, 26, 23, 16]
assert len(PROBA_FEATURES) == len(POSSIBLE_FEATURES), "Mismatch in features probability table"
assert sum(PROBA_FEATURES) == 100, f"Sum of proba tiles is {sum(PROBA_FEATURES)} not 100"


if __name__ == '__main__':
    assert False, "Do not run this script"
