#!/usr/bin/env python3


"""
File : command.py

Handle any command issued by the player
"""

import typing

import mylogger
import constants
import mapping
import dungeon
import hidden
import gui
import actions
import monsters
import monsters_ai
import heavyrocks


COMMAND_2_DIRECTION = {
    gui.CommandEnum.MOVE_DOWN: actions.DirectionEnum.DOWN,
    gui.CommandEnum.MOVE_UP: actions.DirectionEnum.UP,
    gui.CommandEnum.MOVE_LEFT: actions.DirectionEnum.LEFT,
    gui.CommandEnum.MOVE_RIGHT: actions.DirectionEnum.RIGHT,
    gui.CommandEnum.MOVE_UPLEFT: actions.DirectionEnum.UPLEFT,
    gui.CommandEnum.MOVE_UPRIGHT: actions.DirectionEnum.UPRIGHT,
    gui.CommandEnum.MOVE_DOWNLEFT: actions.DirectionEnum.DOWNLEFT,
    gui.CommandEnum.MOVE_DOWNRIGHT: actions.DirectionEnum.DOWNRIGHT,
    gui.CommandEnum.MOVE_CLIMB_UP: actions.DirectionEnum.CLIMB_UP,
    gui.CommandEnum.MOVE_CLIMB_DOWN: actions.DirectionEnum.CLIMB_DOWN
}


