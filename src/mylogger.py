#!/usr/bin/env python3

"""
File : mylogger.py

Interface layer to the logger. Useful for debug (no print possible)
"""

# pylint: disable=global-statement

import os
import logging
import logging.handlers

# global : no init
LOGGER: logging.Logger


def start_logger(simpler: bool = False) -> None:
    "Function to be called once to start the logging mechanics"

    # create a standard logger
    pid = os.getpid()
    if simpler:
        handler = logging.handlers.WatchedFileHandler(f"./log/pnethack.log")
    else:
        handler = logging.handlers.WatchedFileHandler(f"./log/pnethack-{pid}.log")
    formatter = logging.Formatter(logging.BASIC_FORMAT)
    handler.setFormatter(formatter)

    # configure it
    logging.basicConfig(level=logging.DEBUG)

    # on file
    global LOGGER
    LOGGER = logging.getLogger('pnethack')
    LOGGER.addHandler(handler)

    # not on console
    LOGGER.propagate = False


if __name__ == '__main__':
    assert False, "Do not run this script"
