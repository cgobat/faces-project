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
import sys

def _reparent(view, container):
    view.Reparent(container)
    view.Move((0, 0))
    


class Stacker(wx.Panel):
    sash_height = 6
    min_height = 30
    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, style=wx.BORDER)
        self.layouter = wx.LayoutAlgorithm()
        c = wx.Panel(self, -1)
        self.views = [ (c, c) ]
        self.last_focused = None
        
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_SASH_DRAGGED(self, wx.ID_ANY, self.OnSashDrag)
        wx.EVT_IDLE(self, self.OnIdle)


    def OnIdle(self, event):
        self.__save_focus()


    def OnSashDrag(self, event):
        sash = event.GetEventObject()
        
        size = event.GetDragRect().GetSize()
        if event.GetDragStatus() == wx.SASH_STATUS_OUT_OF_RANGE:
            size.SetHeight(0)
            
        sash.SetDefaultSize(size)

        self.adjust_layout()
        self.refresh_focus()


    __last_size = None
    def OnSize(self, event):
        if event.GetSize() != self.__last_size:
            self.__last_size = event.GetSize()
            wx.CallAfter(self.adjust_layout)
        

    def resize(self, view, delta):
        if not isinstance(view, (int, long)):
            view = self.index_of(view)

        views = self.views
        if view == len(views) - 1:
            view -= 1
            delta = -delta
            
        v, c = views[view]
        sash = c.GetParent()
        height = sash.GetSizeTuple()[1]
        sash.SetDefaultSize((-1, height + delta))
        self.adjust_layout()


    def index_of(self, view):
        index = 0
        for v, c in self.views:
            if v is view: break
            index += 1

        return index
    

    def remove(self, view):
        if not isinstance(view, (int, long)):
            view = self.index_of(view)

        self.__remove(view)
        

    def replace(self, pos, view):
        v, c = self.views[pos]
        v.Destroy()
        _reparent(view, c)
        self.views[pos] = (view, c)
        self.refresh_focus()
        return view
        

    def insert(self, pos, view, height=None):
        views = self.views
        if len(views) == 1:
            v, c = views[0]
            if v is c:
                # no view is here yet
                views[0] = (view, c)
                _reparent(view, c)
                self.adjust_layout()
                self.refresh_focus()
                return view

        # calculate new size of all views
        new_count = len(views) + 1
        total_height = self.GetClientSizeTuple()[1]

        if not height:
            height = total_height - (new_count - 1) * self.sash_height
            height /= new_count
            
        rest_height = total_height - height

        for v, c in views[:-1]:
            h = c.GetSizeTuple()[1]
            new_height = int(rest_height * float(h) / float(total_height))
            rest_height -= new_height
            size = (-1, new_height)
            c.GetParent().SetDefaultSize(size)
            c.SetSize(size)

        if pos >= new_count - 1:
            # view is below mainspace
            v, c = views[-1]
            new = self._create_sash_container(rest_height)
            _reparent(v, new)
            views[-1] = (v, new)
            _reparent(view, c)
            views.append((view, c))
            self.adjust_layout()
            self.refresh_focus()
            return view
        
        # append new sash (sashes can only be appended)
        # and reparent all view below pos
        new = self._create_sash_container(20)
        views.insert(new_count - 2, (None, new))

        last_view = view
        last_height = height + self.sash_height
        for i in range(pos, new_count - 1):
            v, c = views[i]
            h = c.GetSizeTuple()[1]
            c.GetParent().SetDefaultSize((-1, last_height))
            _reparent(last_view, c)
            views[i] = (last_view, c)
            last_view = v
            last_height = h
           
        self.adjust_layout()
        self.refresh_focus()
        return view


    def adjust_layout(self):
        min_height = self.min_height
        views = self.views
        self.layouter.LayoutWindow(self, views[-1][1])

        if self.GetClientSizeTuple()[1] > min_height:
            r = range(len(views) - 1, -1, -1)
            for i in r:
                view, container = views[i]
                if container.GetSizeTuple()[1] < min_height:
                    self.__remove(i)
                    self.layouter.LayoutWindow(self, views[-1][1])

        for v, c in views:
            v.SetSize(c.GetClientSize())

        self.__save_focus()


    def refresh_focus(self):
        if self.last_focused:
            self.last_focused.SetFocus()


    def find_view(self, window):
        """returns the view, the window is a child of or None"""
        views = map(lambda v: v[0], self.views)
        while window and window not in views:
            window = window.GetParent()

        return window


    def __remove(self, pos):
        views = self.views
        count = len(views)

        if pos >= count: return

        if pos == count - 1:
            v, c = views[pos]
            if v is not c:
                v.ProcessEvent(wx.CloseEvent(wx.wxEVT_CLOSE_WINDOW, v.GetId()))
                wx.CallAfter(v.Destroy)

            if pos > 0:
                av, ac = views[pos - 1]
                _reparent(av, c)
                wx.CallAfter(ac.GetParent().Destroy)
                ac.GetParent().SetDefaultSize((-1, 0))
                views[pos] = (av, c)
                del views[pos - 1]
            else:
                views[pos] = (c, c)
        else:
            v, c = views[pos]
            v.ProcessEvent(wx.CloseEvent(wx.wxEVT_CLOSE_WINDOW, v.GetId()))
            wx.CallAfter(v.Destroy)
            wx.CallAfter(c.GetParent().Destroy)
            c.GetParent().SetDefaultSize((-1, 0))
            del views[pos]

        wx.CallAfter(self.__find_new_focus, pos)


    def _create_sash_container(self, height):
        sash = wx.SashLayoutWindow(self, wx.NewId(),
                                   style=wx.NO_BORDER|wx.SW_3D)
        sash.SetDefaultBorderSize(self.sash_height)
        sash.SetDefaultSize((-1, height))
        sash.SetOrientation(wx.LAYOUT_HORIZONTAL)
        sash.SetAlignment(wx.LAYOUT_TOP)
        sash.SetSashVisible(wx.SASH_BOTTOM, True)

        # inserting a wxPanel between the sash and the view
        # is patch for wxWindows: Some controls (i.e wx.stc.StyledTextCtrl)
        # don't change the cursor shape after the cursor was over a sash
        return wx.Panel(sash, wx.NewId())

    def __save_focus(self):
        focus = wx.Window_FindFocus()
        if not isinstance(focus, (wx.SashLayoutWindow, Stacker)):
            self.last_focused = focus


    def __find_new_focus(self, pos):
        self.__save_focus()
        if not self.last_focused:
            pos = min(pos, len(self.views) - 1)
            v, c = self.views[pos]
            v.SetFocus()
        else:
            self.last_focused.SetFocus()

