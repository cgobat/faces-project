#@+leo-ver=4
#@+node:@file gui/editor/__init__.py
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
#@<< Imports >>
#@+node:<< Imports >>
from browser import Browser
from editor import Editor
from metapie.gui import controller
from metapie.navigator import View
import weakref
import ConfigParser
import wx
import faces.plocale
import faces.gui.editor.task
import faces.gui.editor.resource
#@nonl
#@-node:<< Imports >>
#@nl

_is_source_ = True
_ = faces.plocale.get_gettext()

#@+others
#@+node:is_bool_option
def is_bool_option(name, default=True):
    try:
        return controller().config.getboolean("DEFAULT", name)
    except ConfigParser.NoOptionError:
        return default
#@-node:is_bool_option
#@+node:class PlanEditorProxy
class PlanEditorProxy(wx.PyPanel, View):
    #@    @+others
    #@+node:__init__
    def __init__(self, model, parent):
        wx.PyPanel.__init__(self, parent)

        self.model = weakref.ref(model)
        editor = model.editor
        editor.show(self)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(editor, 1, wx.EXPAND)
        self.SetSizer(sizer)

        #@    << redirect methods >>
        #@+node:<< redirect methods >>
        self.show_object = editor.show_object
        self.sync_text = editor.sync_text
        self.refresh = editor.refresh
        self.goto_line = editor.goto_line
        self.find_in_source = editor.find_in_source
        self.SetFocus = editor.editor.SetFocus
        self.on_make_menu = editor.browser.on_make_menu
        self.find_resource_references = editor.find_resource_references
        self.find_task_references = editor.find_task_references
        #@nonl
        #@-node:<< redirect methods >>
        #@nl
    #@-node:__init__
    #@+node:Destroy
    def Destroy(self):
        editor = self.GetChildren()[0]
        self.GetSizer().Detach(editor)
        editor.hide()
        wx.PyPanel.Destroy(self)
    #@-node:Destroy
    #@-others
#@-node:class PlanEditorProxy
#@+node:class PlanEditor
class PlanEditor(wx.SplitterWindow):
    #@	@+others
    #@+node:__init__
    def __init__(self, model):
        wx.SplitterWindow.__init__(self, controller().hidden_parent, 
                                   -1, style=wx.SP_3DSASH)
        self.browser_menu = None
        self.browser = Browser(self)
        self.editor = Editor(model, self)
        self.browser.bind_events()
        self.Initialize(self.editor)
        #@    << redirect methods >>
        #@+node:<< redirect methods >>
        self.show_object = self.editor.show_object
        self.sync_text = self.editor.sync_text
        self.refresh = self.editor.refresh
        self.find_resource_references = self.editor.find_resource_references
        self.find_task_references = self.editor.find_task_references
        self.get_module = self.editor.get_module
        #@nonl
        #@-node:<< redirect methods >>
        #@nl
        self.editor.SetMinSize((0, 0))
        self.Bind(wx.EVT_SPLITTER_UNSPLIT, self._on_unsplit)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING, self._on_shash_pos_change)

        if is_bool_option("show_browser"):
            wx.CallAfter(self.toggle_browser)
    #@nonl
    #@-node:__init__
    #@+node:_on_shash_pos_change
    def _on_shash_pos_change(self, evt):
        width = self.GetClientSize()[0]
        sw = self.GetSashSize()
        if evt.GetSashPosition() >= width - sw - 1:
            evt.SetSashPosition(width - sw - 1)
            self.SetSashGravity(1.0)
        else:
            self.SetSashGravity(0.0)
    #@nonl
    #@-node:_on_shash_pos_change
    #@+node:_on_unsplit
    def _on_unsplit(self, event):
        if event.GetWindowBeingRemoved() is self.browser:
            self.browser.open_width = self.browser.GetSize()[0]
            self.browser_menu.check(False)
        else:
            raise RuntimeError("editor may not unsplit")

    #@-node:_on_unsplit
    #@+node:show
    def show(self, parent):
        self.Reparent(parent)

        view_menu = controller().view_menu
        self.browser_menu = view_menu.make_item(parent,
                                                _("&Project Browser\tF9"),
                                                self.toggle_browser,
                                                pos=8000,
                                                check_item=True)
        view_menu.make_separator(_("&Project Browser\tF9"), True)
        self.browser_menu.check(False)

        if self.browser.IsShown():
            wx.CallAfter(self.toggle_browser, True)
    #@-node:show
    #@+node:hide
    def hide(self):
        if self.browser.IsShown():
            self.browser.open_width = self.browser.GetSize()[0]

        self.browser_menu = None
        self.Reparent(controller().hidden_parent)

    #@-node:hide
    #@+node:toggle_browser
    def toggle_browser(self, show=None):
        if show is None:
            show = not self.browser.IsShown()

        if show:
            try:
                width = self.browser.open_width
            except AttributeError:
                width = self.browser.width

            if self.IsSplit():
                self.SetSashPosition(width)
            else:
                self.browser.Show()
                self.SplitVertically(self.browser, self.editor, width)

            self.browser.update_menus()
            self.SetSashGravity(0.0)
        elif self.IsSplit():
            self.browser.open_width = self.browser.GetSize()[0]
            self.Unsplit(self.browser)
            self.browser.Hide()

        try:
            self.browser_menu.check(show)
        except AttributeError: pass

        controller().config.set("DEFAULT", "show_browser", str(show))
    #@-node:toggle_browser
    #@+node:goto_line
    def goto_line(self, line):
        editor = self.editor
        pos = editor.PositionFromLine(line - 1)
        editor.GotoPos(pos)
        editor.SetFocus()
    #@-node:goto_line
    #@+node:find_in_source
    def find_in_source(self, obj):
        self.editor.show_object(obj)
        self.editor.SetFocus()
    #@-node:find_in_source
    #@-others
#@-node:class PlanEditor
#@-others
#@-node:@file gui/editor/__init__.py
#@-leo
