#@+leo-ver=4
#@+node:@file gui/editor/editorlib.py
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
A library of classes that, can be used for edit dialogs
"""
#@<< Imports >>
#@+node:<< Imports >>
import wx
import metapie.gui.views as views
from metapie.gui import controller
from faces.gui.patches import PatchedDialog
#@nonl
#@-node:<< Imports >>
#@nl

_is_source_ = True

#@+others
#@+node:class MainView
class MainView(views.FormView):
    border = 5

    format_buttons = """
btn_ok{r}|btn_refresh{r}|btn_cancel{r}
"""

    #@    @+others
    #@+node:__init__
    def __init__(self, parent, style=0):
        views.FormView.__init__(self, parent, style)
        parent.keep_alive = self # ensure that the view lives as long as the parent
        sizer = parent.GetSizer()
        sizer.Add(self, border=self.border, flag=wx.ALL|wx.EXPAND, proportion=1)
    #@nonl
    #@-node:__init__
    #@+node:button_cancel
    def button_cancel(self):
        self.GetParent().EndModal(wx.ID_CANCEL)
        self.rollback()
        try:
            self.imodel.cancel()
        except AttributeError:
            pass
    #@-node:button_cancel
    #@+node:button_ok
    def button_ok(self):
        if self.save():
            self.GetParent().EndModal(wx.ID_OK)
            self.imodel.realize()
    #@nonl
    #@-node:button_ok
    #@+node:button_refresh
    def button_refresh(self):
        if self.save():
            self.GetParent().EndModal(wx.ID_OK)
            self.imodel.realize()
            controller().session.menu_recalc()
    #@nonl
    #@-node:button_refresh
    #@+node:layout
    def layout(self):
        views.FormView.layout(self)
        parent = self.GetParent()
        w, h = parent.GetClientSize()
        wm, hm = self.GetSizer().CalcMin()
        wm += 2 * self.border
        hm += 2 * self.border
        parent.SetClientSize((max(w, wm, 360), max(h, hm)))
        parent.SetMinSize((wm, hm))
    #@nonl
    #@-node:layout
    #@+node:get_stock_control
    def get_stock_control(self, parent, name):
        if name == "btn_refresh":
            parent.btn_refresh = wx.Button(parent, wx.ID_REFRESH)
            parent.btn_refresh.Bind(wx.EVT_BUTTON, lambda ev: self.button_refresh())
            parent.btn_refresh.SetDefault()
            self.set_default_item(parent.btn_refresh)
            return parent.btn_refresh

        ctrl = super(MainView, self).get_stock_control(parent, name)
        if name == "btn_ok" and not hasattr(parent, "btn_refresh"):
            ctrl.SetDefault()
            self.set_default_item(ctrl)

        return ctrl
    #@nonl
    #@-node:get_stock_control
    #@-others
#@-node:class MainView
#@-others
#@nonl
#@-node:@file gui/editor/editorlib.py
#@-leo
