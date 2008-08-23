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

"""
Patched Renderers of matplotlib
"""

import matplotlib.numerix as numerix
import matplotlib.transforms as mtrans
import matplotlib.backends.backend_agg as agg
import math


class PatchedRendererAgg(agg.RendererAgg):
    def __init__(self, *args, **kwargs):
        agg.RendererAgg.__init__(self, *args, **kwargs)
        self.old_draw_lines = self.draw_lines
        self.draw_lines = self.patched_draw_lines
        self.dumy_trans = mtrans.identity_transform()


    def patched_draw_lines(self, gc, xs, ys, trans=None):
        self.old_draw_lines(gc, xs, ys, trans or self.dumy_trans)


    def draw_line(self, gc, x1, y1, x2, y2):
        """
        x and y are equal length arrays, draw lines connecting each
        point in x, y
        """
        x = numerix.array([x1,x2], typecode=numerix.Float)
        y = numerix.array([y1,y2], typecode=numerix.Float)
        self.patched_draw_lines(gc, x, y)


    def draw_text(self, gc, x, y, s, prop, angle, ismath):
        if ismath:
            return self.draw_mathtext(gc, x, y, s, prop, angle)

        font = self._get_agg_font(prop)
        if font is None: return None
        if len(s)==1 and ord(s)>127:
            font.load_char(ord(s))
        else:
            font.set_text(s, angle)
        font.draw_glyphs_to_bitmap()

        decent = font.get_descent() / 64.0
        #print x, y, int(x), int(y)
        
        self._renderer.draw_text(font, int(x), int(y + decent), gc)


class PatchedFigureCanvasAgg(agg.FigureCanvasAgg):
    def get_renderer(self):
        l,b,w,h = self.figure.bbox.get_bounds()
        key = w, h, self.figure.dpi.get()
        try: self._lastKey, self.renderer
        except AttributeError: need_new_renderer = True
        else:  need_new_renderer = (self._lastKey != key)

        if need_new_renderer:
            self.renderer = PatchedRendererAgg(w, h, self.figure.dpi)
            self._lastKey = key

        return self.renderer


class SpeedupGraphicsContext(agg.GraphicsContextBase):
    def set_alpha(self, alpha):
        # workaround for alpha bug in agg (needed for WidgetAxes.speed_up)
        # If normal alpha would be set, the object is to light by factor alpha
        # in speed_up cache.
        agg.GraphicsContextBase.set_alpha(self, math.sqrt(alpha))


class SpeedupRenderer(PatchedRendererAgg):
    def new_gc(self):
        """
        Return an instance of a GraphicsContextBase
        """
        return SpeedupGraphicsContext()
