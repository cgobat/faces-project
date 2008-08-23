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

import wx
from wx.lib import buttons
import sys


def save_func(func, *args):
    try:
        func(*args)
    except:
        pass


class _RightClickButton:
    def __init__(self):
        wx.EVT_RIGHT_DOWN(self, self.OnRightDown)
        

    def OnRightDown(self, event):
        evt = buttons.GenButtonEvent(wx.wxEVT_COMMAND_RIGHT_CLICK,
                                     self.GetId())
        evt.SetIsDown(not self.up)
        evt.SetButtonObj(self)
        evt.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(evt)


class _BitmapTextTitle(buttons.GenBitmapTextButton, _RightClickButton):
    def __init__(self, parent, id_, bitmap, title):
        buttons.GenBitmapTextButton.__init__(self, parent, id_, bitmap, title)
        _RightClickButton.__init__(self)


class _TextTitle(buttons.GenButton, _RightClickButton):
    def __init__(self, parent, id_, title):
        buttons.GenButton.__init__(self, parent, id_, title)
        _RightClickButton.__init__(self)




class _ContentButton(buttons.GenBitmapButton, _RightClickButton):
    mouse_inside = False
    
    def __init__(self, parent, id, bitmap, title):
        self.title = title
        if not bitmap: bitmap = None
        buttons.GenBitmapButton.__init__(self, parent, id, bitmap)
        _RightClickButton.__init__(self)
        self.SetLabel(title)
        wx.EVT_LEAVE_WINDOW(self, self.OnLeave)
        wx.EVT_ENTER_WINDOW(self, self.OnEnter)
        
    
    def OnPaint(self, event):
        (width, height) = self.GetClientSizeTuple()
        x1 = y1 = 0
        x2 = width-1
        y2 = height-1
        dc = wx.BufferedPaintDC(self)
        if self.up:
            dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour(), wx.SOLID))
        else:
            dc.SetBackground(wx.Brush(self.faceDnClr, wx.SOLID))
            
        dc.Clear()
        if self.mouse_inside:
            self.DrawBezel(dc, x1, y1, x2, y2)
            
        self.DrawLabel(dc, width, height)
        if self.hasFocus and self.useFocusInd:
            self.DrawFocusIndicator(dc, width, height)


    def OnEnter(self, event):
        self.mouse_inside = True
        self.Refresh(False)


    def OnLeave(self, event):
        self.mouse_inside = False
        self.Refresh(False)


    def _GetLabelSize(self):
        """ used internally """

        w, h = self.GetTextExtent(self.title)
        if not self.bmpLabel:
            return w, h, True       # if there isn't a bitmap use the size of the text

        w_bmp = self.bmpLabel.GetWidth()+2
        h_bmp = self.bmpLabel.GetHeight()+2
        height = h + h_bmp + 2
        width = max(w_bmp, w)
        return width, height, True


    def DrawLabel(self, dc, width, height, dx=0, dh=0):
        bmp = self.bmpLabel
        if bmp != None:     # if the bitmap is used
            if self.bmpDisabled and not self.IsEnabled():
                bmp = self.bmpDisabled
            if self.bmpFocus and self.hasFocus:
                bmp = self.bmpFocus
            if self.bmpSelected and not self.up:
                bmp = self.bmpSelected
            bw,bh = bmp.GetWidth(), bmp.GetHeight()
            if not self.up:
                dx = dh = self.labelDelta
            hasMask = bmp.GetMask() != None
        else:
            bw = bh = 0     # no bitmap -> size is zero

        dc.SetFont(self.GetFont())
        if self.IsEnabled():
            dc.SetTextForeground(self.GetForegroundColour())
        else:
            back_color = wxSystemSettings_GetSystemColour(wxSYS_COLOUR_GRAYTEXT)
            dc.SetTextForeground(back_color)

        label = self.title
        tw, th = dc.GetTextExtent(label)        # size of text
        if not self.up:
            dw = dy = self.labelDelta

        # adjust for bitmap and text to verical centre
        pos_y = (height-bh-th)/2+dh      
        if bmp !=None:
            dc.DrawBitmap(bmp, (width-bw)/2+dx, pos_y, hasMask)
            pos_y = pos_y + 2   # extra spacing from bitmap

        dc.DrawText(label, (width-tw)/2+dx, pos_y + dh+bh)      # draw the text


class _SpacePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.SetSizeHints(0, 0)
        try:
            self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        except:
            pass
        wx.EVT_ERASE_BACKGROUND(self, self.OnEraseBackground)

    def OnEraseBackground(self, event):
        dc = event.GetDC()
        dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour(), wx.SOLID))
        dc.Clear()


