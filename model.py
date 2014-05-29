from __future__ import print_function
from __future__ import division

# All ommmunication to view happens via pubsub.
from wx.lib.pubsub import pub

import copy

import dat
import poke

class Model:

    def __init__(self):
        # Mirrored with view; used by events.
        self.poke_name = ''
        self.level = ''
        self.is_wild = False
        self.a_move_name = ''
        self.d_move_name = ''

        self.a_atk_stage = 0
        self.a_dfn_stage = 0
        self.a_spd_stage = 0
        self.a_spc_stage = 0
        self.d_atk_stage = 0
        self.d_dfn_stage = 0
        self.d_spd_stage = 0
        self.d_spc_stage = 0

        self.atk_boosts = 0
        self.dfn_boosts = 0
        self.spd_boosts = 0
        self.spc_boosts = 0


        # Elements manipulated by events.
        self.d_moveset = []

        self._party = []
        self._current_party = 0

        # Elements manipulated by model.
        self._events = [] # Persists across saves.
        self._current_event = 0 # 1 more than current selection; used in view

    def _clear(self):
        self._events = []
        self._reset()

    def _reset(self):
        self._party = []
        self._current_party = 0
        self._current_event = 0

    def advance_to(self, i):
        self._reset()
        while self._current_event <= i:
            self.advance()

    def advance(self):
        self.cur_event().run(self)
        self._current_event += 1

    def add_event(self, cls, args):
        if cls.is_valid(self):
            event = cls(*args)
            self._events.insert(self._current_event, event)
            pub.sendMessage("HISTORY_UPDATE", data=self.history_info())
            self.advance()

    def remove(self, i):
        del[self._events[self._current_event - 1]]
        self._current_event -= 1
        pub.sendMessage("HISTORY_UPDATE", data=self.history_info())

    def add_to_party(self, party_poke):
        self._party.append(party_poke)

    # Triggers
    def t_add_to_party(self):
        self.add_event(AddPokeEvent, [self.poke_name, self.level, self.is_wild])

    def t_defeat(self):
        self.add_event(KillEvent, [self.poke_name, self.level, self.is_wild])

    def t_share(self):
        self.add_event(KillEvent, [self.poke_name, self.level, self.is_wild, 2])

    def t_delete_event(self, i):
        self.remove(i)

    def t_use_item(self, i):
        if i in poke.item_names:
            self.add_event(ItemEvent, [i])

    def t_switch(self, i):
        self.add_event(SwitchEvent, [i])

    def t_save(self, fname):
        f = open(fname, 'w')
        f.write('RBSim\n')
        for event in self._events:
            f.write(repr(event) + '\n')
        f.close()


    def t_open(self, fname):
        f = open(fname, 'r')
        line = f.readline()
        if line.strip() != 'RBSim':
            print('Invalid file.')
            return
        self._clear()
        while True:
            line = f.readline()
            if not line:
                break
            event = eval(line)
            self._events.append(event)
        pub.sendMessage("HISTORY_UPDATE", data=self.history_info())
        f.close()

    # Observers
    def history_info(self):
        return [repr(event) for event in self._events]

    def party_info(self):
        if self._current_event == 0:
            return 'No event to display'

        return self.prev_event().overall_info(self)

    def event_info(self):
        if self._current_event == 0:
            return 'No event to display'

        return self.prev_event().info(self)

    def party_choices(self):
        return [i.short_name() for i in self._party]


    def prev_event(self):
        return self._events[self._current_event-1]

    def cur_event(self):
        return self._events[self._current_event]

    def cur_poke(self):
        if len(self._party) == 0:
            return None
        return self._party[self._current_party]

class PartyPoke():
    """Wrapper around poke.Pokemon."""

    def __init__(self, poke_name, level, is_wild):
        species = dat.get_species(poke_name)
        level = int(level)
        is_wild = bool(is_wild)
        self.poke = poke.get_Pokemon(species, level, is_wild)

    def copy(self):
        # XXX Assumes poke.Pokemon immutable (which it isn't in general),
        # In this case, it's OK because we only use .defeat, .consume on it.
        # But this can be improved.
        return copy.copy(self)

    def defeat(self, other, participants):
        self.poke = self.poke.defeat(other.poke, participants)

    def detailed_stats(self, spd_stage, spd_boosts):
        exp = self.poke.exp
        species = self.poke.species
        lvl = self.poke.lvl
        exp1 = species.exp_for_level(lvl + 1) - exp

        return self.poke.name() + ' (' + str(exp1) + ' exp left)\n' + self.stats(spd_stage, spd_boosts) + \
            '\n' + self.extra_info()

    def stats(self, spd_stage, spd_boosts=0):
        return self.poke.get_stats(include_spd=True, spd_stage=spd_stage,
                                       spd_boosts=spd_boosts)

    def dmg(self, other, move_name, **kargs):
        return self.poke.get_dmg(other.poke, move_name, **kargs)

    def moveset(self):
        return list(self.poke.default_moveset())

    def name(self):
        return self.poke.name()

    def DV(self):
        return str(self.poke.DV)

    def stat_exp(self):
        return str(self.poke.cur_stat_exp)

    def SP(self):
        return str(self.poke.get_SP())

    def extra_info(self):
        exp = self.poke.exp
        species = self.poke.species
        lvl = self.poke.lvl
        overflow = exp - species.exp_for_level(lvl)
        exp1 = species.exp_for_level(lvl + 1) - exp
        exp2 = species.exp_for_level(lvl + 2) - exp
        return str(exp) + ' total exp (' +  str(overflow) + ' overflow)\n' + \
            str(exp1) + ' exp to lv' + str(lvl+1) + ", " + str(exp2) + ' to lv' + str(lvl+2) + \
            ('\nDV ' + self.DV() if self.DV() != 'None' else '') + \
            '\nSE ' + self.stat_exp() + '\nSP ' + self.SP()

    def exp_given(self, participants):
        return str(self.poke.exp_given(participants))

    def crit_chance(self, move_name):
        # XXX ugly
        return '(' + dat.get_move(move_name).crit_chance(self.poke.species.base_stats[3]) + ' crit)'

    def consume(self, item):
        self.poke = self.poke.consume_item(item)

    def short_name(self):
        return self.poke.name()[:2] + str(self.poke.lvl)

    @staticmethod
    def is_valid(poke_name, level):
        return dat.is_species(poke_name) and level.isdigit()



