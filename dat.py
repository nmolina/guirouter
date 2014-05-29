from __future__ import print_function
from __future__ import division

import numpy as np

import ptype

"""
Classes in this module: Species and Move
"""

class Species():
    """An immutable class representing a Pokemon species.

    A species has stats and levels up.
    """

    def __init__(self, name, base_stats, ptypes, exp_curve, kill_exp, moveset):
        self.name = name
        self.base_stats = np.array(base_stats)
        self.ptypes = ptypes
        self.exp_curve = exp_curve
        self.kill_exp = kill_exp
        self.moveset = moveset

    def get_stats(self, level, DV, SP):
        """Gets stats, as (HP, atk, dfn, spd, spc) numpy array.

        Arguments:
        level -- the Pokemon's level
        DV -- the DVs, as (HP, atk, dfn, spd, spc) numpy array.
        SP -- the SPs, as (HP, atk, dfn, spd, spc) numpy array.
        """
    	numerator = 2 * (DV + self.base_stats) + SP
        stats = (numerator * level / 100).astype(int) + 5
        stats[0] += level + 5  # HP functions differently
        return stats

    def stat_exp_given(self, participants):
        """Gets stat exp given, as (HP, atk, dfn, spd, spc) numpy array."""
        return self.base_stats // participants

    def exp_given(self, level, is_wild, participants):
        """Gets exp given, per participant.

        Arguments:
        level -- the Pokemon's level
        is_wild -- whether the Pokemon is is_wild
        participants -- the number of participants in the battle
        """
        return self.kill_exp // participants * level // 7 * 3 // (3 if is_wild else 2)

    def exp_for_level(self, n):
        """Gets total exp needed for the level n."""
        exp_curve = self.exp_curve
        if exp_curve == "slow":
            return 5 * n * n * n // 4
        if exp_curve == "medslow":
            return 6 * n * n * n // 5 - 15 * n * n + 100 * n - 140
        if exp_curve == "med":  # alias for medfast
            return n * n * n
        if exp_curve == "medfast":
            return n * n * n
        if exp_curve == "fast":
            return 4 * n * n * n / 5

    def get_ptypes(self):
        return self.ptypes

    def get_species(self):
        return self.species

    def default_moveset(self, level):
        valid_moves = [i for i in self.moveset if i[1] <= level]
        return (i[0] for i in valid_moves[-4:])


high_crit = set(['crabhammer', 'karate chop', 'razor leaf', 'slash'])

class Move():
    """An immutable class representing a Pokemon move.

    A move has a power, an effectiveness and is either special or physical.
    """
    
    def __init__(self, name, power, ptype, accuracy, pp):
        self.name = name
        self.power = power
        self.ptype = ptype
        self.accuracy = accuracy
        self.pp = pp

    def get_power(self):
        return self.power

    def is_special(self):
        return self.ptype in ptype.special

    def effectiveness(self, other):
        other = other.get_species()
        t = self.ptype
        immune = ptype.immune[t]
        seffect = ptype.super_effective[t]
        neffect = ptype.not_very_effective[t]
        ans = 1
        for s_t in other.get_ptypes():
            if s_t in immune:
                return 0
            if s_t in seffect:
                ans *= 2
            if s_t in neffect:
                ans /= 2
        return ans

    def stab(self, me):
        me = me.get_species()
        if self.ptype in me.get_ptypes():
            return 1.5
        return 1

    def crit_chance(self, base_speed):
        return str(int(100*self._crit_chance(base_speed))) + '%'

    def _crit_chance(self, base_speed):
        denominator = 64 if self.name in high_crit else 512
        return base_speed / denominator
        

M = None
S = None
execfile('rb_dump.py')

def get_move(name):
    """Gets move, returning None if not found.

    name : The name of the move, or the Move itself.
    """
    if isinstance(name, Move):
        return name
    if name in M:
        return M[name]
    return None

def is_move(name):
    return isinstance(name, Move) or name in M

def move_names():
    return M.keys()

def get_species(name):
    """Gets species, returning None if not found.

    name : The name of a species, or the Species itself.
    """
    if isinstance(name, Species):
        return name
    if name in S:
        return S[name]
    return None

def is_species(name):
    return isinstance(name, Species) or name in S

def species_names():
    return S.keys()