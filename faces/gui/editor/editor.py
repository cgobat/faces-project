#@+leo-ver=4
#@+node:@file gui/editor/editor.py
#@@language python
#@<< Copyright >>
#@+node:<< Copyright >>
############################################################################
#   Copyright (C) 2005, 2006, 2007, 2008 by Reithinger GmbH
#   mreithinger@web.de
#
#   This file is part of faces.
#                                                                         
#   faces is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   faces is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the
#   Free Software Foundation, Inc.,
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
############################################################################

#@-node:<< Copyright >>
#@nl
"""
The Editor Control
"""
#@<< Imports >>
#@+node:<< Imports >>
import wx
import wx.lib.buttons as buttons
import re
import bisect
import faces
import faces.plocale
import faces.task as ftask
import faces.resource
import faces.gui.snapshot
import faces.generator
import docparser
import inspect
import weakref
import sys
import itertools
from classifiers import *
import metapie.gui.pyeditor as pyeditor
from context import Context, PTask
from metapie.gui import controller, ResourceManager
from dialogs import CalendarDialog

#@-node:<< Imports >>
#@nl
#@<< Editor Completions >>
#@+node:<< Editor Completions >>
_editor_completions = [ ("faces_show_call_tips", "faces_show_call_tips = False" ),
                        ("faces_dimmer_color", 'faces_dimmer_color = "#A0A0A0"' ),
                        ("faces_task_completions", 
                         'faces_task_completions = [ (\'notes\', \'notes = """\\n\\n"""\') ]'),
                         ("alt_week_locator", "alt_week_locator()") ]
#@nonl
#@-node:<< Editor Completions >>
#@nl

_is_source_ = True
_ = faces.plocale.get_gettext()

#@+others
#@+node:project_names
def is_project_name(n):
    try:
        return n[0] != "_" and issubclass(getattr(ftask, n), ftask._ProjectBase)
    except TypeError:
        return False

project_names = tuple([name for name in dir(ftask) if is_project_name(name)])

del is_project_name




#@-node:project_names
#@+node:Task CodeItem Functions
def get_code_item_path(code_item):
    item = code_item
    path = []
    while item:
        path.append(item.name)
        item = item.get_parent()

    path.reverse()
    path[0] = "root"
    return ".".join(path)

#@-node:Task CodeItem Functions
#@+node:class SearchTool
class SearchTool(pyeditor.SearchControl):
    #@	@+others
    #@+node:__init__
    def __init__(self, parent, id, editor, forward=True):
        pyeditor.SearchControl.__init__(self, parent, id, editor, forward)
        top = controller().get_top_menu()
        edit_menu = top.make_menu(_("&Edit"), pos=100)
        menu = lambda *args, **kw: edit_menu.make_item(self, *args, **kw)
        menu(_("&Find\tCTRL-F"), self.menu_find_forward)
        menu(_("Find &Backward\tCTRL-B"), self.menu_find_backward)
        self.SetToolTip(wx.ToolTip(_("Press Ctrl-F for next and Ctrl-B for "\
                                     "Prev\n and Ctrl-W for word")))
    #@-node:__init__
    #@-others
#@-node:class SearchTool
#@+node:class ContextButton
if 'wxMac' in wx.PlatformInfo:
    #a dummy context button to disable
    class ContextButton(wx.PyPanel):
        def __init__(self, editor):
            wx.PyPanel.__init__(self, editor)
            self.Hide()

        def set_bitmap(self, bmp_name): pass
        def hide(self): pass
        def move(self, x, y): pass
        def IsShown(self): return False
        def Show(self): pass

else:
    class ContextButton(wx.PyPanel):
        action = None
        #@        @+others
        #@+node:__init__
        def __init__(self, editor):
            wx.PyPanel.__init__(self, editor)
            self.button = buttons.GenBitmapButton(self, -1, None)
            def on_enter(evt): self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
            def on_action(evt): self.action and self.action(editor) or editor.SetFocus()
            self.button.Bind(wx.EVT_ENTER_WINDOW, on_enter)
            self.button.Bind(wx.EVT_BUTTON, on_action)


        #@-node:__init__
        #@+node:set_bitmap
        def set_bitmap(self, bmp_name):
            bmp = ResourceManager.load_bitmap(bmp_name)
            self.button.SetBitmapLabel(bmp)
            self.button.SetSize(self.button.GetBestSize())
            self.SetClientSize(self.button.GetSize())
            self.Refresh(False)
        #@nonl
        #@-node:set_bitmap
        #@+node:hide
        def hide(self):
            self.Hide()
            self.action = None
        #@nonl
        #@-node:hide
        #@+node:move
        def move(self, x, y):
            self.MoveXY(x, y)
            self.Hide()
            self.Show()
        #@nonl
        #@-node:move
        #@-others



#@-node:class ContextButton
#@+node:class ShadowStyler
class DimmerStyler(object):
    dimmer_color = "#f0aeb8"
    _marker_number = 1

    #@    @+others
    #@+node:__init__
    def __init__(self):
        self.__start_pos = self.__end_pos = 0
        self.MarkerDefine(self._marker_number, 
                          wx.stc.STC_MARK_BACKGROUND, 
                          "white", "white")
    #@-node:__init__
    #@+node:StyleSetSpec
    def StyleSetSpec(self, style_index, spec):
        if style_index != wx.stc.STC_STYLE_LINENUMBER: 
            spec += ",back:%s" % self.dimmer_color

        super(DimmerStyler, self).StyleSetSpec(style_index, spec)
    #@-node:StyleSetSpec
    #@+node:highlite
    def highlite(self, start_line=0, end_line=0):
        end_line = end_line or self.GetLineCount() - 1

        self.__start_pos = self.PositionFromLine(start_line)
        self.__end_pos = self.GetLineEndPosition(end_line)
        self.__last_style_end = 0

        self.Freeze()

        MarkerAdd = self.MarkerAdd
        marker_number = self._marker_number
        self.MarkerDeleteAll(marker_number)
        for i in range(start_line, end_line + 1):
            MarkerAdd(i, marker_number)

        self.Thaw()
    #@-node:highlite
    #@-others
#@-node:class ShadowStyler
#@+node:class Editor
class _EditorBase(pyeditor.PythonEditCtrl):
    #@    << _parse_evaluation >>
    #@+node:<< _parse_evaluation >>
    def _parse_evaluation(self, text):
        pos = text.index("=")
        if 0 <= text.find("#") < pos:
            return False

        self._type = EVALUATION
        self._name = text[:pos].strip()
        self._header = False
        return True

    #@-node:<< _parse_evaluation >>
    #@nl

