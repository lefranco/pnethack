#!/usr/bin/env python3


"""
Slight improvement to json decoder
"""

import typing
import pathlib
import json


# No type checking here
def prevent_duplicates(pairs: typing.Any) -> typing.Any:
    """Reject duplicate keys."""
    dict_check: typing.Dict[str, typing.Any] = dict()
    for key, value in pairs:
        assert key not in dict_check, f"Entry {key} was duplicated in the json file"
        dict_check[key] = value
    return dict_check


class JsonReader:
    """ Slight improvement to json decoder """

    def __init__(self, file_name: str) -> None:
        # check file is present

        self._full_path_name = f"./levels/{file_name}.json"
        my_file = pathlib.Path(self._full_path_name)
        assert my_file.is_file(), f"Seems file {self._full_path_name} is missing, please advise"

    def extract(self) -> typing.Any:
        """ read json file """
        with open(self._full_path_name, 'r') as infile:
            loaded_content = json.load(infile, object_pairs_hook=prevent_duplicates)
            return loaded_content
