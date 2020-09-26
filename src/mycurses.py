#!/usr/bin/env python3


"""
File : mycurses.py

Interface layer to curses, the library handling the screen and the keyboard.
"""

import typing
import curses
import os

import constants
import mylogger


def color(front: int, back: int) -> int:
    """ color """
    if front == 0 and back == 0:
        return curses.color_pair(8 * 8)
    return curses.color_pair(front * 8 + back)


def curses_loop(stdscr: typing.Any, game_loop: typing.Callable[[typing.Any, typing.Any], None]) -> int:
    """ curses_loop """

    def curses_start() -> int:
        """ curses_start """

        def color_pairs() -> None:
            """ we use standard pairs """
            for i in range(0, 8):
                for j in range(0, 8):
                    if i == 0 and j == 0:
                        continue
                    curses.init_pair(8 * i + j, i, j)
            curses.init_pair(8 * 8, 0, 0)

        # terminal
        mylogger.LOGGER.info("terminal name is %s", curses.longname())

        # cursor
        prev_curs = curses.curs_set(0)

        # colors
        assert curses.has_colors(), "Need colors to run"
        curses.start_color()
        color_pairs()

        return prev_curs

    def curses_end(prev_curs: int) -> None:
        """ curses_end """

        # cursor
        curses.curs_set(prev_curs)

        # terminal
        curses.endwin()

    # curses.initscr() done by curses.wrapper()
    prev_curs = curses_start()

    # game window size
    game_height = constants.DUNGEON_HEIGHT + constants.MESSAGES_BUFFER_SIZE + constants.PROMPT_BUFFER_SIZE + constants.STATUS_INFORMATION_SIZE + constants.HELP_INFORMATION_SIZE
    game_width = constants.DUNGEON_WIDTH

    # check window can cater the game
    os_height, os_width = stdscr.getmaxyx()
    mylogger.LOGGER.info("height=%d width=%d", os_height, os_width)
    if os_height < game_height + 1:
        curses_end(prev_curs)
        return -1
    if os_width < game_width + 1:
        curses_end(prev_curs)
        return -2

    window = curses.newwin(game_height, game_width)
    stdscr.refresh()

    game_loop(stdscr, window)

    curses_end(prev_curs)
    return 0


def start(game_loop: typing.Callable[[typing.Any, typing.Any], None]) -> None:
    """ starts the curses stuff """

    # to avoid pressing escape cuasing a ine second delay
    os.environ.setdefault('ESCDELAY', '25')

    # does stdscr=curses.initscr()
    wrapper_status = curses.wrapper(curses_loop, game_loop)

    if wrapper_status == -1:
        print("Please resize to a bigger window (more height)")
    elif wrapper_status == -2:
        print("Please resize to a bigger window (more width)")


if __name__ == '__main__':
    assert False, "Do not run this script"
