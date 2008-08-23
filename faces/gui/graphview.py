############################################################################
#   Copyright (C) 2006 by Reithinger GmbH
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

import faces.observer
import wx
import faces.plocale
import metapie.navigator as navigator
import tempfile


_is_source_ = True
_ = faces.plocale.get_gettext()

def _graph_factory(title, chart, model):
    return lambda parent: GraphView(parent, chart, model, title)

faces.observer.factories["graphviz_chart"] = _graph_factory

class GraphView(wx.PyScrolledWindow, navigator.View):
    def __init__(self, parent, chart, model, title):
        wx.PyScrolledWindow.__init__(self, parent, -1)
        self.disk_mem = tempfile.NamedTemporaryFile("w+r")
        self.replace_data(chart)
        
        
        
        #print "self.disk_mem", self.disk_mem
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        

    def replace_data(self, chart):
        self.chart = chart()
        self.build_image()
        self.Refresh(False)
        

    def build_image(self):
        self.chart.render(self.disk_mem, "gif")
        #size = self.disk_mem.tell()
        #self.disk_mem.seek(0)
        #data = self.disk_mem.read()
        #image = wx.Image(self.disk_mem, wx.BITMAP_TYPE_BMP)
        #self.bitmap = wx.BitmapFromImage(image)
        #self.bitmap = wx.Bitmap(self.disk_mem.name, wx.BITMAP_TYPE_BMP)
        self.bitmap = wx.Bitmap("/tmp/tst.gif", wx.BITMAP_TYPE_GIF)



    def _on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bitmap, 0, 0)
        
        
    def accept_sibling(self, new_view):
        return navigator.SIBLING_BELOW

    
