#!/usr/bin/env python3


"""
File : hero.py

Stuff related to the hero (the monster controlled by the player) only.
"""

import typing

import constants
import myrandom
import abstractlevel
import alignment
import monsters
import mapping


class Attribute:
    """ Attribute class """

    # will be superseded
    short_name = "à"

    def __init__(self, value: int) -> None:
        self._value = value
        self._value_min = 3
        self._value_max = 25

    def __str__(self) -> str:
        return f"{type(self).short_name}:{self._value}"

    def improve(self) -> None:
        """ improve """
        if self._value == self._value_max:
            return
        self._value += 1

    def worsen(self) -> None:
        """ worsen """
        if self._value < self._value_min:
            return
        self._value -= 1

    @property
    def value(self) -> int:
        """ property """
        return self._value


class AttributeStrength(Attribute):
    """ Strength """
    name = "Strength"
    short_name = "St"

    def __init__(self, value: int) -> None:
        Attribute.__init__(self, value)
        self._value_max = 30

    def to_hit_bonus(self) -> int:
        """ to hit bonus from strength """
        if self._value <= 5:
            return -2
        if self._value <= 7:
            return -1
        if self._value <= 16:
            return 0
        if self._value <= 19:
            return 1
        if self._value <= 22:
            return 2
        return 3

    def damage_bonus(self) -> int:
        """ damage bonus from strength """
        if self._value <= 5:
            return -1
        if self._value <= 15:
            return 0
        if self._value <= 17:
            return 1
        if self._value <= 18:
            return 2
        if self._value <= 20:
            return 3
        if self._value <= 21:
            return 4
        if self._value <= 22:
            return 5
        return 6

    def __str__(self) -> str:
        if self._value <= 18:
            strength_value = str(self._value)
        elif self._value == 19:
            strength_value = "18/50"
        elif self._value == 20:
            strength_value = "18/63"
        elif self._value == 21:
            strength_value = "18/83"
        elif self._value == 22:
            strength_value = "18/95"
        elif self._value == 23:
            strength_value = "18:/**"
        else:
            strength_value = str(self._value - 5)
        return f"{type(self).short_name}:{strength_value}"


class AttributeDexterity(Attribute):
    """ Dexterity """
    name = "Dexterity"
    short_name = "Dx"


class AttributeConstitution(Attribute):
    """ Constitution """
    name = "Constitution"
    short_name = "Co"


class AttributeIntelligence(Attribute):
    """ Intelligence """
    name = "Intelligence"
    short_name = "In"


class AttributeWisdom(Attribute):
    """ Wisdom """
    name = "Wisdom"
    short_name = "Wi"


class AttributeCharisma(Attribute):
    """ Charisma """
    name = "Charisma"
    short_name = "Ch"


class Attributes:
    """ Attributes """

    def __init__(self, strength: int, dexterity: int, constitution: int, intelligence: int,
                 wisdom: int, charisma: int) -> None:
        self._strength = AttributeStrength(strength)
        self._dexterity = AttributeDexterity(dexterity)
        self._constitution = AttributeConstitution(constitution)
        self._intelligence = AttributeIntelligence(intelligence)
        self._wisdom = AttributeWisdom(wisdom)
        self._charisma = AttributeCharisma(charisma)

    @property
    def strength(self) -> AttributeStrength:
        """ property """
        return self._strength

    def __str__(self) -> str:
        return f"{self._strength} {self._dexterity} {self._constitution} " f"{self._intelligence} {self._wisdom} {self._charisma}"


class ExperiencePoints:
    """ Experience points """

    name = "Experience Points"
    short_name = "Exp"

    def __init__(self, value: int) -> None:
        self._value = value

    def gain(self, increase: int) -> None:
        """ gains some XPs """
        self._value += increase

    def __str__(self) -> str:
        return f"{type(self).short_name}:{self._value}"


