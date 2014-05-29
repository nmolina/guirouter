import wx

import model
from dat import species_names, move_names
from poke import item_names

from wx.lib.pubsub import pub

class PromptingComboBox(wx.ComboBox):
    # See: http://wiki.wxpython.org/Combo%20Box%20that%20Suggests%20Options

    def __init__(self, parent, value, choices=[], style=0, **par):
        choices = sorted(choices)
        wx.ComboBox.__init__(self, parent, wx.ID_ANY, value, style=style|wx.CB_DROPDOWN, choices=choices, **par)
        self.choices = choices
        self.Bind(wx.EVT_TEXT, self.EvtText)
        self.Bind(wx.EVT_CHAR, self.EvtChar)
        self.Bind(wx.EVT_COMBOBOX, self.EvtCombobox)
        self.ignoreEvtText = False
    
    def EvtCombobox(self, event):
        self.ignoreEvtText = True
        event.Skip()
        
    def EvtChar(self, event):
        if event.GetKeyCode() == 8:
            self.ignoreEvtText = True
        event.Skip()
        
    def EvtText(self, event):
        if self.ignoreEvtText:
            self.ignoreEvtText = False
            return
        currentText = event.GetString()
        found = False
        for choice in self.choices :
            if choice.startswith(currentText):
                self.ignoreEvtText = True
                self.SetValue(choice)
                self.SetInsertionPoint(len(currentText))
                self.SetMark(len(currentText), len(choice))
                found = True
                break
        if not found:
            event.Skip()

    def SetChoices(self, choices):
        if choices == self.choices:
            return
        self.choices = choices
        self.SetItems(choices)


