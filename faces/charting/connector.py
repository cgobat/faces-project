#@+leo-ver=4
#@+node:@file charting/connector.py
#@@language python
"""
Line connectors between two widgets.
"""
#@<< Copyright >>
#@+node:<< Copyright >>
############################################################################
#   Copyright (C) 2005, 2006, 2007, 2008 by Reithinger GmbH
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

#@-node:<< Copyright >>
#@nl
#@<< Imports >>
#@+node:<< Imports >>
import widgets
import matplotlib.transforms as mtrans
import matplotlib.colors as colors
import math
from tools import *



#@-node:<< Imports >>
#@nl

_is_source_ = True
_colorConverter = colors.colorConverter

#@+others
#@+node:get_arrow
def get_arrow(cos, sin, tx, ty, width, height):
    h = Lazy(height)
    wm = Lazy(-width * 0.5)
    wp = Lazy(width * 0.5)

    arrow = [ (h, wm), (0, 0), (h, wp) ]

    m11 = HSEP * cos
    m12 = -HSEP * sin
    m21 = VSEP * sin
    m22 = VSEP * cos

    def multplus(vector):
        return (m11 * vector[0] + m12 * vector[1] + tx,
                m21 * vector[0] + m22 * vector[1] + ty)

    return map(multplus, arrow)
#@-node:get_arrow
#@+node:intersect
def intersect(l1, l2):
    """
    Intersects two lines:
        l = (p, d) == p + a * d

        p1 + a * d1 = p2 + b * d2

        returns a, b
    """
    #@    << extract coordinates >>
    #@+node:<< extract coordinates >>
    p1, d1 = l1
    p2, d2 = l2

    p1x, p1y = p1
    d1x, d1y = d1

    p2x, p2y = p2
    d2x, d2y = d2
    #@nonl
    #@-node:<< extract coordinates >>
    #@nl
    l1x = p1x, d1x
    l1y = p1y, d1y
    l2x = p2x, d2x
    l2y = p2y, d2y

    #@    << define calc >>
    #@+node:<< define calc >>
    def calc(mx, my, nx, ny):
        ax, bx = mx
        ay, by = my
        cx, dx = nx
        cy, dy = ny

        rf = bx / by
        n = ((cx - ax - rf * (cy - ay))) 
        d = rf * dy - dx
        beta = n / d
        beta.get()

        if bx.get():
            alpha = (cx + beta * dx - ax) / bx
        else:
            alpha = (cy + beta * dy - ay) / by

        return alpha, beta
    #@nonl
    #@-node:<< define calc >>
    #@nl

    try:
        a, b = calc(l1x, l1y, l2x, l2y)
        return a, b
    except ZeroDivisionError: pass

    try:
        a, b = calc(l1y, l1x, l2y, l2x)
        return a, b
    except ZeroDivisionError: pass

    try:
        b, a = calc(l2x, l2y, l1x, l1y)
        return a, b
    except ZeroDivisionError: pass

    try:
        b, a = calc(l2y, l2x, l1y, l1x)
        return a, b
    except ZeroDivisionError:
        #lines are parallel
        return mtrans.Value(-1), mtrans.Value(-1)
#@-node:intersect
#@+node:GanttConnector
#@+node:Classes for calculating a line path
#@+node:class ConnectorPath
class ConnectorPath(object):
    """
    Base class for path calculation.
    """
    #@	@+others
    #@+node:calc_start_end
    def calc_start_end(cls, src, dest):
        x_ends = cls.calc_x_ends(src, dest)
        return min(x_ends), max(x_ends)

    calc_start_end = classmethod(calc_start_end)
    #@nonl
    #@-node:calc_start_end
    #@+node:get_lines
    def get_lines(cls, src, dest, transform):
        src_end, dest_end = cls.calc_x_ends(src, dest)

        def nearest_x(to_find, verts):
            return float(min(map(lambda v: (abs(float(v[0]) - to_find), v[0]),
                                 verts))[1])
        so = src_end
        do = dest_end
        src_end = nearest_x(src_end, src.shape[0].get_verts())
        dest_end = nearest_x(dest_end, dest.shape[0].get_verts())

        return cls.get_edges((src_end, src.row.y.get(), src),
                             (dest_end, dest.row.y.get(), dest))

    get_lines = classmethod(get_lines)
    #@nonl
    #@-node:get_lines
    #@+node:point_near
    def point_near(cls, point_widget, wanted_y):
        """find all possible connector ends for a given x, y"""
        x, y, widget = point_widget

        bb_shape = mtrans.bound_vertices(widget.shape[0].get_verts())
        set_helpers(bb_shape, bb_shape)
        verts = widget.shape[0].get_verts()
        wy = wanted_y.get()

        def dist_point(point):
            #freeze points
            px = float(point[0])
            py = float(point[1])
            dx = abs(px - x) / HSEP.get()
            dy = abs(py - wy) / VSEP.get()
            return (dx + dy, (point[0], point[1]))

        return min([ dist_point(p) for p in verts ])[1]

    point_near = classmethod(point_near)
    #@nonl
    #@-node:point_near
    #@+node:find_y_pos
    def find_y_pos(cls, src, dest):
        if src[1] < dest[1]: return TOP, BOTTOM
        if src[1] > dest[1]: return BOTTOM, TOP
        return VCENTER, VCENTER

    find_y_pos = classmethod(find_y_pos)
    #@nonl
    #@-node:find_y_pos
    #@+node:get_edges
    def get_edges(cls, src, dest):
        src_y, dest_y = cls.find_y_pos(src, dest)
        return (cls.point_near(src, src_y), cls.point_near(dest, dest_y))

    get_edges = classmethod(get_edges)
    #@nonl
    #@-node:get_edges
    #@-others

