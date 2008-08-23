############################################################################
#   Copyright (C) 2005, 2006 by Reithinger GmbH
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
"""
A collection of dialogs
"""

import wx
import wx.calendar
import faces.plocale
import calendar

_is_source_ = True
_ = faces.plocale.get_gettext()


class CalendarDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, _("Insert Date"),
                           style=wx.DEFAULT_DIALOG_STYLE)

        style = wx.calendar.CAL_SHOW_SURROUNDING_WEEKS |\
                wx.calendar.CAL_SEQUENTIAL_MONTH_SELECTION
        if calendar.firstweekday() == calendar.SUNDAY:
            style |= wx.calendar.CAL_SUNDAY_FIRST
        else:
            style |= wx.calendar.CAL_MONDAY_FIRST

        self.cal = wx.calendar.CalendarCtrl(self, -1, wx.DateTime_Now(),
                                            style=style)

        ok = wx.Button(self, wx.ID_OK)
        cancel = wx.Button(self, wx.ID_CANCEL)

        hs = wx.BoxSizer(wx.HORIZONTAL)
        hs.Add((0, 0), 1)
        hs.Add(ok, 0, wx.ALIGN_CENTER)
        hs.Add((0, 0), 1)
        hs.Add(cancel, 0, wx.ALIGN_CENTER)
        hs.Add((0, 0), 1)
        vs = wx.BoxSizer(wx.VERTICAL)
        vs.Add(self.cal, 0, wx.ALIGN_CENTER)
        vs.Add((0, 10))
        vs.Add(hs, 0, wx.EXPAND)
        self.SetSizer(vs)
        self.SetClientSize(vs.CalcMin())

        def close_calendar(evt):
            self.EndModal(wx.ID_OK)
            
        wx.calendar.EVT_CALENDAR(self, -1, close_calendar)

