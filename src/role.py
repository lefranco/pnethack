#!/usr/bin/env python3


"""
File : role.py

Handles the role (class) of the monster controlled by the player - that is his profession.
"""

import hero


class HeroRole(hero.HeroParentClass):
    """ all roles must derive from this """

    # will be superseded
    role_name = "à"

    def __init__(self) -> None:
        hero.HeroParentClass.__init__(self)
        self._dummy = 1


class Fighter(HeroRole):
    """ Fighter object """

    role_name = "Fighter"

    def __init__(self) -> None:
        HeroRole.__init__(self)
        self._dummy = 1


class Wizard(HeroRole):
    """ Wizard object """

    role_name = "Wizard"

    def __init__(self) -> None:
        HeroRole.__init__(self)
        self._success_secret_detection *= 0.8


class Priest(HeroRole):
    """ Priest object """

    role_name = "Priest"

    def __init__(self) -> None:
        HeroRole.__init__(self)
        self._success_secret_detection *= 0.9


class Rogue(HeroRole):
    """ Rogue object """

    role_name = "Rogue"

    def __init__(self) -> None:
        HeroRole.__init__(self)
        self._success_secret_detection *= 1.5


if __name__ == '__main__':
    assert False, "Do not run this script"
