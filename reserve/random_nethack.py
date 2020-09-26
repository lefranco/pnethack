# TODO : decide if we keep .. complicated...
def rnl_luck(number: int, luck: int) -> int:
    """ Will be uselful later on !
        the rnl function, biased by luck
        used by : any luck influenced decision
    """

    assert number > 0, "Bad parameter for rnl_luck()"

    sgn: typing.Callable[[int], int] = lambda x: 1 if x > 0 else -1 if x < 0 else 0

    adj = luck
    if number <= 15:
        adj = ((abs(adj) + 1) // 3) * sgn(adj)

    ret = random.randint(0, number - 1)
    if adj and random.randint(0, 37 + abs(adj)) != 0:
        ret -= adj
        if ret < 0:
            ret = 0
        elif ret > number - 1:
            ret = number - 1

    return ret


# TODO : decide if we keep .. complicated...
def rne_level(number: int, level: int) -> int:
    """ Will be uselful later on !
        the rne function, biased by level
        used by : enchantement of weapons, armors, rings
                  rnz below
    """
    assert number > 0, "Bad parameter for rne_level()"

    ret_max = 5 if level < 15 else level // 3

    ret = 1
    while ret < ret_max and random.randint(0, number) != 0:
        ret += 1

    return ret

# TODO : decide if we keep .. complicated...
def rnz_level(number: int, level: int) -> int:
    """ Will be uselful later on !
        the rnz function influenced by the rne
        used for prayer timeout, artifact invokement timeout, corpse desintegration
    """

    assert number > 0, "Bad parameter for rnz_level()"

    adj = 1000
    adj += random.randint(0, 999)
    adj *= rne_level(4, level)

    ret = number
    if random.randint(0, 1) == 0:
        ret *= adj
        ret //= 1000
    else:
        ret *= 1000
        ret //= adj

    return ret
    
    
def test_rnd() -> None:
    """ some TU """

    number = int(sys.argv[1])
    luck = int(sys.argv[2])
    level = int(sys.argv[3])

    sum_rnl = 0
    sum_rne = 0
    sum_rnz = 0
    nb_test = 0
    for _ in range(10000):
        sum_rnl += rnl_luck(number, luck)
        sum_rne += rne_level(number, level)
        sum_rnz += rnz_level(number, level)
        nb_test += 1

    avg_rnl = float(sum_rnl) / float(nb_test)
    avg_rne = float(sum_rne) / float(nb_test)
    avg_rnz = float(sum_rnz) / float(nb_test)

    print(f"rnl n={number} luck={luck} -> {avg_rnl}")
    print(f"rne n={number} level={level} -> {avg_rne}")
    print(f"rnz n={number} level={level} -> {avg_rnz}")




