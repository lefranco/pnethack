#!/usr/bin/env python3


"""
File : roomlevel.py

Random creation of a room level.
"""

import typing
import random
import itertools
import math

import constants
import myrandom
import mylogger
import hidden
import features
import heavyrocks
import places
import alignment
import abstractlevel
import monsters

# for debug only
# import debug.wingdbstub

ROOM_ATTEMPTS = 10000
REMOVALS_MAX = 10000
CORRIDOR_ATTEMPTS = 10000
CONNECTION_ATTEMPTS = 1000
LEVEL_ATTEMPTS = 1000
VAULT_ATTEMPTS = 1000

NB_FAKE_ROOMS = 1
MIN_NB_ROOM = 8
MAX_NB_ROOM = 8

# Probability of big room possible
PROBA_BIG_ROOM_POSSIBLE = 25

# Probability of light (lightness of darkness) presence
PROBA_SPECIAL_LIGHT = 40

# Probability of dark light
PROBA_DARK_LIGHT = 30

# Probability of shop presence (affected by depth)
PROBA_SHOP = 90
DECREASE_PROBA_SHOP = 3

# Probability of special room presence
PROBA_SPECIAL_ROOM = 75

# Probability of feature presence
PROBA_FEATURE = 35

# Probability of engraving presence
PROBA_ENGRAVING = 13

# Probability of heavy rock presence
PROBA_HEAVYROCK = 25

# Probability of door to be open
PROBA_OPENED_DOOR = 33

# Probability of door to be open
PROBA_LOCKED_DOOR = 45

# Probability of secret door
PROBA_SECRET_DOOR = 15

# Probability of secret corridor
PROBA_SECRET_CORRIDOR = 4

# for moving...
MOVES_TABLE = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


class Occupier:
    """ A corridor or a room that must not share space """

    def __init__(self) -> None:
        # for collisions
        self._extended_cells: typing.Set[typing.Tuple[int, int]] = set()

    @property
    def extended_cells(self) -> typing.Set[typing.Tuple[int, int]]:
        """ property """
        return self._extended_cells

    def collides(self, other: 'Occupier') -> bool:
        """ Do these two room/corridor collide ? """
        return bool(self._extended_cells & other.extended_cells)