class Editor(DimmerStyler, _EditorBase):
    #@	<< declarations >>
    #@+node:<< declarations >>
    show_call_tips = True
    task_completions = None

    _patterns = _EditorBase._patterns \
                + tuple(map(lambda p: ("[a-zA-Z0-9_.]+[ ]*=[ ]*%s(" % p, \
                                       _EditorBase._parse_evaluation), \
                            project_names))

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, model, parent):
        _EditorBase.__init__(self, parent, wx.SUNKEN_BORDER)
        DimmerStyler.__init__(self)

        self.model = weakref.proxy(model)
        self.macro = None
        self.last_char = None
        self.should_be_corrected = False

        self.context = Context.default
        self.context.activate(self, 0, None, None, False)
        self.context_button = ContextButton(self)
        self.context_button.hide()

        self.MarkerDefine(2, wx.stc.STC_MARK_ROUNDRECT, "blue", "blue")
        self.SetMarginWidth(1, 12)
        self.SetMarginMask(1, 5)

        self.SetModEventMask(wx.stc.STC_MOD_INSERTTEXT | \
                             wx.stc.STC_MOD_DELETETEXT | \
                             wx.stc.STC_MOD_CHANGEFOLD | \
                             wx.stc.STC_PERFORMED_UNDO | \
                             wx.stc.STC_PERFORMED_USER | \
                             wx.stc.STC_PERFORMED_REDO)

        #@    << Editor Adjustments >>
        #@+node:<< Editor Adjustments >>
        self.AutoCompStops("(){}[]")
        self.AutoCompSetSeparator(ord("\t"))
        self.AutoCompSetIgnoreCase(0)
        self.AutoCompSetDropRestOfWord(1)
        self.AutoCompSetAutoHide(1)
        self.SetCaretLineVisible(True)
        #@nonl
        #@-node:<< Editor Adjustments >>
        #@nl
        #@    << Bind Events >>
        #@+node:<< Bind Events >>
        self.Bind(wx.stc.EVT_STC_USERLISTSELECTION, self._on_insert_completion)
        self.Bind(wx.stc.EVT_STC_MACRORECORD, self._on_macro_notify)
        self.Bind(wx.EVT_RIGHT_DOWN, self._on_right_down)
        self.Bind(wx.EVT_SET_FOCUS, self._on_get_focus)

        self.Bind(wx.EVT_COMMAND_FIND, self._on_find)
        self.Bind(wx.EVT_COMMAND_FIND_NEXT, self._on_find)
        self.Bind(wx.EVT_COMMAND_FIND_REPLACE, self._on_find)
        self.Bind(wx.EVT_COMMAND_FIND_REPLACE_ALL, self._on_find)
        self.Bind(wx.EVT_FIND_CLOSE, self._on_find_close)
        #@-node:<< Bind Events >>
        #@nl
    #@-node:__init__
    #@+node:wxPython Methods
    #@+node:_on_pos_changed
    __pending_check_context = 0
    def _on_pos_changed(self, old, new):
        line = self.LineFromPosition(new)

        if self.LineFromPosition(old or 0) != line:
            def check_context():
                #enables fast scrolling without getting stuck
                self.__pending_check_context -= 1
                if self.__pending_check_context > 0: return
                self.__pending_check_context = 0
                self.check_context(line)
                self.context.make_button(self.context_button,
                                         self.get_expression(line))
                self.move_context_button()

            self.__pending_check_context += 1
            wx.FutureCall(70, check_context)

    #@-node:_on_pos_changed
    #@+node:_on_get_focus
    def _on_get_focus(self, event):
        event.Skip()

        try:
            parent = event.GetWindow().GetParent()
        except AttributeError:
            parent = None

        my_parent = self.GetParent()
        while parent:
            if parent is my_parent: return
            parent = parent.GetParent()

        self.set_menus()
    #@-node:_on_get_focus
    #@+node:_on_change
    __change_count = 0
    def _on_change(self, event):
        if not self.GetModify(): return

        mod_type = event.GetModificationType()
        line = self.GetCurrentLine()

        if mod_type & (wx.stc.STC_MOD_INSERTTEXT | 
                       wx.stc.STC_MOD_DELETETEXT):
            #@        << make backup if necessary >>
            #@+node:<< make backup if necessary >>
            self.__change_count += 1
            if self.__change_count >= 50:
                self.model.save_backup()
                self.__change_count = 0
            #@nonl
            #@-node:<< make backup if necessary >>
            #@nl
            #@        << change the context button if neccessary >>
            #@+node:<< change the context button if neccessary >>
            text = event.GetText()
            if text.find("=") >= 0 or not text.strip():
                self.context.make_button(self.context_button, 
                                         self.get_expression(line))
            #@nonl
            #@-node:<< change the context button if neccessary >>
            #@nl
            self.move_context_button()

        if mod_type & wx.stc.STC_MOD_CHANGEFOLD:
            line = self.GetCurrentLine()
            if line == event.GetLine():
                #@            << renew the context >>
                #@+node:<< renew the context >>
                self.check_context(line)
                self.context.make_button(self.context_button, 
                                         self.get_expression(line))
                self.move_context_button()
                #@nonl
                #@-node:<< renew the context >>
                #@nl

        _EditorBase._on_change(self, event)
        self.check_modified()
    #@-node:_on_change
    #@+node:_on_find_close
    def _on_find_close(self, event):
        event.GetDialog().Destroy()
        self.EndUndoAction()
    #@-node:_on_find_close
    #@+node:_on_find
    def _on_find(self, event):
        findstr = event.GetFindString()
        replacestr = event.GetReplaceString()
        ev_type = event.GetEventType()
        flags = event.GetFlags()

        macro = self.macro

        self.macro = None
        self.__find(findstr, replacestr, ev_type, flags)
        self.macro = macro
        if macro:
            macro.add_command(self.__find, findstr,
                              replacestr, ev_type, flags)
    #@-node:_on_find
    #@+node:_on_right_down
    def _on_right_down(self, event):
        top = controller().get_top_menu()
        menu = top.make_menu(_("&Edit"))
        self.PopupMenu(menu.wxobj, event.GetPosition())
    #@-node:_on_right_down
    #@+node:_on_new_char
    def _on_new_char(self, event):
        key_ascii = unichr(event.GetKey())
        self.last_char = key_ascii
        _EditorBase._on_new_char(self, event)
        self.show_completion()
    #@-node:_on_new_char
    #@+node:_on_macro_notify
    def _on_macro_notify(self, event):
        if self.macro:
            msg = event.GetMessage()
            if msg == 2170: # == REPLACE_SEL
                self.macro.add_command(self.smart_replace_selection,
                                       self.last_char)
            else:
                self.macro.add_command(self.CmdKeyExecute, msg)
    #@-node:_on_macro_notify
    #@+node:_on_insert_completion
    def _on_insert_completion(self, event):
        start_pos = event.GetListType() - 1
        text = event.GetText()[start_pos:].replace(r"\n", "\n")
        cur_pos = self.GetCurrentPos()
        self.AddText(text.replace("|", ""))
        lines = len(text.split("\n"))
        line = self.LineFromPosition(cur_pos)

        cursor = text.rfind("|")
        if cursor >= 0:
            self.GotoPos(cur_pos + cursor)

        for l in range(1, lines):
            self.autoindent(self.PositionFromLine(line + l), False)

        attrib = event.GetText()

        try:
            #if text has an = show the call tip for the assigned attribute
            attrib = attrib[:attrib.index("=")].strip()
        except ValueError:
            attrib = None

        self.show_call_tip(attrib=attrib)

    #@-node:_on_insert_completion
    #@-node:wxPython Methods
    #@+node:Menu Methods
    #@+node:set_menus
    def set_menus(self):
        self.model.set_menus()

        ctrl = controller()
        owner = ctrl.find_view_of(self)
        top = ctrl.get_top_menu()

        edit_menu = top.make_menu(_("&Edit"), pos=100)
        fold_menu = edit_menu.make_menu(_("Fold"), pos=1000)
        help_menu = top.make_menu(_("&Help"), pos=99999, id=wx.ID_HELP)
        file_menu = top.make_menu(_("&File"))

        menu = lambda *args, **kw: edit_menu.make_item(owner, *args, **kw)
        def nrc(func):
            def no_record_call():
                self.no_record_call(func)
            return no_record_call

        #@    << create help menu >>
        #@+node:<< create help menu >>
        help_menu.make_item(owner, _("Current Calltip\tCTRL-F1"),
                            self.show_call_tip, pos=10)
        #@nonl
        #@-node:<< create help menu >>
        #@nl
        #@    << create snapshot menu >>
        #@+node:<< create snapshot menu >>
        try:
            main_buffer_editor = ctrl.session.main_buffer.editor
        except AttributeError:
            main_buffer_editor = None

        file_menu.make_item(owner, _("&Create Snapshot..."),
            self.menu_snapshot, "stamp16", pos=45,
            help=_("Create a snapshot of the current project."))\
                .enable(main_buffer_editor is self.GetParent())
        #@nonl
        #@-node:<< create snapshot menu >>
        #@nl
        #@    << create basic edit menus >>
        #@+node:<< create basic edit menus >>
        #@<< copy & cut patch >>
        #@+node:<< copy & cut patch >>
        #self.Copy and self.Cut fill the clipoard only the second time
        #when they are called. ==> this is annyoing an they are replaced
        #by wxPython clipboard functions
        def copy(clear=False):
            txt = self.GetSelectedText()
            if txt:
                clipboard = wx.Clipboard_Get()
                if clipboard.Open():
                    clipboard.SetData(wx.TextDataObject(txt))
                    clipboard.Close()
                    if clear:
                        self.ReplaceSelection("")

        def cut():
            copy(True)
        #@-node:<< copy & cut patch >>
        #@nl

        menu(_("&Undo\tCTRL-Z"), nrc(self.Undo), "undo16", pos=100)
        menu(_("&Redo\tCTRL-R"), nrc(self.Redo), "redo16", pos=200)
        menu(_("Cut\tCTRL-X"), cut, "editcut16", pos=300)
        menu(_("&Copy\tCTRL-C"), nrc(copy), "editcopy16", pos=400)
        menu(_("&Paste\tCTRL-V"), nrc(self.Paste), "editpaste16", pos=500)
        menu(_("Insert &Date\tCTRL-D"), nrc(self.menu_insert_date), pos=550)
        #@-node:<< create basic edit menus >>
        #@nl
        #@    << create comment menus >>
        #@+node:<< create comment menus >>
        menu(_("Co&mment\tCTRL-#"), self.menu_comment_selection, pos=600)
        menu(_("&Uncomment"), self.menu_uncomment_selection, pos=601)
        #@nonl
        #@-node:<< create comment menus >>
        #@nl
        #@    << create bookmark menus >>
        #@+node:<< create bookmark menus >>
        menu(_("Toggle Bookmark\tCTRL-F2"), self.toggle_bookmark, pos=650)
        menu(_("Next Bookmark\tF2"), self.goto_next_bookmark, pos=651)
        menu(_("Previous Bookmark\tSHIFT-F2"), self.goto_prev_bookmark, pos=652)
        #@nonl
        #@-node:<< create bookmark menus >>
        #@nl
        #@    << create find menus >>
        #@+node:<< create find menus >>
        menu(_("&Find\tCTRL-F"), self.menu_find_forward, "find16", pos=700)
        menu(_("Find &Backward\tCTRL-B"), self.menu_find_backward, pos=710)
        menu(_("Replace"), self.menu_replace, pos=720)
        menu(_("Goto &Line\tCTRL-G"), self.menu_goto_line, pos=730)
        #@nonl
        #@-node:<< create find menus >>
        #@nl
        #@    << create macro menus >>
        #@+node:<< create macro menus >>
        mb = menu(_("Start Macro Recording"), self.start_macro, pos=900)
        ms = menu(_("Stop Macro Recording"), self.stop_macro, pos=901)
        me = menu(_("Execute Macro\tCTRL-E"), self.execute_macro, pos=902)

        self.menu_macro_start = mb
        self.menu_macro_stop = ms
        self.menu_macro_execute = me
        if ctrl.macro:
            mb.enable(False)
            me.enable(False)
            ms.enable(True)
        else:
            me.enable(bool(self.macro))
            mb.enable(True)
            ms.enable(False)
        #@nonl
        #@-node:<< create macro menus >>
        #@nl
        #@    << create context menu >>
        #@+node:<< create context menu >>
        def show_completion():
            wx.CallAfter(self.show_completion, True)

        menu(_("Context..."), show_completion, pos=1010)
        #@nonl
        #@-node:<< create context menu >>
        #@nl
        #@    << create correct code menu >>
        #@+node:<< create correct code menu >>
        project_menu = top.make_menu(_("&Project"), pos=110)
        project_menu.make_item(owner, _("Correct Code"), self.correct_code, pos=100, 
                               help=_("Tries to resolve broken references and renamed items"))
        project_menu.make_separator(_("Correct Code"))
        #@nonl
        #@-node:<< create correct code menu >>
        #@nl
        #@    << create menu separators >>
        #@+node:<< create menu separators >>
        edit_menu.make_separator(_("Co&mment"), True)
        edit_menu.make_separator(_("Toggle Bookmark"), True)
        edit_menu.make_separator(_("Cut"), True)
        edit_menu.make_separator(_("Find"), True)
        edit_menu.make_separator(_("Fold"), True)
        edit_menu.make_separator(_("Start Macro Recording"), True)
        #@nonl
        #@-node:<< create menu separators >>
        #@nl
        #@    << create fold menus >>
        #@+node:<< create fold menus >>
        def fmenu(level):
            def fold(): self.fold_to_level(level)
            fold_menu.make_item(owner,
                                _("To Level %i\tALT-%i") % (level, level),
                                fold)

        map(fmenu, range(0, 10))
        #@nonl
        #@-node:<< create fold menus >>
        #@nl
        #@    << create Generate HTML menu >>
        #@+node:<< create Generate HTML menu >>
        try:
            func = faces.generator.create_generate_html
        except AttributeError:
            pass
        else:
            menu = top.make_menu(_("&Tools"), pos=9980)
            menu.make_item(owner, _("Generate HTML..."), func(self), "run16", pos=10)
        #@nonl
        #@-node:<< create Generate HTML menu >>
        #@nl

        return True
    #@-node:set_menus
    #@+node:menu_snapshot
    def menu_snapshot(self):
        module = controller().session.get_module(self.model.path)
        create_snapshot = faces.gui.snapshot.create
        recalc, import_name = create_snapshot(module, self.model.get_encoding())
        if import_name:
            imports = filter(lambda c: c.obj_type == pyeditor.IMPORT,
                             self.code_items)
            if not imports:
                #don't know where to place the import statement
                #this case should never happen
                return

            line = imports[-1].get_last_line()
            self.InsertText(self.PositionFromLine(line),
                            _("import %s #This module contains snapshots\n")\
                            % import_name)
            self.sync_text()

        if recalc:
            controller().session.execute_plan()
    #@-node:menu_snapshot
    #@+node:menu_insert_date
    def menu_insert_date(self):
        dlg = CalendarDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            date = dlg.cal.GetDate()
            self.ReplaceSelection('"%s"' % date.FormatDate())

        dlg.Destroy()
    #@-node:menu_insert_date
    #@+node:menu_uncomment_selection
    __comment_lines_pattern = re.compile(r'^#+', re.MULTILINE)
    __free_lines_pattern = re.compile(r'^', re.MULTILINE)

    def menu_uncomment_selection(self):
        text = self.GetSelectedText()
        text = self.__comment_lines_pattern.sub("", text)
        self.ReplaceSelection(text)
    #@-node:menu_uncomment_selection
    #@+node:menu_comment_selection
    def menu_comment_selection(self):
        text = self.GetSelectedText()
        text = self.__free_lines_pattern.sub("#", text)
        self.ReplaceSelection(text)
    #@-node:menu_comment_selection
    #@+node:menu_find_forward
    def menu_find_forward(self):
        macro = controller().macro
        if macro: macro.pop()
        self.create_search(SearchTool)
    #@-node:menu_find_forward
    #@+node:menu_find_backward
    def menu_find_backward(self):
        macro = controller().macro
        if macro: macro.pop()
        self.create_search(SearchTool, False)
    #@-node:menu_find_backward
    #@+node:menu_replace
    def menu_replace(self):
        macro = controller().macro
        if macro: macro.pop()
        data = wx.FindReplaceData()
        data.SetFindString(self.GetSelectedText())
        dialog = wx.FindReplaceDialog(self, data, _("Replace"),
                                      wx.FR_REPLACEDIALOG)
        dialog.data = data
        dialog.Show(True)
        self.BeginUndoAction()
    #@-node:menu_replace
    #@+node:menu_goto_line
    def menu_goto_line(self):
        dialog = wx.TextEntryDialog(self, _("Goto Line"), _("Goto Line"))
        if dialog.ShowModal() == wx.ID_OK:
            val = int(dialog.GetValue()) - 1
            self.GotoLine(val)
            self.SetFocus()

        dialog.Destroy()
    #@-node:menu_goto_line
    #@-node:Menu Methods
    #@+node:Macro Methods
    #@+node:no_record_call
    def no_record_call(self, function, *args):
        macro = self.macro
        self.macro = None
        result = function(*args)
        self.macro = macro
        return result
    #@-node:no_record_call
    #@+node:start_macro
    def start_macro(self):
        self.menu_macro_execute.enable(False)
        self.menu_macro_start.enable(False)
        self.menu_macro_stop.enable(True)
        ctrl = controller()
        ctrl.status_bar.SetStatusText(_("Recording..."), 1)
        self.macro = ctrl.start_recording()
        self.StartRecord()
    #@-node:start_macro
    #@+node:stop_macro
    def stop_macro(self):
        self.menu_macro_stop.enable(False)
        self.menu_macro_start.enable(True)
        self.menu_macro_execute.enable(True)
        ctrl = controller()
        ctrl.status_bar.SetStatusText("", 1)
        self.StopRecord()
        ctrl.stop_recording()
    #@-node:stop_macro
    #@+node:execute_macro
    def execute_macro(self):
        if self.macro:
            if not self.macro.execute():
                self.macro = None
                self.menu_macro_execute.enable(False)
    #@-node:execute_macro
    #@+node:smart_replace_selection
    def smart_replace_selection(self, text):
        self.ReplaceSelection(text)
        self.inspect_indent_char(text)
    #@-node:smart_replace_selection
    #@+node:inspect_indent_char
    def inspect_indent_char(self, key):
        super_meth = _EditorBase.inspect_indent_char
        return self.no_record_call(super_meth, self, key)
    #@-node:inspect_indent_char
    #@-node:Macro Methods
    #@+node:Completion and Calltip Methods
    #@+node:guess_object
    def guess_object(self, name, pos=None, context=None):
        """
        try to calculate the value of variable "name", 
        by finding an assignment to name
        """
        #@    << calculate search end >>
        #@+node:<< calculate search end >>
        if not pos:
            if context:
                end = self.GetLineEndPosition(context.code_item.get_last_line())
            else:
                end = self.GetCurrentPos()
        #@nonl
        #@-node:<< calculate search end >>
        #@nl
        #@    << find context start line >>
        #@+node:<< find context start line >>
        context = context or self.context
        try:
            line = context.code_item.get_line()
        except AttributeError:
            line = 0

        #@-node:<< find context start line >>
        #@nl
        #@    << define find_last >>
        #@+node:<< define find_last >>
        find_str_eq = r"\<%s\>[^=]*=" % name
        find_str_in = r"for.*\<%s\>.*\<in\>" % name

        def find(start, fstr):
            pos = start
            while pos >= 0:
                last_pos = pos
                pos = self.FindText(pos + 1, end, fstr,
                                    wx.stc.STC_FIND_REGEXP\
                                    |wx.stc.STC_FIND_MATCHCASE)

            if last_pos <= start: last_pos = sys.maxint 
            return last_pos


        def find_last(pos):
            p1 = find(pos, find_str_eq)
            p2 = find(pos, find_str_in)
            pos = min(p1, p2)
            if p1 == p2: return -1, False
            return pos, pos == p2

        #@-node:<< define find_last >>
        #@nl
        pos, is_seq = find_last(self.PositionFromLine(line))

        if pos >= 0:
            expression = self.get_expression(self.LineFromPosition(pos))
            if is_seq:
                expression = expression[:expression.index(":")] + ": break"

            try:
                attribs = self.eval_expression(expression, {name : None},
                                               context=context)
                return attribs[name]
            except Exception: pass

        return None

    #@-node:guess_object
    #@+node:make_attrib_list
    def make_attrib_list(self, obj):
        def function_mapper(name):
            attr = getattr(obj, name, None)
            if not callable(attr): return name
            return getattr(attr, "__call_completion__", name)

        try:
            attrlist = obj.__all__
        except AttributeError:
            attrlist = dir(obj)

        return map(lambda x: (x, function_mapper(x)), \
                   filter(lambda n: n[0] != "_", attrlist or ()))
    #@nonl
    #@-node:make_attrib_list
    #@+node:get_dot_object
    def get_dot_object(self, name):
        first_dot = name.index(".")
        last_dot = name.rindex(".")

        root_name = name[:first_dot]
        obj = self.context.find_object(root_name)

        if obj is None:
            obj = self.guess_object(root_name)

        if obj is None:
            obj = getattr(self.get_module(), root_name, None)

        try:
            return eval("obj%s" % name[first_dot:last_dot])
        except:
            return None

    #@-node:get_dot_object
    #@+node:get_doc_object
    def get_doc_object(self, obj):
        if not obj or isinstance(obj, (int, basestring)): return None

        parser = docparser.ClassDoc
        if inspect.isfunction(obj) or inspect.ismethod(obj):
            parser = docparser.FunctionDoc
        elif inspect.ismodule(obj):
            parser = docparser.ModuleDoc
        elif not isinstance(obj, type):
            try:
                obj = obj.__class__
            except AttributeError:
                pass

        id_ = id(obj)
        try:
            return self.__doc_cache[id_]
        except AttributeError:
            self.__doc_cache = { id_ : parser(obj) }
        except KeyError:
            self.__doc_cache[id_] = parser(obj)

        return self.__doc_cache[id_]
    #@nonl
    #@-node:get_doc_object
    #@+node:get_word_at
    def get_word_at(self, pos=None, complete=False):
        pos = pos or self.GetCurrentPos()

        #get start of dot sequence
        start = self.WordStartPosition(pos, 1)
        char_before = chr(self.GetCharAt(start - 1))
        while(start > 0 and chr(self.GetCharAt(start - 1)) == "."):
            start = self.WordStartPosition(start - 1, 1)

        prev_word_start = self.WordStartPosition(start - 1, 1)
        if self.GetTextRange(prev_word_start, start).startswith("def"):
            #a def will be included despite the space to allow
            #the autocomplete of functions
            start = prev_word_start

        if complete:
            return self.GetTextRange(start, self.WordEndPosition(pos, 1))
        else:
            return self.GetTextRange(start, pos)
    #@-node:get_word_at
    #@+node:get_session_completions
    def get_session_completions(self, obj=None):
        module = self.get_module()
        try:
            return module.__attrib_completions__
        except AttributeError:
            return self.make_attrib_list(module)


    #@-node:get_session_completions
    #@+node:get_resource_completions
    def get_resource_completions(self, obj=None):
        return map(lambda r: (r, r), self.model.resources.keys())
    #@nonl
    #@-node:get_resource_completions
    #@+node:get_calendar_completions
    def get_calendar_completions(self, obj=None):
        return map(lambda r: (r, r), self.model.calendars.keys())
    #@nonl
    #@-node:get_calendar_completions
    #@+node:get_evaluation_completions
    def get_evaluation_completions(self, obj=None):
        return map(lambda kv: (kv[0], kv[0]), self.model.evaluations.iteritems())

    #@-node:get_evaluation_completions
    #@+node:show_completion
    #caching values
    __completion_list = None 
    __completion_dots = 0
    def show_completion(self, force=False):
        current = self.GetCurrentPos()

        text = self.get_word_at(current)
        auto_active = self.AutoCompActive()

        if not text and not force:
            if auto_active: self.AutoCompCancel()
            return

        #@    << check style >>
        #@+node:<< check style >>
        #no completion inside strings an comments
        style = self.GetStyleAt(current)
        if style in  (wx.stc.STC_P_TRIPLEDOUBLE,
                      wx.stc.STC_P_TRIPLE,
                      wx.stc.STC_P_STRING,
                      wx.stc.STC_P_COMMENTLINE,
                      wx.stc.STC_P_COMMENTBLOCK):
            return
        #@nonl
        #@-node:<< check style >>
        #@nl

        dots = len(filter(lambda c: c == ".", text))
        if not auto_active or self.__completion_dots != dots:
            try:
                #@            << try to create dot completion list >>
                #@+node:<< try to create dot completion list >>
                obj = self.get_dot_object(text)
                if obj:
                    self.__completion_list = self.make_attrib_list(obj)
                else:
                    self.__completion_list = None
                #@-node:<< try to create dot completion list >>
                #@nl
            except ValueError:            
                #@            << create non dot completion list >>
                #@+node:<< create non dot completion list >>
                line = self.LineFromPosition(current)
                start = self.PositionFromLine(line)
                subname = self.GetTextRange(start, current)
                try:
                    subname = subname[:subname.index("=")].strip()
                except ValueError:
                    try:
                        subname = subname[:subname.index("(")].strip()
                    except ValueError:
                        subname = None

                if subname:
                    self.__completion_list = self.context.get_sub_completion_list(subname)
                else:
                    self.__completion_list = self.context.get_main_completion_list()

                #@-node:<< create non dot completion list >>
                #@nl

            self.__completion_dots = dots

        compl = self.__completion_list
        if compl is None: return
        if not compl:
            #@        << find an alternative completion list >>
            #@+node:<< find an alternative completion list >>
            compl = self.__completion_list = self.get_session_completions()
            try:
                if self.context.code_item.obj_type == pyeditor.FUNCTION:
                    args = self.context.code_item.get_args()
                    compl += map(lambda a: (a, a), args)
            except AttributeError: pass
            #@nonl
            #@-node:<< find an alternative completion list >>
            #@nl

        #@    << show list >>
        #@+node:<< show list >>
        try:
            # cut of last token of dot sequence
            text = text[text.rindex(".") + 1:] 
        except ValueError: pass

        compl = filter(lambda c: c[0].startswith(text), compl)
        if not compl: return

        if len(compl) == 1 and text == compl[0][0]:
            try:
                self.show_call_tip()
            except AttributeError: pass
            return  

        compl = [ c[1].replace("\n", r"\n") for c in compl ]
        compl.sort()
        self.UserListShow(len(text) + 1, "\t".join(compl))
        #@-node:<< show list >>
        #@nl

    #@-node:show_completion
    #@+node:show_call_tip
    def show_call_tip(self, obj=None, attrib=None):
        if not self.show_call_tips: return False

        #@    << calculate obj and attrib >>
        #@+node:<< calculate obj and attrib >>
        attrib = attrib or self.get_word_at(complete=True)
        try:
            #attrib contains dots
            obj = self.get_dot_object(attrib)
            attrib = attrib[attrib.rindex(".") + 1:] 
        except ValueError:
            try:
                obj = obj or self.context.code_item.obj
            except AttributeError: pass
        #@-node:<< calculate obj and attrib >>
        #@nl

        doc = self.get_doc_object(obj)
        doc = doc and doc.get_doc(attrib)
        if not doc:
            try:
                val = getattr(obj, attrib)
            except AttributeError:
                val = getattr(self.get_module(), attrib, None)

            if isinstance(val, (ftask.Task, PTask)):
                doc = 0, val.title
            else:
                doc = self.get_doc_object(val)
                doc = doc and doc.constructor(attrib)
        else:
            pass

        if doc:
            txt = doc[1].decode(self.model.get_encoding(), 'ignore')
            self.CallTipShow(self.GetCurrentPos(), txt)
            self.CallTipSetHighlight(0, doc[0])
            return True

        return False

    #@-node:show_call_tip
    #@-node:Completion and Calltip Methods
    #@+node:Misc Methods
    #@+node:show_task
    def show_task(self, search_task, attrib=None, caller=None):
        obj = None
        item = None

        def context_result(found_item, found_attrib=False):
            if attrib is not None: return found_item, found_attrib
            return found_item

        for item in self.code_items:
            obj = getattr(item, "obj", None)
            if isinstance(obj, ftask.Task):
                if obj._function.func_code is search_task._function.func_code:
                    break
        else:
            return context_result(False)

        item_line = item.get_line()

        def goto_declaration():
            start = self.PositionFromLine(item_line)
            end = self.GetLineEndPosition(item_line)
            pos = self.FindText(start, end, "def", 0)
            self.GotoPos(pos + 3)
            self.WordPartRight()
            return context_result(True)

        self.LineScroll(0, item_line - self.GetFirstVisibleLine())
        if not attrib:
            return goto_declaration()

        line = min(item.get_last_line(), self.next_item_line(item_line + 1))
        start = self.GetLineEndPosition(line)
        end = self.GetLineEndPosition(item_line)
        pos = self.FindText(start, end, attrib, 0)
        if pos < 0:
            return goto_declaration()

        end = start
        start = pos + len(attrib)

        line_end = self.GetLineEndPosition(self.LineFromPosition(start))
        if self.FindText(start, end, "=") < 0:
            # attribs have always a = behind
            return goto_declaration()

        scenario = search_task.root.scenario
        tpos = self.FindText(start, end, scenario, 0)
        if tpos >= 0: start = tpos + len(scenario)

        org_val = search_task._original_values.get(attrib, "") or \
                  getattr(search_task, attrib, "")

        try:
            org_val = org_val.decode(self.model.get_encoding())
        except AttributeError:
            org_val = str(org_val)

        if org_val:
            tpos = self.FindText(start, end, org_val, 0)
            if tpos > 0:
                self.GotoPos(tpos)
                self.SetSelectionEnd(tpos + len(org_val))
                return True, True

        self.GotoPos(pos)
        return True, False
    #@-node:show_task
    #@+node:show_object
    def show_object(self, search_object, attrib=None, caller=None):
        if hasattr(search_object, "_function"):
            return self.show_task(search_object, attrib, caller)

        for c in self.code_items:
            if getattr(c, "obj", None) is search_object:
                line = c.get_line()
                self.LineScroll(0, line - self.GetFirstVisibleLine())
                start = self.PositionFromLine(line)
                end = self.GetLineEndPosition(line)
                pos = self.FindText(start, end, "class", 0)
                self.GotoPos(pos + 4)
                self.WordPartRight()
                return True

        return False
    #@-node:show_object
    #@+node:check_modified
    def check_modified(self):
        frame = controller().frame
        try:
            if self.GetModify():
                self.model.modified(True)
                frame.SetStatusText("C", 1)
            else:
                frame.SetStatusText("", 1)
                self.model.modified(False)
        except AttributeError:
            pass
    #@-node:check_modified
    #@+node:sync_text
    def sync_text(self, reset_savepoint=False):
        try:
            self.model.text = self.GetText().encode(self.model.get_encoding())
        except AttributeError:
            pass
        else:
            if self.model.text[-1] != "\n":
                self.model.text += "\n"

        if reset_savepoint:
            self.SetSavePoint()
            self.check_modified()
    #@-node:sync_text
    #@+node:refresh
    __last_module_id = 0
    def refresh(self, refresh_text=False):
        module = self.get_module()
        if not refresh_text:
            #@        << module settings >>
            #@+node:<< module settings >>
            if self.__last_module_id != id(module):
                self.browse_code()
                if module: 
                    self.update_code_info(module)
                    self.show_call_tips = getattr(module, "faces_show_call_tips", True)
                    self.dimmer_color = getattr(module, "faces_dimmer_color", "#f0aeb8")
                    self.task_completions = getattr(module, "faces_task_completions", None)

                self.check_context(self.GetCurrentLine())
                self.GetParent().browser.refresh()
                self.__last_module_id = id(module)


            self.setup_style()
            #@-node:<< module settings >>
            #@nl
            return

        self.Freeze()
        self.unlisten()

        if self.AutoCompActive(): self.AutoCompCancel()
        model = self.model

        #@    << save current position >>
        #@+node:<< save current position >>
        pos = self.GetCurrentPos()
        line = self.GetFirstVisibleLine()
        offset = self.GetXOffset()
        #@nonl
        #@-node:<< save current position >>
        #@nl
        #@    << create new document >>
        #@+node:<< create new document >>
        self.SetUndoCollection(0)
        self.SetText(unicode(model.text, model.get_encoding(), "replace"))
        self.SetSavePoint()
        self.SetUndoCollection(1)
        #@nonl
        #@-node:<< create new document >>
        #@nl
        #@    << misc document settings >>
        #@+node:<< misc document settings >>
        self.setup_eol()
        self.SetCodePage(wx.stc.STC_CP_UTF8)
        self.__change_count = 0
        self.check_modified()
        #@nonl
        #@-node:<< misc document settings >>
        #@nl
        #@    << module settings >>
        #@+node:<< module settings >>
        if self.__last_module_id != id(module):
            self.browse_code()
            if module: 
                self.update_code_info(module)
                self.show_call_tips = getattr(module, "faces_show_call_tips", True)
                self.dimmer_color = getattr(module, "faces_dimmer_color", "#f0aeb8")
                self.task_completions = getattr(module, "faces_task_completions", None)

            self.check_context(self.GetCurrentLine())
            self.GetParent().browser.refresh()
            self.__last_module_id = id(module)


        self.setup_style()
        #@-node:<< module settings >>
        #@nl
        #@    << restore position >>
        #@+node:<< restore position >>
        self.GotoPos(pos)
        self.LineScroll(0, line - self.GetFirstVisibleLine())
        self.SetXOffset(offset)
        self.check_context(self.LineFromPosition(pos))
        #@-node:<< restore position >>
        #@nl

        self.check_context(line)
        self.listen()
        self.Thaw()
    #@-node:refresh
    #@+node:update_code_info
    def update_code_info(self, module=None):
        session = controller().session
        path = self.model.path

        for varname, eval in session.evaluations.iteritems():
            #@        << assign tasks to code_items >>
            #@+node:<< assign tasks to code_items >>
            for t in eval:
                code = t._function.func_code
                if path != code.co_filename: continue
                line = code.co_firstlineno
                item = self.code_item_at(line - 1)
                if item and item.name == t.name:
                    item.obj = t
                    # The next assignments are needed in correct_code and find_task_references
                    item.task_path = t.path 
                    t._function.code_item = weakref.proxy(item)
            #@-node:<< assign tasks to code_items >>
            #@nl

        #@    << assign observers and resources to code_items >>
        #@+node:<< assign observers and resources to code_items >>
        is_class = lambda i: i.obj_type == pyeditor.CLASS
        for ci in filter(is_class, self.code_items):
            v = module.__dict__.get(ci.name)
            if inspect.isclass(v): ci.obj = v
        #@nonl
        #@-node:<< assign observers and resources to code_items >>
        #@nl
        #@    << assign evaluations to code_items >>
        #@+node:<< assign evaluations to code_items >>
        for ci in filter(is_evaluation, self.code_items):
            v = module.__dict__.get(ci.name)
            if isinstance(v, ftask._ProjectBase): ci.obj = v
        #@nonl
        #@-node:<< assign evaluations to code_items >>
        #@nl
    #@-node:update_code_info
    #@+node:get_module
    def get_module(self):
        return controller().session.get_module(self.model.path)
    #@-node:get_module
    #@+node:check_context
    __last_attrib = None
    def check_context(self, line):
        prev, next = self.code_items_near(line)
        inside = self.code_item_at(line)
        ctrl = controller()

        last_code_item = self.context.code_item
        #@    << find and activate the current context >>
        #@+node:<< find and activate the current context >>
        if not self.context.activate(self, line, prev, next, inside):
            #oldc = self.context
            for c in Context.context_list:
                if self.context is c: continue
                if c.activate(self, line, prev, next, inside):
                    self.context = c
                    break
            else:
                c = self.context = Context.default
                c.activate(self, line, prev, next, inside)
        #@nonl
        #@-node:<< find and activate the current context >>
        #@nl
        update_siblings = False
        if last_code_item is not self.context.code_item:
            item = self.context.code_item
            #@        << update browser and refresh >>
            #@+node:<< update browser and refresh >>
            self.Refresh(False)
            if item: self.GetParent().browser.update_selection(item)

            #@-node:<< update browser and refresh >>
            #@nl
            #@        << highlite context >>
            #@+node:<< highlite context >>
            try:
                self.highlite(item.get_line(), item.get_last_line())
            except AttributeError:
                self.highlite()
            #@nonl
            #@-node:<< highlite context >>
            #@nl

            update_siblings = True
            self.__last_attrib  = None

        #@    << calculate attribute name >>
        #@+node:<< calculate attribute name >>
        line = self.GetLine(line)
        try:
            attrib_name = line[:line.index("=")].strip()
        except ValueError:
            attrib_name = None
        #@nonl
        #@-node:<< calculate attribute name >>
        #@nl

        update_siblings += attrib_name != self.__last_attrib
        if update_siblings:
            #@        << update my siblings >>
            #@+node:<< update my siblings >>
            if wx.Window_FindFocus() is self:
                try:
                    self.model.show_object(self.GetParent().GetParent(), 
                                           self.context.code_item.obj, 
                                           attrib_name)
                except AttributeError:
                    pass

            self.__last_attrib = attrib_name
            #@-node:<< update my siblings >>
            #@nl
    #@-node:check_context
    #@+node:__find
    def __find(self, findstr, replacestr, ev_type, flags):
        sflags = 0

        if flags & wx.FR_WHOLEWORD: sflags |= wx.stc.STC_FIND_WHOLEWORD
        if flags & wx.FR_MATCHCASE: sflags |= wx.stc.STC_FIND_MATCHCASE

        utf8findstr = findstr.encode("utf-8", "ignore") # a bug in scincilla

        if ev_type == wx.wxEVT_COMMAND_FIND_REPLACE_ALL:
            self.BeginUndoAction()
            end = self.GetLength()
            start = self.FindText(0, end, findstr, sflags)
            while start >= 0:
                self.GotoPos(start)
                self.SetSelectionEnd(start + len(utf8findstr))
                self.ReplaceSelection(replacestr)
                start = self.FindText(start + len(utf8findstr),
                                      end, findstr, sflags)

            self.EndUndoAction()
            return

        if flags & wx.FR_DOWN:
            start = self.GetCurrentPos() + 1
            end = self.GetLength()
        else:
            start = self.GetSelectionStart() - 1
            end = 0

        pos = self.FindText(start, end, findstr, sflags)
        if pos > 0:
            self.GotoPos(pos)
            self.SetSelectionEnd(pos + len(utf8findstr))
            if ev_type == wx.wxEVT_COMMAND_FIND_REPLACE:
                self.ReplaceSelection(replacestr)
                self.GotoPos(pos)
                self.SetSelectionEnd(pos + len(replacestr))
    #@-node:__find
    #@+node:move_context_button
    def move_context_button(self):
        if self.context_button.IsShown():
            line = self.GetCurrentLine()
            pos = self.GetLineEndPosition(line)
            pos = self.PointFromPosition(pos)
            w, h = self.context_button.GetSize()
            th = self.TextHeight(line)
            self.context_button.move(pos.x + 10, pos.y + (th - h) / 2)
    #@nonl
    #@-node:move_context_button
    #@+node:toggle_bookmark
    def toggle_bookmark(self): 
        line = self.GetCurrentLine()
        if self.MarkerGet(line) & 4:
            self.MarkerDelete(line, 2)
        else:
            self.MarkerAdd(line, 2)
    #@nonl
    #@-node:toggle_bookmark
    #@+node:goto_next_bookmark
    def goto_next_bookmark(self):
        next = self.MarkerNext(self.GetCurrentLine() + 1, 4)
        if next < 0:
            next = self.MarkerNext(0, 4)

        if next >= 0:
            self.GotoLine(next)
    #@-node:goto_next_bookmark
    #@+node:goto_prev_bookmark
    def goto_prev_bookmark(self):
        prev = self.MarkerPrevious(self.GetCurrentLine() - 1, 4)
        if prev < 0:
            prev = self.MarkerPrevious(self.GetLineCount(), 4)

        if prev >= 0:
            self.GotoLine(prev)
    #@-node:goto_prev_bookmark
    #@-node:Misc Methods
    #@+node:Methods for external editing
    #@+node:find_resource_references
    #@+doc
    # returns the code_item, the found line, and the start and end position
    #@-doc
    #@@code
    def find_resource_references(self, resource_name):
        for ci in self.code_items:
            if is_task(ci) or is_project(ci):
                try:
                    line = self.get_attribs(ci)["resource"]
                except KeyError: continue

                start, end = self.get_expression_range(line)
                try:
                    self.GetTextRange(start, end).index(resource_name)
                    yield ci, line, start, end
                except ValueError: pass

    #@-node:find_resource_references
    #@+node:find_task_references
    #@+doc
    # code_item has to be a reference on a task
    #@-doc
    #@@code
    def find_task_references(self, code_item):
        try:
            task = code_item.obj
        except AttributeError: return

        #tasks and tasks children dependencies
        dependencies = reduce(lambda a, b: a + b, 
                              [ t._dependencies.values() for t in task ])

        for path_attrib_map in dependencies:
            for path_attrib in path_attrib_map.iterkeys():        
                path, attrib = ftask._split_path(path_attrib)
                dst = task.get_task(path)

                try:
                    dst_item = dst._function.code_item
                except AttributeError: continue
                except weakref.ReferenceError: continue

                try:
                    line = self.get_attribs(dst_item)[attrib]
                except KeyError: continue

                yield dst_item, attrib, line
    #@-node:find_task_references
    #@+node:find_evaluation_references
    #@+doc
    # returns the code_item and the found line
    #@-doc
    #@@code
    def find_evaluation_references(self, code_item):
        evaluation_name = code_item.name
        start = self.PositionFromLine(code_item.get_line() + 1)
        end = self.GetLength()
        while True:
            start = self.FindText(start, end, evaluation_name, \
                                  wx.stc.STC_FIND_MATCHCASE\
                                  |wx.stc.STC_FIND_WHOLEWORD)
            if start < 0: break
            line = self.LineFromPosition(start)
            start += 1
            text = self.GetLine(line)
            try:
                #comments are no references
                if text.index("#") < text.index(evaluation_name): continue
            except ValueError: pass

            yield self.code_item_at(line), line


    #@-node:find_evaluation_references
    #@+node:correct_code
    __correct_code_cal = False
    def correct_code(self):
        if self.__correct_code_cal: return
        self.__correct_code_cal = True

        self.should_be_corrected = False

        self.BeginUndoAction()

        ctrl = controller()
        task_items = [ i for i in self.code_items if is_task(i) or is_project(i)]
        resource_items = [ i for i in self.code_items if is_resource(i) ]    

        ctrl.progress_start(_("correct code"), 
                            len(task_items) + len(resource_items))

        counter = 1

        for ti in task_items: 
            self.correct_task_code(ti)
            ctrl.progress_update(counter)
            counter += 1

        for r in resource_items:
            self.correct_resource_code(r)
            ctrl.progress_update(counter)
            counter += 1

        ctrl.progress_end()            
        self.EndUndoAction()
        self.__correct_code_cal = False
    #@-node:correct_code
    #@+node:correct_task_code
    def correct_task_code(self, code_item):
        self.BeginUndoAction()
        try:
            task = code_item.obj
            old_path = code_item.task_path
        except AttributeError: return

        path = get_code_item_path(code_item)
        if path == old_path: return

        code_item.task_path = path
        #@    << change all relative paths of my sources >>
        #@+node:<< change all relative paths of my sources >>
        attribs = self.get_attribs(code_item)
        for attrib, source_path_attribs in task._sources.iteritems():
            try:
                line = attribs[attrib]
            except KeyError: continue

            expr = self.get_expression(line)

            for path_attrib in source_path_attribs:
                spath, attrib = ftask._split_path(path_attrib)
                stask = task.get_task(spath)

                try:
                    sitem = stask._function.code_item
                except AttributeError: continue
                except weakref.ReferenceError: continue

                spath = get_code_item_path(sitem)
                rel_path = ftask.create_relative_path(path, spath)
                old_rel_path = ftask.create_relative_path(old_path, spath)
                expr = expr.replace(old_rel_path, rel_path)

            expr = "\n".join([s.strip() for s in expr.split("\n")]) #strip each line
            self.replace_expression(expr, line, move_cursor=False)
        #@-node:<< change all relative paths of my sources >>
        #@nl
        #@    << change the path in all tasks that depend on me >>
        #@+node:<< change the path in all tasks that depend on me >>
        for dst_item, attrib, line in self.find_task_references(code_item):
            dst_path = get_code_item_path(dst_item)
            expr = self.get_expression(line)

            rel_path = ftask.create_relative_path(dst_path, path)
            old_rel_path = ftask.create_relative_path(dst_path, old_path)
            expr = expr.replace(old_rel_path, rel_path)
            expr = expr.replace(old_path, path)
            expr = "\n".join([s.strip() for s in expr.split("\n")]) #strip each line
            self.replace_expression(expr, line, move_cursor=False)
        #@-node:<< change the path in all tasks that depend on me >>
        #@nl
        self.EndUndoAction()
    #@-node:correct_task_code
    #@+node:correct_resource_code
    def correct_resource_code(self, code_item):
        try:
            if code_item.obj.name == code_item.name: return
        except AttributeError: return

        refs = self.find_resource_references(code_item.obj.name)
        for ci, line, start, end in refs:
            text = self.GetTextRange(start, end)
            self.SetTargetStart(start)
            self.SetTargetEnd(end)
            self.ReplaceTarget(text.replace(code_item.obj.name,
                                            code_item.name))

        code_item.obj.name = code_item.name
    #@-node:correct_resource_code
    #@+node:get_attribs
    __assignment_pattern = re.compile(r'([^=#]+)=[^=]')

    def get_attribs(self, code_item):
        """
        get all assigned attribs of code_item
        """
        code_line = code_item.get_line()
        last_code_line = code_item.get_last_line() + 1
        lines = xrange(code_line, last_code_line)

        #@    << filter out child code >>
        #@+node:<< filter out child code >>
        nline = self.next_item_line(code_line + 1)
        if nline < last_code_line:
            indent = self.GetLineIndentation(nline)
            lines = [ i for i in lines if self.GetLineIndentation(i) <= indent ]
        #@nonl
        #@-node:<< filter out child code >>
        #@nl

        if code_item.obj_type == pyeditor.FUNCTION:
            def get_attrib(line):
                text = self.GetLine(line)
                mo = self.__assignment_pattern.match(text)
                return mo and (mo.group(1).strip(), line)
        else:
            def get_attrib(line):
                text = self.GetLine(line)
                mo = self.__assignment_pattern.match(text)
                return mo and (mo.group(1).strip(), line)

        return dict(filter(bool, [ get_attrib(l) for l in lines ]))



    #@-node:get_attribs
    #@+node:eval_expression
    def eval_expression(self, expression, globvars={}, context=None):
        locdict = { }
        context = context or self.context

        if globvars:
            globdict = self.get_module().__dict__.copy()
            globdict.update(globvars)
        else:
            globdict = self.get_module().__dict__

        while True:
            try:
                exec expression in globdict, locdict
                return locdict
            except NameError, e:
                name = str(e).split("'")[1]
                obj = context.find_object(name)
                if obj is None:
                    obj = self.guess_object(name, context=context)

                if obj is None or globdict.has_key(name):
                    # may be a python bug but "globdict.has_key(name)" can happen!
                    raise

                globdict[name] = obj

    #@-node:eval_expression
    #@+node:get_expression_range
    def get_expression_range(self, line=None, with_end=False):
        """
        returns the start and end pos of the expression at line
        Note: the expression can go over several lines
        """
        line = line or self.GetCurrentLine()
        indent = self.GetLineIndentation
        length = self.LineLength
        text = self.GetLine
        takewhile = itertools.takewhile

        #@    << find start of expression >>
        #@+node:<< find start of expression >>
        try:    
            min_line = self.find_parent_line(line)
        except ValueError:
            block_indent = 0
            min_line = -1
        else:
            block_indent = indent(min_line + 1)

        is_sub_block = lambda l: indent(l) > block_indent
        lines = tuple(takewhile(is_sub_block, xrange(line, min_line, -1)))
        start_line = lines and lines[-1] - 1 or line

        #@-node:<< find start of expression >>
        #@nl
        #@    << find end of expression >>
        #@+node:<< find end of expression >>
        def is_child(l):
            cindent = indent(l)
            return cindent > block_indent or cindent == length(l) - 1

        def has_content(l):
            return indent(l) < length(l) - 1

        lines = filter(has_content, 
                       takewhile(is_child, xrange(line + 1, self.GetLineCount())))

        end_line = lines and lines[-1] or line
        #@-node:<< find end of expression >>
        #@nl

        return self.GetLineIndentPosition(start_line), \
               self.GetLineEndPosition(end_line) + bool(with_end)

    #@-node:get_expression_range
    #@+node:find_parent_line
    def find_parent_line(self, line_no):
        """
        returns the parent line of line
        """

        find = self.FindText
        line = self.LineFromPosition
        end = self.GetLineEndPosition
        text = self.GetTextRange
        indent = self.GetLineIndentation

        child_indent = indent(line_no)
        pos = self.PositionFromLine(line_no)
        pos = find(pos, 0, ":")
        while pos >= 0:
            #@        << check if pos ident is smaller >>
            #@+node:<< check if pos ident is smaller >>
            if indent(line(pos)) >= child_indent:
                pos = find(pos - 1, 0, ":")
                continue
            #@nonl
            #@-node:<< check if pos ident is smaller >>
            #@nl
            #@        << check if pos is not in a string or comment >>
            #@+node:<< check if pos is not in a string or comment >>
            style = self.GetStyleAt(pos)
            if style in  (wx.stc.STC_P_TRIPLEDOUBLE,
                          wx.stc.STC_P_TRIPLE,
                          wx.stc.STC_P_STRING,
                          wx.stc.STC_P_COMMENTLINE,
                          wx.stc.STC_P_COMMENTBLOCK):
                pos = find(pos - 1, 0, ":")
                continue
            #@nonl
            #@-node:<< check if pos is not in a string or comment >>
            #@nl
            #@        << check if pos is at the end of an expression >>
            #@+node:<< check if pos is at the end of an expression >>
            rest_text = text(pos, end(line(pos))).split()
            try:
                if not rest_text[1].startswith("#"): 
                    pos = find(pos - 1, 0, ":")
                    continue
            except IndexError: pass
            break
            #@nonl
            #@-node:<< check if pos is at the end of an expression >>
            #@nl
        else:
            raise ValueError("no parent line")

        return line(pos)
    #@-node:find_parent_line
    #@+node:get_expression
    def get_expression(self, line=None):
        start, end = self.get_expression_range(line)
        return self.GetTextRangeUTF8(start, end).strip()

    #@-node:get_expression
    #@+node:replace_expression
    def replace_expression(self, text, start_line=None, with_end=False, move_cursor=True):
        self.BeginUndoAction()

        start, end = self.get_expression_range(start_line, with_end)
        start_line = self.LineFromPosition(start)
        start_indent = self.GetLineIndentation(start_line)

        if start < end:
            self.SetTargetStart(start)
            self.SetTargetEnd(end)
            self.ReplaceTarget(text)
        else:
            self.InsertText(start, text)

        if move_cursor: self.GotoPos(start + len(text))

        lines = text.split("\n")
        #@    << auto indent text >>
        #@+node:<< auto indent text >>
        #scincilla has to format the text before we can correctly autoindent
        self.Colourise(start, start + len(text))
        self.SetLineIndentation(start_line, start_indent)
        line = start_line
        for line, line_text in enumerate(lines[1:]):
            line += start_line + 1
            self.autoindent(self.PositionFromLine(line), False)
        #@nonl
        #@-node:<< auto indent text >>
        #@nl
        self.EndUndoAction()
        self.check_code_updates(start_line, line)
    #@-node:replace_expression
    #@+node:insert_expression
    def insert_expression(self, code_item, text, move_cursor=True):
        """
        insert the expression after the last non empty line 
        before the first child
        """
        self.BeginUndoAction()
        line = code_item.get_line()
        indent = code_item.indent
        next_line = self.next_item_line(line + 1)
        for i in range(next_line - 1, line - 1, -1):
            if self.GetLineIndentation(i) > indent \
                and self.GetLine(i).strip():
                break

        start_line = i + 1
        text += "\n"
        if self.GetLine(start_line).strip():
            start_line -= 1
            text = "\n" + text

        start = self.GetLineEndPosition(start_line)
        self.InsertText(start, text)

        if move_cursor: self.GotoPos(start + len(text))

        lines = text.split("\n")
        self.UpdateWindowUI()
        #@    << auto indent text >>
        #@+node:<< auto indent text >>
        #scincilla has to format the text before we can correctly autoindent
        self.Colourise(start, start + len(text))
        for line, line_text in enumerate(lines):
            line += start_line
            self.autoindent(self.PositionFromLine(line), False)
        #@nonl
        #@-node:<< auto indent text >>
        #@nl
        self.EndUndoAction()

    #@-node:insert_expression
    #@-node:Methods for external editing
    #@-others
#@-node:class Editor
#@-others
#@-node:@file gui/editor/editor.py
#@-leo
