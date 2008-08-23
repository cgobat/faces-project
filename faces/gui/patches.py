#@+leo-ver=4
#@+node:@file gui/patches.py
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
Patched versions of buggy wxpython objects
"""
#@<< Imports >>
#@+node:<< Imports >>
import wx
from wx.__version__ import VERSION
from metapie.gui import controller
#@nonl
#@-node:<< Imports >>
#@nl

_is_source_ = True

#@+others
#@+node:class PatchedDialog
if wx.Platform == '__WXGTK__':
    #@    << gtk patched dialog >>
    #@+node:<< gtk patched dialog >>
    class PatchedDialog(wx.Dialog):
        def __init__(self, *args, **kwargs):
            kwargs["style"] = kwargs.get("style", wx.DEFAULT_DIALOG_STYLE)\
                              & ~wx.CLOSE_BOX 
            wx.Dialog.__init__(self, *args, **kwargs)
            self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))

        #a real ShowModal will break the popup controls under gtk
        def simulate_modal(self, focused, call_after=None):
            self.focused = focused
            self.call_after = call_after
            controller().frame.Enable(False)
            self.Bind(wx.EVT_CLOSE, self._on_close)
            self.Show()
            self.SetFocus()


        def _on_close(self, event=None):
            if event: event.Skip()

            focused = self.focused
            def after_close():
                controller().frame.Enable()
                if focused: focused.SetFocus()

            wx.CallAfter(after_close)


        def EndModal(self, id):
            if self.call_after: self.call_after()
            self._on_close()
            self.Destroy()


    #@-node:<< gtk patched dialog >>
    #@nl
else:
    #@    << original dialog >>
    #@+node:<< original dialog >>
    class PatchedDialog(wx.Dialog):
        def __init__(self, *args, **kwargs):
            wx.Dialog.__init__(self, *args, **kwargs)
            self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))


        def simulate_modal(self, focused, call_after=None):
            self.ShowModal()
            if call_after: call_after()
            if focused: focused.SetFocus()
            self.Destroy()

    #@-node:<< original dialog >>
    #@nl
#@nonl
#@-node:class PatchedDialog
#@-others
#@nonl
#@-node:@file gui/patches.py
#@-leo