#@-node:class ConnectorPath
#@+node:class StartEndPath
class StartEndPath(ConnectorPath):
    #@	@+others
    #@+node:calc_x_ends
    def calc_x_ends(src, dest):
        return src.start, dest.end

    calc_x_ends = staticmethod(calc_x_ends)
    #@nonl
    #@-node:calc_x_ends
    #@+node:get_edges
    def get_edges(cls, src, dest):
        src_y, dest_y = cls.find_y_pos(src, dest)

        if src[0] == dest[0]:
            return (cls.point_near(src, src_y),
                    cls.point_near(dest, dest_y))

        if dest[0] < src[0]:
            s = cls.point_near(src, VCENTER)
            d = cls.point_near(dest, dest_y)
            return (s, (d[0], s[1]), d)

        sp = cls.point_near(src, src_y)
        dp = cls.point_near(dest, dest_y)

        # src[0] > dest[0]
        row = src[2].row
        if src[1] < dest[1]:
            next_floor = row.y + VSEP * row.top_sep / 2
        else:
            next_floor = row.y - row.height - row.bottom_sep / 2 * VSEP

        return (sp, (sp[0], next_floor), (dp[0], next_floor), (dp))

    get_edges = classmethod(get_edges)
    #@nonl
    #@-node:get_edges
    #@-others

#@-node:class StartEndPath
#@+node:class StartStartPath
class StartStartPath(ConnectorPath):
    #@	@+others
    #@+node:calc_x_ends
    def calc_x_ends(src, dest):
        return src.start, dest.start

    calc_x_ends = staticmethod(calc_x_ends)
    #@nonl
    #@-node:calc_x_ends
    #@+node:get_edges
    def get_edges(cls, src, dest):
        src_y, dest_y = cls.find_y_pos(src, dest)

        if src[0] == dest[0]:
            src = cls.point_near(src, src_y)
            dest = cls.point_near(dest, dest_y)
            return (src, dest)

        if dest[0] < src[0]:
            src = cls.point_near(src, VCENTER)
            dest = cls.point_near(dest, dest_y)
            return (src, (dest[0], src[1]), dest)

        src = cls.point_near(src, src_y)
        dest = cls.point_near(dest, VCENTER)

        # src[0] > dest[0]
        return (src, (src[0], dest[1]), dest)

    get_edges = classmethod(get_edges)
    #@nonl
    #@-node:get_edges
    #@-others

#@-node:class StartStartPath
#@+node:class EndStartPath
class EndStartPath(ConnectorPath):
    #@	@+others
    #@+node:calc_x_ends
    def calc_x_ends(src, dest):
        return src.end, dest.start

    calc_x_ends = staticmethod(calc_x_ends)
    #@-node:calc_x_ends
    #@+node:get_edges
    def get_edges(cls, src, dest):
        src_y, dest_y = cls.find_y_pos(src, dest)

        if src[0] == dest[0]:
            return (cls.point_near(src, src_y),
                    cls.point_near(dest, dest_y))

        if src[0] < dest[0]:
            s = cls.point_near(src, VCENTER)
            d = cls.point_near(dest, dest_y)
            return (s, (d[0], s[1]), d)

        s = cls.point_near(src, src_y)
        d = cls.point_near(dest, dest_y)

        # src[0] > dest[0]
        row = src[2].row
        if src[1] < dest[1]:
            next_floor = row.y + VSEP * row.top_sep / 2
        else:
            next_floor = row.y - row.height - row.bottom_sep / 2 * VSEP

        return (s, (s[0], next_floor), (d[0], next_floor), d)

    get_edges = classmethod(get_edges)
    #@nonl
    #@-node:get_edges
    #@-others
