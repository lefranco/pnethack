#!/usr/bin/env python3


"""
File : places.py

Handle tiles, things that are sitting in the dungeon.
"""

import typing
import enum
import itertools

import display
import hidden
import features
import pickables
import alignment
import monsters
import traps


@enum.unique
class TileTypeEnum(display.SomethingSeen, enum.Enum):
    """ All possible tiles types """
    # Id = (desc, glyph, block_vision)

    MATTER = ("some hard matter", " ", True)  # "interpunct", not point aka "period"
    GROUND_TILE = ("a ground", "·", False)

    ROOM_V_WALL = ("a room wall", "║", True)
    ROOM_H_WALL = ("a room wall", "═", True)
    ROOM_UL_CORNER = ("a room corner wall", "╔", True)
    ROOM_UR_CORNER = ("a room corner wall", "╗", True)
    ROOM_LL_CORNER = ("a room corner wall", "╚", True)
    ROOM_LR_CORNER = ("a room corner wall", "╝", True)
    MAZE_V_WALL = ("a maze wall", "│", True)
    MAZE_H_WALL = ("a maze wall", "─", True)
    MAZE_X_CORNER = ("a maze corner wall", "┼", True)
    MAZE_L_0_CORNER = ("a maze corner wall", "└", True)
    MAZE_L_90_CORNER = ("a maze corner wall", "┌", True)
    MAZE_L_180_CORNER = ("a maze corner wall", "┐", True)
    MAZE_L_270_CORNER = ("a maze corner wall", "┘", True)
    MAZE_T_0_CORNER = ("a maze corner wall", "┬", True)
    MAZE_T_90_CORNER = ("a maze corner wall", "┤", True)
    MAZE_T_180_CORNER = ("a maze corner wall", "┴", True)
    MAZE_T_270_CORNER = ("a maze corner wall", "├", True)
    MAZE_I_0_CORNER = ("a maze corner wall", "╵", True)
    MAZE_I_90_CORNER = ("a maze corner wall", "╶", True)
    MAZE_I_180_CORNER = ("a maze corner wall", "╷", True)
    MAZE_I_270_CORNER = ("a maze corner wall", "╴", True)

    STAIRS_DOWN = ("stairs going down", ">", False)
    STAIRS_UP = ("stairs going up", "<", False)
    MOAT = ("a moat", "}", False)

    def __init__(self, desc: str, tile_glyph: str, blocks_vision: bool) -> None:
        display.SomethingSeen.__init__(self, desc)
        self._tile_glyph = tile_glyph
        self._blocks_vision = blocks_vision

    @property
    def tile_glyph(self) -> str:
        """ property """
        return self._tile_glyph

    @property
    def blocks_vision(self) -> bool:
        """ property """
        return self._blocks_vision


class Tile(display.Displayable):
    """ A Tile object """

    def __init__(self, mytype: TileTypeEnum) -> None:
        self._mytype = mytype

    def glyph(self) -> str:
        """ property """
        return self._mytype.tile_glyph

    def whatis(self) -> str:
        """ for whatis() """
        return self._mytype.desc

    @property
    def mytype(self) -> TileTypeEnum:
        """ property """
        return self._mytype


@enum.unique
class LightLevelEnum(enum.Enum):
    """ A level of light """
    DARK = enum.auto()
    NORMAL = enum.auto()
    LIT = enum.auto()


class LightSourceRecord(typing.NamedTuple):
    """ A light source """
    level_pos: typing.Tuple[int, int]
    light_level: LightLevelEnum
    light_radius: int


