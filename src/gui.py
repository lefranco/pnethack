#!/usr/bin/env python3


"""
File : gui.py

General user interface to the player.
"""

import typing
import enum
import curses
import curses.panel

import mycurses
import constants

# Seems these values are subject to change
# Needed to have diagonal moves on a laptop
CONTROL_PLUS_RIGHT = 560
CONTROL_PLUS_LEFT = 545
CONTROL_PLUS_DOWN = 525
CONTROL_PLUS_UP = 566

# help window height
CONTENT_WINDOW_HEIGHT = 30
CONTENT_WINDOW_WIDTH = 70

# menu window height
CONTENT_MENU_HEIGHT = 21


@enum.unique
class DirectionModeEnum(enum.Flag):
    """ Mode of direction selection """

    DIR_ORTHOGONAL = enum.auto()  # MOVE_DOWN, MOVE_UP, MOVE_LEFT, MOVE_RIGHT
    DIR_DIAGONAL = enum.auto()  # MOVE_UPLEFT, MOVE_RIGHT, MOVE_DOWNLEFT, MOVE_DOWNRIGHT
    DIR_VERTICAL = enum.auto()    # MOVE_CLIMB_UP, MOVE_CLIMB_DOWN
    DIR_STAND = enum.auto()        # MOVE_STAND

    def __str__(self) -> str:
        elements = list()
        if self & DirectionModeEnum.DIR_ORTHOGONAL:
            elements.append("orthogonal")
        if self & DirectionModeEnum.DIR_DIAGONAL:
            elements.append("diagonal")
        if self & DirectionModeEnum.DIR_VERTICAL:
            elements.append("verical")
        if self & DirectionModeEnum.DIR_VERTICAL:
            elements.append("stand")
        return " ".join(elements)


@enum.unique
class CommandEnum(enum.Enum):
    """ Command """

    # move commands
    MOVE_DOWN = enum.auto()
    MOVE_UP = enum.auto()
    MOVE_LEFT = enum.auto()
    MOVE_RIGHT = enum.auto()
    MOVE_UPLEFT = enum.auto()
    MOVE_UPRIGHT = enum.auto()
    MOVE_DOWNLEFT = enum.auto()
    MOVE_DOWNRIGHT = enum.auto()
    MOVE_CLIMB_UP = enum.auto()
    MOVE_CLIMB_DOWN = enum.auto()
    MOVE_STAND = enum.auto()

    # in game commands
    OPEN_DOOR = enum.auto()
    CLOSE_DOOR = enum.auto()
    SEARCH = enum.auto()
    KICK = enum.auto()
    PICK_UP = enum.auto()
    THROW = enum.auto()
    DROP = enum.auto()
    REST = enum.auto()

    # information commands
    INVENTORY = enum.auto()
    WHAT_IS = enum.auto()

    # meta commands
    GAME_VERSION = enum.auto()
    LOAD_GAME = enum.auto()
    SAVE_GAME = enum.auto()
    QUIT_GAME = enum.auto()

    # help commands
    QUICK_HELP = enum.auto()
    DETAILED_HELP = enum.auto()

    # special gui commands
    PREVIOUS_MESSAGES = enum.auto()
    NEXT_MESSAGES = enum.auto()

    # wizard mode commands
    SHOW_PATH = enum.auto()
    SHOW_LOS = enum.auto()
    SHOW_SECRET = enum.auto()
    MAP_LEVEL = enum.auto()
    CREATE_MONSTER = enum.auto()
    INTRA_LEVEL_TELEPORT = enum.auto()
    TRANS_LEVEL_TELEPORT = enum.auto()
    MAKE_WISH = enum.auto()
    SHOW_ATTRIBUTES = enum.auto()

    def is_move_command(self, direction_mode: DirectionModeEnum) -> bool:
        """ Is it a move command corresponding to the mode ? """
        if direction_mode & DirectionModeEnum.DIR_ORTHOGONAL:
            if self in [CommandEnum.MOVE_DOWN, CommandEnum.MOVE_UP, CommandEnum.MOVE_LEFT, CommandEnum.MOVE_RIGHT]:
                return True
        if direction_mode & DirectionModeEnum.DIR_DIAGONAL:
            if self in [CommandEnum.MOVE_UPLEFT, CommandEnum.MOVE_UPRIGHT, CommandEnum.MOVE_DOWNLEFT, CommandEnum.MOVE_DOWNRIGHT]:
                return True
        if direction_mode & DirectionModeEnum.DIR_VERTICAL:
            if self in [CommandEnum.MOVE_CLIMB_UP, CommandEnum.MOVE_CLIMB_DOWN]:
                return True
        if direction_mode & DirectionModeEnum.DIR_STAND:
            if self is CommandEnum.MOVE_STAND:
                return True
        return False


