#!/usr/bin/env python3


"""
File : pickables.py

Objects to be picked up and dropped
"""
import typing
import enum

import display

# ========================================
# upper level
# ========================================


class Something(display.SomethingSeen):
    """ Parent class for enums that have a desc """
    def __init__(self, desc: str, weight: int) -> None:

        display.SomethingSeen.__init__(self, desc)
        self._weight = weight

    @property
    def weight(self) -> int:
        """ property """
        return self._weight


class Pickable(display.Displayable):
    """ All level must derive from this class """

    class_glyph = 'à'
    poss_type: typing.Any = None  # will be superseded
    cur_ident = 1

    def __init__(self, mytype: typing.Any) -> None:
        self._mytype = mytype
        self._ident = type(self).cur_ident
        type(self).cur_ident += 1

    # will be superseded
    def desc(self) -> str:  # pylint: disable=no-self-use
        """ for whatis """
        assert False, "Missing desc for Pickable"
        return ""

    def glyph(self) -> str:
        """ glyph """
        return self.class_glyph

    def whatis(self) -> str:
        """ whatis """
        return f"{self.desc()} [{self.mytype.desc}/{self._ident}]"

    def __lt__(self, other: 'Pickable') -> bool:
        self_index = Pickable.__subclasses__().index(type(self))
        other_index = Pickable.__subclasses__().index(type(other))
        if self_index != other_index:
            return self_index < other_index
        return self._ident < other.ident

    @property
    def mytype(self) -> typing.Any:
        """ property """
        return self._mytype

    @property
    def ident(self) -> int:
        """ property """
        return self._ident


class Putable:
    """ Any thing that can be put  """
    pass


class Wieldable:
    """ Any thing that can be wielded  """
    pass


class Throwable:
    """ Any thing that can be thrown  """
    pass


class Wearable:
    """ Any thing that can be worn  """
    pass


class Eatable:
    """ Any thing that can be eaten  """
    pass


class Drinkable:
    """ Any thing that can be drunk  """
    pass


class Readable:
    """ Any thing that can be read  """
    pass


class Zapable:
    """ Any thing that can be zapped  """
    pass


class Appliable:
    """ Any thing that can be applied  """
    pass


class Lootable:
    """ Any thing that can be looted  """
    pass

# ========================================
# lower level
# ========================================

#########
#  WEAPON etc...
#########


@enum.unique
class WeaponTypeEnum(Something, enum.Enum):
    """ Possible types of weapon """
    # Id = (desc, weight)
    DAGGER = ("dagger", 10)
    LONG_SWORD = ("long sword", 40)
    POLEARM = ("polearm", 100)


class Weapon(Pickable, Wieldable):
    """ A weapon """
    class_glyph = ")"
    poss_type = WeaponTypeEnum

    def desc(self) -> str:
        """ desc """
        return "a weapon"


@enum.unique
class ThrowerTypeEnum(Something, enum.Enum):
    """ Possible types of throwers """
    # Id = (desc, weight)
    BOW = ("bow", 30)
    SLING = ("sling", 3)
    CROSSBOW = ("crossbow", 50)


class Thrower(Pickable, Wieldable):
    """ A thrower """
    class_glyph = "("
    poss_type = ThrowerTypeEnum

    def desc(self) -> str:
        """ desc """
        return "a thrower"


@enum.unique
class ProjectileTypeEnum(Something, enum.Enum):
    """ Possible types of projectiles """
    # Id = (desc, weight)
    ARROW = ("arrow", 1)
    FLINSTONE = ("flinstone", 10)
    BOLT = ("bolt", 1)
    JAVELIN = ("javelin", 20)
    DART = ("dart", 1)


class Projectile(Pickable, Throwable):
    """ A projectile """
    class_glyph = "-"
    poss_type = ProjectileTypeEnum

    def desc(self) -> str:
        """ desc """
        return "a projectile"

#########
#  ARMOR
#########


