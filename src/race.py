#!/usr/bin/env python3


"""
File : race.py

Handles the race of the monster controlled by the player.
"""

import hero


class HeroRace(hero.HeroParentClass):
    """ Race class """

    # will be superseded
    race_name = "à"

    """ all races must derive from this """
    def __init__(self) -> None:
        hero.HeroParentClass.__init__(self)
        self._dummy = 1


class Human(HeroRace):
    """ A Human object """

    race_name = "Human"

    def __init__(self) -> None:
        HeroRace.__init__(self)
        self._dummy = 1


class Elf(HeroRace):
    """ An Elf object """

    race_name = "Elf"

    def __init__(self) -> None:
        HeroRace.__init__(self)
        self._success_secret_detection *= 1.2


class Dwarf(HeroRace):
    """ An Dwarf object """

    race_name = "Dwarf"

    def __init__(self) -> None:
        HeroRace.__init__(self)
        self._success_secret_detection *= 0.9


if __name__ == '__main__':
    assert False, "Do not run this script"