#@-node:class EndStartPath
#@+node:class EndEndPath
class EndEndPath(ConnectorPath):
    #@	@+others
    #@+node:calc_x_ends
    def calc_x_ends(src, dest):
        return src.end, dest.end

    calc_x_ends = staticmethod(calc_x_ends)
    #@-node:calc_x_ends
    #@+node:get_edges
    def get_edges(cls, src, dest):
        src_y, dest_y = cls.find_y_pos(src, dest)

        if src[0] == dest[0]:
            src = cls.point_near(src, src_y)
            dest = cls.point_near(dest, dest_y)
            return (src, dest)

        if src[0] < dest[0]:
            src = cls.point_near(src, VCENTER)
            dest = cls.point_near(dest, dest_y)
            return (src, (dest[0], src[1]), dest)

        src = cls.point_near(src, src_y)
        dest = cls.point_near(dest, VCENTER)

        # src[0] > dest[0]
        return (src, (src[0], dest[1]), dest)

    get_edges = classmethod(get_edges)
    #@nonl
    #@-node:get_edges
    #@-others
#@-node:class EndEndPath
#@+node:class ShortestPath
class ShortestPath(ConnectorPath):
    #@	@+others
    #@+node:calc_x_ends
    def calc_x_ends(src, dest):
        if src.start <= dest.end and dest.start <= src.end:
            start = (min(src.end, dest.end) + max(src.start, dest.start)) / 2
            return start, start

        if src.start > dest.end: return src.start, dest.end
        return src.end, dest.start

    calc_x_ends = staticmethod(calc_x_ends)
    #@nonl
    #@-node:calc_x_ends
    #@-others
#@-node:class ShortestPath
#@-node:Classes for calculating a line path
#@+node:class GanttConnector
class GanttConnector(widgets.Widget):
    """
    A connecor path between two gantt widgets.
    """

    #@	<< declarations >>
    #@+node:<< declarations >>
    properties = {
        "width" : 3,
        "height" : 3,
        "edgecolor" : "darkslategray",
        "facecolor" : "darkslategray",
        "open" : False
        }

    zorder = -2

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, src, dest, path, properties=None):
        widgets.Widget.__init__(self, properties)
        self.src = src
        self.dest = dest
        self.set_path(path)
    #@-node:__init__
    #@+node:set_path
    def set_path(self, path):
        self.path = path
        self.start, self.end = path.calc_start_end(self.src, self.dest)
    #@-node:set_path
    #@+node:set_property
    def set_property(self, name, value):
        if name.find("connector") < 0:
            # a convinience hack
            name = "connector." + name

        widgets.Widget.set_property(self, name, value)
    #@-node:set_property
    #@+node:get_bounds
    def get_bounds(self, renderer):
        return self.bbox
    #@-node:get_bounds
    #@+node:contains
    def contains(self, x, y):
        return False
    #@-node:contains
    #@+node:prepare_draw
    def prepare_draw(self, renderer, point_to_pixel, fig_point_to_pixel):
        #fetch all properties
        self.get_patch("connector")
        self.get_patch("connector.end")
        self.get_property("connector.end.open")
        self.get_property("connector.end.width")
        self.get_property("connector.end.height")
        self.get_property("connector.end.facecolor")

        self.set_font_factor(point_to_pixel, fig_point_to_pixel)

        transform = self.get_transform()
        lines = self.path.get_lines(self.src, self.dest, transform)

        self.xs = map(lambda e: e[0], lines)
        self.ys = map(lambda e: e[1], lines)

        self.edx = (self.xs[-2] - self.xs[-1]) / HSEP
        self.edy = (self.ys[-2] - self.ys[-1]) / VSEP
        self.LL = self.edx * self.edx + self.edy * self.edy
        self.cos = Lazy(1)
        self.sin = Lazy(0)

        prop = self.get_property

        awidth = prop("connector.end.width")
        aheight = prop("connector.end.height")

        self.arrow = get_arrow(self.cos, self.sin,
                               self.xs[-1], self.ys[-1],
                               awidth, aheight)

        Point = mtrans.Point
        Value = mtrans.Value
        Bbox = mtrans.Bbox

        to_float = lambda v: (float(v), v)
        xs = map(to_float, self.xs)
        ys = map(to_float, self.ys)

        left = min(xs)[1] - (awidth * 0.5) * HSEP
        right = max(xs)[1] + (awidth * 0.5) * HSEP
        bottom = min(ys)[1]
        top = max(ys)[1]
        self.bbox = Bbox(Point(left.val, bottom.val),
                         Point(right.val, top.val))
        return True, True
    #@-node:prepare_draw
    #@+node:draw
    def draw(self, renderer, data_box):
        if not self.get_visible() or not self.overlaps(data_box): return False
        transform = self.get_transform()

        gc = renderer.new_gc()
        if self.get_clip_on():
            gc.set_clip_rectangle(self.clipbox.get_bounds())

        self.set_gc(gc, "connector")
        draw_lines(renderer, gc, self.xs, self.ys, transform)

        l = math.sqrt(float(self.LL)) or 1.0
        self.cos.set(float(self.edx) / l)
        self.sin.set(float(self.edy) / l)

        self.set_gc(gc, "connector.end")
        if self.get_property("connector.end.open"):
            draw_lines(renderer, gc,
                       map(lambda a: a[0], self.arrow),
                       map(lambda a: a[1], self.arrow),
                       transform)
        else:
            face = self.get_property("connector.end.facecolor")
            face = _colorConverter.to_rgb(face)
            renderer.draw_polygon(gc, face, transform.seq_xy_tups(self.arrow))

        return False
    #@-node:draw
    #@-others