class Place:
    """ A place object """

    def __init__(self, tile: Tile) -> None:
        self._tile = tile
        self._inscription = ""
        self._trap: typing.Optional[traps.Trap] = None
        self._feature: typing.Optional[features.Feature] = None
        self._door: typing.Optional[hidden.Door] = None
        self._corridor: typing.Optional[hidden.Corridor] = None
        self._items: typing.List[pickables.Pickable] = list()
        self._occupant: typing.Optional[monsters.Occupant] = None

    def display_glyph(self) -> str:
        """ what to display """
        if self._occupant:
            return self._occupant.glyph()
        if self._items:
            return self._items[0].glyph()
        if self._corridor:
            return self._corridor.glyph()
        if self._door:
            return self._door.glyph()
        if self._feature:
            return self._feature.glyph()
        if self._trap:
            return self._trap.glyph()
        if self._inscription:
            return ","
        return self._tile.glyph()

    def bumped_into(self) -> str:
        """ bumped into what ? """
        if self._corridor:
            return self._corridor.whatis()
        if self._door:
            return self._door.whatis()
        if self._feature:
            return self._feature.whatis()
        return self._tile.whatis()

    def all_that_is_there(self) -> typing.List[str]:
        """ what to say whe saying all that is there """
        is_there = list()
        if self._occupant:
            desc = self._occupant.whatis()
            is_there.append(f"There is {desc} at this position")
        elif self._items:
            if len(self._items) > 1:
                is_there.append(f"There are several objects at this position")
            else:
                item = self._items[0]
                desc = item.whatis()
                is_there.append(f"There is {desc} at this position")
        elif self._corridor:
            desc = self._corridor.whatis()
            is_there.append(f"There is {desc} at this position")
        elif self._door:
            desc = self._door.whatis()
            is_there.append(f"There is {desc} at this position")
        elif self._feature:
            desc = self._feature.whatis()
            is_there.append(f"There is {desc} at this position")
        if not is_there:
            desc = self._tile.whatis()
            is_there.append(f"There is {desc} at this position")
        return is_there

    def blocks_vision(self) -> bool:
        """
        Does place block vision ?
        Note : this seems to be the method by far cosuming the most CPU time...
        """

        # matter or walls block vision
        if self.tile.mytype.blocks_vision:
            return True

        # secret door or corridor block vision
        if self.tile.mytype is TileTypeEnum.GROUND_TILE:
            if self.door:
                if self.door.blocks_vision():
                    return True
            if self.corridor:
                if self.corridor.blocks_vision():
                    return True

        # some occupants may block vision
        if self.occupant:
            if self.occupant.blocks_vision():
                return True

        return False

    def may_have_secret(self) -> bool:
        """ to detect if searching is pertinent """

        # room walls
        if self.tile.mytype in [TileTypeEnum.ROOM_V_WALL, TileTypeEnum.ROOM_H_WALL, TileTypeEnum.ROOM_UL_CORNER, TileTypeEnum.ROOM_UR_CORNER, TileTypeEnum.ROOM_LL_CORNER, TileTypeEnum.ROOM_LR_CORNER]:
            return True

        # maze walls
        if self.tile.mytype in [TileTypeEnum.MAZE_V_WALL, TileTypeEnum.MAZE_H_WALL, TileTypeEnum.MAZE_X_CORNER, TileTypeEnum.MAZE_L_0_CORNER, TileTypeEnum.MAZE_L_90_CORNER, TileTypeEnum.MAZE_L_180_CORNER, TileTypeEnum.MAZE_L_270_CORNER, TileTypeEnum.MAZE_T_0_CORNER, TileTypeEnum.MAZE_T_90_CORNER, TileTypeEnum.MAZE_T_180_CORNER, TileTypeEnum.MAZE_T_270_CORNER]:
            return True

        return False

    def may_access(self) -> bool:
        """ Can place be accessed (walked on) ? """

        if self.tile.mytype is TileTypeEnum.GROUND_TILE:
            if self.corridor:
                return self.corridor.may_access()
            if self.door:
                return self.door.may_access()
            return True
        if self.tile.mytype in [TileTypeEnum.STAIRS_DOWN, TileTypeEnum.STAIRS_UP]:
            return True
        return False

    def may_access_diagonally(self) -> bool:
        """ may_access_diagonally """
        if self.tile.mytype is not TileTypeEnum.GROUND_TILE:
            return True
        if not self.door:
            return True
        return False

    def may_climb_up(self) -> bool:
        """ Can place be climb on (up) ? """
        return self.tile.mytype is TileTypeEnum.STAIRS_UP

    def may_climb_down(self) -> bool:
        """ Can place be climb on (down) ? """
        return self.tile.mytype is TileTypeEnum.STAIRS_DOWN

    def engraving_messages(self) -> typing.List[str]:
        """ Describes engravings that are here """

        messages: typing.List[str] = list()

        # from a headstone
        if self.feature:
            if isinstance(self.feature, features.HeadStone):
                headstone = self.feature
                messages.append("There is something written on the grave...")
                messages.append(f"It says : \"{headstone.inscription}\" ")

        # from tile directly
        if self._inscription:
            messages.append("There is a graffiti written here...")
            messages.append(f"It says : \"{self._inscription}\" ")
        return messages

    @property
    def tile(self) -> Tile:
        """ property """
        return self._tile

    @property
    def corridor(self) -> typing.Optional[hidden.Corridor]:
        """ property """
        return self._corridor

    @corridor.setter
    def corridor(self, corridor: hidden.Corridor) -> None:
        """ setter """
        self._corridor = corridor

    @property
    def door(self) -> typing.Optional[hidden.Door]:
        """ property """
        return self._door

    @door.setter
    def door(self, door: hidden.Door) -> None:
        """ setter """
        self._door = door

    @property
    def feature(self) -> typing.Optional[features.Feature]:
        """ property """
        return self._feature

    @feature.setter
    def feature(self, feature: features.Feature) -> None:
        """ setter """
        self._feature = feature

    @property
    def inscription(self) -> str:
        """ property """
        return self._inscription

    @inscription.setter
    def inscription(self, inscription: str) -> None:
        """ setter """
        self._inscription = inscription

    @property
    def items(self) -> typing.List[pickables.Pickable]:
        """ property """
        return self._items

    @property
    def occupant(self) -> typing.Optional[monsters.Occupant]:
        """ property """
        return self._occupant

    @occupant.setter
    def occupant(self, occupant: monsters.Occupant) -> None:
        """ setter """
        self._occupant = occupant