class CommandHandler:
    """ The class to handle a command """

    def __init__(self, the_hero: typing.Any, the_messages: gui.Messages, the_gui: gui.Gui, the_dungeon: dungeon.Dungeon, the_monsters_ai: monsters_ai.MonstersAI):
        self._the_hero = the_hero
        self._the_messages = the_messages
        self._the_gui = the_gui
        self._the_dungeon = the_dungeon
        self._monsters_ai = the_monsters_ai
        self._must_quit = False

    def move(self, direction: actions.DirectionEnum) -> typing.List[actions.Action]:
        """ Handles move command... returns list of actions... """

        cur_pos = self._the_hero.position
        cur_level = self._the_hero.dungeon_level

        # vertical move
        if direction == actions.DirectionEnum.CLIMB_UP:
            if not cur_level.data[cur_pos].may_climb_up():
                self._the_messages.store("You cannot climb up from here")
                return list()

        if direction == actions.DirectionEnum.CLIMB_DOWN:
            if not cur_level.data[cur_pos].may_climb_down():
                self._the_messages.store("You cannot climb down from here")
                return list()

        return [actions.Action(actions.ActionEnum.MOVE, the_monster=self._the_hero, the_direction=direction)]

    def climb(self, direction: actions.DirectionEnum) -> typing.List[actions.Action]:
        """ Handles move command... returns list of actions... """
        return [actions.Action(actions.ActionEnum.CLIMB, the_monster=self._the_hero, the_direction=direction)]

    def attack(self, monster: monsters.Monster) -> typing.List[actions.Action]:
        """ Handles attack command... returns list of actions... """
        return [actions.Action(actions.ActionEnum.ATTACK, the_monster=self._the_hero, the_victim=monster)]

    def push(self, direction: actions.DirectionEnum) -> typing.List[actions.Action]:
        """ Handles push command... returns list of actions... """
        return [actions.Action(actions.ActionEnum.PUSH, the_monster=self._the_hero, the_direction=direction)]

    def open_door(self) -> typing.List[actions.Action]:
        """ Handles open door command... returns list of actions... """

        x_pos, y_pos = self._the_hero.position
        possible_doors = list()
        for (delta_x, delta_y) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_pos = (x_pos + delta_x, y_pos + delta_y)
            door = self._the_hero.dungeon_level.data[new_pos].door
            if door and door.status in [hidden.DoorStatusEnum.CLOSED, hidden.DoorStatusEnum.LOCKED]:
                possible_doors.append(door)

        if not possible_doors:
            self._the_messages.store("Sorry. I see no closed door nearby...")
            return list()

        if len(possible_doors) > 1:
            status, direction_command = self._the_gui.select_direction(gui.DirectionModeEnum.DIR_ORTHOGONAL, "You must select the door to open...")
            if not status:
                return list()
            direction = COMMAND_2_DIRECTION[direction_command]
            delta_x, delta_y = actions.DIRECTION_2_DELTA[direction]
            new_pos = (x_pos + delta_x, y_pos + delta_y)
            door = self._the_hero.dungeon_level.data[new_pos].door
            if not door:
                self._the_messages.store("Sorry. No closed door in this direction...")
                return list()
            if door.status not in [hidden.DoorStatusEnum.CLOSED, hidden.DoorStatusEnum.LOCKED]:
                self._the_messages.store("Sorry. This door is not closed...")
                return list()
        else:
            door = possible_doors[0]

        return [actions.Action(actions.ActionEnum.OPEN_DOOR, the_monster=self._the_hero, the_door=door)]

    def close_door(self) -> typing.List[actions.Action]:
        """ Handles close door command... returns list of actions... """

        x_pos, y_pos = self._the_hero.position
        possible_doors = list()
        for (delta_x, delta_y) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_pos = (x_pos + delta_x, y_pos + delta_y)
            door = self._the_hero.dungeon_level.data[new_pos].door
            if door and door.status == hidden.DoorStatusEnum.OPENED:
                possible_doors.append(door)

        if not possible_doors:
            self._the_messages.store("Sorry. I see no open door nearby...")
            return list()

        if len(possible_doors) > 1:
            status, direction_command = self._the_gui.select_direction(gui.DirectionModeEnum.DIR_ORTHOGONAL, "You must select the door to close...")
            if not status:
                return list()

            direction = COMMAND_2_DIRECTION[direction_command]
            delta_x, delta_y = actions.DIRECTION_2_DELTA[direction]
            new_pos = (x_pos + delta_x, y_pos + delta_y)
            door = self._the_hero.dungeon_level.data[new_pos].door
            if not door:
                self._the_messages.store("Sorry. No open door in this direction...")
                return list()
            if door.status is not hidden.DoorStatusEnum.OPENED:
                self._the_messages.store("Sorry. This door is not open...")
                return list()
        else:
            door = possible_doors[0]

        door_pos = door.position
        occupant = self._the_hero.dungeon_level.data[door_pos].occupant
        if occupant:
            if isinstance(occupant, monsters.Monster):
                self._the_messages.store("You can't. There is a monster in the way...")
            else:
                self._the_messages.store("You can't. There is a something in the way...")
            return list()
        if self._the_hero.dungeon_level.data[door_pos].items:
            self._the_messages.store("You can't. There is at least one object in the way...")
            return list()

        return [actions.Action(actions.ActionEnum.CLOSE_DOOR, the_monster=self._the_hero, the_door=door)]

    def kick_stuff(self) -> typing.List[actions.Action]:
        """ Handles kick command... returns list of actions... """

        x_pos, y_pos = self._the_hero.position

        # lets see if there are doors nearby
        possible_doors = list()
        for (delta_x, delta_y) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_pos = (x_pos + delta_x, y_pos + delta_y)
            door = self._the_hero.dungeon_level.data[new_pos].door
            if door and door.status in [hidden.DoorStatusEnum.CLOSED, hidden.DoorStatusEnum.LOCKED]:
                possible_doors.append(door)

        # lets see if there are objects nearby
        possible_items_deltas = list()
        for (delta_x, delta_y) in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            new_pos = (x_pos + delta_x, y_pos + delta_y)
            items = self._the_hero.dungeon_level.data[new_pos].items
            if items:
                possible_items_deltas.append((delta_x, delta_y))

        # not possible
        if not (possible_doors or possible_items_deltas):
            self._the_messages.store("Sorry. I see no closed door nor no items nearby...")
            return list()

        # let's see if there is still ambiguity
        door = None
        item_delta = None

        # single possibility door
        if len(possible_doors) == 1 and not possible_items_deltas:
            door = possible_doors[0]

        # single possibility items
        elif len(possible_items_deltas) == 1 and not possible_doors:
            # must find direction
            item_delta = possible_items_deltas[0]
            for direction in actions.DIRECTION_2_DELTA:
                if actions.DIRECTION_2_DELTA[direction] == item_delta:
                    break

        # must ask direction
        else:

            # direction
            status, direction_command = self._the_gui.select_direction(gui.DirectionModeEnum.DIR_ORTHOGONAL | gui.DirectionModeEnum.DIR_DIAGONAL, "Kick in what direction ?")
            if not status:
                return list()

            # what is there
            direction = COMMAND_2_DIRECTION[direction_command]
            delta_x, delta_y = actions.DIRECTION_2_DELTA[direction]
            new_pos = (x_pos + delta_x, y_pos + delta_y)

            # check in game
            if new_pos not in self._the_hero.dungeon_level.data:
                return list()

            # check door there
            door = self._the_hero.dungeon_level.data[new_pos].door
            # door must be closed
            if door and door.status not in [hidden.DoorStatusEnum.CLOSED, hidden.DoorStatusEnum.LOCKED]:
                door = None

            # check item there
            items = self._the_hero.dungeon_level.data[new_pos].items
            if items:
                item_delta = (delta_x, delta_y)

        # ok now we know what to do

        # must kick a door
        if door:
            return [actions.Action(actions.ActionEnum.KICK, the_monster=self._the_hero, the_door=door)]

        if item_delta:
            return [actions.Action(actions.ActionEnum.KICK, the_monster=self._the_hero, the_direction=direction)]

        return list()

    def pickup_stuff(self) -> typing.List[actions.Action]:
        """ Handles pick up command... returns list of actions... """

        hero_pos = self._the_hero.position
        place = self._the_hero.dungeon_level.data[hero_pos]
        local_items = place.items
        if not local_items:
            self._the_messages.store("There is nothing here to pick up")
            return list()
        items_select = {i.whatis(): i for i in local_items}
        if len(items_select) > 1:
            sel = self._the_gui.select_some("What do you want to pick up ?", items_select, True)
            if not sel:
                return list()
        else:
            sel = set(items_select.values())

        return [actions.Action(actions.ActionEnum.PICK_UP, the_monster=self._the_hero, the_item=i) for i in sel]

    def drop_stuff(self) -> typing.List[actions.Action]:
        """ Handles drop command... returns list of actions... """

        if not self._the_hero.backsack.list_content():
            self._the_messages.store("You do not have anything to drop!")
            return list()

        items_select = {i.whatis(): i for i in self._the_hero.backsack.list_content()}
        if len(items_select) > 1:
            sel = self._the_gui.select_some("What do you want to drop ?", items_select, True)
            if not sel:
                return list()
        else:
            sel = set(items_select.values())

        return [actions.Action(actions.ActionEnum.DROP, the_monster=self._the_hero, the_item=i) for i in sel]

    def throw_stuff(self) -> typing.List[actions.Action]:
        """ Handles throw command... returns list of actions... """

        if not self._the_hero.backsack.list_content():
            self._the_messages.store("You do not have anything to throw!")
            return list()

        status, direction_command = self._the_gui.select_direction(gui.DirectionModeEnum.DIR_ORTHOGONAL | gui.DirectionModeEnum.DIR_DIAGONAL, "In which direction ?")
        if not status:
            return list()

        items_select = {i.whatis(): i for i in self._the_hero.backsack.list_content()}
        if len(items_select) > 1:
            item = self._the_gui.select_one("What do you want to throw ?", 0, items_select, True)
            if not item:
                return list()
        else:
            item = list(items_select.values())[0]

        direction = COMMAND_2_DIRECTION[direction_command]
        action = actions.Action(actions.ActionEnum.THROW, the_monster=self._the_hero, the_direction=direction, the_item=item)
        return [action]

    def search(self) -> typing.List[actions.Action]:
        """ Handles search command... returns list of actions... """

        x_pos, y_pos = self._the_hero.position
        possible_secrets = list()
        for (delta_x, delta_y) in [(-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
            new_pos = (x_pos + delta_x, y_pos + delta_y)
            if self._the_hero.dungeon_level.data[new_pos].may_have_secret():
                possible_secrets.append(new_pos)
            door = self._the_hero.dungeon_level.data[new_pos].door
            if door and door.secret:
                possible_secrets.append(new_pos)
            corridor = self._the_hero.dungeon_level.data[new_pos].corridor
            if corridor:
                possible_secrets.append(new_pos)

        if not possible_secrets:
            self._the_messages.store("Sorry. I see nowhere to search nearby...")
            return list()

        action = actions.Action(actions.ActionEnum.SEARCH, the_monster=self._the_hero)
        return [action]

    def rest(self) -> typing.List[actions.Action]:
        """ Handles rest command... returns list of actions... """

        assert self._the_hero
        action = actions.Action(actions.ActionEnum.REST, the_monster=self._the_hero)
        return [action]

    def handle_in_game_command(self, my_command: gui.CommandEnum) -> typing.List[actions.Action]:
        """ Handles an in game command returns True if accepted """

        # move command
        if my_command.is_move_command(gui.DirectionModeEnum.DIR_ORTHOGONAL | gui.DirectionModeEnum.DIR_DIAGONAL | gui.DirectionModeEnum.DIR_VERTICAL | gui.DirectionModeEnum.DIR_STAND):

            direction = COMMAND_2_DIRECTION[my_command]

            if direction is actions.DirectionEnum.CLIMB_UP:
                new_pos = self._the_hero.position
                if not self._the_hero.dungeon_level.data[new_pos].may_climb_up():
                    self._the_messages.store(f"I see no stairs going up here!")
                    return list()
                return self.climb(direction)

            if direction is actions.DirectionEnum.CLIMB_DOWN:
                new_pos = self._the_hero.position
                if not self._the_hero.dungeon_level.data[new_pos].may_climb_down():
                    self._the_messages.store(f"I see no stairs going down here!")
                    return list()
                return self.climb(direction)

            # new pos
            x_pos, y_pos = self._the_hero.position
            delta_x, delta_y = actions.DIRECTION_2_DELTA[direction]
            new_pos = (x_pos + delta_x, y_pos + delta_y)

            # not in level : internal error
            if new_pos not in self._the_hero.dungeon_level.data:
                self._the_messages.store(f"Internal error : could try to move out of level !")
                return list()

            occupant = self._the_hero.dungeon_level.data[new_pos].occupant
            if occupant:

                # monster there : standard attack
                if isinstance(occupant, monsters.Monster):
                    return self.attack(occupant)

                # boulder : push it
                if isinstance(occupant, heavyrocks.Boulder):
                    self._the_messages.store(f"Ok, let's push that boulder !")
                    return self.push(direction)

                # other cases like hitting a statue : let the hero loose some time

            return self.move(direction)

        # open door command
        if my_command == gui.CommandEnum.OPEN_DOOR:
            return self.open_door()

        # close door command
        if my_command == gui.CommandEnum.CLOSE_DOOR:
            return self.close_door()

        # kick command
        if my_command == gui.CommandEnum.KICK:
            return self.kick_stuff()

        # pick up command
        if my_command == gui.CommandEnum.PICK_UP:
            return self.pickup_stuff()

        # drop command
        if my_command == gui.CommandEnum.DROP:
            return self.drop_stuff()

        # throw command
        if my_command == gui.CommandEnum.THROW:
            return self.throw_stuff()

        # search command
        if my_command == gui.CommandEnum.SEARCH:
            return self.search()

        # rest command
        if my_command == gui.CommandEnum.REST:
            return self.rest()

        assert False, "Problem with command !!!"
        return list()

    def treat_player_command(self, my_map: mapping.Mapping, my_command: gui.CommandEnum) -> typing.List[actions.Action]:
        """ command from player : return 'played' if actually played """

        # game version
        if my_command == gui.CommandEnum.GAME_VERSION:
            self._the_messages.store(f"Pnethack (nethack clone in python) version {constants.VERSION}")
            self._the_messages.display()
            return list()

        # load game
        if my_command == gui.CommandEnum.LOAD_GAME:
            self._the_messages.store("Load game not implemented sorry")
            self._the_messages.display()
            return list()

        # save game
        if my_command == gui.CommandEnum.SAVE_GAME:
            self._the_messages.store("Save game not implemented sorry")
            self._the_messages.display()
            return list()

        # quit game
        if my_command == gui.CommandEnum.QUIT_GAME:
            self._the_messages.store("Beware : if you quit, there will be not return !")
            self._the_messages.display()
            if not self._the_gui.confirm("Really quit ?"):
                return list()
            # goodbye message
            self._the_messages.store("See you soon!")
            self._must_quit = True
            mylogger.LOGGER.info("asked to quit")
            return list()

        # help command simple
        if my_command == gui.CommandEnum.QUICK_HELP:
            with open("./info/HELP.TXT", "r") as filepointer:
                help_content = filepointer.readlines()
            self._the_gui.show_content(help_content, True)
            return list()

        # help command complete
        if my_command == gui.CommandEnum.DETAILED_HELP:
            cur_pos = 0
            poss_table = {"Monsters": "./info/HELP_MONSTERS.TXT",
                          "Tiles": "./info/HELP_TILES.TXT",
                          "Objects": "./info/HELP_ITEMS.TXT",
                          "Overall map": "./info/HELP_MAP.TXT"}
            while True:
                file_name = self._the_gui.select_one("Detailed help about what ?", cur_pos, poss_table, True)
                if not file_name:
                    break
                with open(file_name, "r") as filepointer:
                    help_content = filepointer.readlines()
                    self._the_gui.show_content(help_content, True)
                cur_pos = list(poss_table.values()).index(file_name)
            return list()

        # what is command
        if my_command == gui.CommandEnum.WHAT_IS:

            status, new_pos = self._the_gui.select_position("?", "Select tile")
            if not status:
                return list()

            x_pos, y_pos = new_pos
            if not my_map.knows(x_pos, y_pos):
                self._the_messages.store(f"You have not visited this position yet!")
                return list()

            place = my_map.level.data[new_pos]
            is_there = place.all_that_is_there()
            for mess in is_there:
                self._the_messages.store(mess)
            return list()

        # debug - show path
        if my_command == gui.CommandEnum.SHOW_PATH:
            self._the_messages.store("Revealing path to hero for first monster")
            length = my_map.level.show_path(self._monsters_ai, self._the_hero.position)
            self._the_messages.store(f"Length is {length}")
            return list()

        # debug - show los
        if my_command == gui.CommandEnum.SHOW_LOS:
            self._the_messages.store("Revealing line of sight to hero for first monster")
            success = my_map.level.show_los(self._monsters_ai, self._the_hero.position)
            self._the_messages.store(f"Sees : {success}")
            return list()

        # debug - show secret
        if my_command == gui.CommandEnum.SHOW_SECRET:
            self._the_messages.store("Revealing secret doors and passages")
            my_map.level.reveal_secret()
            return list()

        # debug - map level
        if my_command == gui.CommandEnum.MAP_LEVEL:
            self._the_messages.store("Mapping level")
            my_map.set_knows_all()
            return list()

        # debug - create monster
        if my_command == gui.CommandEnum.CREATE_MONSTER:
            self._the_messages.store(f"Create monster in wizard mode command not implemented yet sorry")
            return list()

        # debug - intra level teleport
        if my_command == gui.CommandEnum.INTRA_LEVEL_TELEPORT:

            status, new_pos = self._the_gui.select_position("@", "Enter teleportation destination")
            if not status:
                return list()

            if not self._the_hero.dungeon_level.data[new_pos].may_access():
                self._the_messages.store("Nope. You cannot go there !")
                return list()

            if self._the_hero.dungeon_level.data[new_pos].occupant:
                self._the_messages.store("Nope. There is something or someone on the way !")
                return list()

            self._the_hero.moves_to(self._the_hero.dungeon_level, new_pos)
            self._the_messages.store(f"Ok, teleported to tile {new_pos}")

            # still need a rest after teleport
            action = actions.Action(actions.ActionEnum.REST, the_monster=self._the_hero)
            return [action]

        # debug - trans level teleport
        if my_command == gui.CommandEnum.TRANS_LEVEL_TELEPORT:

            reply = self._the_gui.input_string("Enter level to go to like '1D' : ", 5)
            new_level = self._the_dungeon.get_level(reply)
            if new_level is None:
                self._the_messages.store(f"Sorry, no such level as '{reply}'")
                return list()

            new_pos = new_level.random_position()
            self._the_hero.move(new_level, new_pos)
            self._the_messages.store(f"Ok, teleported to level {new_level.name} to random position tile {new_pos}")

            # still need a rest after teleport
            action = actions.Action(actions.ActionEnum.REST, the_monster=self._the_hero)
            return [action]

        # debug - wish
        if my_command == gui.CommandEnum.MAKE_WISH:
            self._the_messages.store(f"Wish wizard mode command not implemented yet sorry")
            return list()

        # debug - show attributes
        if my_command == gui.CommandEnum.SHOW_ATTRIBUTES:
            enlightment_content = self._the_hero.enlightment()
            self._the_gui.show_content(enlightment_content, False)
            return list()

        # special : recall messages (go up)
        if my_command == gui.CommandEnum.PREVIOUS_MESSAGES:
            self._the_messages.upper()
            self._the_messages.display()
            return list()

        # special : recall messages (go down)
        if my_command == gui.CommandEnum.NEXT_MESSAGES:
            self._the_messages.lower()
            self._the_messages.display()
            return list()

        # special : inventory command
        if my_command == gui.CommandEnum.INVENTORY:
            inventory_content_str = str(self._the_hero.backsack)
            inventory_content = inventory_content_str.split("\n")
            self._the_gui.show_content(inventory_content, True)
            return list()

        # normal game command
        return self.handle_in_game_command(my_command)

    @property
    def must_quit(self) -> bool:
        """ property """
        return self._must_quit


if __name__ == '__main__':
    assert False, "Do not run this script"