def key2command(key: int) -> typing.Optional[CommandEnum]:
    """ Unifomized acces point to keyboard for game command """

    if key == curses.KEY_DOWN or key == ord("2"):
        return CommandEnum.MOVE_DOWN

    if key == curses.KEY_UP or key == ord("8"):
        return CommandEnum.MOVE_UP

    if key == curses.KEY_LEFT or key == ord("4"):
        return CommandEnum.MOVE_LEFT

    if key == curses.KEY_RIGHT or key == ord("6"):
        return CommandEnum.MOVE_RIGHT

    if key == curses.KEY_HOME or key == ord("7") or key == CONTROL_PLUS_LEFT:
        return CommandEnum.MOVE_UPLEFT

    if key == curses.KEY_PPAGE or key == ord("9") or key == CONTROL_PLUS_UP:
        return CommandEnum.MOVE_UPRIGHT

    if key == curses.KEY_END or key == ord("1") or key == CONTROL_PLUS_DOWN:
        return CommandEnum.MOVE_DOWNLEFT

    if key == curses.KEY_NPAGE or key == ord("3") or key == CONTROL_PLUS_RIGHT:
        return CommandEnum.MOVE_DOWNRIGHT

    if key == ord("<"):
        return CommandEnum.MOVE_CLIMB_UP

    if key == ord(">"):
        return CommandEnum.MOVE_CLIMB_DOWN

    # open / close door
    if key == ord("o"):
        return CommandEnum.OPEN_DOOR
    if key == ord("c"):
        return CommandEnum.CLOSE_DOOR
    # search
    if key == ord("s"):
        return CommandEnum.SEARCH
    # kick
    if key == ord("k"):
        return CommandEnum.KICK
    # pick up
    if key == ord("p"):
        return CommandEnum.PICK_UP
    # throw
    if key == ord("t"):
        return CommandEnum.THROW
    # drop
    if key == ord("d"):
        return CommandEnum.DROP
    # rest
    if key == 32:
        return CommandEnum.REST

    # inventory
    if key == ord("i"):
        return CommandEnum.INVENTORY

    # game version
    if key == ord("v"):
        return CommandEnum.GAME_VERSION
    # load game
    if key == 12:  # ctrl-L
        return CommandEnum.LOAD_GAME
    # save game
    if key == 19:  # ctrl-S
        return CommandEnum.SAVE_GAME
    # quit game
    if key == 17:  # ctrl-Q
        return CommandEnum.QUIT_GAME

    # what is
    if key == ord("?"):
        return CommandEnum.WHAT_IS

    # help
    if key == ord("h"):
        return CommandEnum.QUICK_HELP
    if key == ord("H"):
        return CommandEnum.DETAILED_HELP

    # Special GUI commands
    if key == 16:  # ctrl-P
        return CommandEnum.PREVIOUS_MESSAGES
    if key == 14:  # ctrl-N
        return CommandEnum.NEXT_MESSAGES

    # Retricted debug commands
    if key == 1:  # ctrl-A
        if constants.DEBUG_MODE:
            return CommandEnum.SHOW_PATH
        return None
    if key == 2:  # ctrl-B
        if constants.DEBUG_MODE:
            return CommandEnum.SHOW_LOS
        return None
    if key == 5:  # ctrl-E
        if constants.DEBUG_MODE:
            return CommandEnum.SHOW_SECRET
        return None
    if key == 6:  # ctrl-F
        if constants.DEBUG_MODE:
            return CommandEnum.MAP_LEVEL
        return None
    if key == 7:  # ctrl-G
        if constants.DEBUG_MODE:
            return CommandEnum.CREATE_MONSTER
        return None
    if key == 20:  # ctrl-T
        if constants.DEBUG_MODE:
            return CommandEnum.INTRA_LEVEL_TELEPORT
        return None
    if key == 22:  # ctrl-V
        if constants.DEBUG_MODE:
            return CommandEnum.TRANS_LEVEL_TELEPORT
        return None
    if key == 23:  # ctrl-W
        if constants.DEBUG_MODE:
            return CommandEnum.MAKE_WISH
        return None
    if key == 8:  # ctrl-H
        if constants.DEBUG_MODE:
            return CommandEnum.SHOW_ATTRIBUTES
        return None

    return None