class Room(Occupier):
    """ A room object """

    def __init__(self, vault: bool) -> None:

        def set_light_level() -> None:
            """ Change light level of room """
            # Difference between light level of room and light sources:
            #   - light level applies to a room
            #   - if a room is lit or dark we will put a light source in the middle of it
            if isinstance(self, Vault):
                return
            if myrandom.percent_chance(PROBA_SPECIAL_LIGHT):
                if myrandom.percent_chance(PROBA_DARK_LIGHT):
                    self._room_light_level = places.LightLevelEnum.DARK
                else:
                    self._room_light_level = places.LightLevelEnum.LIT

        #  == start of init here ==

        # Explicit init of parent class
        Occupier.__init__(self)

        # a size for the room
        # declare
        self._container_height = 0
        self._container_width = 0
        # vault
        if vault:
            self._container_height = 3
            self._container_width = 3
        # non vault
        else:
            if myrandom.percent_chance(PROBA_BIG_ROOM_POSSIBLE):
                max_width = constants.DUNGEON_WIDTH // 3
                max_height = constants.DUNGEON_HEIGHT // 3
            else:
                max_width = constants.DUNGEON_WIDTH // 4
                max_height = constants.DUNGEON_HEIGHT // 4

            assert max_height >= 4, "Bad max_height"
            assert max_width >= 4, "Bad max_width"
            self._container_height = myrandom.randint(4, max_height)
            self._container_width = myrandom.randint(4, max_width)

        # a position for the room
        self._upper_left_x = myrandom.randint(0, constants.DUNGEON_WIDTH - self._container_width - 1)
        self._upper_left_y = myrandom.randint(0, constants.DUNGEON_HEIGHT - self._container_height - 1)

        # light level
        self._room_light_level = places.LightLevelEnum.NORMAL

        # cells include walls and walls include corners
        self._cells = {(x, y) for x in range(self._upper_left_x, self._upper_left_x + self._container_width + 1) for y in range(self._upper_left_y, self._upper_left_y + self._container_height + 1)}
        self._walls = {(x, y) for x in range(self._upper_left_x, self._upper_left_x + self._container_width + 1) for y in range(self._upper_left_y, self._upper_left_y + self._container_height + 1) if x in [self._upper_left_x, self._upper_left_x + self._container_width] or y in [self._upper_left_y, self._upper_left_y + self._container_height]}
        self._corners = {(self._upper_left_x, self._upper_left_y), (self._upper_left_x + self._container_width, self._upper_left_y), (self._upper_left_x, self._upper_left_y + self._container_height), (self._upper_left_x + self._container_width, self._upper_left_y + self._container_height)}

        # for collisions
        self._extended_cells.update({(x, y) for x in range(self._upper_left_x - 1, self._upper_left_x + self._container_width + 2) for y in range(self._upper_left_y - 1, self._upper_left_y + self._container_height + 2)})

        # set light level
        set_light_level()

        # will be created later
        self._room_features: typing.List[features.Feature] = list()
        self._room_engravings: typing.List[abstractlevel.Engraving] = list()
        self._room_heavyrocks: typing.List[heavyrocks.HeavyRock] = list()

        # will be created later
        self._room_doors: typing.List[hidden.Door] = list()

        # will be created later
        self._room_staircase: typing.Optional[typing.Tuple[int, int]] = None

    def door_is_vertical(self, door_pos: typing.Tuple[int, int]) -> bool:
        """ Says if door is on vertical wall """

        (x_pos, y_pos) = door_pos
        if (x_pos, y_pos - 1) in self._walls and (x_pos, y_pos + 1) in self._walls:
            return True
        if (x_pos - 1, y_pos) in self._walls and (x_pos - 1, y_pos) in self._walls:
            return False
        assert False, "Strange door inside this room"
        return False

    def put_staircase(self) -> None:
        """ Put randomly a staircase in room """
        x_room_pos, y_room_pos = myrandom.randint(2, self._container_width - 2), myrandom.randint(2, self._container_height - 2)
        self._room_staircase = (self.upper_left_x + x_room_pos, self.upper_left_y + y_room_pos)

    def inside_tiles(self) -> typing.List[typing.Tuple[int, int]]:
        """ Return all tiles inside room not be next to door nor to wall """

        candidates: typing.List[typing.Tuple[int, int]] = list()

        # must not be close to wall
        for x_pos in range(self.upper_left_x + 2, self.upper_left_x + self._container_width - 1):
            for y_pos in range(self.upper_left_y + 2, self.upper_left_y + self._container_height - 1):

                # must not be close to door
                found_door_close_by = False
                for (delta_x, delta_y) in MOVES_TABLE:  # A
                    new_x, new_y = x_pos + delta_x, y_pos + delta_y
                    for door in self._room_doors:  # B
                        if door.position == (new_x, new_y):
                            found_door_close_by = True
                            break  # loop B
                    if found_door_close_by:
                        break  # loop A

                if found_door_close_by:
                    continue

                candidates.append((x_pos, y_pos))

        return candidates

    def add_feature(self) -> None:
        """ Insert a feature in the room """

        candidates = self.inside_tiles()

        # select position randomly
        if not candidates:
            mylogger.LOGGER.debug("roomlevel : adding feature : no candidates")
            return

        feature_pos_choice = random.choice(candidates)

        # select feature randomly
        feature_class_choices = random.choices(features.POSSIBLE_FEATURES, features.PROBA_FEATURES)
        feature_class_choice = feature_class_choices[0]

        # put it
        abstractlevel.put_feature(feature_pos_choice, feature_class_choice, self._room_features)

    def add_engraving(self) -> None:
        """ Insert a engraving in the room """

        # all tiles inside room
        candidates = list()
        for x_pos in range(self.upper_left_x + 1, self.upper_left_x + self._container_width):
            for y_pos in range(self.upper_left_y + 1, self.upper_left_y + self._container_height):
                candidates.append((x_pos, y_pos))

        # select position randomly
        if not candidates:
            mylogger.LOGGER.debug("roomlevel : adding engraving : no candidates")
            return

        engraving_pos_choice = random.choice(candidates)

        # put it
        abstractlevel.put_engraving(engraving_pos_choice, self._room_engravings)

    def add_heavyrock(self, dungeon_level: abstractlevel.AbstractLevel) -> None:
        """ Insert a heavyrock in the room """

        candidates = self.inside_tiles()

        # remove the tiles with a feature
        feature_tiles = [f.position for f in self._room_features]
        candidates = list(set(candidates) - set(feature_tiles))

        # select position randomly
        if not candidates:
            mylogger.LOGGER.debug("roomlevel : adding heavyrock : no candidates")
            return

        heavyrock_pos_choice = random.choice(candidates)

        # select feature randomly
        heavyrock_class_choices = random.choices(heavyrocks.POSSIBLE_HEAVYROCKS, heavyrocks.PROBA_HEAVYROCKS)
        heavyrock_class_choice = heavyrock_class_choices[0]

        # put it
        abstractlevel.put_heavyrock(dungeon_level, heavyrock_pos_choice, heavyrock_class_choice, self._room_heavyrocks)

    def make_special(self, special_type: abstractlevel.SpecialRoomEnum) -> None:
        """ Add stuff in room to make it a special room """

        # all positions where to put stuff
        candidates_pos = [(x_pos, y_pos) for x_pos in range(2, self._container_width - 1) for y_pos in range(2, self._container_height - 1)]

        if special_type is abstractlevel.SpecialRoomEnum.SHOP:
            # LATER ON : send shop keeper and items etc...
            return

        if special_type is abstractlevel.SpecialRoomEnum.THRONE_ROOM:
            throne_pos = random.choice(candidates_pos)
            candidates_pos.remove(throne_pos)
            throne_feature = features.Throne(throne_pos)
            self._room_features.append(throne_feature)
            # LATER ON : send chest
            return

        if special_type is abstractlevel.SpecialRoomEnum.TREASURE_ZOO:
            # LATER ON : send some animals and some gold
            return

        if special_type is abstractlevel.SpecialRoomEnum.TEMPLE:
            altar_pos = random.choice(candidates_pos)
            candidates_pos.remove(altar_pos)
            altar_alignment = random.choice(list(alignment.AlignmentEnum))
            altar_feature = features.Altar(altar_pos, altar_alignment)
            self._room_features.append(altar_feature)
            return

        if special_type is abstractlevel.SpecialRoomEnum.GRAVEYARD:
            nb_graves = 5 + myrandom.dice("d6")
            for _ in range(nb_graves):
                if candidates_pos:  # in case no space left
                    grave_pos = random.choice(candidates_pos)
                    candidates_pos.remove(grave_pos)
                    with open("./data/headstones.dat") as file:
                        lines = file.read().splitlines()
                    inscription = random.choice(lines)
                    headstone_feature = features.HeadStone(grave_pos, inscription)
                    self._room_features.append(headstone_feature)
            # LATER ON : send undeads, corpses and some chests
            return

        if special_type is abstractlevel.SpecialRoomEnum.BARRACKS:
            # LATER ON : send some soldiers and some chests
            return

        if special_type is abstractlevel.SpecialRoomEnum.ORACLE:
            assert False, "Oracle level should not be generated"

        if special_type is abstractlevel.SpecialRoomEnum.FUNGUS_FARM:  # Type C
            # LATER ON : send some fungi
            return

        if special_type is abstractlevel.SpecialRoomEnum.LEPRECHAUN_HALL:
            # LATER ON : send some leprechauns and some gold
            return

        if special_type is abstractlevel.SpecialRoomEnum.BEEHIVE:
            # LATER ON : send some bees and some royal jelly
            return

        if special_type is abstractlevel.SpecialRoomEnum.NYMPH_GARDEN:
            # LATER ON : send some nymphs (trees if possible)
            return

        if special_type is abstractlevel.SpecialRoomEnum.ANTHOLE:
            # LATER ON : send some ants
            return

        if special_type is abstractlevel.SpecialRoomEnum.COCKATRICE_NEST:
            nb_statues = 5 + myrandom.dice("d6")
            for _ in range(nb_statues):
                if candidates_pos:  # in case no space left
                    statue_pos = random.choice(candidates_pos)
                    candidates_pos.remove(statue_pos)
                    monster = random.choice([m for m in monsters.MonsterTypeEnum if m.statue_possible])
                    statue = heavyrocks.Statue(self, statue_pos, monster)
                    self._room_heavyrocks.append(statue)
            # LATER ON : send some cockatrices
            return

        if special_type is abstractlevel.SpecialRoomEnum.GIANT_COURT:
            throne_pos = random.choice(candidates_pos)
            candidates_pos.remove(throne_pos)
            throne_feature = features.Throne(throne_pos)
            self._room_features.append(throne_feature)
            # LATER ON : send some giants and put chest
            return

        if special_type is abstractlevel.SpecialRoomEnum.DRAGON_LAIR:
            # LATER ON : send some dragons and a lot of gold
            return

    def __lt__(self, other: 'Room') -> bool:
        """ need to sort rooms for determinism """
        return self.upper_left_y < other.upper_left_y or (self.upper_left_y == other.upper_left_y and self.upper_left_x < other.upper_left_x)

    @property
    def upper_left_x(self) -> int:
        """ property """
        return self._upper_left_x

    @property
    def upper_left_y(self) -> int:
        """ property """
        return self._upper_left_y

    @property
    def container_width(self) -> int:
        """ property """
        return self._container_width

    @property
    def container_height(self) -> int:
        """ property """
        return self._container_height

    @property
    def cells(self) -> typing.Set[typing.Tuple[int, int]]:
        """ property """
        return self._cells

    @property
    def walls(self) -> typing.Set[typing.Tuple[int, int]]:
        """ property """
        return self._walls

    @property
    def corners(self) -> typing.Set[typing.Tuple[int, int]]:
        """ property """
        return self._corners

    @property
    def room_doors(self) -> typing.List[hidden.Door]:
        """ property """
        return self._room_doors

    @room_doors.setter
    def room_doors(self, room_doors: typing.List[hidden.Door]) -> None:
        """ setter """
        self._room_doors = room_doors

    @property
    def room_features(self) -> typing.List[features.Feature]:
        """ property """
        return self._room_features

    @property
    def room_engravings(self) -> typing.List[abstractlevel.Engraving]:
        """ property """
        return self._room_engravings

    @property
    def room_heavyrocks(self) -> typing.List[heavyrocks.HeavyRock]:
        """ property """
        return self._room_heavyrocks

    @property
    def room_light_level(self) -> places.LightLevelEnum:
        """ property """
        return self._room_light_level

    @property
    def room_staircase(self) -> typing.Tuple[int, int]:
        """ property """
        assert self._room_staircase, "No staircase in this room"
        return self._room_staircase


