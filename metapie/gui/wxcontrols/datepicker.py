############################################################################
#   Copyright (C) 2005 by Reithinger GmbH
#   mreithinger@web.de
#
#   This file is part of metapie.
#                                                                         
#   metapie is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   pyplan is distributed in the hope that it will be useful,
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
For GTK a working datepicker
"""
import wx

class _AdjustSize(object):
    def __init__(self, window):
        size_str = '8' * len(wx.DateTime.Today().FormatDate())
        w, h = window.GetTextExtent(size_str + "i")
        w1, h = window.GetBestSize()
        window.SetClientSize((w, -1))
        w, h1 = window.GetSize()
        
        try:
            window.CacheBestSize((w, h))
        except AttributeError:
            pass
        
        window.SetMinSize((w, h))
        


if wx.Platform == '__WXGTK__':
    import expander
    import wx.calendar
    import wx.lib.masked as masked
    import datetime
    import time

    #unfortunatly we can not use wx.DateTime.ParseDate
    #because it works wrong under locals
    def to_datetime(src):
        """
        a tolerant conversion function to convert different strings
        to a datetime.dateime
        """
        formats = [ "%x",
                    "%d/%m/%Y",
                    "%d/%m/%y",
                    "%Y-%m-%d",
                    "%y-%m-%d",
                    "%d.%m.%Y",
                    "%d.%m.%y",
                    "%Y%m%d" ]
        for f in formats:
            try:
                conv = time.strptime(src, f)
                date = datetime.datetime(*conv[0:-3])
                return wx.DateTimeFromDMY(date.day, date.month - 1, date.year)
            except Exception:
                pass
            

        raise TypeError("'%s' (%s) is not a datetime" % (src, str(type(src))))

    
    class DatePickerCtrl(expander.Expander, _AdjustSize):
        def __init__(self, parent, id, value=wx.DateTime.Now(), **kwargs):
            self.value = value
            value = value.FormatDate()
                
            expander.Expander.__init__(self, parent, id, value, **kwargs)
            _AdjustSize.__init__(self, self.textCtrl)
            self.SetMinSize(self.GetBestSize())
            
            wx.EVT_KILL_FOCUS(self.textCtrl, self._on_text_kill_focus)


        def _on_text_kill_focus(self, event):
            event.Skip()
            value = self.get_value()
            if self.value != value:
                self._notify()
                self.value = value
            

        def create_content(self, parent):
            cal = wx.calendar
            calendar = cal.CalendarCtrl(parent, -1)
            cal.EVT_CALENDAR_SEL_CHANGED(calendar, -1, self._on_cal_changed)
            cal.EVT_CALENDAR(calendar, -1, self._on_cal_selected)
            self.content = calendar
            return calendar
                    

        # Method called when a day is selected in the calendar
        def _on_cal_changed(self, evt):
            self.set_value(self.content.GetDate())


        def _on_cal_selected(self, evt):
            self._on_cal_changed(evt)
            self.unpop()


        def _notify(self):
            event = wx.DateEvent(self, self.get_value(), wx.wxEVT_DATE_CHANGED)
            self.ProcessEvent(event)


        def before_display(self):
            self.content.SetDate(self.get_value())


        def SetValue(self, value):
            self.value = value
            self.set_value(value)


        def GetValue(self):
            return self.get_value()


        def set_value(self, value):
            assert(isinstance(value, wx.DateTime))
            value = value.FormatDate()
            self.textCtrl.SetValue(value)


        def get_value(self):
            try:
                date = to_datetime(self.textCtrl.GetValue())
                return date
            except TypeError, e:
                self.textCtrl.SetValue(self.value.FormatDate())
                return self.value
else:
    class DatePickerCtrl(wx.DatePickerCtrl, _AdjustSize):
        def __init__(self, *args, **kwargs):
            wx.DatePickerCtrl.__init__(self, *args, **kwargs)
            _AdjustSize.__init__(self, self)
            w, h = self.GetMinSize()
            w += 21 # add button width
            self.SetMinSize((w, h))
            self.CacheBestSize((w, h))
            

if __name__ == '__main__':
    app = wx.PySimpleApp()
    f = wx.Frame(None)

    date = wx.DateTime()
    print "no parse", date.ParseDate("1.1.2005"), date.FormatDate()

    
    p = wx.Panel(f)
    d = DatePickerCtrl(p, -1, date, style=wx.DP_DROPDOWN)
    t = wx.TextCtrl(p, -1)

    print "d", d.GetMinSize(), d.GetBestSize()
    print "t", t.GetMinSize(), t.GetBestSize()
    #set ticker properties here if you want
    s = wx.BoxSizer(wx.VERTICAL)
    #s = wx.BoxSizer(wx.HORIZONTAL)
    s.Add(d, flag=wx.GROW, proportion=0)
    s.Add(t, flag=wx.GROW, proportion=0)
    p.SetSizer(s)
    f.Show()
    app.MainLoop()


    
    
