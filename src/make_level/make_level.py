#!/usr/bin/env python3

# pylint: disable=line-too-long
# pylint: disable=global-statement, too-few-public-methods, too-many-statements, too-many-locals


"""
File : make_level.py

Import dungeon from text file
Input should be something like this :

  ---
  |.|
  |..--
  |...|
  ----

Will create :
  - lines of ground (using .)
  - vertical walls (using |)
  - horizontal walls (using -)

"""

# import debug.wingdbstub

import argparse
import typing

NUM_ITEM = 0


class Ground:
    """ A ground """
    def __init__(self, x: int, y: int, l: int) -> None:
        self._upper_left_x = x
        self._upper_left_y = y
        self._length = l
        global NUM_ITEM
        NUM_ITEM += 1
        self._num = NUM_ITEM

    def __str__(self) -> str:
        return f"\t\"ground_{self._num}\": {{\n" + \
            "\t\t\"type\" : \"line\",\n" + \
            "\t\t\"use\" : \"ground\",\n" + \
            f"\t\t\"orientation\" : \"horizontal\",\n" + \
            f"\t\t\"upper_left\": {{ \"x\": {self._upper_left_x}, \"y\": {self._upper_left_y}}},\n" + \
            f"\t\t\"length\" : {self._length}\n" + \
            "\t},\n"


class Wall:
    """ A wall """
    def __init__(self, x: int, y: int, l: int, v: int) -> None:
        self._upper_left_x = x
        self._upper_left_y = y
        self._length = l
        self._vertical = v
        global NUM_ITEM
        NUM_ITEM += 1
        self._num = NUM_ITEM

    def __str__(self) -> str:
        orientation = "vertical" if self._vertical else "horizontal"
        return f"\t\"wall_{orientation[0]}_{self._num}\": {{\n" + \
            "\t\t\"type\" : \"wall\",\n" + \
            f"\t\t\"upper_left\": {{ \"x\": {self._upper_left_x}, \"y\": {self._upper_left_y}}},\n" + \
            f"\t\t\"length\" : {self._length},\n" + \
            f"\t\t\"orientation\" : \"{orientation}\"\n" + \
            "\t},\n"


class Door:
    """ A door """
    def __init__(self, x: int, y: int, secret: bool) -> None:
        self._upper_left_x = x
        self._upper_left_y = y
        self._secret = secret
        global NUM_ITEM
        NUM_ITEM += 1
        self._num = NUM_ITEM

    def __str__(self) -> str:
        return f"\t\"door_{self._num}\": {{\n" + \
            "\t\t\"type\" : \"door\",\n" + \
            ("\t\t\"secret\" : true,\n" if self._secret else "") + \
            f"\t\t\"position\": {{ \"x\": {self._upper_left_x}, \"y\": {self._upper_left_y}}}\n" + \
            "\t},\n"


def main() -> None:
    """ main """

    def scan_grounds(lines: typing.List[str]) -> None:
        global NUM_ITEM
        NUM_ITEM = 0
        target = '.'
        for row, line in enumerate(lines):
            charprev = None
            line += ' '
            for col, char in enumerate(line):
                if char in ['+', 'S']:  # doors
                    char = '.'
                if char in ['^', '>', '<']:  # makes it easier
                    char = '.'
                assert char in ['|', '-', ' ', '.'], f"Revise file content : found '{char}'"
                if char != charprev:
                    if char == target and charprev != target:
                        start = col
                    if char != target and charprev == target:
                        end = col
                        ground = Ground(start, row, end - start)
                        grounds.append(ground)
                    charprev = char

    def scan_walls(lines: typing.List[str], vertical: bool) -> None:
        global NUM_ITEM
        NUM_ITEM = 0
        target = '|' if vertical else '-'
        for row, line in enumerate(lines):
            charprev = None
            line += ' '
            for col, char in enumerate(line):
                if char in ['+', 'S']:  # doors
                    char = '.'
                if char in ['^', '>', '<']:  # makes it easier
                    char = '.'
                assert char in ['|', '-', ' ', '.'], "Revise file content : found '{char}'"
                if char != charprev:
                    if char == target and charprev != target:
                        start = col
                    if char != target and charprev == target:
                        end = col
                        if vertical:
                            wall = Wall(row, start, end - start, True)
                        else:
                            wall = Wall(start, row, end - start, False)
                        walls.append(wall)
                    charprev = char

    def scan_doors(lines: typing.List[str]) -> None:
        global NUM_ITEM
        NUM_ITEM = 0
        for row, line in enumerate(lines):
            for col, char in enumerate(line):
                if char in ['+', 'S']:  # doors
                    door = Door(row, col, char == 'S')
                    doors.append(door)

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='Input file in text format (map)')
    parser.add_argument('-a', '--additional', required=True, help='Additional input file in json format')
    parser.add_argument('-o', '--output', required=True, help='Output file in json format')
    args = parser.parse_args()

    lines = []
    with open(args.input) as file_p:
        for line in file_p.readlines():
            lines.append(line.rstrip('\n'))

    lines_add = []
    with open(args.additional) as file_p:
        for line in file_p.readlines():
            lines_add.append(line.rstrip('\n'))

    with open(args.output, "w") as file_p:

        grounds: typing.List[Ground] = list()
        walls: typing.List[Wall] = list()
        doors: typing.List[Door] = list()

        # grounds
        scan_grounds(lines)

        # horizontal wall
        scan_walls(lines, False)

        # vertical wall
        nbcols = max([len(l) for l in lines])
        columns_table = dict()
        for col in range(nbcols):
            columns_table[col] = ""
        for line in lines:
            for col, char in enumerate(line):
                columns_table[col] += char  # str add (concatenate)
        columns = list(columns_table.values())
        scan_walls(columns, True)

        # doors
        scan_doors(columns)

        print("{\n", file=file_p)

        for wall in walls:
            print(wall, file=file_p)
        for ground in grounds:
            print(ground, file=file_p)
        for door in doors:
            print(door, file=file_p)

        for add in lines_add:
            print(add, file=file_p)

        print("}\n", file=file_p)


if __name__ == '__main__':
    main()
