from __future__ import print_function
from __future__ import division

import numpy as np
import collections


def damage_tuple(level, power, atk_o, dfn_o, atk_stage, dfn_stage, stab, effect,
                 crit=None, roll=None, atk_boosts=0, dfn_boosts=0):
    # Damage tuples are by default (normal_damage_range, crit_damage_range)
    atk = modify(atk_o, atk_stage, boosts=atk_boosts)
    dfn = modify(dfn_o, dfn_stage, boosts=dfn_boosts)
    no_crit = int(int(((2 * level // 5 + 2) * atk * power // 50 // dfn + 2) * stab+.001) * effect+.001)
    a_crit = int(int(((4 * level // 5 + 2) * atk_o * power // 50 // dfn_o + 2) * stab+.001) * effect+.001)
    if crit is None:
        return damage_range(no_crit, roll), damage_range(a_crit, roll)
    if crit:
        return damage_range(a_crit, roll)
    return damage_range(no_crit, roll)

def damage_range(full, roll=None):
    # Damage ranges are by default (lowest_damage, full_damage, average_damage)
    # Rounding occurs to 2 decimal places
    if roll is None:
        rolls = [max(1, full * i // 255) for i in range(217, 256)]
        return (rolls[0], rolls[-1], round(np.mean(rolls), 2))
    if roll == 'avg':
        rolls = [max(1, full * i // 255) for i in range(217, 256)]
        return round(np.mean(rolls), 2)
    return max(1, full * roll // 255)


def get_DV(DV):
    # DV is either None (undetermined) or (HP, atk, def, spd, spc)
    # However it can also be initialized via (atk, def, spd, spc)
    if DV is None:
        return None
    if isinstance(DV, collections.Iterable):
        if len(DV) == 4:
            return np.array([HP_DV(DV)] + DV)
        if len(DV) == 5:
            return np.array(DV)
        print("Error setting DV!")
        return None
    return np.array([DV]*5)


def modify(val, stage, boosts = 0):
    val = val * multiplier100(stage) // 100
    for _ in range(boosts):
        val = val * 9 // 8
    return max(1, min(999, val))

################################################################################


def HP_DV(DV):
    return ((DV[0] & 1) << 3) + ((DV[1] & 1) << 2) + ((DV[3] & 1) << 1) + (DV[2] & 1)


# XXX rounding may be off here (especially for negative stages)
def multiplier100(stage):
    if stage < -6 or stage > 6:
        return 100
    return {-6:25,
            - 5:28,
            - 4:33,
            - 3:40,
            - 2:50,
            - 1:66,
            0:100,
            1:150,
            2:200,
            3:250,
            4:300,
            5:350,
            6:400}[stage]