class Vault(Room):
    """ A cault. Just a smaller room """
    def __init__(self) -> None:
        Room.__init__(self, True)


class CorridorSuite(Occupier):
    """ A corridor object """

    def __init__(self, room_one: Room, room_two: Room, taboo_tiles: typing.Set[typing.Tuple[int, int]], fake: bool) -> None:

        sgn: typing.Callable[[int], int] = lambda x: 1 if x > 0 else -1 if x < 0 else 0

        def inside(x_pos: int, y_pos: int) -> bool:
            """ Are coordinates inside level ? """
            return 0 <= x_pos < constants.DUNGEON_WIDTH and 0 <= y_pos < constants.DUNGEON_HEIGHT

        def good_move(delta_x: int, delta_y: int, ideal_delta_x: int, ideal_delta_y: int) -> bool:
            """ Is move a good move ? """
            if delta_x != 0 and delta_x == -ideal_delta_x:
                return False
            if delta_y != 0 and delta_y == -ideal_delta_y:
                return False
            return True

        def orthogonal(move: typing.Tuple[int, int]) -> bool:
            """ Is the move orthogonal ? """
            x_move, y_move = move
            return x_move == 0 or y_move == 0

        #  == start of init here ==

        # Explicit init of parent class
        Occupier.__init__(self)

        self._complete = False
        self._tiles: typing.List[hidden.Corridor] = list()

        # we start from center of room one
        x_pos, y_pos = room_one.upper_left_x + room_one.container_width // 2, room_one.upper_left_y + room_one.container_height // 2
        assert (x_pos, y_pos) not in room_one.corners, "Starting from corner of room !"

        # we aim for center or room two
        x_goal, y_goal = room_two.upper_left_x + room_two.container_width // 2, room_two.upper_left_y + room_two.container_height // 2
        assert (x_goal, y_goal) not in room_one.corners, "Aiming from corner of room !"

        counter = 0
        while True:
            counter += 1
            if counter > CORRIDOR_ATTEMPTS:
                mylogger.LOGGER.debug("roomlevel : failed making corridor : being walking for too long")
                return

            # are we reaching the wall of room one ("true" wall, not corners) ?
            if (x_pos, y_pos) in room_one.walls:  # do not need to check for corners because they are taboo
                door_status = hidden.DoorStatusEnum.CLOSED
                if myrandom.percent_chance(PROBA_OPENED_DOOR):
                    door_status = hidden.DoorStatusEnum.OPENED
                elif myrandom.percent_chance(PROBA_LOCKED_DOOR):
                    door_status = hidden.DoorStatusEnum.LOCKED
                secret_door = myrandom.percent_chance(PROBA_SECRET_DOOR)
                door_one = hidden.Door((x_pos, y_pos), door_status, secret_door, hidden.DoorContextEnum.ROOM)
                door_one.vertical = room_one.door_is_vertical((x_pos, y_pos))
                # we do not want to come back to the start room
                taboo_tiles.update(room_one.cells)

            # are we reaching the wall of room two ?
            if (x_pos, y_pos) in room_two.walls:  # do not need to check for corners because they are taboo
                door_status = hidden.DoorStatusEnum.CLOSED
                if myrandom.percent_chance(PROBA_OPENED_DOOR):
                    door_status = hidden.DoorStatusEnum.OPENED
                elif myrandom.percent_chance(PROBA_LOCKED_DOOR):
                    door_status = hidden.DoorStatusEnum.LOCKED
                secret_door = myrandom.percent_chance(PROBA_SECRET_DOOR)
                door_two = hidden.Door((x_pos, y_pos), door_status, secret_door, hidden.DoorContextEnum.ROOM)
                door_two.vertical = room_two.door_is_vertical((x_pos, y_pos))
                # we are done
                break

            # we do have a piece of corridor
            if (x_pos, y_pos) not in room_one.cells:
                secret_passage = myrandom.percent_chance(PROBA_SECRET_CORRIDOR)
                corridor_tile = hidden.Corridor((x_pos, y_pos), secret_passage)
                self._tiles.append(corridor_tile)
                self._extended_cells.add((x_pos, y_pos))

            # we do not want to come back here
            taboo_tiles.add((x_pos, y_pos))

            # where can we go now ?
            ideal_dx, ideal_dy = sgn(x_goal - x_pos), sgn(y_goal - y_pos)
            poss_moves = [m for m in MOVES_TABLE if good_move(m[0], m[1], ideal_dx, ideal_dy) and (x_pos + m[0], y_pos + m[1]) not in taboo_tiles and inside(x_pos + m[0], y_pos + m[1])]

            # from door_one we can only move orthogonally
            if (x_pos, y_pos) in room_one.walls:
                poss_moves = [m for m in poss_moves if orthogonal(m)]  # we will not stay in the walls or starting room since it is taboo

            # if a move reaches a room_two wall it must be orthogonally
            # no need to check corners since it is taboo
            poss_moves = [m for m in poss_moves if not((x_pos + m[0], y_pos + m[1]) in sorted(room_two.walls) and not orthogonal(m))]

            if not poss_moves:
                mylogger.LOGGER.debug("roomlevel : failed making corridor: reached a dead end")
                return

            # prefer best move
            if (ideal_dx, ideal_dy) in poss_moves:
                mdx, mdy = ideal_dx, ideal_dy
            else:
                mdx, mdy = random.choice(poss_moves)

            # change
            x_pos += mdx
            y_pos += mdy

        if not fake:
            room_one.room_doors.append(door_one)
            room_two.room_doors.append(door_two)

        mylogger.LOGGER.debug("roomlevel : succeeded making corridor counter=%d", counter)
        self._complete = True

    @property
    def tiles(self) -> typing.List[hidden.Corridor]:
        """ property """
        return self._tiles

    @property
    def complete(self) -> bool:
        """ property """
        return self._complete

    @property
    def extended_cells(self) -> typing.Set[typing.Tuple[int, int]]:
        """ property """
        return self._extended_cells