@enum.unique
class ArmorTypeEnum(Something, enum.Enum):
    """ Possible types of armors """
    # Id = (desc, weight)
    SHIRT = ("shirt", 5)
    LEATHER_SUIT = ("leather suit", 150)
    RING_MAIL = ("ring mail", 250)
    CHAIN_MAIL = ("chain mail", 300)
    SCALE_MAIL = ("scale mail", 250)
    SPLINT_MAIL = ("splint mail", 400)
    PLATE_MAIL = ("plate mail", 450)
    PROTECTION_CLOAK = ("protection cloak", 10)
    HELM = ("helm", 50)
    LEATHER_GLOVES = ("leather gloves", 10)
    SMALL_SHIELD = ("small shield", 30)


class Armor(Pickable, Wearable):
    """ An piece of armor """
    class_glyph = "["
    poss_type = ArmorTypeEnum

    def desc(self) -> str:
        """ desc """
        return "a piece of armor"

#########
#  COMESTIBLE
#########


@enum.unique
class ComestibleTypeEnum(Something, enum.Enum):
    """ Possible types of comestible """
    # Id = (desc, weight)
    FOOD_RATION = ("food ration", 20)
    APPLE = ("apple", 2)


class Comestible(Pickable, Eatable):
    """ A comestible """
    class_glyph = "%"
    poss_type = ComestibleTypeEnum

    def desc(self) -> str:
        """ desc """
        return "a comestible"


#########
#  SCROLLS
#########

@enum.unique
class ScrollTypeEnum(Something, enum.Enum):
    """ Possible types of scrolls """
    # Id = (desc, weight)
    ENCHANT_WEAPON = ("enchant weapon", 5)
    MAGIC_MAPPING = ("magic mapping", 5)
    LIGHT = ("light", 5)


class Scroll(Pickable, Readable):
    """ A scroll """
    class_glyph = "?"
    poss_type = ScrollTypeEnum

    def desc(self) -> str:
        """ desc """
        return "a scroll"

#########
#  POTIONS
#########


@enum.unique
class PotionTypeEnum(Something, enum.Enum):
    """ Possible types of potions """
    # Id = (desc, weight)
    BOOZE = ("booze", 20)
    EXTRA_HEALING = ("extra healing", 20)
    RAISE_LEVEL = ("raise level", 20)


class Potion(Pickable, Drinkable):
    """ A potion """
    class_glyph = "!"
    poss_type = PotionTypeEnum

    def desc(self) -> str:
        """ desc """
        return "a potion"


#########
#  WANDS AND STAVES
#########

@enum.unique
class WandTypeEnum(Something, enum.Enum):
    """ Possible types of wands """
    # Id = (desc, weight)
    FIRE = ("fire", 7)
    COLD = ("cold", 7)
    DEATH = ("death", 7)


class Wand(Pickable, Zapable):
    """ A wand """
    class_glyph = "/"
    poss_type = WandTypeEnum

    def desc(self) -> str:
        """ desc """
        return "a wand"


@enum.unique
class StaffTypeEnum(Something, enum.Enum):
    """ Possible types of staves """
    # Id = (desc, weight)
    QUARTERSTAFF = ("quaterstaff", 40)


class Staff(Pickable, Wieldable):
    """ A staff """
    class_glyph = "\\"
    poss_type = StaffTypeEnum

    def desc(self) -> str:
        """ desc """
        return "a staff"

#########
#  RINGS
#########


@enum.unique
class RingTypeEnum(Something, enum.Enum):
    """ Possible types of rings """
    # Id = (desc, weight)
    ADORNMENT = ("adornment", 3)
    GAIN_STRENGTH = ("gain strength", 3)
    SEARCHING = ("searching", 3)


class Ring(Pickable, Putable):
    """ A ring """
    class_glyph = "="
    poss_type = RingTypeEnum

    def desc(self) -> str:
        """ desc """
        return "a ring"

#########
#  SPELLBOOKS
#########


@enum.unique
class SpellbookTypeEnum(Something, enum.Enum):
    """ Possible types of spell books """
    # Id = (desc, weight)
    MAGIC_MISSILE = ("magic missile", 50)
    PROTECTION = ("protection", 50)
    LIGHT = ("light", 50)
    SLEEP = ("sleep", 50)
    TELEPORT_AWAY = ("teleport away", 50)
    HEALING = ("healing", 50)
    WIZARD_LOCK = ("wizard_lock", 50)


