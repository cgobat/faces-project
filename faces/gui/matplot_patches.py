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
import matplotlib.backend_bases as bases
import matplotlib.backends.backend_wxagg as wxagg
import faces.charting.renderer as renderer
import math


"""
Patches of buggy matplolib Classes for the ui
"""

class LocationEvent(bases.Event):
    """
    see the original LocationEvent in matplotlib.backend_bases
    This class finds the last axes which the pointer is in not the first
    """
    x      = None
    y      = None
    button = None
    inaxes = None
    xdata  = None
    ydata  = None

    def __init__(self, name, canvas, x, y, guiEvent=None):
        bases.Event.__init__(self, name, canvas, guiEvent=guiEvent)
        self.x = x
        self.y = y

        if self.x is None or self.y is None:
            # cannot check if event was in axes if no x,y info
            return

        self.inaxes = None
        try:
            iterator = reversed(self.canvas.figure.get_axes())
        except:
            iterator = map(lambda x: x, self.canvas.figure.get_axes())
            iterator.reverse()

        
        for a in iterator:
            if a.in_axes(self.x, self.y):
                self.inaxes = a

                try: xdata, ydata = a.transData.inverse_xy_tup((self.x, self.y))
                except ValueError:
                    self.xdata  = None
                    self.ydata  = None
                else:
                    self.xdata  = xdata
                    self.ydata  = ydata

                break


class MouseEvent(LocationEvent):
    x      = None       # x position - pixels from left of canvas
    y      = None       # y position - pixels from right of canvas
    button = None       # button pressed None, 1, 2, 3
    inaxes = None       # the Axes instance if mouse us over axes
    xdata  = None       # x coord of mouse in data coords
    ydata  = None       # y coord of mouse in data coords

    def __init__(self, name, canvas, x, y, button=None, key=None,
                 guiEvent=None):
        LocationEvent.__init__(self, name, canvas, x, y, guiEvent=guiEvent)
        self.button = button
        self.key = key


class KeyEvent(LocationEvent):
    def __init__(self, name, canvas, key, x=0, y=0, guiEvent=None):
        LocationEvent.__init__(self, name, canvas, x, y, guiEvent=guiEvent)
        self.key = key

bases.LocationEvent = LocationEvent
bases.MouseEvent = MouseEvent
bases.KeyEvent = KeyEvent



_AggCanvas = renderer.PatchedFigureCanvasAgg

class FigureCanvasWx(_AggCanvas, wx.PyPanel):
    keyvald = {
        wx.WXK_CONTROL : 'control',
        wx.WXK_SHIFT   : 'shift',
        wx.WXK_ALT     : 'alt',
        wx.WXK_LEFT    : 'left',
        wx.WXK_UP      : 'up',
        wx.WXK_RIGHT   : 'right',
        wx.WXK_DOWN    : 'down',
        }    

    def __init__(self, parent, id, figure):
        _AggCanvas.__init__(self, figure)
        
        # Set preferred window size hint - helps the sizer (if one is
        # connected)
        l,b,w,h = figure.bbox.get_bounds()
        w = int(math.ceil(w))
        h = int(math.ceil(h))
 
        wx.PyPanel.__init__(self, parent, id, size=wx.Size(w, h))

        self.bitmap = wx.EmptyBitmap(w, h)
        wx.EVT_SIZE(self, self._onSize)
        wx.EVT_PAINT(self, self._onPaint)
        wx.EVT_KEY_DOWN(self, self._onKeyDown)
        wx.EVT_KEY_UP(self, self._onKeyUp)
        wx.EVT_RIGHT_DOWN(self, self._onRightButtonDown)
        wx.EVT_RIGHT_UP(self, self._onRightButtonUp)
        wx.EVT_MOUSEWHEEL(self, self._onMouseWheel)
        wx.EVT_LEFT_DOWN(self, self._onLeftButtonDown)
        wx.EVT_LEFT_UP(self, self._onLeftButtonUp)
        wx.EVT_MOTION(self, self._onMotion)
        wx.EVT_SET_FOCUS(self, self._on_set_focus)
        wx.EVT_KILL_FOCUS(self, self._on_kill_focus)
        wx.EVT_ERASE_BACKGROUND (self, self._on_erase_background)


    def _on_erase_background(self, event):
        #just avoid flickering on windows
        pass

    def _on_set_focus(self, event):
        self.GetParent()._on_set_focus(event)


    def _on_kill_focus(self, event):
        self.GetParent()._on_kill_focus(event)
            

    def draw(self, repaint=True):
        _AggCanvas.draw(self)
        self.bitmap = wxagg._convert_agg_to_wx_bitmap(self.get_renderer(), None)
        if repaint:
            self.gui_repaint()


    def gui_repaint(self, drawDC=None):
        if drawDC is None:
            drawDC=wx.ClientDC(self)

        drawDC.BeginDrawing()
        drawDC.DrawBitmap(self.bitmap, 0, 0)
        drawDC.EndDrawing()


    def _onPaint(self, evt):
        self.GetParent().update_state()
        self.gui_repaint(drawDC=wx.PaintDC(self))
      

    def _onSize(self, evt):
        width, height = self.GetClientSize()
        if width <= 1 or height <= 1: return # Empty figure
        dpival = self.figure.dpi.get()
        winch = width / dpival
        hinch = height / dpival
        self.figure.set_figsize_inches(winch, hinch)


    def _get_key(self, evt):
        keyval = evt.m_keyCode
        if self.keyvald.has_key(keyval):
            key = self.keyvald[keyval]
        elif keyval <256:
            key = chr(keyval)
        else:
            key = None

        # why is wx upcasing this?
        if key is not None: key = key.lower()

        return key

    def _onKeyDown(self, evt):
        """Capture key press."""
        key = self._get_key(evt)
        evt.Skip()
        _AggCanvas.key_press_event(self, key, guiEvent=evt)

    def _onKeyUp(self, evt):
        """Release key."""
        key = self._get_key(evt)
        #print 'release key', key
        evt.Skip()
        _AggCanvas.key_release_event(self, key, guiEvent=evt)

    def _onRightButtonDown(self, evt):
        """Start measuring on an axis."""
        x = evt.GetX()
        y = self.figure.bbox.height() - evt.GetY()
        evt.Skip()
        _AggCanvas.button_press_event(self, x, y, 3, guiEvent=evt)


    def _onRightButtonUp(self, evt):
        """End measuring on an axis."""
        x = evt.GetX()
        y = self.figure.bbox.height() - evt.GetY()
        evt.Skip()
        _AggCanvas.button_release_event(self, x, y, 3, guiEvent=evt)

    def _onLeftButtonDown(self, evt):
        """Start measuring on an axis."""
        x = evt.GetX()
        y = self.figure.bbox.height() - evt.GetY()
        evt.Skip()
        _AggCanvas.button_press_event(self, x, y, 1, guiEvent=evt)

    def _onLeftButtonUp(self, evt):
        """End measuring on an axis."""
        x = evt.GetX()
        y = self.figure.bbox.height() - evt.GetY()
        #print 'release button', 1
        evt.Skip()
        _AggCanvas.button_release_event(self, x, y, 1, guiEvent=evt)

    def _onMouseWheel(self, evt):
        # TODO: implement mouse wheel handler
        pass

    def _onMotion(self, evt):
        """Start measuring on an axis."""

        x = evt.GetX()
        y = self.figure.bbox.height() - evt.GetY()
        evt.Skip()
        _AggCanvas.motion_notify_event(self, x, y, guiEvent=evt)


