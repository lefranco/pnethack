#!/usr/bin/env python3


"""
File : constants.py

Stores all constants of the game. Loaded from config file.
"""

import typing
import configparser

CONFIG = None

# -----------------------
# from configuration file
# -----------------------

# initialization values do not make sense
VERSION = ""
DUNGEON_WIDTH = 0
DUNGEON_HEIGHT = 0
FOV_RADIUS = 0
MESSAGES_BUFFER_SIZE = 0
PROMPT_BUFFER_SIZE = 0
STATUS_INFORMATION_SIZE = 0
HELP_INFORMATION_SIZE = 0
HERO_NAME = ""
NB_SEGMENTS = 0

# ----------------------
# from command parameter
# ----------------------

# initialization values do make sense
DEBUG_MODE = False
LOAD_LEVEL = ""
GENERATE_LEVEL = ""
GENERATE_LEVEL_DEPTH = 1
REVERSE = False


class ConfigFile:
    """    Just reads an ini file   """

    def __init__(self, filename: str) -> None:
        self._config = configparser.ConfigParser()
        assert self._config.read(filename), f"Missing ini file named {filename}"

    def section(self, section_name: str) -> configparser.SectionProxy:
        """ A section (dict)  """
        assert self._config.has_section(section_name), "Missing section in ini file"
        return self._config[section_name]

    def section_list(self) -> typing.List[str]:
        """ List of all sections """
        return self._config.sections()


class GlobalConfiguration:
    """ Gathers all configuration data of the project """

    def __init__(self) -> None:

        # Stores information read from general configuration file (all except clients data)
        self._general_config = ConfigFile('pnethack.ini')

    @property
    def general_config(self) -> ConfigFile:
        """ property """
        return self._general_config


def load_config() -> None:
    """ Create configuration object once for ever """

    global CONFIG
    CONFIG = GlobalConfiguration()

    section = CONFIG.general_config.section('version')
    global VERSION
    VERSION = section['version']

    section = CONFIG.general_config.section('dungeon')
    global DUNGEON_WIDTH
    DUNGEON_WIDTH = int(section['dungeon_width'])
    global DUNGEON_HEIGHT
    DUNGEON_HEIGHT = int(section['dungeon_height'])
    global FOV_RADIUS
    FOV_RADIUS = int(section['fov_radius'])

    section = CONFIG.general_config.section('interface')
    global MESSAGES_BUFFER_SIZE
    MESSAGES_BUFFER_SIZE = int(section['messages_buffer_size'])
    global PROMPT_BUFFER_SIZE
    PROMPT_BUFFER_SIZE = int(section['prompt_buffer_size'])
    global STATUS_INFORMATION_SIZE
    STATUS_INFORMATION_SIZE = int(section['status_information_size'])
    global HELP_INFORMATION_SIZE
    HELP_INFORMATION_SIZE = int(section['help_information_size'])

    section = CONFIG.general_config.section('sequencer')
    global NB_SEGMENTS
    NB_SEGMENTS = int(section['nb_segments'])

    section = CONFIG.general_config.section('hero')
    global HERO_NAME
    HERO_NAME = section['hero_name']


if __name__ == '__main__':
    assert False, "Do not run this script"
