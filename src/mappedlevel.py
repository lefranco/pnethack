#!/usr/bin/env python3


"""
File : mappedlevel.py

Random creation of a mappped level - read from a .lev file.
"""

import typing
import random
import math

import constants
import myjson
import mylogger
import places
import alignment
import features
import heavyrocks
import hidden
import abstractlevel
import monsters

NB_LAYERS = 5


class Layer:
    """ A layer of the level to make differences """

    def __init__(self) -> None:
        self.moats: typing.List[typing.Tuple[int, int]] = list()
        self.grounds: typing.List[typing.Tuple[int, int]] = list()


class MappedLevel(abstractlevel.AbstractLevel):
    """ A mapped level object """

    def __init__(self, level_name: str, depth: int, branch: str, already_special_rooms: typing.Set[abstractlevel.SpecialRoomEnum], nb_down_stairs: int = 1, nb_up_stairs: int = 1, entry_level: bool = False) -> None:  # pylint: disable=unused-argument

        def read_level(loaded_content: typing.Dict[str, typing.Any]) -> None:
            """ reads a level from json file """

            sgn: typing.Callable[[int], int] = lambda x: 1 if x > 0 else -1 if x < 0 else 0
            dist: typing.Callable[[int, int, int, int], int] = lambda x1, y1, x2, y2: (x2 - x1) ** 2 + (y2 - y1) ** 2

            def put_stuff(x_pos: int, y_pos: int, layer: int, thing: str) -> None:
                """ put in layer """
                if thing == "moat":
                    self._layers[layer].moats.append((x_pos, y_pos))
                elif thing == "ground":
                    self._layers[layer].grounds.append((x_pos, y_pos))

            for item_name in loaded_content:

                item_data = loaded_content[item_name]
                item_type = item_data["type"]
                item_layer = item_data["layer"] if "layer" in item_data else 1

                if item_type == "stain":
                    upper_left = item_data["upper_left"]
                    x_startpos = upper_left["x"]
                    y_pos = upper_left["y"]
                    patterns = item_data["patterns"]
                    for pattern in patterns:
                        x_pos = x_startpos
                        for tile in pattern:
                            if tile == '1':
                                put_stuff(x_pos, y_pos, item_layer, item_data["use"])
                            x_pos += 1
                        y_pos += 1

                elif item_type == "line":
                    upper_left = item_data["upper_left"]
                    length = item_data["length"]
                    orientation = item_data["orientation"]
                    if orientation == "vertical":
                        x_pos = upper_left["x"]
                        for offset in range(length):
                            y_pos = upper_left["y"] + offset
                            put_stuff(x_pos, y_pos, item_layer, item_data["use"])
                    if orientation == "horizontal":
                        y_pos = upper_left["y"]
                        for offset in range(length):
                            x_pos = upper_left["x"] + offset
                            put_stuff(x_pos, y_pos, item_layer, item_data["use"])

                elif item_type == "ellipse":
                    center = item_data["center"]
                    size = item_data["size"]
                    for y_rel in range(- size["height"] // 2, size["height"] // 2 + 1):
                        delta_y = y_rel / (size["height"] // 2)
                        for x_rel in range(-size["width"] // 2, size["width"] // 2 + 1):
                            delta_x = x_rel / (size["width"] // 2)
                            if delta_x ** 2 + delta_y ** 2 <= 1:
                                x_pos = center["x"] + x_rel
                                y_pos = center["y"] + y_rel
                                put_stuff(x_pos, y_pos, item_layer, item_data["use"])

                elif item_type == "polygon":
                    points = item_data["points"]
                    y_min = min([p["y"] for p in points])
                    y_max = max([p["y"] for p in points])
                    for y_line in range(y_min, y_max + 1):
                        intersects = list()
                        for num1, _ in enumerate(points):
                            num2 = num1 + 1 if num1 < len(points) - 1 else 0
                            point1 = points[num1]
                            point2 = points[num2]
                            if min(point1["y"], point2["y"]) <= y_line < max(point1["y"], point2["y"]):
                                if point2["y"] == point1["y"]:
                                    continue
                                kval = (point2["x"] - point1["x"]) / (point2["y"] - point1["y"])
                                x_inter = point1["x"] + kval * (y_line - point1["y"])
                                # need to store point number too for further usage
                                intersects.append((x_inter, num1))
                        intersect_sorted = sorted(intersects)
                        fill = True
                        for num in range(len(intersect_sorted) - 1):
                            if intersect_sorted[num][0] == intersect_sorted[num + 1][0]:
                                num1 = intersect_sorted[num][1]
                                # need sometimes to consider the other point of the edge
                                if points[num1]["y"] == y_line:
                                    num1 = num1 + 1 if num1 < len(points) - 1 else 0
                                num2 = intersect_sorted[num + 1][1]
                                if points[num2]["y"] == y_line:
                                    num2 = num2 + 1 if num2 < len(points) - 1 else 0
                                if sgn(points[num1]["y"] - y_line) != sgn(points[num2]["y"] - y_line):
                                    continue
                            if fill:
                                x_start = math.ceil(intersect_sorted[num][0])
                                x_end = math.floor(intersect_sorted[num + 1][0])
                                for x_pos in range(x_start, x_end + 1):
                                    put_stuff(x_pos, y_line, item_layer, item_data["use"])
                            fill = not fill

                # from now on layer is not relevant

                elif item_type == "room":
                    upper_left = item_data["upper_left"]
                    size = item_data["size"]
                    fake = item_data["fake"] if "fake" in item_data else False
                    if not fake:
                        for x_pos in range(upper_left["x"] + 1, upper_left["x"] + size["width"]):
                            for y_pos in range(upper_left["y"] + 1, upper_left["y"] + size["height"]):
                                self._insiderooms.append((x_pos, y_pos))
                        for y_pos in [upper_left["y"], upper_left["y"] + size["height"]]:
                            for x_pos in range(upper_left["x"], upper_left["x"] + size["width"] + 1):
                                self._wallscorners.append((x_pos, y_pos))
                        for x_pos in [upper_left["x"], upper_left["x"] + size["width"]]:
                            for y_pos in range(upper_left["y"], upper_left["y"] + size["height"] + 1):
                                self._wallscorners.append((x_pos, y_pos))
                    if "special_type" in item_data:
                        # Type A
                        if item_data["special_type"] == "shop":
                            special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.SHOP, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]))
                        # Type B
                        elif item_data["special_type"] == "throne":
                            special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.THRONE_ROOM, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]))
                        elif item_data["special_type"] == "zoo":
                            special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.TREASURE_ZOO, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]))
                        elif item_data["special_type"] == "temple":
                            if item_data["alignment"] == "lawful":
                                special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.TEMPLE, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]), alignment.AlignmentEnum.LAWFUL)
                            elif item_data["alignment"] == "neutral":
                                special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.TEMPLE, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]), alignment.AlignmentEnum.NEUTRAL)
                            elif item_data["alignment"] == "chaotic":
                                special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.TEMPLE, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]), alignment.AlignmentEnum.CHAOTIC)
                            elif item_data["alignment"] == "unaligned":
                                special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.TEMPLE, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]), alignment.AlignmentEnum.UNALIGNED)
                            else:
                                assert False, "Unknown alignment for temple"
                        elif item_data["special_type"] == "graveyard":
                            special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.GRAVEYARD, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]))
                        elif item_data["special_type"] == "barracks":
                            special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.BARRACKS, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]))
                        elif item_data["special_type"] == "oracle":
                            special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.ORACLE, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]))
                        # Type C
                        elif item_data["special_type"] == "fungus":
                            special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.FUNGUS_FARM, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]))
                        elif item_data["special_type"] == "leprechaun":
                            special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.LEPRECHAUN_HALL, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]))
                        elif item_data["special_type"] == "beehive":
                            special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.BEEHIVE, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]))
                        elif item_data["special_type"] == "nymph":
                            special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.NYMPH_GARDEN, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]))
                        elif item_data["special_type"] == "ant":
                            special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.ANTHOLE, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]))
                        elif item_data["special_type"] == "cockatrice":
                            special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.COCKATRICE_NEST, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]))
                        elif item_data["special_type"] == "giant":
                            special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.GIANT_COURT, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]))
                        elif item_data["special_type"] == "dragon":
                            special_room = abstractlevel.SpecialRoom(abstractlevel.SpecialRoomEnum.DRAGON_LAIR, (upper_left["x"], upper_left["y"]), (size["width"], size["height"]))
                        else:
                            assert False, "Unknown special room type"
                        self._level_special_rooms.append(special_room)

                elif item_type == "wall":
                    upper_left = item_data["upper_left"]
                    length = item_data["length"]
                    orientation = item_data["orientation"]
                    if orientation == "vertical":
                        x_pos = upper_left["x"]
                        for offset in range(length):
                            y_pos = upper_left["y"] + offset
                            self._wallscorners.append((x_pos, y_pos))
                    if orientation == "horizontal":
                        y_pos = upper_left["y"]
                        for offset in range(length):
                            x_pos = upper_left["x"] + offset
                            self._wallscorners.append((x_pos, y_pos))

                elif item_type == "stairs":
                    direction = item_data["direction"]
                    position = item_data["position"]
                    x_pos = position["x"]
                    y_pos = position["y"]
                    staircase = (x_pos, y_pos)
                    if direction == "down":
                        self._downstairs.add(staircase)
                    if direction == "up":
                        self._upstairs.add(staircase)

                elif item_type == "corridor":
                    starts = item_data["starts"]
                    x_pos = starts["x"]
                    y_pos = starts["y"]
                    points = item_data["points"]
                    find_corridor = dict()
                    for point in points:
                        x_endpos = point["x"]
                        y_endpos = point["y"]
                        while (x_pos, y_pos) != (x_endpos, y_endpos):
                            corridor = hidden.Corridor((x_pos, y_pos), False)
                            self._level_corridors.append(corridor)
                            find_corridor[(x_pos, y_pos)] = corridor
                            nearest_x, nearest_y = x_pos, y_pos
                            for delta_x in [-1, 0, 1]:
                                for delta_y in [-1, 0, 1]:
                                    neigh_x, neigh_y = x_pos + delta_x, y_pos + delta_y
                                    if dist(neigh_x, neigh_y, x_endpos, y_endpos) < dist(nearest_x, nearest_y, x_endpos, y_endpos):
                                        nearest_x, nearest_y = neigh_x, neigh_y
                            x_pos, y_pos = nearest_x, nearest_y
                    if "secret_points" in item_data:
                        secret_points = item_data["secret_points"]
                        for point in secret_points:
                            x_pos = point["x"]
                            y_pos = point["y"]
                            assert (x_pos, y_pos) in find_corridor, "Where is this secret passage ?"
                            old_corridor = find_corridor[(x_pos, y_pos)]
                            self._level_corridors.remove(old_corridor)
                            new_corridor = hidden.Corridor((x_pos, y_pos), True)
                            self._level_corridors.append(new_corridor)

                elif item_type == "door":
                    position = item_data["position"]
                    x_pos = position["x"]
                    y_pos = position["y"]
                    self._wallscorners.append((x_pos, y_pos))
                    is_open = ("open" in item_data and item_data["open"])
                    door_status = hidden.DoorStatusEnum.OPENED if is_open else hidden.DoorStatusEnum.CLOSED
                    is_secret = ("secret" in item_data and item_data["secret"])
                    door = hidden.Door((x_pos, y_pos), door_status, is_secret, hidden.DoorContextEnum.MAZE)
                    self._level_doors.append(door)

                elif item_type == "feature":
                    feature_type = item_data["feature_type"]
                    position = item_data["position"]
                    x_pos = position["x"]
                    y_pos = position["y"]
                    if feature_type == "fountain":
                        fountain = features.Fountain((x_pos, y_pos))
                        self.level_features.append(fountain)
                    elif feature_type == "sink":
                        sink = features.Sink((x_pos, y_pos))
                        self.level_features.append(sink)
                    elif feature_type == "throne":
                        throne = features.Throne((x_pos, y_pos))
                        self.level_features.append(throne)
                    elif feature_type == "altar":
                        alignment_name = item_data["alignment"]
                        if alignment_name == "lawful":
                            altar = features.Altar((x_pos, y_pos), alignment.AlignmentEnum.LAWFUL)
                            self.level_features.append(altar)
                        elif alignment_name == "neutral":
                            altar = features.Altar((x_pos, y_pos), alignment.AlignmentEnum.NEUTRAL)
                            self.level_features.append(altar)
                        elif alignment_name == "chaotic":
                            altar = features.Altar((x_pos, y_pos), alignment.AlignmentEnum.CHAOTIC)
                            self.level_features.append(altar)
                        elif alignment_name == "unaligned":
                            altar = features.Altar((x_pos, y_pos), alignment.AlignmentEnum.UNALIGNED)
                            self.level_features.append(altar)
                        else:
                            assert False, f"What is this alignment {alignment_name} ?"
                    elif feature_type == "headstone":
                        inscription = item_data["inscription"]
                        headstone = features.HeadStone((x_pos, y_pos), inscription)
                        self.level_features.append(headstone)
                    else:
                        assert False, f"What is this feature : {feature_type} ? "

                elif item_type == "engraving":
                    position = item_data["position"]
                    x_pos = position["x"]
                    y_pos = position["y"]
                    inscription = item_data["inscription"]
                    engraving = abstractlevel.Engraving((x_pos, y_pos), inscription)
                    self.level_engravings.append(engraving)

                elif item_type == "heavyrock":
                    heavyrock_type = item_data["heavyrock_type"]
                    position = item_data["position"]
                    x_pos = position["x"]
                    y_pos = position["y"]
                    if heavyrock_type == "statue":
                        statue_of_name = item_data["statue_of"]
                        statue_of = monsters.MonsterTypeEnum.find(statue_of_name)
                        statue = heavyrocks.Statue(self, (x_pos, y_pos), statue_of)
                        self.level_heavyrocks.append(statue)
                    if heavyrock_type == "boulder":
                        boulder = heavyrocks.Boulder(self, (x_pos, y_pos))
                        self.level_heavyrocks.append(boulder)

                else:
                    assert False, "Unknown item type"

        #  start of init here

        abstractlevel.AbstractLevel.__init__(self, level_name, depth, branch, nb_down_stairs, nb_up_stairs, entry_level)

        self._layers: typing.Dict[int, Layer] = dict()
        for ind_layer in range(NB_LAYERS + 1):
            layer = Layer()
            self._layers[ind_layer] = layer

        self._level_corridors: typing.List[hidden.Corridor] = list()
        self._level_doors: typing.List[hidden.Door] = list()

        self._insiderooms: typing.List[typing.Tuple[int, int]] = list()
        self._wallscorners: typing.List[typing.Tuple[int, int]] = list()

        # json machinery
        json_reader = myjson.JsonReader(f"{level_name}.lev")
        loaded_content = json_reader.extract()
        read_level(loaded_content)

        mylogger.LOGGER.info("mappedlevel : made level")

        # put stairs in level from room in places where they go up
        if entry_level:
            # specify reverse to enter a generated level by downstairs
            if self._upstairs and not constants.REVERSE:
                entry_staircase = random.choice(sorted(self._upstairs))
            elif self._downstairs:  # case we debug a level
                entry_staircase = random.choice(sorted(self._downstairs))
            # could be the dungeon entry point
            self._entry_position = entry_staircase

        self._free_downstairs = self._downstairs.copy()
        self._free_upstairs = self._upstairs.copy()

    def convert_to_places(self) -> None:
        """ Converts logical just created level to table of tiles the game will use """

        def read_layer(layer: int) -> None:
            # moats
            for moat_pos in self._layers[layer].moats:
                tile = places.Tile(places.TileTypeEnum.MOAT)
                place = places.Place(tile)
                self._data[moat_pos] = place

            # grounds
            for ground_pos in self._layers[layer].grounds:
                tile = places.Tile(places.TileTypeEnum.GROUND_TILE)
                place = places.Place(tile)
                self._data[ground_pos] = place

        for layer in range(NB_LAYERS, 0, -1):
            read_layer(layer)

        # inside rooms
        for insideroom_pos in self._insiderooms:
            tile = places.Tile(places.TileTypeEnum.GROUND_TILE)
            place = places.Place(tile)
            self._data[insideroom_pos] = place

        #  walls / corners : decide final shape
        for wallcorner_pos in self._wallscorners:
            x_pos, y_pos = wallcorner_pos
            north = (x_pos, y_pos - 1) in self._wallscorners
            east = (x_pos + 1, y_pos) in self._wallscorners
            south = (x_pos, y_pos + 1) in self._wallscorners
            west = (x_pos - 1, y_pos) in self._wallscorners
            nb_connect = len([p for p in [north, east, south, west] if p])
            if nb_connect == 0:
                assert False, f"Lonely wall in {x_pos}, {y_pos}"
            elif nb_connect == 1:
                if north:
                    tile = places.Tile(places.TileTypeEnum.MAZE_I_0_CORNER)
                elif east:
                    tile = places.Tile(places.TileTypeEnum.MAZE_I_90_CORNER)
                elif south:
                    tile = places.Tile(places.TileTypeEnum.MAZE_I_180_CORNER)
                elif west:
                    tile = places.Tile(places.TileTypeEnum.MAZE_I_270_CORNER)
            elif nb_connect == 2:
                if north and south:
                    tile = places.Tile(places.TileTypeEnum.MAZE_V_WALL)
                elif west and east:
                    tile = places.Tile(places.TileTypeEnum.MAZE_H_WALL)
                elif north and east:
                    tile = places.Tile(places.TileTypeEnum.MAZE_L_0_CORNER)
                elif east and south:
                    tile = places.Tile(places.TileTypeEnum.MAZE_L_90_CORNER)
                elif south and west:
                    tile = places.Tile(places.TileTypeEnum.MAZE_L_180_CORNER)
                elif west and north:
                    tile = places.Tile(places.TileTypeEnum.MAZE_L_270_CORNER)
            elif nb_connect == 3:
                if not north:
                    tile = places.Tile(places.TileTypeEnum.MAZE_T_0_CORNER)
                elif not east:
                    tile = places.Tile(places.TileTypeEnum.MAZE_T_90_CORNER)
                elif not south:
                    tile = places.Tile(places.TileTypeEnum.MAZE_T_180_CORNER)
                elif not west:
                    tile = places.Tile(places.TileTypeEnum.MAZE_T_270_CORNER)
            elif nb_connect == 4:
                tile = places.Tile(places.TileTypeEnum.MAZE_X_CORNER)

            place = places.Place(tile)
            self._data[wallcorner_pos] = place

        # layer zero that takes precedence on rooms
        layer = 0
        read_layer(layer)

        # export corridors
        for corridor in self._level_corridors:
            corridor_pos = corridor.position
            tile = places.Tile(places.TileTypeEnum.GROUND_TILE)
            place = places.Place(tile)
            place.corridor = corridor
            self._data[corridor_pos] = place

        # export doors
        for door in self._level_doors:
            door_pos = door.position
            tile = places.Tile(places.TileTypeEnum.GROUND_TILE)
            place = places.Place(tile)
            wall_there = self._data[door_pos]
            door.vertical = (wall_there.tile.mytype == places.TileTypeEnum.MAZE_V_WALL)
            place.door = door
            self._data[door_pos] = place

        # export features
        for feature in self._level_features:
            feature_level_pos = feature.position
            feature_place = self._data[feature_level_pos]
            assert feature_place.tile.mytype is places.TileTypeEnum.GROUND_TILE, "feature not on ground tile"
            feature_place.feature = feature

        # export engravings
        for engraving in self._level_engravings:
            engraving_level_pos = engraving.position
            engraving_place = self._data[engraving_level_pos]
            assert engraving_place.tile.mytype is places.TileTypeEnum.GROUND_TILE, "engraving not on ground tile"
            engraving_place.inscription = engraving.inscription

        # export heavyrocks
        for heavyrock in self._level_heavyrocks:
            heavyrock_level_pos = heavyrock.position
            heavyrock_place = self._data[heavyrock_level_pos]
            assert heavyrock_place.tile.mytype is places.TileTypeEnum.GROUND_TILE, "heavyrock not on ground tile"
            assert heavyrock_place.feature is None, "Putting a heavyrock on a feature"
            heavyrock_place.occupant = heavyrock

        # export stairs
        self.export_stairs()


if __name__ == '__main__':
    assert False, "Do not run this script"