"""
Events

"""
class Event():
    @staticmethod
    def is_valid(model):
        raise NotImplementedError
    def run(self, model):
        raise NotImplementedError
    def info(self, model):
        raise NotImplementedError
    def overall_info(self, model):
        raise NotImplementedError
    def __repr__(self):
        raise NotImplementedError

class AddPokeEvent(Event):
    """The addition of a pokemon to party."""

    def __init__(self, poke_name, level, is_wild):
        self.poke_name = poke_name
        self.level = level
        self.is_wild = is_wild

    @staticmethod
    def is_valid(model):
        return PartyPoke.is_valid(model.poke_name, model.level)

    def run(self, model):
        self.poke = PartyPoke(self.poke_name, self.level, self.is_wild)
        model.add_to_party(self.poke)

    def info(self, model):
        return ''

    def overall_info(self, model):
        return self.poke.detailed_stats(model.a_spd_stage, model.spd_boosts)

    def __repr__(self):
        return 'AddPokeEvent(' + repr(self.poke_name) + ',' + repr(self.level) + ',' + repr(self.is_wild) + ')'


class KillEvent(Event):
    """The defeat of a pokemon."""

    def __init__(self, poke_name, level, is_wild, participants=1):
        self.poke_name = poke_name
        self.level = level
        self.is_wild = is_wild
        self.participants = participants

    @staticmethod
    def is_valid(model):
        return (model.cur_poke() and PartyPoke.is_valid(model.poke_name, model.level))

    def run(self, model):
        self.mine = model.cur_poke()
        self.pre_mine = self.mine.copy() # me before battle
        self.theirs = PartyPoke(self.poke_name, self.level, self.is_wild)
        model.d_moveset = self.theirs.moveset()
        self.mine.defeat(self.theirs, self.participants)

    def info(self, model):
        ans = ''
        if dat.is_move(model.a_move_name):
            move_name = model.a_move_name
            dmg = self.pre_mine.dmg(self.theirs, move_name,
                                    atk_stage=model.a_atk_stage, dfn_stage=model.d_dfn_stage,
                                    spc_a_stage=model.a_spc_stage, spc_d_stage=model.d_spc_stage,
                                    atk_boosts=model.atk_boosts, spc_a_boosts=model.spc_boosts)
            ans += 'Attack with ' + move_name + ' ' + self.pre_mine.crit_chance(move_name) + '\n' + dmg + '\n'
        if dat.is_move(model.d_move_name):
            move_name = model.d_move_name
            dmg = self.theirs.dmg(self.pre_mine, move_name,
                                  atk_stage=model.d_atk_stage, dfn_stage=model.a_dfn_stage,
                                  spc_a_stage=model.d_spc_stage, spc_d_stage=model.a_spc_stage,
                                  dfn_boosts=model.dfn_boosts, spc_d_boosts=model.spc_boosts)
            ans += 'Defend ' + move_name + ' ' + self.theirs.crit_chance(move_name) + '\n' + dmg + '\n'
        
        ans += 'Key: no_crit range, crit range'
        return ans

    def overall_info(self, model):
        return 'My ' + self.pre_mine.name() + ' stats\n' + self.pre_mine.stats(model.a_spd_stage, model.spd_boosts) + \
            'Their ' + self.theirs.name() + ' stats\n' + self.theirs.stats(model.d_spd_stage) + \
            '\n' + 'Exp gained: ' + self.theirs.exp_given(self.participants) + '\n' + \
            self.mine.detailed_stats(model.a_spd_stage, model.spd_boosts)

    def __repr__(self):
        return 'KillEvent(' + repr(self.poke_name) + ',' + repr(self.level) + ',' + \
            repr(self.is_wild) + (',' + str(self.participants) if self.participants != 1 else '') + ')'

class ItemEvent(Event):
    """Consumption of an item."""

    def __init__(self, item):
        # item must be a valid item name
        self.item = item

    def run(self, model):
        model.cur_poke().consume(self.item)

    @staticmethod
    def is_valid(model):
        return bool(model.cur_poke())

    def info(self, model):
        return ''

    def overall_info(self, model):
        return model.cur_poke().detailed_stats(model.a_spd_stage, model.spd_boosts)

    def __repr__(self):
        return 'ItemEvent(' + repr(self.item) + ')'

class SwitchEvent(Event):
    """Switch a pokemon to top of party."""

    def __init__(self, i):
        self.i = i

    def run(self, model):
        if self.i >= len(model._party) or self.i < 0:
            print('SWITCH ERROR')
        model._current_party = self.i

    @staticmethod
    def is_valid(model):
        return True

    def info(self, model):
        return ''

    def overall_info(self, model):
        return model.cur_poke().detailed_stats(model.a_spd_stage, model.spd_boosts)

    def __repr__(self):
        return 'SwitchEvent(' + repr(self.i) + ')'