class TopFrame(wx.Frame):
    def __init__(self, model, *args, **kargs):
        wx.Frame.__init__(self, *args, **kargs)
        self.icon = wx.Icon('calc.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)
        self.model = model
        self.panel = wx.Panel(self)
        self.events = []

        self.dirname = None
        self.filename = None

        # Menu Bar
        self.frame_menubar = wx.MenuBar()
        tmp_menu = wx.Menu()
        load = tmp_menu.Append(wx.ID_ANY, "Open", "", wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.on_open, load)
        save = tmp_menu.Append(wx.ID_ANY, "Save", "", wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.on_save, save)
        self.frame_menubar.Append(tmp_menu, "File")
        self.SetMenuBar(self.frame_menubar)
        # Menu Bar end

        # Row 1 start
        self.poke_name = PromptingComboBox(self.panel, "", choices=species_names())
        self.level = wx.TextCtrl(self.panel, wx.ID_ANY, "", size=(40, -1), style=wx.TE_PROCESS_ENTER)
        self.level.Bind(wx.EVT_TEXT_ENTER, self.on_defeat) # Enter on Level is same as "Kill"
        self.is_wild = wx.CheckBox(self.panel, wx.ID_ANY, "wild?")

        self.defeat_button = wx.Button(self.panel, wx.ID_ANY, "Kill", style=wx.BU_EXACTFIT)
        self.defeat_button.Bind(wx.EVT_BUTTON, self.on_defeat)
        self.share_button = wx.Button(self.panel, wx.ID_ANY, "Share", style=wx.BU_EXACTFIT)
        self.share_button.Bind(wx.EVT_BUTTON, self.on_share)
        self.add_button = wx.Button(self.panel, wx.ID_ANY, "Add", style=wx.BU_EXACTFIT)
        self.add_button.Bind(wx.EVT_BUTTON, self.on_add)
        
        self.a_move_name = PromptingComboBox(self.panel, "", choices=move_names(), style=wx.TE_PROCESS_ENTER)
        self.a_move_name.Bind(wx.EVT_TEXT_ENTER, self.on_new_a_move)
        self.d_move_name = PromptingComboBox(self.panel, "", choices=[], style=wx.TE_PROCESS_ENTER)
        self.d_move_name.Bind(wx.EVT_TEXT_ENTER, self.on_new_d_move)

        self.item_sep = wx.StaticLine(self.panel, style=wx.LI_VERTICAL)
        self.item_choice = PromptingComboBox(self.panel, "", choices=item_names, style=wx.TE_PROCESS_ENTER)
        self.item_choice.Bind(wx.EVT_TEXT_ENTER, self.on_new_item)
        self.party_sep = wx.StaticLine(self.panel, style=wx.LI_VERTICAL)
        self.party_choice = wx.Choice(self.panel, wx.ID_ANY, choices=[], size=(60, -1))
        self.party_choice.Bind(wx.EVT_CHOICE, self.on_party_switch)
        # Row 1 end

        # Row 2 start
        self.badge_label = wx.StaticText(self.panel, wx.ID_ANY, "Boosts ")
        self.atk_badge = wx.SpinCtrl(self.panel, wx.ID_ANY, "", size=(40, -1))
        self.dfn_badge = wx.SpinCtrl(self.panel, wx.ID_ANY, "", size=(40, -1))
        self.spd_badge = wx.SpinCtrl(self.panel, wx.ID_ANY, "", size=(40, -1))
        self.spc_badge = wx.SpinCtrl(self.panel, wx.ID_ANY, "", size=(40, -1))
        self.atk_badge.Bind(wx.EVT_SPINCTRL, self.on_new_boosts)
        self.dfn_badge.Bind(wx.EVT_SPINCTRL, self.on_new_boosts)
        self.spd_badge.Bind(wx.EVT_SPINCTRL, self.on_new_boosts)
        self.spc_badge.Bind(wx.EVT_SPINCTRL, self.on_new_boosts)

        self.a_stage_label = wx.StaticText(self.panel, wx.ID_ANY, "My stages ")
        self.a_atk_stage = wx.SpinCtrl(self.panel, wx.ID_ANY, "", min=-6, max=6, size=(40, -1))
        self.a_dfn_stage = wx.SpinCtrl(self.panel, wx.ID_ANY, "", min=-6, max=6, size=(40, -1))
        self.a_spd_stage = wx.SpinCtrl(self.panel, wx.ID_ANY, "", min=-6, max=6, size=(40, -1))
        self.a_spc_stage = wx.SpinCtrl(self.panel, wx.ID_ANY, "", min=-6, max=6, size=(40, -1))
        self.a_atk_stage.Bind(wx.EVT_SPINCTRL, self.on_new_boosts)
        self.a_dfn_stage.Bind(wx.EVT_SPINCTRL, self.on_new_boosts)
        self.a_spd_stage.Bind(wx.EVT_SPINCTRL, self.on_new_boosts)
        self.a_spc_stage.Bind(wx.EVT_SPINCTRL, self.on_new_boosts)

        self.d_stage_label = wx.StaticText(self.panel, wx.ID_ANY, "Their stages ")
        self.d_atk_stage = wx.SpinCtrl(self.panel, wx.ID_ANY, "", min=-6, max=6, size=(40, -1))
        self.d_dfn_stage = wx.SpinCtrl(self.panel, wx.ID_ANY, "", min=-6, max=6, size=(40, -1))
        self.d_spd_stage = wx.SpinCtrl(self.panel, wx.ID_ANY, "", min=-6, max=6, size=(40, -1))
        self.d_spc_stage = wx.SpinCtrl(self.panel, wx.ID_ANY, "", min=-6, max=6, size=(40, -1))
        self.d_atk_stage.Bind(wx.EVT_SPINCTRL, self.on_new_boosts)
        self.d_dfn_stage.Bind(wx.EVT_SPINCTRL, self.on_new_boosts)
        self.d_spd_stage.Bind(wx.EVT_SPINCTRL, self.on_new_boosts)
        self.d_spc_stage.Bind(wx.EVT_SPINCTRL, self.on_new_boosts)
        # Row 2 end

        self.events_box = wx.ListBox(self.panel, wx.ID_ANY, style=wx.LB_SINGLE)
        self.events_box.Bind(wx.EVT_LISTBOX, self.move_in_history)
        self.events_box.Bind(wx.EVT_KEY_DOWN, self.history_key_down)
        self.party_info = wx.TextCtrl(self.panel, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.event_info = wx.TextCtrl(self.panel, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_READONLY)

        pub.subscribe(self.update_events_box, "HISTORY_UPDATE")

        self.__set_properties()
        self.__do_layout()
        
        topSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer.Add(self.panel, 1, wx.EXPAND)
        # topSizer.Fit(self)
        self.SetSizer(topSizer)
        topSizer.Layout()

    def __set_properties(self):
        self.SetTitle("RB Sim")
        self.SetSize((780, 550))

    def __do_layout(self):
        vsizer = wx.BoxSizer(wx.VERTICAL)
        bottom = wx.BoxSizer(wx.HORIZONTAL)
        middle = wx.BoxSizer(wx.HORIZONTAL)
        top = wx.BoxSizer(wx.HORIZONTAL)

        # Stop top row
        top.Add(self.poke_name, 0, wx.LEFT, 2)
        top.Add(self.level, 0, 0, 0)
        top.Add(self.is_wild, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        top.Add(self.defeat_button, 0, 0, 0)
        top.Add(self.share_button, 0, 0, 0)
        top.Add(self.add_button, 0, 0, 0)

        top.Add(self.a_move_name, 0, 0, 0)
        top.Add(self.d_move_name, 0, 0, 0)

        top.Add(self.item_sep, 0, wx.ALL | wx.EXPAND, 2)
        top.Add(self.item_choice, 0, 0, 0)
        top.Add(self.party_sep, 0, wx.ALL | wx.EXPAND, 2)
        top.Add(self.party_choice, 0, 0, 0)
        # End top row

        # Start middle row
        middle.Add(self.badge_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 2)
        middle.Add(self.atk_badge, 0, 0, 0)
        middle.Add(self.dfn_badge, 0, 0, 0)
        middle.Add(self.spd_badge, 0, 0, 0)
        middle.Add(self.spc_badge, 0, 0, 0)

        middle.Add(self.a_stage_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 20)
        middle.Add(self.a_atk_stage, 0, 0, 0)
        middle.Add(self.a_dfn_stage, 0, 0, 0)
        middle.Add(self.a_spd_stage, 0, 0, 0)
        middle.Add(self.a_spc_stage, 0, 0, 0)

        middle.Add(self.d_stage_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 20)
        middle.Add(self.d_atk_stage, 0, 0, 0)
        middle.Add(self.d_dfn_stage, 0, 0, 0)
        middle.Add(self.d_spd_stage, 0, 0, 0)
        middle.Add(self.d_spc_stage, 0, 0, 0)
        # End middle row

        bottom.Add(self.events_box, 1, wx.EXPAND, 0)
        bottom.Add(self.party_info, 1, wx.EXPAND, 0)
        bottom.Add(self.event_info, 1, wx.EXPAND, 0)

        vsizer.Add(top, 0, wx.EXPAND, 0)
        vsizer.Add(middle, 0, wx.EXPAND, 0)
        vsizer.Add(bottom, 1, wx.EXPAND, 0)

        self.panel.SetSizer(vsizer)
        self.panel.Layout()

    def on_save(self, e):
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.FD_SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            self.model.t_save(os.path.join(self.dirname, self.filename))
        dlg.Destroy()

    def on_open(self, e):
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            self.model.t_open(os.path.join(self.dirname, self.filename))
        dlg.Destroy()

    def update_model(self):
        self.model.poke_name = str(self.poke_name.GetValue())
        self.model.level = str(self.level.GetValue())
        self.model.is_wild = self.is_wild.GetValue()
        self.model.a_move_name = self.a_move_name.GetValue()
        self.model.d_move_name = self.d_move_name.GetValue()

        self.model.atk_boosts = self.atk_badge.GetValue()
        self.model.dfn_boosts = self.dfn_badge.GetValue()
        self.model.spd_boosts = self.spd_badge.GetValue()
        self.model.spc_boosts = self.spc_badge.GetValue()

        self.model.a_atk_stage = self.a_atk_stage.GetValue()
        self.model.a_dfn_stage = self.a_dfn_stage.GetValue()
        self.model.a_spd_stage = self.a_spd_stage.GetValue()
        self.model.a_spc_stage = self.a_spc_stage.GetValue()

        self.model.d_atk_stage = self.d_atk_stage.GetValue()
        self.model.d_dfn_stage = self.d_dfn_stage.GetValue()
        self.model.d_spd_stage = self.d_spd_stage.GetValue()
        self.model.d_spc_stage = self.d_spc_stage.GetValue()


    def history_key_down(self, e):
        if e.GetKeyCode() == wx.WXK_DELETE:
            self.model.t_delete_event(self.events_box.GetSelection())
        e.Skip()

    def update_events_box(self, data):
        self.events_box.Clear()
        self.events_box.AppendItems(data)
        self.update_from_model()

    def update_from_model(self):
        self.party_info.SetValue(model.party_info())
        self.event_info.SetValue(model.event_info())
        self.d_move_name.SetChoices(model.d_moveset)
        self.events_box.SetSelection(model._current_event - 1)

        party_choices = model.party_choices()
        if self.party_choice.GetItems() != party_choices:
            self.party_choice.Clear()
            self.party_choice.AppendItems(party_choices)
        self.party_choice.SetSelection(model._current_party)

    def __use_model(f):
        def g(self, *args, **kargs):
            self.update_model()
            f(self, *args, **kargs)
            self.update_from_model()
        return g

    @__use_model
    def on_add(self, e):
        self.model.t_add_to_party()

    @__use_model
    def on_share(self, e):
        self.model.t_share()

    @__use_model
    def on_defeat(self, e):
        self.model.t_defeat()

    @__use_model
    def on_new_a_move(self, e):
        pass

    @__use_model
    def on_new_d_move(self, e):
        pass

    @__use_model
    def on_new_boosts(self, e):
        pass

    @__use_model
    def on_party_switch(self, e):
        self.model.t_switch(self.party_choice.GetSelection())

    def on_new_item(self, e):
        self.model.t_use_item(str(self.item_choice.GetValue()))

    def move_in_history(self, e):
        self.model.advance_to(e.GetInt())
        self.update_from_model()

# Set taskbar icon on Windows
import os
if os.name == 'nt':
    import ctypes
    myappid = 'rbsim'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


model = model.Model()

app = wx.App(False)
frame = TopFrame(model, None, wx.ID_ANY, "")
app.SetTopWindow(frame)
frame.Show()

app.MainLoop()