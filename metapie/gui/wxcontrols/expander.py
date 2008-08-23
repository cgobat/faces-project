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
A better working popup control

"""

import wx
from wx.lib.buttons import GenButtonEvent


class PopButton(wx.PyControl):
    def __init__(self,*_args,**_kwargs):
        apply(wx.PyControl.__init__,(self,) + _args,_kwargs)

        self.up = True
        self.didDown = False

        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_PAINT, self.OnPaint)


    def Notify(self):
        evt = GenButtonEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, self.GetId())
        evt.SetIsDown(not self.up)
        evt.SetButtonObj(self)
        evt.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(evt)


    def OnEraseBackground(self, event):
        pass


    def OnLeftDown(self, event):
        if not self.IsEnabled():
            return
        self.didDown = True
        self.up = False
        self.CaptureMouse()
        self.GetParent().textCtrl.SetFocus()
        self.Refresh()
        event.Skip()
        

    def OnLeftUp(self, event):
        if not self.IsEnabled():
            return
        if self.didDown:
            self.ReleaseMouse()
            if not self.up:
                self.Notify()
            self.up = True
            self.Refresh()
            self.didDown = False
        event.Skip()


    def OnMotion(self, event):
        if not self.IsEnabled():
            return
        if event.LeftIsDown():
            if self.didDown:
                x,y = event.GetPosition()
                w,h = self.GetClientSize()
                if self.up and x<w and x>=0 and y<h and y>=0:
                    self.up = False
                    self.Refresh()
                    return
                if not self.up and (x<0 or y<0 or x>=w or y>=h):
                    self.up = True
                    self.Refresh()
                    return
        event.Skip()


    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        rect = wx.RectS(self.GetClientSize())
        if self.up:
            flag = wx.CONTROL_CURRENT
        else:
            flag = wx.CONTROL_PRESSED
        
        wx.RendererNative_Get().DrawComboBoxDropButton(self, dc, rect, flag)



class ExpanderPopup(wx.PopupWindow):
    def __init__(self, parent):
        wx.PopupWindow.__init__(self, parent)
        self.container = wx.Panel(self, -1, style=wx.RAISED_BORDER)
        self.Bind(wx.EVT_SIZE, self._on_size)
        
        
    def has_common_parent(self, window):
        if not window: return True
        parent = self.GetParent()
        while window and window is not parent:
            window = window.GetParent()

        return bool(window)


    def _on_idle(self, event):
        event.Skip()
        if not self.IsShown(): return
        focus = wx.Window_FindFocus()
        if not self.has_common_parent(focus): self.hide()


    def _on_size(self, evt):
        size = self.GetClientSize()
        self.container.SetSize(size)
        size = self.container.GetClientSize()
        self.content.SetSize(size)
        self.content.Move((0, 0))
        self.container.Move((0,0))
        

    def display(self):
        parent = self.GetParent()
        x, y = parent.ClientToScreen((0,0))
        dsize = wx.GetDisplaySize()
        msize = self.GetSize()
        psize = parent.GetSize()

        if x + msize.width > dsize.width:
            x = dsize.width - msize.width - 1

        if y + psize.height + msize.height > dsize.height:
            y -= msize.height + 1
        else:
            y += psize.height + 1

        self.Move((x, y))
        self.Show()
    

    def hide(self):
        self.Hide()


    def set_content(self):
        self.content = self.container.GetChildren()[0]
        self.content.Bind(wx.EVT_IDLE, self._on_idle)


    def adjust_size(self):
        self.container.SetClientSize(self.content.GetBestSize())
        self.SetClientSize(self.container.GetSize())


class Expander(wx.PyControl):
    def __init__(self, parent, id, value="", pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        super(Expander, self).__init__(parent, id, pos, size,
                                       style|wx.NO_BORDER)
        
        self._prepare_text(value)
        self._prepare_popup()
        self.button = PopButton(self, -1)
        self._on_size(None)

        wx.EVT_SIZE(self, self._on_size)
        wx.EVT_BUTTON(self.button, -1, self._on_button)
        wx.EVT_SET_FOCUS(self, self._on_focus)


    def _on_focus(self, event):
        # embedded control should get focus on TAB keypress
        self.textCtrl.SetFocus()
        event.Skip()
        

    def _on_size(self, evtent):
        w,h = self.GetClientSize()
        self.textCtrl.SetDimensions(0,0,w-17,h)
        self.button.SetDimensions(w-17,0,17,h)


    def _on_button(self, event):
        if not self.popup.IsShown():
            self.before_display()
            self.popup.display()
        else:
            self.popup.hide()


    def _on_key_down(self, event):
        if event.ShiftDown() and event.GetKeyCode() == wx.WXK_DOWN:
            self._on_button(event)
            return
        else:
            event.Skip()


    def _prepare_text(self, value):
        self.textCtrl = wx.TextCtrl(self, -1, value, pos=(0,0))
        wx.EVT_KEY_DOWN(self.textCtrl, self._on_key_down)


    def _prepare_popup(self):
        self.popup = ExpanderPopup(self)
        self.create_content(self.popup.container)
        self.popup.set_content()
        self.popup.adjust_size()


    def create_content(self, parent):
        raise RuntimeError("You have to overwrite this method")


    def unpop(self):
        self.popup.hide()
        self.textCtrl.SetFocus()


    def is_open(self):
        return self.popup.IsShown()

        
    def before_display(self):
        wx.CallAfter(self.popup.content.SetFocus)
        

    def Enable(self, flag):
        super(Expander, self).Enable(flag)
        self.textCtrl.Enable(flag)
        self.button.Enable(flag)
        

    def SetValue(self, value):
        try:
            self.textCtrl.SetValue(value)
        except wx.PyDeadObjectError:
            pass


    def GetValue(self):
        return self.textCtrl.GetValue()


    def DoGetBestSize(self):
        tsize = self.textCtrl.GetBestSize()
        return (tsize.GetWidth() + tsize.GetHeight(), tsize.GetHeight())