class KeyboardHelp:
    """ Little message with available keys """

    def __init__(self, stdscr: typing.Any, position: int, max_width: int) -> None:
        self._stdscr = stdscr
        self._position = position
        self._max_width = max_width

    def display(self, message: str) -> None:
        """ Put message """
        assert len(message) < self._max_width, f"Please shorter message for help : '{message}'"
        attr = mycurses.color(curses.COLOR_GREEN, curses.COLOR_BLACK)
        self._stdscr.addstr(self._position, 0, (self._max_width - len(message) - 1) * " ")
        self._stdscr.addstr(self._position, self._max_width - len(message) - 1, message, attr)
        self._stdscr.refresh()

    def clear(self) -> None:
        """ Clear message """
        self._stdscr.addstr(self._position, 0, (self._max_width - 1) * " ")
        self._stdscr.refresh()


class Gui:
    """ GUI toolbox """

    def __init__(self, window: typing.Any, stdscr: typing.Any, keyboard_help: KeyboardHelp, hero: typing.Any) -> None:
        self._window = window
        self._stdscr = stdscr
        self._keyboard_help = keyboard_help
        self._hero = hero

        self._background_panel = curses.panel.new_panel(self._window)

        self._cursor_win = curses.newwin(1, 2)
        self._cursor_panel = curses.panel.new_panel(self._cursor_win)

    def get_command(self) -> typing.Optional[CommandEnum]:
        """ Get on game command """

        key = self._stdscr.getch()
        return key2command(key)

    def prompt_user_noreturn(self, prompt: str) -> str:
        """ Direct iput from user - this is low level method """

        input_win = curses.newwin(constants.PROMPT_BUFFER_SIZE, len(prompt) + 2, constants.MESSAGES_BUFFER_SIZE, 0)
        input_win.addstr(0, 0, prompt, curses.A_BOLD)
        input_win.refresh()

        help_message = "Hit a key"
        self._keyboard_help.display(help_message)

        # get input
        curses.echo()
        key_input = self._stdscr.getch()
        assert isinstance(key_input, int), "User input not integer"
        user_input = chr(key_input)
        curses.noecho()

        # done
        self._keyboard_help.clear()
        input_win.clear()
        input_win.refresh()

        return user_input

    def prompt_user_return(self, prompt: str, answer_len: int) -> str:
        """ Direct iput from user - this is low level method """

        input_win = curses.newwin(constants.PROMPT_BUFFER_SIZE, len(prompt) + answer_len + 2, constants.MESSAGES_BUFFER_SIZE, 0)
        input_win.addstr(0, 0, prompt, curses.A_BOLD)
        input_win.refresh()

        help_message = "Enter a string and finish with RETURN"
        self._keyboard_help.display(help_message)

        # get input
        curses.echo()
        user_input = input_win.getstr()
        if isinstance(user_input, int):
            user_input = str(user_input)
        elif isinstance(user_input, bytes):
            user_input = user_input.decode()
        curses.noecho()

        # done
        self._keyboard_help.clear()
        input_win.clear()
        input_win.refresh()

        return user_input

    def select_direction(self, direction_mode: DirectionModeEnum, information_message: str) -> typing.Tuple[bool, CommandEnum]:
        """ Asks user a direction """

        input_win = curses.newwin(constants.PROMPT_BUFFER_SIZE, len(information_message) + 1, constants.MESSAGES_BUFFER_SIZE, 0)
        input_win.addstr(0, 0, information_message, curses.A_BOLD)
        input_win.refresh()

        help_message = f"Use the usual move commands ({direction_mode})"
        self._keyboard_help.display(help_message)

        while True:

            # wait keypress
            key = self._stdscr.getch()

            # specific keys first

            if key == 27:  # escape
                self._keyboard_help.clear()
                input_win.clear()
                input_win.refresh()
                return False, CommandEnum.MOVE_STAND

            command = key2command(key)
            if command is None:
                continue

            if command.is_move_command(direction_mode):
                self._keyboard_help.clear()
                input_win.clear()
                input_win.refresh()
                return True, command

    def select_position(self, cursor_shape: str, information_message: str) -> typing.Tuple[bool, typing.Tuple[int, int]]:
        """ Ask user a position """

        input_win = curses.newwin(constants.PROMPT_BUFFER_SIZE, len(information_message) + 1, constants.MESSAGES_BUFFER_SIZE, 0)
        input_win.addstr(0, 0, information_message, curses.A_BOLD)
        input_win.refresh()

        help_message = "Use left right, up and down to move, space/validate (esc/abort)"
        self._keyboard_help.display(help_message)

        (x_pos, y_pos) = self._hero.position
        self._cursor_win.addstr(0, 0, cursor_shape)

        while True:

            self._cursor_panel.move(constants.MESSAGES_BUFFER_SIZE + constants.PROMPT_BUFFER_SIZE + y_pos, x_pos)
            curses.panel.update_panels()
            curses.doupdate()

            # wait keypress
            key = self._stdscr.getch()

            # specific keys first

            if key == 27:  # escape
                self._keyboard_help.clear()
                input_win.clear()
                input_win.refresh()
                return False, (0, 0)

            if key == 32:  # space
                self._keyboard_help.clear()
                input_win.clear()
                input_win.refresh()
                return True, (x_pos, y_pos)

            command = key2command(key)
            if command is None:
                continue

            if not command.is_move_command(DirectionModeEnum.DIR_ORTHOGONAL):
                continue

            if command is CommandEnum.MOVE_DOWN:
                y_pos += 1
                if y_pos > constants.DUNGEON_HEIGHT - 1:
                    curses.beep()  # does not work here ???
                    curses.flash()
                    y_pos = constants.DUNGEON_HEIGHT - 1

            if command is CommandEnum.MOVE_UP:
                y_pos -= 1
                if y_pos < 0:
                    curses.beep()  # does not work here ???
                    curses.flash()
                    y_pos = 0

            if command is CommandEnum.MOVE_LEFT:
                x_pos -= 1
                if x_pos < 0:
                    curses.beep()  # does not work here ???
                    curses.flash()
                    x_pos = 0

            if command is CommandEnum.MOVE_RIGHT:
                x_pos += 1
                if x_pos > constants.DUNGEON_WIDTH - 1:
                    curses.beep()  # does not work here ???
                    curses.flash()
                    x_pos = constants.DUNGEON_WIDTH - 1

    def confirm(self, mess: str) -> bool:
        """ Asks user a confirmation  """

        input_key = self.prompt_user_noreturn(mess + " (y/n)")
        return input_key in ["Y", "y"]

    def input_string(self, prompt: str, answer_len: int) -> str:
        """ String input from user : no box """

        return self.prompt_user_return(prompt, answer_len)

    def show_content(self, content: typing.List[str], clear_after: bool) -> None:
        """ Display a list of strings on screen : with box """

        help_message = "Use [page]up and [page]down left and right to move, (esc/abort)"
        self._keyboard_help.display(help_message)

        # store size
        nb_lines_present = len(content)
        nb_lines_used = min(nb_lines_present, CONTENT_WINDOW_HEIGHT)
        nb_cols_present = max([len(l) for l in content])
        nb_cols_used = min(nb_cols_present, CONTENT_WINDOW_WIDTH)
        x_pos = 0
        y_pos = 0

        # display

        help_win = curses.newwin(nb_lines_used + 2, nb_cols_used + 2, 1, 1)

        while True:

            help_win.clear()

            # put text in window
            line_number = 1
            for (line_number, line) in enumerate(content[y_pos: y_pos + nb_lines_used]):
                help_win.addstr(line_number + 1, 1, line[x_pos: x_pos + nb_cols_used], curses.A_BOLD)

            help_win.box()

            # put current page
            cur_pos = round((y_pos + nb_lines_used) * 100 / nb_lines_present)
            page_info = f"{cur_pos} %"
            help_win.addstr(nb_lines_used + 1, nb_cols_used - len(page_info) - 1, page_info)

            # display
            help_win.refresh()
            self._window.refresh()

            # wait keypress
            key = self._stdscr.getch()

            # specific keys first

            if key == 27:  # escape
                break

            if key == 338:  # page down
                y_pos += CONTENT_WINDOW_HEIGHT
                if y_pos > nb_lines_present - CONTENT_WINDOW_HEIGHT:
                    y_pos = nb_lines_present - CONTENT_WINDOW_HEIGHT

            if key == 339:  # page up
                y_pos -= CONTENT_WINDOW_HEIGHT
                if y_pos < 0:
                    y_pos = 0

            command = key2command(key)

            if command is CommandEnum.MOVE_DOWN:
                y_pos += 1
                if y_pos > max(0, nb_lines_present - CONTENT_WINDOW_HEIGHT):
                    curses.beep()  # does not work here ???
                    curses.flash()
                    y_pos = max(0, nb_lines_present - CONTENT_WINDOW_HEIGHT)

            if command is CommandEnum.MOVE_UP:
                y_pos -= 1
                if y_pos < 0:
                    curses.beep()  # does not work here ???
                    curses.flash()
                    y_pos = 0

            if command is CommandEnum.MOVE_RIGHT:
                x_pos += 1
                if x_pos > max(0, nb_cols_present - CONTENT_WINDOW_WIDTH):
                    curses.beep()  # does not work here ???
                    curses.flash()
                    x_pos = max(0, nb_cols_present - CONTENT_WINDOW_WIDTH)

            if command is CommandEnum.MOVE_LEFT:
                x_pos -= 1
                if x_pos < 0:
                    curses.beep()  # does not work here ???
                    curses.flash()
                    x_pos = 0

        # done
        if clear_after:
            self._stdscr.clear()
            self._stdscr.refresh()

    def select_one(self, information_message: str, position: int, table: typing.Dict[str, typing.Any], clear_after: bool) -> typing.Any:
        """ Selection from user : exactly one possible """

        input_win = curses.newwin(constants.PROMPT_BUFFER_SIZE, len(information_message) + 1, constants.MESSAGES_BUFFER_SIZE, 0)
        input_win.addstr(0, 0, information_message, curses.A_BOLD)
        input_win.refresh()

        help_message = "Use [page]up and [page]down to move, return/validate (esc/abort)"
        self._keyboard_help.display(help_message)

        nb_lines_present = len(table)
        nb_lines_used = min(nb_lines_present, CONTENT_MENU_HEIGHT)
        nb_cols = max([len(l) for l in table])

        curs_pos = position  # cursor position
        y_pos = max(0, curs_pos - nb_lines_used // 2 - 1)  # position of top element in list
        loc_curs_pos = curs_pos - y_pos

        menu_win = curses.newwin(nb_lines_used + 2, nb_cols + 2, constants.MESSAGES_BUFFER_SIZE + 1, 2)
        menu_panel = curses.panel.new_panel(menu_win)

        while True:

            menu_win.clear()

            # put text in menu
            for i, text in enumerate(table):
                if y_pos <= i < y_pos + nb_lines_used:
                    mode = curses.A_REVERSE if i == curs_pos else curses.A_NORMAL
                    menu_win.addstr(i - y_pos + 1, 1, text, mode)
                    if i == curs_pos:
                        final_sel = table[text]
            cur_pos1 = round((y_pos + nb_lines_used) * 100 / nb_lines_present)
            page_info = f"{cur_pos1} %"
            menu_win.addstr(nb_lines_used + 1, nb_cols - len(page_info) - 1, page_info)

            curses.panel.update_panels()
            curses.doupdate()

            # wait keypress
            key = self._stdscr.getch()

            # specific keys first

            if key == 27:  # escape
                final_sel = None
                break

            if key == 10:  # return
                for i, text in enumerate(table):
                    if i == curs_pos:
                        final_sel = table[text]
                        break
                break

            if key == 338:  # page down
                y_pos += CONTENT_MENU_HEIGHT
                if y_pos > nb_lines_present - nb_lines_used:
                    y_pos = nb_lines_present - nb_lines_used

            if key == 339:  # page up
                y_pos -= CONTENT_MENU_HEIGHT
                if y_pos < 0:
                    y_pos = 0

            command = key2command(key)

            if command is CommandEnum.MOVE_DOWN:
                loc_curs_pos += 1
                if loc_curs_pos > nb_lines_used - 1:
                    loc_curs_pos = nb_lines_used - 1
                    y_pos += 1
                    if y_pos > nb_lines_present - nb_lines_used:
                        curses.beep()  # does not work here ???
                        curses.flash()
                        y_pos = nb_lines_present - nb_lines_used
                curs_pos = y_pos + loc_curs_pos

            if command is CommandEnum.MOVE_UP:
                loc_curs_pos -= 1
                if loc_curs_pos < 0:
                    loc_curs_pos = 0
                    y_pos -= 1
                    if y_pos < 0:
                        curses.beep()  # does not work here ???
                        curses.flash()
                        y_pos = 0
                curs_pos = y_pos + loc_curs_pos

        menu_panel.hide()
        input_win.clear()
        input_win.refresh()
        self._keyboard_help.clear()

        # done
        if clear_after:
            self._stdscr.clear()
            self._stdscr.refresh()

        return final_sel

    def select_some(self, information_message: str, table: typing.Dict[str, typing.Any], clear_after: bool) -> typing.Any:
        """ Selection from user : more or less than one possible """

        input_win = curses.newwin(constants.PROMPT_BUFFER_SIZE, len(information_message) + 1, constants.MESSAGES_BUFFER_SIZE, 0)
        input_win.addstr(0, 0, information_message, curses.A_BOLD)
        input_win.refresh()

        help_message = "[page]up and [page]down, espace/select, a/ll n/one return/validate (esc/abort)"
        self._keyboard_help.display(help_message)

        nb_lines_present = len(table)
        nb_lines_used = min(nb_lines_present, CONTENT_MENU_HEIGHT)
        nb_cols = max([len(l) for l in table])

        curs_pos = 0  # cursor position
        y_pos = 0  # position of top element in list
        loc_curs_pos = 0

        selected: typing.Set[typing.Any] = set()

        menu_win = curses.newwin(nb_lines_used + 2, nb_cols + 2, constants.MESSAGES_BUFFER_SIZE + 1, 2)
        menu_panel = curses.panel.new_panel(menu_win)

        # dict number -> element selected
        selection = dict()
        for i, text in enumerate(table):
            elt = table[text]
            selection[i] = elt

        while True:

            menu_win.clear()

            for i, text in enumerate(table):
                if y_pos <= i < y_pos + nb_lines_used:
                    mode = curses.A_REVERSE if i == curs_pos else curses.A_NORMAL
                    mode += curses.A_BOLD if selection[i] in selected else 0
                    menu_win.addstr(i - y_pos + 1, 1, text, mode)
            cur_pos1 = round((y_pos + nb_lines_used) * 100 / nb_lines_present)
            page_info = f"{cur_pos1} %"
            menu_win.addstr(nb_lines_used + 1, nb_cols - len(page_info) - 1, page_info)

            curses.panel.update_panels()
            curses.doupdate()

            # wait keypress
            key = self._stdscr.getch()

            # specific keys first

            if key == 27:  # escape
                final_sel = None
                break

            if key == 10:  # return
                final_sel = selected
                break

            if key == ord("a"):
                selected = set(selection.values())

            if key == ord("n"):
                selected = set()

            if key == 32:  # space
                # Toggle
                elt = selection[curs_pos]
                if elt in selected:
                    selected.remove(elt)
                else:
                    selected.add(elt)

            if key == 338:  # page down
                y_pos += CONTENT_MENU_HEIGHT
                if y_pos > nb_lines_present - nb_lines_used:
                    y_pos = nb_lines_present - nb_lines_used

            if key == 339:  # page up
                y_pos -= CONTENT_MENU_HEIGHT
                if y_pos < 0:
                    y_pos = 0

            command = key2command(key)

            if command is CommandEnum.MOVE_DOWN:
                loc_curs_pos += 1
                if loc_curs_pos > nb_lines_used - 1:
                    loc_curs_pos = nb_lines_used - 1
                    y_pos += 1
                    if y_pos > nb_lines_present - nb_lines_used:
                        curses.beep()  # does not work here ???
                        curses.flash()
                        y_pos = nb_lines_present - nb_lines_used
                curs_pos = y_pos + loc_curs_pos

            if command is CommandEnum.MOVE_UP:
                loc_curs_pos -= 1
                if loc_curs_pos < 0:
                    loc_curs_pos = 0
                    y_pos -= 1
                    if y_pos < 0:
                        curses.beep()  # does not work here ???
                        curses.flash()
                        y_pos = 0
                curs_pos = y_pos + loc_curs_pos

        menu_panel.hide()
        input_win.clear()
        input_win.refresh()
        self._keyboard_help.clear()

        # done
        if clear_after:
            self._stdscr.clear()
            self._stdscr.refresh()

        return final_sel


class Messages:
    """ Messages from system to player """

    def __init__(self, stdscr: typing.Any, my_gui: Gui, buffer_position: int, buffer_size: int, max_width: int) -> None:
        self._stdscr = stdscr
        self._my_gui = my_gui
        self._buffer_position = buffer_position
        self._buffer_size = buffer_size
        self._max_width = max_width
        self._table: typing.List[str] = list()
        self._nb_unread = 0
        self._offset = 0

    def upper(self) -> None:
        """ Ctrl-P / Previous messages """
        self._offset += 1
        if self._offset > len(self._table) - self._buffer_size:
            curses.beep()  # does not work here ???
            curses.flash()
            self._offset = len(self._table) - self._buffer_size

    def lower(self) -> None:
        """ Ctrl-N / Next messages """
        self._offset -= 1
        if self._offset < 0:
            curses.beep()  # does not work here ???
            curses.flash()
            self._offset = 0

    def store(self, mess: str) -> None:
        """ Store a message - split it if too large """
        self._offset = 0
        while mess:
            # find the last space
            last_space_pos = None
            for index, char in enumerate(mess):
                if index == self._max_width:
                    break
                if char == ' ':
                    last_space_pos = index
            # cut at last space if overflows
            cut = self._max_width
            if len(mess) > self._max_width and last_space_pos is not None:
                cut = last_space_pos
            # now segment string
            part = mess[0: cut]
            self._table.append(part)
            mess = mess[cut:]
            self._nb_unread += 1

    def display(self) -> None:
        """ Display messages ask for a key if more unread messages that space available """
        attr = mycurses.color(curses.COLOR_YELLOW, curses.COLOR_BLACK) | curses.A_BOLD
        while True:
            start = max(0, len(self._table) - max(self._nb_unread, self._buffer_size))
            nb_mess = min(self._buffer_size, len(self._table))
            for i in range(nb_mess):
                content = self._table[start - self._offset + i]
                padding = " " * (self._max_width - len(content))
                self._stdscr.addstr(self._buffer_position + i, 0, content + padding, attr)
            self._stdscr.refresh()
            self._nb_unread = max(0, self._nb_unread - nb_mess)
            if self._nb_unread == 0:
                return
            self._my_gui.prompt_user_noreturn("-- Press a key for more --")


class Status:
    """ Status information of hero """

    def __init__(self, stdscr: typing.Any, position: int, max_width: int) -> None:
        self._stdscr = stdscr
        self._position = position
        self._max_width = max_width
        self._content: str = ""

    def store(self, content: str) -> None:
        """ Store """
        self._content = content

    def display(self) -> None:
        """ Extract """
        attr = mycurses.color(curses.COLOR_WHITE, curses.COLOR_BLACK) | curses.A_BOLD
        for num, line in enumerate(self._content):
            assert len(line) < self._max_width, f"Please shorter message for status : '{line}'"
            self._stdscr.addstr(self._position + num, 0, line, attr)
            self._stdscr.addstr(self._position + num, len(line), ' ' * (constants.DUNGEON_WIDTH - len(line)))
        self._stdscr.refresh()


if __name__ == '__main__':
    assert False, "Do not run this script"
