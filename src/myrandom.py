#!/usr/bin/env python3


"""
File : myrandom.py

Interface layer to the random unit. Direct calls to random are tolerated in dungeon creation.
Functions choice() and choices() of random module may still be called
"""

import typing
import time
import random
import sys

import mylogger

DIGITS = [chr(n) for n in range(ord('0'), ord('9') + 1)]

SEED_VALUE = None


def dice(specif: str) -> int:
    """ Throws one or more dices according to specification provided as argument"""

    assert specif, "Empty spec as input"

    cur_state = 0
    cur_pos = 0
    cur_val = 0
    final_add = True
    dices: typing.Set[int] = set()

    result = 0
    # to check cannot be negative
    min_result = 0

    while True:

        cur_c = specif[cur_pos]

        if cur_state == 0:
            if cur_c in ['D', 'd']:
                if cur_val:
                    multiplier = cur_val
                else:
                    multiplier = 1
                cur_val = 0
                cur_state = 1
            elif cur_c in DIGITS:
                if cur_val == 0:
                    assert cur_c != '0', "Number cannot start by zero"
                cur_val *= 10
                cur_val += ord(cur_c) - ord('0')
            else:
                assert False, "Error in dice spec from state 0 : unexpected input"
            cur_pos += 1
            if cur_pos == len(specif):
                assert False, "Error in dice spec from state 0 : missing value after D"

        elif cur_state == 1:
            if cur_c in ['+']:
                assert cur_val > 0, "Error in dice spec from state 1 : missing number value before +"
                assert cur_val not in dices, "Found more than once a dice"
                dices.add(cur_val)
                for _ in range(multiplier):
                    result += random.randint(1, cur_val)
                min_result += multiplier
                cur_val = 0
                cur_state = 3
            elif cur_c in ['-']:
                assert cur_val > 0, "Error in dice spec from state 1 : missing number value before -"
                assert cur_val not in dices, "Found more than once a dice"
                dices.add(cur_val)
                for _ in range(multiplier):
                    result += random.randint(1, cur_val)
                min_result += multiplier
                cur_val = 0
                final_add = False
                cur_state = 2
            elif cur_c in DIGITS:
                if cur_val == 0:
                    assert cur_c != '0', "Number cannot start by zero"
                cur_val *= 10
                cur_val += ord(cur_c) - ord('0')
            else:
                assert False, "Error in dice spec from state 1 : unexpected input"
            cur_pos += 1
            if cur_pos == len(specif):
                assert cur_val > 0, "Error in dice spec from state 1 : missing number value before end"
                assert cur_val not in dices, "Found more than once a dice"
                dices.add(cur_val)
                for _ in range(multiplier):
                    result += random.randint(1, cur_val)
                min_result += multiplier
                assert min_result >= 0, "Error in dice spec : result could be negative"
                return result

        elif cur_state == 2:
            if cur_c in DIGITS:
                if cur_val == 0:
                    assert cur_c != '0', "Number cannot start by zero"
                cur_val *= 10
                cur_val += ord(cur_c) - ord('0')
            else:
                assert False, "Error in dice spec from state 2 : unexpected input"
            cur_pos += 1
            if cur_pos == len(specif):
                if final_add:
                    min_result += cur_val
                    result += cur_val
                else:
                    min_result -= cur_val
                    result -= cur_val
                assert min_result >= 0, "Error in dice spec : result could be negative"
                return result

        elif cur_state == 3:
            if cur_c in ['D', 'd']:
                cur_state = 0
            elif cur_c in DIGITS:
                cur_state = 2
            else:
                assert False, "Error in dice spec from state 3 : unexpected input"

        else:
            assert False, "Error in dice spec state ???"


def toss_coin() -> bool:
    """ toss coin """
    return random.randint(0, 1) == 0


def percent_chance(proba: int) -> bool:
    """ percent chance """
    assert isinstance(proba, int), "Bad proba type for percent_chance()"
    assert 1 <= proba <= 99, "Bad proba value for percent_chance()"
    return random.randint(1, 100) <= proba


def decide_success(chance: int, luck_value: int, debug: bool = False) -> bool:
    """ decide success of action """

    normalize: typing.Callable[[int], int] = lambda x: 1 if x < 1 else 99 if x > 99 else x

    chance = normalize(chance)
    assert -13 <= luck_value <= 13
    adjusted_chance = int((chance / 100) ** (1 - (luck_value / 13)) * 100)
    adjusted_chance = normalize(adjusted_chance)
    if debug:
        print(f"decide_success(chance={chance} luck={luck_value}) -> adjusted_chance={adjusted_chance}")
    return percent_chance(adjusted_chance)


def randint(low_value: int, high_value: int) -> int:
    """ just to impose all random in this file """
    return random.randint(low_value, high_value)


def force_seed(seed_value: int) -> None:
    """ To reproduce a problem, forces random seed """
    global SEED_VALUE
    SEED_VALUE = seed_value
    print(f"Will use value {seed_value} as random seed")
    time.sleep(0.5)


def start_random() -> None:
    """ Get random seed from time or already stored and store it in logfile """
    global SEED_VALUE
    if SEED_VALUE is None:
        now = time.time()
        SEED_VALUE = int(now * 1000000)
    mylogger.LOGGER.info("Using seed value %d", SEED_VALUE)
    random.seed(SEED_VALUE)


def restart_random() -> None:
    """ Get random seed from time and store it in logfile - used only in testing context """
    global SEED_VALUE
    now = time.time()
    SEED_VALUE = int(now * 1000000)
    mylogger.LOGGER.info("Using seed value %d", SEED_VALUE)
    random.seed(SEED_VALUE)


def test_dice() -> None:
    """ Some TU """

    if len(sys.argv) != 2:
        print("Argument missing")
        sys.exit(1)
    specif = sys.argv[1]

    num = 100000
    sum_ = 0
    for _ in range(num):

        dice_value = dice(specif)
        sum_ += dice_value

    avg = sum_ / num
    print(f"avg={avg}")
    sys.exit(0)


def test_decide_success() -> None:
    """ TU """
    restart_random()

    for chance in range(0, 100, 5):
        for luck in range(-13, 14, 2):
            decide_success(chance, luck, True)


if __name__ == "__main__":
    test_dice()
    # test_decide_success()
