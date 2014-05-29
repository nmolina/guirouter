from __future__ import print_function
from __future__ import division

import numpy as np
import collections

import calc
import dat

item_names = set(["rare candy"])

def p(name, lvl, wild=False):
    # wild == 1 gives pokemon with random DVs
    # wild == 2 gives pokemon with undetermined DVs
    # wild == -X gives pokemon with DVs (_, X, X, X, X)
    if not wild:
        DV = [9, 8, 8, 8]
    elif wild == 1:
        DV = [collections.randrange(16) for _ in range(4)]
    elif wild == 2:
        DV = None
    elif wild < 0:
        DV = [-wild] * 4
    return Pokemon(dat.S[name], lvl, DV, (True if wild != 0 else False))

def rounder(m):
    """Recursively rounds."""
    if isinstance(m, collections.Iterable):
        return [round(i, 2) for i in m]
    return round(m, 2)

def zipper(*args):
    """Zips, unless there's nothing to zip."""
    if isinstance(args[0], collections.Iterable):
        return zip(*args)
    return args


def get_Pokemon(species, lvl, is_wild):
    """Pokemon factory.

    DVs are undetermined for wild pokemon.
    
    """
    if is_wild:
        return Pokemon(species, lvl, None, is_wild)

    return Pokemon(species, lvl, [9, 8, 8, 8], is_wild)


class Pokemon:
    def __init__(self, species, lvl, DV, is_wild):
        """Pokemon constructor.

        Arguments:
        species - species of the Pokemon
        lvl - level of the Pokemon
        DV - Pokemon DVs (None means "undetermined")
        is_wild - whether the Pokemon is wild

        """
        self.species = species # Immutable
        self.lvl = lvl
        self.DV = calc.get_DV(DV) # Immutable, mutated temporarily within functions.
        self.is_wild = is_wild # Immutable
        self.exp = species.exp_for_level(lvl)
        self.stat_exp = np.array([0]*5)
        self.cur_stat_exp = np.array([0]*5)

    def copy(self):
        if self.DV is None:
            DV_copy = None
        else:
            DV_copy = np.copy(self.DV)
        c = Pokemon(self.species, self.lvl, DV_copy, self.is_wild)
        c.exp = self.exp
        c.stat_exp = np.copy(self.stat_exp)
        c.cur_stat_exp = np.copy(self.cur_stat_exp)
        return c

    def get_species(self):
        return self.species

    def _use_DV(f):
        def g(self, *args, **kargs):
            if self.DV is None:
                ans = ''
                for i in range(16):
                    self.DV = np.array([i] * 5)
                    ans += str(i) + " " + f(self, *args, **kargs) + "\n"
                self.DV = None
                return ans
            else:
                return f(self, *args, **kargs) + "\n"
        return g

    def stats(self):
        print(self.get_stats(), end="")

    def default_moveset(self):
        return self.species.default_moveset(self.lvl)

    def defeat(self, other, participants=1):
        return self.copy().defeatm(other, participants=participants)
        
    def exp_given(self, participants=1):
        return self.species.exp_given(self.lvl, self.is_wild, participants)

    def defeatm(self, other, participants=1):
        self.cur_stat_exp += other.species.stat_exp_given(participants)
        self.exp += other.exp_given(participants)
        while self.species.exp_for_level(self.lvl + 1) < self.exp or self.lvl == 100:
            self.lvl += 1
            self.stat_exp = np.copy(self.cur_stat_exp)
        return self

    def get_SP(self):
        return (np.minimum(255, np.ceil(np.sqrt(self.stat_exp))) / 4).astype(int)

    def consume_item(self, item):
        return self.copy().consume_item_m(item)

    def consume_item_m(self, item):
        if item == 'rare candy':
            self.lvl += 1
            self.stat_exp = np.copy(self.cur_stat_exp)
            self.exp = self.species.exp_for_level(self.lvl)
        return self

    @_use_DV
    def get_stats(self, include_spd=False, spd_stage=0, spd_boosts=0):
        stats = self._stats()
        if include_spd:
            return str(stats) + ' ' + str(calc.modify(stats[3], spd_stage, spd_boosts))
        return str(stats)

    def _stats(self):
        return self.species.get_stats(self.lvl, self.DV, self.get_SP())

    def dmg(self, *args, **kargs):
        print(self.get_dmg(*args, **kargs), end="")

    @_use_DV
    def get_dmg(self, other, move,
                atk_stage=0, dfn_stage=0, spc_a_stage=0, spc_d_stage=0,
                crit=None, roll=None, atk_boosts=0,
                dfn_boosts=0, spc_a_boosts=0, spc_d_boosts=0):
        move = dat.get_move(move)
        special = move.is_special()
        stats = self._stats()
        atk_o = stats[-1] if special else stats[1]
        effect = move.effectiveness(other)
        stab = move.stab(self)
        if special:
            atk_boosts = spc_a_boosts
            dfn_boosts = spc_d_boosts
            atk_stage = spc_a_stage
            dfn_stage = spc_d_stage
        power = move.get_power()

        if other.DV is None:
            # XXX could use some clean up
            tuples = []
            crits = []
            hp = []
            for i in reversed(range(16)):
                other.DV = np.array([i] * 5)
                other_stats = other._stats()
                dfn_o = other_stats[-1] if special else other_stats[2]
                hp.append(other_stats[0])
                tt = calc.damage_tuple(level=self.lvl, power=power, atk_o=atk_o, dfn_o=dfn_o,
                                       atk_stage=atk_stage, dfn_stage=dfn_stage, stab=stab, effect=effect,
                                       crit=crit, roll=roll, atk_boosts=atk_boosts, dfn_boosts=dfn_boosts)
                if crit is None:
                    tuples.append(tt[0])
                    crits.append(tt[1])
                else:
                    tuples.append(tt)
            other.DV = None
            mean_hp = round(np.mean(hp), 2)
            mean_tuple = rounder(np.mean(tuples, axis=0))
            if crits:
                mean_crit = rounder(np.mean(crits, axis=0))
                return (str(zipper(tuples[0], tuples[-1], mean_tuple)) + " " +
                        str(zipper(crits[0], crits[-1], mean_crit)) + " " +
                        str((hp[-1], hp[0], mean_hp)))
            return (str(zipper(tuples[0], tuples[-1], mean_tuple)) + " " +
                    str((hp[-1], hp[0], mean_hp)))


        other_stats = other._stats()
        dfn_o = other_stats[-1] if special else other_stats[2]
        dmg = calc.damage_tuple(level=self.lvl, power=power, atk_o=atk_o, dfn_o=dfn_o,
                                atk_stage=atk_stage, dfn_stage=dfn_stage, stab=stab, effect=effect,
                                crit=crit, roll=roll, atk_boosts=atk_boosts, dfn_boosts=dfn_boosts)
        if crit is None:
            return str(dmg[0]) + " " + str(dmg[1]) + " " + str(other_stats[0])
        return str(dmg) + " " + str(other_stats[0])

    def name(self):
        return self.species.name +  str(self.lvl)