class RoomLevel(abstractlevel.AbstractLevel):
    """ A room level object """

    def __init__(self, level_name: str, depth: int, branch: str, already_special_rooms: typing.Set[abstractlevel.SpecialRoomEnum], nb_down_stairs: int = 1, nb_up_stairs: int = 1, entry_level: bool = False) -> None:

        def rooms_indirectly_connected(a_room: Room, connections: typing.List[typing.Set[Room]]) -> typing.Set[Room]:
            """ Yields set of rooms connected to 'a_room' """
            connected_rooms = set([a_room])
            while True:
                changed = False
                for room in sorted(connected_rooms.copy()):
                    for conn in connections:
                        if room in sorted(conn):
                            other_rooms = conn - set([room])
                            other_room = random.choice(sorted(other_rooms))
                            if other_room not in connected_rooms:
                                connected_rooms.add(other_room)
                                changed = True
                if not changed:
                    break
            return connected_rooms

        #  start of init here

        abstractlevel.AbstractLevel.__init__(self, level_name, depth, branch, nb_down_stairs, nb_up_stairs, entry_level)

        assert nb_up_stairs + nb_down_stairs + 1 <= MAX_NB_ROOM, "Asking too many stairs for a  level"

        level_counter = 0
        while True:

            level_counter += 1
            if level_counter > LEVEL_ATTEMPTS:

                assert False, "roomlevel : cannot make level. Full stop."

            failed = False

            # calculate rooms to put in
            self._rooms: typing.List[Room] = list()
            room_counter = 0
            removal_counter = 0
            while True:

                room_counter += 1
                if room_counter > ROOM_ATTEMPTS:
                    mylogger.LOGGER.debug("roomlevel : making level : giving up putting room, removing bigger one")
                    sorted_rooms = sorted(self._rooms, key=lambda r: (r.container_height * r.container_width, r), reverse=True)
                    biggest = sorted_rooms[0]
                    self._rooms.remove(biggest)
                    room_counter = 0  # restart
                    removal_counter += 1
                    if removal_counter > REMOVALS_MAX:
                        break

                # make a room
                tempted_room = Room(False)

                # does it collide with others ?
                accepted = True
                for other_room in self._rooms:
                    if tempted_room.collides(other_room):
                        accepted = False
                        break

                # inserted
                if accepted:
                    self._rooms.append(tempted_room)

                # one extra room to remove later
                if len(self._rooms) >= MAX_NB_ROOM + NB_FAKE_ROOMS:
                    break

            # remove some rooms
            while True:
                if len(self._rooms) <= MIN_NB_ROOM + NB_FAKE_ROOMS:
                    break
                if myrandom.toss_coin():
                    break
                room_removed = random.choice(self._rooms)
                self._rooms.remove(room_removed)

            # room to pick in
            possible_rooms = set(self._rooms)

            # select up rooms
            self._up_rooms: typing.Set[Room] = set()
            for _ in range(nb_up_stairs):
                room = random.choice(sorted(possible_rooms))
                self._up_rooms.add(room)
                possible_rooms.remove(room)

            # select down rooms
            self._down_rooms: typing.Set[Room] = set()
            for _ in range(nb_down_stairs):
                room = random.choice(sorted(possible_rooms))
                self._down_rooms.add(room)
                possible_rooms.remove(room)

            # select entry room (used as base to make sure all connect)
            self._entry_room = next(iter(self._up_rooms)) if self._up_rooms else next(iter(self._down_rooms))

            # will be created later
            self._corridors: typing.List[CorridorSuite] = list()

            # connections between rooms
            connections: typing.List[typing.Set[Room]] = list()

            # lonely rooms (not connected)
            lonely_rooms: typing.Set[Room] = set()

            connect_counter = 0
            while True:

                # what are the lonely rooms
                lonely_rooms = {r for r in self._rooms if not [conn for conn in connections if r in conn]}

                connect_counter += 1
                if connect_counter > CONNECTION_ATTEMPTS:

                    mylogger.LOGGER.debug("roomlevel : making level : failed to create the net of corridors: so I reset")
                    # Failed to create corridors

                    # remove all corridors
                    self._corridors = list()

                    # remove connections
                    connections = list()

                    if len(self._rooms) <= MIN_NB_ROOM:
                        mylogger.LOGGER.debug("roomlevel : failed making room level : cannot remove room because only three would be left")
                        failed = True
                        break

                    # remove a random room
                    removable_rooms = lonely_rooms
                    removable_rooms -= set(self._up_rooms)
                    removable_rooms -= set(self._down_rooms)
                    if not removable_rooms:
                        mylogger.LOGGER.debug("roomlevel : failed making room level : no suitable room left to remove")
                        failed = True
                        break

                    room_removed = random.choice(sorted(removable_rooms))
                    self._rooms.remove(room_removed)

                    # update lonely rooms set
                    lonely_rooms = {r for r in self._rooms if not [conn for conn in connections if r in conn]}

                # make sure we choose as many not connected rooms as possible
                selectable_rooms_one: typing.List[Room] = list()
                selectable_rooms_two: typing.List[Room] = list()
                if len(lonely_rooms) >= 2:
                    selectable_rooms_one = sorted(lonely_rooms)
                    selectable_rooms_two = sorted(lonely_rooms)
                elif len(lonely_rooms) == 1:
                    selectable_rooms_one = sorted(lonely_rooms)
                    selectable_rooms_two = sorted(self._rooms)
                else:
                    selectable_rooms_one = self._rooms
                    selectable_rooms_two = self._rooms

                assert selectable_rooms_one, "no first room for corridor !"
                assert selectable_rooms_two, "no second room for corridor !"

                possible = list(itertools.product(selectable_rooms_one, selectable_rooms_two))
                possible = [p for p in possible if set([(p[0], p[1])]) not in connections]
                assert possible, "no couple of rooms possible to select"
                (room_one, room_two) = random.choice(possible)

                # build the list of taboo tiles
                taboo_tiles: typing.Set[typing.Tuple[int, int]] = set()
                # tiles form other rooms
                for room in self._rooms:
                    if room in [room_one, room_two]:
                        continue
                    taboo_tiles.update(room.cells)
                # corners of the two rooms
                taboo_tiles.update(room_one.corners)
                taboo_tiles.update(room_two.corners)

                # make the corridor
                corridor = CorridorSuite(room_one, room_two, taboo_tiles, False)
                if corridor.complete:

                    self._corridors.append(corridor)

                    # update list of direct connections
                    connections.append(set([room_one, room_two]))

                    # what the rooms unreachable from the upstairs
                    unreachable_rooms = [r for r in self._rooms if r not in rooms_indirectly_connected(self._entry_room, connections)]

                    if not unreachable_rooms:
                        mylogger.LOGGER.debug("roomlevel : all rooms are reachable rooms !")
                        break

            if not failed:
                break

        # remove a room with only one connection (keep corridors)
        for _ in range(NB_FAKE_ROOMS):
            rooms_shuffled = self._rooms.copy()
            random.shuffle(rooms_shuffled)
            for room in rooms_shuffled:
                if room in self._up_rooms or room in self._down_rooms:
                    continue
                if len(room.room_doors) == 1:
                    mylogger.LOGGER.debug("roomlevel : removed a room !")
                    self._rooms.remove(room)
                    break

        # add a vault if possible
        vault_counter = 0
        while True:
            vault_counter += 1
            if vault_counter > VAULT_ATTEMPTS:
                mylogger.LOGGER.debug("roomlevel : failed to add vault !")
                break
            vault = Vault()
            accepted = True
            for other_room in self._rooms:
                if vault.collides(other_room):
                    accepted = False
                    break
            if accepted:
                for corridor in self._corridors:
                    if vault.collides(corridor):
                        accepted = False
                        break
            if accepted:
                mylogger.LOGGER.debug("roomlevel : added vault !")
                self._rooms.append(vault)
                break

        #  put staircases in rooms
        for room in self._rooms:
            if room in self._up_rooms or room in self._down_rooms:
                room.put_staircase()

        # select rooms to play with
        candidates_rooms = [r for r in self._rooms if not isinstance(r, Vault) and r not in self._up_rooms and r not in self._down_rooms]

        # promote one room as shop (a room with only one door) after level 1
        possible_candidates_rooms = [r for r in candidates_rooms if len(r.room_doors) == 1]
        if depth > 1 and possible_candidates_rooms and myrandom.percent_chance(PROBA_SHOP - depth * DECREASE_PROBA_SHOP):

            # select room randomy (the smaller the better)
            relevances = [1. / (r.container_width * r.container_height) for r in possible_candidates_rooms]
            shop_special_room_choices = random.choices(possible_candidates_rooms, relevances)
            shop_special_room_choice = shop_special_room_choices[0]
            candidates_rooms.remove(shop_special_room_choice)

            # make special room
            special_room_shop = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.SHOP, (shop_special_room_choice.upper_left_x, shop_special_room_choice.upper_left_y), (shop_special_room_choice.container_width, shop_special_room_choice.container_height))
            self._level_special_rooms.append(special_room_shop)
            # add stuff into special room
            shop_special_room_choice.make_special(abstractlevel.SpecialRoomEnum.SHOP)

        # promote one room as special room (not shop) after level 1
        if depth > 1 and candidates_rooms and myrandom.percent_chance(PROBA_SPECIAL_ROOM):

            # select special room type randomy (according to difficulty and frequency)
            relevances = [(srt.frequency * 100) / (1 + abs(srt.difficulty - depth)) if srt not in already_special_rooms else 0 for srt in abstractlevel.SpecialRoomEnum]
            special_room_choices = random.choices(list(abstractlevel.SpecialRoomEnum), relevances)
            special_room_choice = special_room_choices[0]
            already_special_rooms.add(special_room_choice)

            # select room randomy (the smaller with  fewer doors the better)
            relevances = [1. / (r.container_width * r.container_height * len(r.room_doors)) for r in candidates_rooms]
            room_choices = random.choices(candidates_rooms, relevances)
            room_choice = room_choices[0]
            candidates_rooms.remove(room_choice)

            # make special room
            special_room = abstractlevel.SpecialRoom(special_room_choice, (room_choice.upper_left_x, room_choice.upper_left_y), (room_choice.container_width, room_choice.container_height))
            self._level_special_rooms.append(special_room)
            # add stuff into special room
            room_choice.make_special(special_room_choice)

        #  add features to rooms
        for room in candidates_rooms:
            if myrandom.percent_chance(PROBA_FEATURE):
                room.add_feature()

        #  add engravings to rooms
        for room in candidates_rooms:
            if myrandom.percent_chance(PROBA_ENGRAVING):
                room.add_engraving()

        #  add heavyrock to rooms
        for room in candidates_rooms:
            if myrandom.percent_chance(PROBA_HEAVYROCK):
                room.add_heavyrock(self)

        # add source light in middle of room that have a different lighting level
        for room in self._rooms:
            if room.room_light_level != places.LightLevelEnum.NORMAL:
                half_diag = int(math.sqrt((room.container_height // 2)**2 + (room.container_width // 2)**2)) + 1
                pos_light_source = room.upper_left_x + room.container_width // 2, room.upper_left_y + room.container_height // 2
                light_source = places.LightSourceRecord(level_pos=pos_light_source, light_level=room.room_light_level, light_radius=half_diag)
                self._level_light_sources.append(light_source)

        # put stairs in level from room in places where they go down
        for room in self._down_rooms:
            staircase_position = room.room_staircase
            self._downstairs.add(staircase_position)

        # put stairs in level from room in places where they go up
        for room in self._up_rooms:
            staircase_position = room.room_staircase
            self._upstairs.add(staircase_position)

            # set dungeon entry point if applicable
            if entry_level and room == self._entry_room:
                self._entry_position = staircase_position

        self._free_downstairs = self._downstairs.copy()
        self._free_upstairs = self._upstairs.copy()

    def convert_to_places(self) -> None:
        """ Converts logical just created level to table of tiles the game will use """

        # export rooms
        for room in self._rooms:

            # all tiles in room
            for x_room_pos in range(room.container_width + 1):
                for y_room_pos in range(room.container_height + 1):

                    if x_room_pos == 0 and y_room_pos == 0:
                        tile = places.Tile(places.TileTypeEnum.ROOM_UL_CORNER)

                    elif x_room_pos == 0 and y_room_pos == room.container_height:
                        tile = places.Tile(places.TileTypeEnum.ROOM_LL_CORNER)

                    elif x_room_pos == room.container_width and y_room_pos == 0:
                        tile = places.Tile(places.TileTypeEnum.ROOM_UR_CORNER)

                    elif x_room_pos == room.container_width and y_room_pos == room.container_height:
                        tile = places.Tile(places.TileTypeEnum.ROOM_LR_CORNER)

                    elif x_room_pos in [0, room.container_width]:
                        tile = places.Tile(places.TileTypeEnum.ROOM_V_WALL)

                    elif y_room_pos in [0, room.container_height]:
                        tile = places.Tile(places.TileTypeEnum.ROOM_H_WALL)

                    else:
                        tile = places.Tile(places.TileTypeEnum.GROUND_TILE)

                    place = places.Place(tile)
                    level_pos = (room.upper_left_x + x_room_pos, room.upper_left_y + y_room_pos)
                    self._data[level_pos] = place

            # export doors
            for door in room.room_doors:
                tile = places.Tile(places.TileTypeEnum.GROUND_TILE)
                place = places.Place(tile)
                place.door = door
                door_level_pos = door.position
                self._data[door_level_pos] = place

            # export features
            for feature in room.room_features:
                tile = places.Tile(places.TileTypeEnum.GROUND_TILE)
                place = places.Place(tile)
                place.feature = feature
                feature_level_pos = feature.position
                self._data[feature_level_pos] = place

            # export engravings
            for engraving in room.room_engravings:
                tile = places.Tile(places.TileTypeEnum.GROUND_TILE)
                place = places.Place(tile)
                place.inscription = engraving.inscription
                engraving_level_pos = engraving.position
                self._data[engraving_level_pos] = place

            # export heavy rocks
            for heavy_rock in room.room_heavyrocks:
                tile = places.Tile(places.TileTypeEnum.GROUND_TILE)
                place = places.Place(tile)
                place.occupant = heavy_rock
                heavy_rock_level_pos = heavy_rock.position
                self._data[heavy_rock_level_pos] = place

        # export corridors
        for corridor_suite in self._corridors:
            for corridor in corridor_suite.tiles:
                tile = places.Tile(places.TileTypeEnum.GROUND_TILE)
                place = places.Place(tile)
                place.corridor = corridor
                corridor_level_pos = corridor.position
                self._data[corridor_level_pos] = place

        # light sources are not exported

        # export stairs
        self.export_stairs()


if __name__ == '__main__':
    abstractlevel.test(RoomLevel)