class _ContentPanel(wx.ScrolledWindow):
    def __init__(self, parent, id):
        wx.ScrolledWindow.__init__(self, parent, id, style=wx.TAB_TRAVERSAL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        sizer.Add(_SpacePanel(self), 1, flag=wx.EXPAND)
        #self.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_BTNSHADOW))
        

    def insert(self, title, id, bitmap, pos):
        button = _ContentButton(self, id, bitmap, title)
        
        sizer = self.GetSizer()
        if pos == -1:
            pos = len(sizer.GetChildren()) - 1
        
        sizer.Insert(pos, button, 0, flag=wx.EXPAND)
        self.SetupScrolling(False)
        

    def SetupScrolling(self, scroll_x=True, scroll_y=True, rate_x=20, rate_y=20):
        # The following is all that is needed to integrate the sizer and the
        # scrolled window.
        if not scroll_x: rate_x = 0
        if not scroll_y: rate_y = 0

        # Round up the virtual size to be a multiple of the scroll rate
        sizer = self.GetSizer()
        if sizer:
            w, h = sizer.GetMinSize()
            if rate_x:
                w += rate_x - (w % rate_x)
            if rate_y:
                h += rate_y - (h % rate_y)
            self.SetVirtualSize( (w, h) )
            self.SetVirtualSizeHints( w, h )

        self.SetScrollRate(rate_x, rate_y)

        # scroll back to top after initial events
        wx.CallAfter(save_func, self.Scroll, 0, 0)
        

class MenuPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.active_id = 0
        self.__content_ids = {}
        wx.EVT_COMMAND(self, wx.ID_ANY,
                       wx.wxEVT_COMMAND_BUTTON_CLICKED,
                       self._on_button_clicked)


    def _on_button_clicked(self, event):
        title = self.FindWindowById(event.GetId())
        if title.GetParent() == self:
            self.activate(event.GetId())
            return
        else:
            event.Skip()
        

    def get_best_width(self):
        return max([ c.GetBestSize().GetWidth() for c in self.GetChildren() ])
        

    def insert_title(self, title, id_, bitmap=None, pos=-1, active=True):
        if pos == -1:
            pos = len(self.GetChildren())
        else:
            pos *= 2

        if bitmap:
            button = _BitmapTextTitle(self, id_, bitmap, title)
        else:
            button = _TextTitle(self, id_, title)

        cid = wx.NewId()
        self.__content_ids[button] = cid
        content = _ContentPanel(self, cid)
        sizer = self.GetSizer()
        sizer.Insert(pos, button, 0, flag=wx.EXPAND)
        sizer.Insert(pos + 1, content, 1, flag=wx.EXPAND)

        if active or not self.active_id:
            self.activate(id_)
        else:
            sizer.Show(content, False)


    def activate(self, title_id):
        if title_id == self.active_id: return 
        
        sizer = self.GetSizer()
        
        if self.active_id:
            content = self.__get_content(self.active_id)
            sizer.Show(content, False)
                    
        self.active_id = title_id
        content = self.__get_content(self.active_id)
        sizer.Show(content, True)
        self.Layout()


    def insert_content(self, title, id, parent_id, bitmap=None,
                       pos=-1, active=True):
        content = self.__get_content(parent_id)
        if not content: return

        content.insert(title, id, bitmap, pos)
        if active: self.activate(parent_id)


    def remove(self, id):
        button = self.FindWindowById(id)
        if not button: return

        parent = button.GetParent()
        content = self.__get_content(id)
        button.Destroy()

        if content:
            del self.__content_ids[button]
            content.Destroy()
            self.Layout()
        else:
            parent.SetupScrolling(False)
            parent.SetSize((-1, -1))

        if self.active_id == id:
            self.active_id = None
            children = self.GetChildren()
            if children:
                self.activate(children[0].GetId())
            
        
    def index_of(self, id):
        button = self.FindWindowById(id)
        if not button: return None

        parent = button.GetParent()
        siblings = map(lambda c: (c.GetPosition().y, c), parent.GetChildren())
        siblings.sort()
        index = 0
        for ypos, child in siblings:
            if child.GetId() == id: break
            if isinstance(child, button.__class__):
                index += 1
            
        return index


    def id_of(self, parent_title, content_title=None):
        button = wx.FindWindowByLabel(parent_title, self)
        if button:
            if content_title:
                content = self.__get_content(button.GetId())
                button = wx.FindWindowByLabel(content_title, content)

        return button and button.GetId()

        
    def __get_content(self, title_id):
        title = self.FindWindowById(title_id)
        return self.FindWindowById(self.__content_ids.get(title, 0))
        