def test() -> None:
    """ test """

    glyphes = list()

    # tiles
    for tile_type in TileTypeEnum:
        tile = Tile(tile_type)
        glyphes.append(tile.glyph())
        print(f"tile : glyph='{tile.glyph()}' ", end='')
        print(f"whatis='{tile.whatis()}'")

    dummy_pos = (0, 0)

    # corridors
    for secret in True, False:
        corridor = hidden.Corridor(dummy_pos, secret)
        glyphes.append(corridor.glyph())
        print(f"corridor secret={secret}: glyph='{corridor.glyph()}' ", end='')
        print(f"whatis='{corridor.whatis()}'")

    # doors
    for context in hidden.DoorContextEnum:
        for vertical in True, False:
            for secret in True, False:
                for status in hidden.DoorStatusEnum:
                    door = hidden.Door(dummy_pos, status, secret, context)
                    glyphes.append(door.glyph())
                    door.vertical = vertical
                    print(f"door context={context} vertical={vertical} secret={secret} status={status}: glyph='{door.glyph()}' ", end='')
                    print(f"whatis='{door.whatis()}'")

    # traps
    for trap_type in traps.TrapTypeEnum:
        trap = traps.Trap(trap_type)
        glyphes.append(trap.glyph())
        print(f"trap: glyph='{door.glyph()}' ", end='')
        print(f"whatis='{trap.whatis()}'")

    # features
    inscr = "xxx"
    for feature_class in features.Feature.__subclasses__():
        if feature_class is features.Altar:
            class_done = False
            for alig in alignment.AlignmentEnum:
                altar = features.Altar(dummy_pos, alig)
                if not class_done:
                    glyphes.append(altar.glyph())
                    class_done = True
                print(f"feature : glyph='{altar.glyph()}' ", end='')
                print(f"whatis='{altar.whatis()}'")
        elif feature_class is features.HeadStone:
            headstone = features.HeadStone(dummy_pos, inscr)
            glyphes.append(headstone.glyph())
            print(f"feature : glyph='{headstone.glyph()}' ", end='')
            print(f"whatis='{headstone.whatis()}'")
        else:
            feature = feature_class(dummy_pos)
            glyphes.append(feature.glyph())
            print(f"feature : glyph='{feature.glyph()}' ", end='')
            print(f"whatis='{feature.whatis()}'")

    for item_class in pickables.Pickable.__subclasses__():
        class_done = False
        for item_type in item_class.poss_type:
            item = item_class(item_type)
            if not class_done:
                glyphes.append(item.glyph())
                class_done = True
            print(f"item : glyph='{item.glyph()}' ", end='')
            print(f"whatis='{item.whatis()}'")

    for monster_type in monsters.MonsterTypeEnum:
        monster = monsters.Monster(monster_type, None, dummy_pos, 0)
        glyphes.append(monster.glyph())
        print(f"monster : glyph='{monster.glyph()}' ", end='')
        print(f"whatis='{monster.whatis()}'")

    dublins = set()
    for glyph1, glyph2 in itertools.combinations(glyphes, 2):
        if glyph1 == glyph2:
            dublins.add(glyph1)

    for glyph in dublins:
        print(f"Seems glyph {glyph} is used more than once, please check !")


if __name__ == '__main__':
    test()