class Score:
    """ Score """

    name = "Score"
    short_name = "S"

    def __init__(self, value: int) -> None:
        self._value = value

    def gain(self, increase: int) -> None:
        """ Gain of score """
        self._value += increase

    def __str__(self) -> str:
        return f"{type(self).short_name}:{self._value}"


class Luck:
    """ Score """

    def __init__(self) -> None:
        self._value = 0

    def gain(self, increase: int) -> None:
        """ Gain of luck """
        self._value += increase

    def lose(self, increase: int) -> None:
        """ Loss of luck """
        self._value -= increase

    @property
    def value(self) -> int:
        """ property """
        return self._value


class HeroParentClass:
    """ This class is parent to classes HeroClass, HeroRace and GenericHero """

    def __init__(self) -> None:

        # put here stuff that need to be visible by race, role...

        # chances of success of actions (percent)
        self._success_secret_detection = 25.0


class GenericHero(monsters.Monster, HeroParentClass):
    """ Generic Hero class """

    def __init__(self, dungeon_level: abstractlevel.AbstractLevel, position: typing.Tuple[int, int], hero_alignment: alignment.Alignment, money_given: int) -> None:

        monsters.Monster.__init__(self, monsters.MonsterTypeEnum.HERO, dungeon_level, position, money_given)
        HeroParentClass.__init__(self)

        # mapping memory
        self._mapping_memory: typing.Dict[int, typing.Dict[typing.Tuple[int, int], bool]] = dict()

        # attributes
        self._hero_name = constants.HERO_NAME
        self._attributes = Attributes(myrandom.dice("3d6"), myrandom.dice("3d6"), myrandom.dice("3d6"), myrandom.dice("3d6"), myrandom.dice("3d6"), myrandom.dice("3d6"))
        self._xpoints = ExperiencePoints(0)
        self._score = Score(0)
        self._luck = Luck()
        self._hero_alignment = hero_alignment

    def note_mapping(self, level: abstractlevel.AbstractLevel, the_mapping: mapping.Mapping) -> None:
        """ Store mapping info hero has in his head """
        self._mapping_memory[level.identifier] = the_mapping.has_seen

    def recall_mapping(self, level: abstractlevel.AbstractLevel) -> typing.Dict[typing.Tuple[int, int], bool]:
        """ The hero changes level, note what he know the level he is leaving """
        return self._mapping_memory[level.identifier]

    def give_status(self, game_turn: int) -> typing.Tuple[str, str, str]:
        """ Extracts all status information about the hero """
        # pylint: disable=no-member

        line1 = f"{self._hero_name} the {self.race_name} {self.role_name} {self._attributes} {self._hero_alignment} {self._score}"  # type: ignore
        level = f"{self._dungeon_level.depth}{self._dungeon_level.branch}" if self._dungeon_level else "<outside>"
        line2 = f"{level} {self._purse} {self._hit_points} {self._power_points} {self._armourclass} {self._xpoints} {game_turn}"
        line3 = "Bon pied, bon oeil !"
        return (line1, line2, line3)

    def enlightment(self) -> typing.List[str]:
        """ extract all enlightment information """
        table = list()
        table.append(f"Chances of secret detection = {self._success_secret_detection}")
        return table

    def strength_value(self) -> int:
        """ strength """
        return self.attributes.strength.value

    def proba_secret_detection_value(self) -> float:
        """ proba secret detection """
        return self._success_secret_detection

    def luck_value(self) -> int:
        """ luck """
        return self._luck.value

    @property
    def hero_alignment(self) -> alignment.Alignment:
        """ property """
        return self._hero_alignment

    @property
    def attributes(self) -> Attributes:
        """ property """
        return self._attributes


def create_hero_class(hero_race: typing.Type, hero_class: typing.Type) -> typing.Type:  # type: ignore
    """ Important function : create a hero class that inherits from hero, its class, its race """
    hero_class_name = f"{hero_race.race_name}_{hero_class.role_name}"
    return type(hero_class_name, (GenericHero, hero_class, hero_race), {})


if __name__ == '__main__':
    assert False, "Do not run this script"
