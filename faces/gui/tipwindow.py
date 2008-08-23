############################################################################
#   Copyright (C) 2005 by Reithinger GmbH
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

import wx
from metapie.gui import controller
import faces.charting.tools as tools

if 'wxMac' in wx.PlatformInfo:
    class TipWindow(object):
        instance = None
         
        def get():
            if not TipWindow.instance:
                TipWindow.instance = TipWindow()

            return TipWindow.instance

        get = staticmethod(get)

        def set_info(self, info, widget):
            pass

        def is_widget_active(self, widget):
            return True
            
else:
    class TipWindow(wx.PopupTransientWindow):
        label_font = None
        text_font = None
        margin_x = margin_y = 3
        instance = None

        def get():
            if not TipWindow.instance:
                TipWindow.instance = TipWindow(controller().frame)

            return TipWindow.instance

        get = staticmethod(get)

        def __init__(self, parent):
            wx.PopupTransientWindow.__init__(self, parent)
            self.Hide()

            if not self.label_font:
                self.label_font = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD)

            if not self.text_font:
                self.text_font = wx.Font(11, wx.SWISS, wx.NORMAL, wx.NORMAL)

            self.lines = []
            self.object = None
            wx.EVT_ERASE_BACKGROUND(self, self.OnEraseBackground)
            wx.EVT_PAINT(self, self.OnPaint)
            wx.EVT_LEFT_DOWN(self, self.hide)
            wx.EVT_LEAVE_WINDOW(self, self.hide)


        def set_info(self, info, obj):
            def conv(text):
                if isinstance(text, str):
                    return unicode(text, tools.chart_encoding)
                return text

            self.lines = [ (conv(title), conv(data)) for title, data in info ]
            self.object = obj
            if 'wxMSW' in wx.PlatformInfo:
                x, y = self.GetParent().ScreenToClientXY(*wx.GetMousePosition())
            else:
                x, y = wx.GetMousePosition()

            self.SetPosition((x - 10, y - 10))
            self.adjust_size()
            self.Show()


        def OnEraseBackground(self, event):
            pass


        def hide(self, event=None):
            self.object = None
            if not self.IsShown(): return
            wx.CallAfter(self.Hide)


        def OnPaint(self, pdc):
            pdc = wx.PaintDC(self)

            size = self.GetClientSizeTuple()
            pdc.DrawRectangle(0, 0, size[0], size[1])

            y = self.margin_y
            pdc.SetTextBackground(self.GetBackgroundColour());
            pdc.SetTextForeground(self.GetForegroundColour());

            for l in self.lines:
                pdc.SetFont(self.label_font)
                pdc.DrawText(l[0] + ":", self.margin_x, y)
                (w, lh) = pdc.GetTextExtent(l[0] + ": ")

                pdc.SetFont(self.text_font)
                pdc.DrawText(l[1], self.tab1, y)
                (w, th) = pdc.GetTextExtent(l[1])
                y += max(lh, th)


        def adjust_size(self):
            dc = wx.ClientDC(self)
            width = 0
            height = 0
            self.tab1 = 0

            dc.SetFont(self.label_font)
            for l in self.lines:
                (w, lh) = dc.GetTextExtent(l[0] + ": ")
                self.tab1 = max(self.tab1, w)

            dc.SetFont(self.text_font)
            for l in self.lines:
                (w, th) = dc.GetTextExtent(l[1])
                width  = max(width, self.tab1 + w)
                height += max(lh, th)

            size = (width + 2 * self.margin_x,
                    height + 2 * self.margin_y)
            self.SetSize(size)


        def is_widget_active(self, widget):
            return self.object is widget