#@-node:class GanttConnector
#@-node:GanttConnector
#@+node:class WBKConnector
class WBKConnector(widgets.Widget):
    """
    A connector of widgets inside a workbreakdown chart
    """
    #@	<< declarations >>
    #@+node:<< declarations >>
    properties = {
        "connector.linewidth" : 1,
        "connector.edgecolor" : "black",
        }

    zorder = -2

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, src, dest, properties=None):
        widgets.Widget.__init__(self, properties)
        self.src = src
        self.dest = dest

        #fetch all properties
        self.get_patch("connector")
    #@-node:__init__
    #@+node:get_bounds
    def get_bounds(self, renderer):
        return self.bbox
    #@-node:get_bounds
    #@+node:contains
    def contains(self, x, y):
        return False
    #@-node:contains
    #@+node:prepare_draw
    def prepare_draw(self, renderer, point_to_pixel, fig_point_to_pixel):
        self.set_font_factor(point_to_pixel, fig_point_to_pixel)

        HSEP.set(VSEP.get())
        Point = mtrans.Point
        BBox = mtrans.Bbox

        src_box = self.src.bbox
        dst_box = self.dest.bbox

        if self.src.row.y.get() > self.dest.row.y.get():
            self.bbox = BBox(Point(src_box.ur().x(), dst_box.ll().y()),
                             Point(dst_box.ll().x(), src_box.ur().y()))
        else:
            self.bbox = BBox(Point(src_box.ur().x(), src_box.ll().y()),
                             Point(dst_box.ll().x(), dst_box.ur().y()))

        hor_middle = float(self.src.col.x + self.src.col.full_width()\
                           - self.src.col.right_sep * HSEP.get() / 2)
        src_middle = (src_box.ymin() + src_box.ymax()) / 2
        dst_middle = (dst_box.ymin() + dst_box.ymax()) / 2

        self.xs = (src_box.xmax(), hor_middle, hor_middle, dst_box.xmin())
        self.ys = (src_middle, src_middle, dst_middle, dst_middle)
        return True, True
    #@-node:prepare_draw
    #@+node:draw
    def draw(self, renderer, data_box):
        if not self.get_visible() or not self.overlaps(data_box): return False
        transform = self.get_transform()

        gc = renderer.new_gc()
        if self.get_clip_on():
            gc.set_clip_rectangle(self.clipbox.get_bounds())

        self.set_gc(gc, "connector")
        draw_lines(renderer, gc, self.xs, self.ys, transform)
        return False
    #@-node:draw
    #@-others