class Spellbook(Pickable, Readable):
    """ A spellbook """
    class_glyph = "+"
    poss_type = SpellbookTypeEnum

    def desc(self) -> str:
        """ desc """
        return "a spellbook"

#########
#  AMULETS
#########


@enum.unique
class AmuletTypeEnum(Something, enum.Enum):
    """ Possible types of amulet """
    # Id = (desc, weight)
    LIFE_SAVING = ("life saving", 20)
    ESP = ("ESP", 20)


class Amulet(Pickable, Putable):
    """ An amulet """
    class_glyph = "\""
    poss_type = AmuletTypeEnum

    def desc(self) -> str:
        """ desc """
        return "an amulet"

#########
#  TOOLS etc..
#########


@enum.unique
class ToolAccessoryTypeEnum(Something, enum.Enum):
    """ Possible types of tools accessory """
    # Id = (desc, weight)
    BLINDFOLD = ("blindfold", 2)


class ToolAccessory(Pickable, Appliable):
    """ A tool accessory """
    class_glyph = "~"
    poss_type = ToolAccessoryTypeEnum

    def desc(self) -> str:
        """ desc """
        return "an accessory"


@enum.unique
class ToolContainerTypeEnum(Something, enum.Enum):
    """ Possible types of tools containers """
    # Id = (desc, weight)
    CHEST = ("chest", 600)
    BOX = ("box", 350)
    SACK = ("sack", 15)


class ToolContainer(Pickable, Lootable):
    """ A tool container """
    class_glyph = "]"
    poss_type = ToolContainerTypeEnum

    def desc(self) -> str:
        """ desc """
        return "a container"


@enum.unique
class ToolLightSourceTypeEnum(Something, enum.Enum):
    """ Possible types of tools light sources """
    # Id = (desc, weight)
    CANDLE = ("candle", 2)


class ToolLightSource(Pickable, Appliable):
    """ A tool light source """
    class_glyph = "'"
    poss_type = ToolLightSourceTypeEnum

    def desc(self) -> str:
        """ desc """
        return "a light source"


@enum.unique
class ToolUnlockerTypeEnum(Something, enum.Enum):
    """ Possible types of tools unlockers """
    # Id = (desc, weight)
    KEY = ("key", 3)


class ToolUnlocker(Pickable, Appliable):
    """ A tool unlocker """
    class_glyph = ":"
    poss_type = ToolUnlockerTypeEnum

    def desc(self) -> str:
        """ desc """
        return "an unlocker"


@enum.unique
class ToolMiscTypeEnum(Something, enum.Enum):
    """ Possible types of tools misc """
    # Id = (desc, weight)
    MIRROR = ("mirror", 13)
    MAGIC_MARKER = ("magic marker", 2)


class ToolMisc(Pickable, Appliable):
    """ A tool misc. """
    class_glyph = "`"
    poss_type = ToolMiscTypeEnum

    def desc(self) -> str:
        """ desc """
        return "a generic other tool"


#########
#  GEMS
#########


@enum.unique
class GemTypeEnum(Something, enum.Enum):
    """ Possible types of gems """
    # Id = (desc, weight)
    DILITHIUM = ("dilithium", 1)
    RUBY = ("ruby", 1)
    JACINTH = ("jacinth", 1)
    WORTHLESS_GREEN = ("worthless green", 1)
    WORTHLESS_RED = ("worthless red", 1)


class Gem(Pickable):
    """ A gem """
    class_glyph = "*"
    poss_type = GemTypeEnum

    def desc(self) -> str:
        """ desc """
        return "a gem"


# TODO
class Money(int):
    """ Money """
    pass


# type -> (elements, probabilities)
PROBA_ITEMS = {
    "A": ([Weapon, Thrower, Projectile, Armor], [40, 10, 10, 40]),
    "B": ([Potion, Scroll, Wand], [40, 30, 30]),
    "C": ([Ring, Staff, Amulet], [50, 30, 20]),
    "D": ([Spellbook], [100]),
    "E": ([Gem], [100]),
    "F": ([ToolAccessory, ToolContainer, ToolLightSource, ToolUnlocker, ToolMisc], [10, 35, 20, 15, 20]),
    "G": ([Comestible], [100])
}


if __name__ == '__main__':
    assert False, "Do not run this script"
