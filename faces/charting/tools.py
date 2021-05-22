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

import matplotlib.transforms as _mtrans
import matplotlib.patches as _patches
import numpy as _numerix
import matplotlib.font_manager as _font

chart_encoding = "iso8859-15"
_minus = _mtrans.Value(-1)
_value_type = type(_minus)


class ChartWrapper(object):
    forwards = []
    def _find_property_in_chain(self, name):
        for f in self.forwards:
            try:
                return f._find_property_in_chain(name)
            except AttributeError:
                pass
            except KeyError:
                pass
            
        raise KeyError(name)
    

chart_properties = ChartWrapper()

def push_active(chart):
    chart_properties.forwards.append(chart)


def pop_active():
    chart_properties.forwards.pop()



def value(val):
    if isinstance(val, Lazy):
        return val.val

    if type(val) is _value_type:
        return val

    return _mtrans.Value(val)


def get_verts(artist, renderer, transform):
    if isinstance(artist, _patches.Patch):
        return artist.get_verts()

    if isinstance(artist, dtext.Text):
        bbox = artist.get_window_extent(renderer)
        verts = ((bbox.xmin(), bbox.ymin()),
                 (bbox.xmin(), bbox.ymax()),
                 (bbox.xmax(), bbox.ymax()),
                 (bbox.xmax(), bbox.ymin()))
        verts = map(_mtrans.inverse_xy_tup, verts)
        return verts

    raise ValueError("artist not known")
    
   

#make mtrans Value mor comfortable
class Lazy(object):
    def __init__(self, val):
        self.val = self.conv(val)


    def __len__(self):
        raise TypeError("len() of unsized object")
    

    def __float__(self):
        return self.val.get()


    def __nonzero__(self):
        return True
    

    def conv(self, other):
        if type(other) is _value_type:
            return other

        try:
            if other.__class__ is self.__class__:
                return other.val
        except:
            pass
        
        return _mtrans.Value(other)

    def __hash__(self):
        return hash(float(self))


    def __add__(self, other): return Lazy(self.val + self.conv(other))
    def __sub__(self, other): return Lazy(self.val - self.conv(other))
    def __mul__(self, other): return Lazy(self.val * self.conv(other))
    def __div__(self, other): return Lazy(self.val / self.conv(other))
    def __radd__(self, other): return Lazy(self.conv(other) + self.val)
    def __rsub__(self, other): return Lazy(self.conv(other) - self.val)
    def __rmul__(self, other): return Lazy(self.conv(other) * self.val)
    def __rdiv__(self, other): return Lazy(self.conv(other) / self.val)
    def __neg__(self): return Lazy(_minus * self.val)

    def set(self, src):
        if src.__class__ is self.__class__:
            self.val.set(src.get())
            return

        if type(src) is _value_type:
            self.val.set(src.get())
            return

        self.val.set(src)


    def get(self):
        return self.val.get()


class LazyBbox:
    def __init__(self, bbox):
        self.bbox = bbox

    def ll(self): return self.bbox.ll()
    def ur(self): return self.bbox.ur()
    def contains(self, x, y): return self.bbox.contains(x, y)
    def overlaps(self, bbox): return self.bbox.overlaps(bbox)
    def overlapsx(self, bbox): return self.bbox.overlapsx(bbox)
    def overlapsy(self, bbox): return self.bbox.overlapsy(bbox)
    def intervalx(self, ): return self.bbox.intervalx()
    def intervaly(self, ): return self.bbox.intervaly()
    def get_bounds(self, ): return self.bbox.get_bounds()
    def update(self, xys, ignore): return self.bbox.update(xys, ignore)
    def width(self, ): return self.bbox.width()
    def height(self, ): return self.bbox.height()
    def xmax(self, ): return self.bbox.xmax()
    def ymax(self, ): return self.bbox.ymax()
    def xmin(self, ): return self.bbox.xmin()
    def ymin(self, ): return self.bbox.ymin()
    def scale(self, sx,sy): return self.bbox.scale(sx,sy)
    def deepcopy(self, ): return self.bbox.deepcopy()


    
def draw_lines(renderer, gc, xs, ys, trans):
    xs = map(float, xs)
    ys = map(float, ys)
    try:
        renderer.draw_lines(gc, xs, ys, trans)
    except TypeError:
        xs, ys = trans.seq_x_y(xs, ys)
        xs = _numerix.array(xs, typecode=_numerix.Int16)
        ys = _numerix.array(ys, typecode=_numerix.Int16)
        renderer.draw_lines(gc, xs, ys)


def draw_line(renderer, gc, x1, y1, x2, y2, trans):
    #patch because agg_renderer.draw_line has a bug
    x = _numerix.array([x1,x2], typecode=_numerix.Float)
    y = _numerix.array([y1,y2], typecode=_numerix.Float)
    draw_lines(renderer, gc, x, y, trans)


VSEP = Lazy(_font.fontManager.get_default_size() / 4)
HSEP = Lazy(0)
LEFT = Lazy(0)
RIGHT = Lazy(0)
BOTTOM = Lazy(0)
TOP = Lazy(0)
VCENTER = Lazy(0)
HCENTER = Lazy(0)
FACTOR = Lazy(1)


def set_helpers(bbox, all_bbox):
    LEFT.set(bbox.xmin())
    RIGHT.set(bbox.xmax())
    TOP.set(bbox.ymax())
    BOTTOM.set(bbox.ymin())
    HCENTER.set((max(all_bbox.xmin(), bbox.xmin())\
                 + min(all_bbox.xmax(), bbox.xmax())) / 2)
    VCENTER.set((bbox.ymin() + bbox.ymax()) / 2)


def set_default_size(size):
    _font.fontManager.set_default_size(size)
    VSEP.set(size / 4.0)
    

def set_encoding(coding):
    global chart_encoding
    chart_encoding = coding


def make_properties(props, name):
    return { "edgecolor" : props(name + ".edgecolor"),
             "facecolor" : props(name + ".facecolor"),
             "linewidth" : props(name + ".linewidth"),
             "antialiased" : props(name + ".antialiased"),
             "alpha" : props(name + ".alpha"),
             "fill" : props(name + ".fill") }