#@-node:class WBKConnector
#@+node:class ShortConnector
class ShortConnector(widgets.Widget):
    """
    A connector that connects two arbitrary widgets on the shortes path
    """
    #@	<< declarations >>
    #@+node:<< declarations >>
    properties = {
        "connector.linewidth" : 1,
        "connector.edgecolor" : "black",
        "connector.arrow.width" : 3,
        "connector.arrow.height" : 3,
        "connector.arrow.edgecolor" : "darkslategray",
        "connector.arrow.facecolor" : "darkslategray",
        "connector.arrow.open" : False,
        "connector.directed" : True
        }

    zorder = -100

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, src, dest, properties=None):
        widgets.Widget.__init__(self, properties)
        self.src = src
        self.dest = dest

        #fetch all properties
        self.get_patch("connector")
    #@-node:__init__
    #@+node:get_bounds
    def get_bounds(self, renderer):
        return self.bbox
    #@-node:get_bounds
    #@+node:contains
    def contains(self, x, y):
        return False
    #@-node:contains
    #@+node:prepare_draw
    def prepare_draw(self, renderer, point_to_pixel, fig_point_to_pixel):
        self.set_font_factor(point_to_pixel, fig_point_to_pixel)

        HSEP.set(VSEP.get())
        Point = mtrans.Point
        BBox = mtrans.Bbox
        Value = mtrans.Value
        Half = Value(0.5)

        src_box = self.src.bbox
        dst_box = self.dest.bbox

        src_x = (src_box.ur().x() + src_box.ll().x()) * Half
        src_y = (src_box.ur().y() + src_box.ll().y()) * Half
        dst_x = (dst_box.ur().x() + dst_box.ll().x()) * Half
        dst_y = (dst_box.ur().y() + dst_box.ll().y()) * Half

        self.bbox = BBox(Point(src_x, src_y), Point(dst_x, dst_y))


        if self.get_property("connector.directed"):
            #@        << calc arrow position >>
            #@+node:<< calc arrow position >>
            self.dx = dx = dst_x - src_x
            self.dy = dy = dst_y - src_y

            #@<< calc line equations >>
            #@+node:<< calc line equations >>
            connector = ((src_x, src_y), (dx, dy))
            left = ((dst_box.ll().x(), dst_box.ll().y()),
                    (Value(0), dst_box.ur().y() - dst_box.ll().y()))
            right = ((dst_box.ur().x(), dst_box.ll().y()),
                     (Value(0), dst_box.ur().y() - dst_box.ll().y()))
            top = ((dst_box.ll().x(), dst_box.ur().y()),
                   (dst_box.ur().x() - dst_box.ll().x(), Value(0)))
            bottom = ((dst_box.ll().x(), dst_box.ll().y()),
                      (dst_box.ur().x() - dst_box.ll().x(), Value(0)))
            #@nonl
            #@-node:<< calc line equations >>
            #@nl

            #find the intersection point
            ips = [ intersect(connector, l) for l in (left, right, top, bottom) ]
            min_a = min([ (a.get(), a) for a, b in ips if 0 <= b.get() <= 1.0 ])[1]

            # arrow stuff
            self.len = dx * dx + dy * dy
            self.cos = Lazy(1)
            self.sin = Lazy(0)

            prop = self.get_property
            awidth = prop("connector.arrow.width")
            aheight = prop("connector.arrow.height")

            self.arrow = get_arrow(self.cos, self.sin,
                                   src_x + min_a * dx,
                                   src_y + min_a * dy,
                                   awidth, aheight)
            #@nonl
            #@-node:<< calc arrow position >>
            #@nl

        return True, True
    #@nonl
    #@-node:prepare_draw
    #@+node:draw
    def draw(self, renderer, data_box):
        if not self.get_visible() or not self.overlaps(data_box): return False
        transform = self.get_transform()

        gc = renderer.new_gc()
        if self.get_clip_on():
            gc.set_clip_rectangle(self.clipbox.get_bounds())

        self.set_gc(gc, "connector")

        x, y, w, h = self.bbox.get_bounds()
        draw_lines(renderer, gc, (x, x + w), (y, y + h), transform)

        if self.get_property("connector.directed"):
            #@        << draw arrow >>
            #@+node:<< draw arrow >>
            l = math.sqrt(self.len.get()) or 1.0
            self.cos.set(-self.dx.get() / l)
            self.sin.set(-self.dy.get() / l)

            self.set_gc(gc, "connector.arrow")
            if self.get_property("connector.arrow.open"):
                draw_lines(renderer, gc,
                           map(lambda a: a[0], self.arrow),
                           map(lambda a: a[1], self.arrow),
                           transform)
            else:
                face = self.get_property("connector.arrow.facecolor")
                face = _colorConverter.to_rgb(face)
                try:
                    arrow = transform.seq_xy_tups(self.arrow)
                except ZeroDivisionError:
                    print "ZeroDivisionError"
                    #for c, a in enumerate(self.arrow):
                    #    print "  ", c, a[0].get(), a[1].get()
                else:
                    renderer.draw_polygon(gc, face, arrow)
            #@nonl
            #@-node:<< draw arrow >>
            #@nl

        return False
    #@nonl
    #@-node:draw
    #@-others
#@-node:class ShortConnector
#@-others
#@-node:@file charting/connector.py
#@-leo
