#!/usr/bin/env python3


"""
File : pnethack.py

Upper level of pnethack program.

Beware : this program does not work well with font "Ubuntu Mono". Change to "Hack" font (12pt)
"""

import typing
import locale
import sys
import time
import random
import argparse
import os
import collections

import cProfile
import pstats

import constants
import mylogger
import myrandom
import gui
import mapping
import abstractlevel
import dungeon
import alignment
import race
import role
import hero
import mycurses
import sequencer
import actions
import command
import monsters
import monsters_ai

# to use debugger with wing ide
# 1) edit/preferences/Debugger/listening/accept_debug_connections  must be set
# 2) uncomment line below
# import debug.wingdbstub

# Set this to true to profile functions
PROFILE = False


def game_loop(stdscr: typing.Any, window: typing.Any) -> None:
    """ game loop """

    def get_instructions() -> None:

        # loops until game command is issued (command that affects simulation)
        while True:

            # evaluate and display mapping
            my_map.do_place_observer(current_position)
            my_map.do_light_effects()
            my_map.do_update_fov()
            my_map.do_update_has_seen()
            my_map.display(window)
            messages = my_map.check_special_rooms(my_hero.hero_alignment) + my_map.check_engravings()
            for message in messages:
                my_messages.store(message)

            # display all stored messages on screen (must be after)
            my_messages.display()

            # evaluate and display status of hero
            turn = my_sequencer.turn()
            content = my_hero.give_status(turn)
            my_status.store(content)
            my_status.display()

            # loops until input from player is correct
            while True:
                my_command = my_gui.get_command()
                if my_command:
                    break
                # bad command refresh screen
                my_messages.store("Sorry, I do not know this command - perhaps you need to be in debug mode")
                my_messages.store("Try h to get some help...")
                my_messages.display()

            # command understood treat it
            more_actions = my_command_handler.treat_player_command(my_map, my_command)

            # asked to quit
            if my_command_handler.must_quit:
                break

            # if there are actions push them on stack and activate simulation loop
            if more_actions:
                my_actions.extend(more_actions)
                break

    # ========== begin ============

    # create the whole dungeon
    my_dungeon = dungeon.Dungeon()
    mylogger.LOGGER.info("dungeon created")

    # get hero starting position
    start_level, startpos = my_dungeon.start_position()

    # create local mapping
    my_map = mapping.Mapping(start_level)

    # create hero class ('class' in a Python term)
    hero_race = random.choice(race.HeroRace.__subclasses__())
    hero_role = random.choice(role.HeroRole.__subclasses__())
    hero_class = hero.create_hero_class(hero_race, hero_role)

    # create hero
    hero_alignment_chosen = random.choice([a for a in alignment.AlignmentEnum if a.player_allowed()])
    hero_alignment = alignment.Alignment(hero_alignment_chosen)
    money_given = myrandom.dice("d20") + myrandom.dice("d20")

    my_hero = hero_class(start_level, startpos, hero_alignment, money_given)

    # create the user interface

    # engine for keyboard help
    my_keyboard_help = gui.KeyboardHelp(window, constants.MESSAGES_BUFFER_SIZE + constants.PROMPT_BUFFER_SIZE + constants.DUNGEON_HEIGHT + constants.STATUS_INFORMATION_SIZE, constants.DUNGEON_WIDTH)

    # gui singleton
    my_gui = gui.Gui(window, stdscr, my_keyboard_help, my_hero)

    # engine for messages
    my_messages = gui.Messages(window, my_gui, 0, constants.MESSAGES_BUFFER_SIZE, constants.DUNGEON_WIDTH)

    # engine for status
    my_status = gui.Status(window, constants.MESSAGES_BUFFER_SIZE + constants.PROMPT_BUFFER_SIZE + constants.DUNGEON_HEIGHT, constants.DUNGEON_WIDTH)

    # welcome message
    my_messages.store("Welcome to PNethack - Nethack in CPython")
    my_messages.store("This is YANC (Yet Another Nethack Clone)... ;-)")
    my_messages.store("Type h for help about the commands")

    # to detect change of level and new levels
    previous_level: typing.Optional[abstractlevel.AbstractLevel] = None
    visited_levels: typing.Set[abstractlevel.AbstractLevel] = set()

    # artifical intelligence tool for monsters
    my_monsters_ai = monsters_ai.MonstersAI(my_hero)

    # object that will handle command from player
    my_command_handler = command.CommandHandler(my_hero, my_messages, my_gui, my_dungeon, my_monsters_ai)

    # part that is constant for actions
    actions.Action.the_messages = my_messages

    # actions to do from command
    my_actions: typing.Deque[actions.Action] = collections.deque([])

    # sequencer
    my_sequencer = sequencer.Sequencer()

    # over all game loop
    while True:

        # simulation loop
        while True:

            # monsters standby -> ready (back)
            while monsters.Monster.standby_ones:
                monster = monsters.Monster.standby_ones.popleft()
                monsters.Monster.ready_ones.append(monster)

            # monsters rising -> ready + register
            while monsters.Monster.rising_ones:
                monster = monsters.Monster.rising_ones.popleft()
                my_sequencer.register(monster)
                my_monsters_ai.register(monster)
                monsters.Monster.ready_ones.append(monster)

            # monsters ready -> standby + action
            while monsters.Monster.ready_ones:
                monster = monsters.Monster.ready_ones.popleft()

                if my_sequencer.can_do_something(monster):

                    if monster.is_hero():
                        # in this case we need player to say what to do
                        if not my_actions:
                            get_instructions()
                        if my_command_handler.must_quit:
                            return
                        action = my_actions.popleft()
                        my_sequencer.starts_doing(monster, action)

                    else:
                        # in this case we monster A.I. to say what to do
                        action = my_monsters_ai.give_action(monster)
                        my_sequencer.starts_doing(monster, action)

                monsters.Monster.standby_ones.append(monster)

            # monsters dead -> void + unregister
            while monsters.Monster.dead_ones:
                monster = monsters.Monster.dead_ones.popleft()
                my_sequencer.unregister(monster)
                my_monsters_ai.unregister(monster)

            # makes everyone progress
            my_sequencer.tick()

            # where is my hero now ?
            current_level = my_hero.dungeon_level
            current_position = my_hero.position

            # level change
            if current_level != previous_level:

                # quitting because going to void level
                if not current_level:
                    mess = "Beware : if you go upstairs, there will be not return !"
                    my_messages.store(mess)
                    my_messages.display()
                    if my_gui.confirm("Really quit ?"):
                        mylogger.LOGGER.info("quitted by exit")
                        return
                    my_hero.move(start_level, startpos)

                # changing to a non void level
                else:

                    # TODO : remove (temporary just for test)
                    for _ in range(1):
                        random_pos = current_level.random_position()
                        monsters.Monster(monsters.MonsterTypeEnum.ORC, current_level, random_pos, 0)

                    # if quitting a level, take a note (always true except at start
                    if previous_level:
                        my_hero.note_mapping(previous_level, my_map)

                    # store messages from entering level to display
                    my_map = mapping.Mapping(current_level)
                    messages = my_map.enter_level()
                    for message in messages:
                        my_messages.store(message)

                    # if entering unknown level
                    if current_level not in visited_levels:
                        my_messages.store(f"You enter unknown level {current_level.name} at depth {current_level.depth}")
                        visited_levels.add(current_level)

                    # otherwise back to known level
                    else:
                        my_messages.store(f"You are back to level {current_level.name} at depth {current_level.depth}")
                        # remember from last visit
                        has_seen = my_hero.recall_mapping(current_level)
                        my_map.has_seen = has_seen

            # store for next time
            previous_level = current_level


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--seed', required=False, help='force seed value to have a reproducible behaviour')
    parser.add_argument('-d', '--debug', required=False, help='mode debug to test stuff', action='store_true')
    parser.add_argument('-g', '--generate', required=False, help='generate a type of level to test it')
    parser.add_argument('-D', '--depth', required=False, help='when generating a level give the depth')
    parser.add_argument('-l', '--load', required=False, help='load a special level to test it')
    parser.add_argument('-r', '--reverse', required=False, help='start level in stairs going down instead of up', action='store_true')
    parser.add_argument('-f', '--force', required=False, help='force log file to be simpler', action='store_true')
    args = parser.parse_args()
    # print(args)

    force_simpler = args.force
    mylogger.start_logger(force_simpler)
    mylogger.LOGGER.info("Normal start.=============================")

    if args.seed:
        myrandom.force_seed(int(args.seed))

    if args.debug:
        print("Setting Debug/Explore mode")
        mylogger.LOGGER.info("Setting Debug/Explore mode")
        time.sleep(0.5)
        constants.DEBUG_MODE = True

    if args.generate:
        print("Generating a type of level")
        mylogger.LOGGER.info("Generating a type of level")
        constants.GENERATE_LEVEL = args.generate
        if args.depth:
            constants.GENERATE_LEVEL_DEPTH = int(args.depth)
        if args.reverse:
            constants.REVERSE = True

    if args.load:
        print("Loading a level from file")
        mylogger.LOGGER.info("Loading level from file")
        constants.LOAD_LEVEL = args.load
        if args.reverse:
            constants.REVERSE = True

    # random god
    myrandom.start_random()

    # important to work in unicode !
    locale.setlocale(locale.LC_ALL, '')

    # load constants from file to constants module
    constants.load_config()

    mycurses.start(game_loop)

    mylogger.LOGGER.info("Normal termination.===========================")


if __name__ == '__main__':

    if 'WINGDB_ACTIVE' in os.environ:
        print("Ok to debug")
        time.sleep(1)

    # this if script too slow and profile it
    if PROFILE:
        PR = cProfile.Profile()

        PR.enable()  # uncomment to have profile stats
    main()
    if PROFILE:
        PR.disable()

        # stats
        PS = pstats.Stats(PR)
        PS.strip_dirs()
        PS.sort_stats('time')
        PS.print_stats()  # uncomment to have profile stats

    sys.exit(0)
