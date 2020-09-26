#!/usr/bin/env python3

"""
File : experience.py

Handles experience points and levels (monster and player level)
"""

import sys

# local here since linked to experience table
MAX_HERO_LEVEL = 30

EXPERIENCE_TABLE = [
    0, 20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 10000, 20000, 40000, 80000, 160000, 320000, 640000, 1280000, 2560000, 5120000, 10000000, 20000000, 30000000, 40000000, 50000000, 60000000, 70000000, 80000000, 90000000, 100000000]

assert len(EXPERIENCE_TABLE) == MAX_HERO_LEVEL, "Revise MAX_HERO_LEVEL and/or EXPERIENCE_TABLE"


def level(points: int) -> int:
    """ Level from XP points value """
    assert points >= 0, "level : bad parameter !"
    for i in range(len(EXPERIENCE_TABLE) - 1):
        if EXPERIENCE_TABLE[i] <= points < EXPERIENCE_TABLE[i + 1]:
            return i + 1
    return MAX_HERO_LEVEL


def test() -> None:
    """ test """
    num = int(sys.argv[1])
    print(f"{num} -> {level(num)}")


if __name__ == '__main__':
    test()
