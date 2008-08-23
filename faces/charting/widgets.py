#@+leo-ver=4
#@+node:@file charting/widgets.py
#@+at
# Mathplot widgets
#@-at
#@@code
#@@language python
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
import matplotlib.text as dtext
import patches
import sys
import faces.plocale
import matplotlib.artist as artist
import matplotlib.transforms as mtrans
import matplotlib.font_manager as font
from matplotlib.colors import colorConverter
import locale
import tools
from tools import *

#@-node:<< Imports >>
#@nl

_is_source_ = True
_ = faces.plocale.get_gettext()

#@+others
#@+node:class LazyText
class LazyText(dtext.Text):
    #@	<< declarations >>
    #@+node:<< declarations >>
    height_cache = {}

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, x, y, text, *args, **kwargs):
        if isinstance(text, str):
            text = unicode(text, tools.chart_encoding)
        dtext.Text.__init__(self, x, y, text, *args, **kwargs)

    def set_x(self, x):
        self._x = x

    def set_y(self, y):
        self._y = y

    #@-node:__init__
    #@+node:get_prop_tup
    def get_prop_tup(self):
        x, y = self._transform.xy_tup((self._x, self._y))
        return (float(self._x), float(self._y), x, y, self._text, self._color,
                self._verticalalignment, self._horizontalalignment,
                hash(self._fontproperties), self._rotation)
    #@-node:get_prop_tup
    #@+node:draw
    def draw(self, renderer):
        if self.get_size() < 3: return False
        dtext.Text.draw(self, renderer)
        return True
    #@-node:draw
    #@+node:get_bottom_top
    def get_bottom_top(self, renderer):
        height = self.height_cache.get(hash(self._fontproperties))
        if height is None:
            w, height = renderer.get_text_width_height("Xg",
                                                       self._fontproperties,
                                                       False)
            self.height_cache[hash(self._fontproperties)] = height

        if self._verticalalignment=='center': yo = -height/2.
        elif self._verticalalignment=='top': yo = -height
        else: yo = 0
        xb, yb = self._transform.xy_tup((self._x, self._y))
        yt = yb + height
        return yb, yt
    #@-node:get_bottom_top
    #@+node:get_window_extent
    def get_window_extent(self, renderer=None):
        text = self._text
        self._text = self._text.replace(" ", "_")
        result = dtext.Text.get_window_extent(self, renderer)
        self._text = text
        return result
    #@-node:get_window_extent
    #@-others
#@-node:class LazyText
#@+node:class _PropertyType


class _PropertyType(type):
    #@	@+others
    #@+node:__init__
    def __init__(cls, name, bases, dict_):
        super(_PropertyType, cls).__init__(name, bases, dict_)

        bchain = [ cls ]
        for b in (cls, ) + cls.__bases__:
            bchain.extend(getattr(b, "_base_chain", []))

        #remove duplicates and preserve order

        bchain = filter(lambda b: hasattr(b, "properties"), bchain)
        bchain = dict(zip(bchain, enumerate(bchain))).values()
        bchain.sort()
        bchain = map(lambda c: c[1], bchain)
        cls._base_chain = tuple(bchain)

        prop_vars = filter(lambda kv: kv[0].endswith("properties")\
                           and isinstance(kv[1], dict),
                           dict_.items())
        for pk, dv in prop_vars:
            for k, v in dv.iteritems():
                check_property(k, v)
    #@-node:__init__
    #@-others
#@-node:class _PropertyType
#@+node:check_property
def check_property(name, value):
    def do_raise(choices=None):
        if choices:
            raise ValueError(_('Invalid value "%(value)s" '\
                               'for property "%(name)s. Possible Values are: %(choices)s"') %
                             { "name" : name, "value" : str(value), 'choices' : choices } )
        else:
            raise ValueError(_('Invalid value "%(value)s" '\
                               'for property "%(name)s"') %
                             { "name" : name, "value" : str(value) } )

    def name_mends(*args):
        for n in args:
            if name.endswith(n): return True
        return False

    name_ends = name.endswith

    if name_ends("color"):
        try:
            colorConverter.to_rgb(value)
        except ValueError:
            do_raise()

    elif name_mends("width", "alpha", "magnification", "height"):
        try:
            float(value)
        except ValueError:
            do_raise()

    elif name_ends("family"):
        try:
            font.fontManager.ttfdict[value]
        except KeyError:
            default_names = ['serif', 'sans-serif', 'cursive',
                             'fantasy', 'monospace', 'sans']
            if value not in default_names:
                do_raise(", ".join(font.fontManager.ttfdict.keys()\
                                   + default_names))

    elif name.endswith("weight"):
        try:
            if not (isinstance(value, basestring) and font.weight_dict[value]):
                int(value)
        except Exception:
            do_raise()

    elif name.endswith("size"):
        try:
            if not (isinstance(value, basestring) and font.font_scalings[value]):
                int(value)
        except Exception:
            do_raise()

    elif name.endswith("variant"):
        if value not in ('normal', 'capitals', 'small-caps'):
            do_raise()

    elif name.endswith("linestyle"):
        if value not in ("solid", "dashed", "dashdot", "dotted"):
            do_raise()

    elif name.endswith("joinstyle"):
        if value not in ('miter', 'round', 'bevel'):
            do_raise()

    elif name.endswith("style"):
        if value not in ("italics", "oblique", "normal"):
            do_raise()

    elif name == "tickers":
        if not isinstance(value, (tuple, list, int)):
            do_raise()
#@-node:check_property
#@+node:class _PropertyAware





class _PropertyAware(object):
    #@	<< class _PropertyAware declarations >>
    #@+node:<< class _PropertyAware declarations >>
    __metaclass__ = _PropertyType 

    search_chain = ()
    font_attribs = ("family", "style", "weight", "size", "variant")
    patch_attribs = ("edgecolor", "linewidth", "antialiased", \
                     "fill", "facecolor", "alpha" )


    #@-node:<< class _PropertyAware declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, properties=None):
        self.properties = {}
        if properties:
            self.properties.update(properties)
    #@-node:__init__
    #@+node:set_property
    def set_property(self, name, value):
        """
        Sets a specific property
        """
        check_property(name, value)
        self.properties[name] = value
    #@-node:set_property
    #@+node:remove_property
    def remove_property(self, name):
        """
        Removes a property, and restores a default value.
        """

        try:
            del self.properties[name]
        except:
            pass
    #@-node:remove_property
    #@+node:_find_property_in_chain
    def _find_property_in_chain(self, name):
        try:
            return self.properties[name]
        except KeyError:
            pass

        for s in getattr(self, "search_chain", ()):
            try:
                return s._find_property_in_chain(name)
            except KeyError: pass


        for s in self._base_chain:
            try:
                return s.properties[name]
            except KeyError: pass

        raise KeyError(name)
    #@-node:_find_property_in_chain
    #@+node:_find_property
    def _find_property(self, name):
        index = 0
        while True:
            try:
                value = self._find_property_in_chain(name[index:])
                self.properties[name] = value
                return value
            except KeyError: pass
            index = name.find(".", index) + 1
            if index <= 0: break

        raise KeyError("Key error: %s" % name)
    #@-node:_find_property
    #@+node:get_font
    def get_font(self, name):
        kwargs = {}
        for a in self.font_attribs:
            kwargs[a] = self.get_property(name + "." + a)

        return font.FontProperties(**kwargs)
    #@-node:get_font
    #@+node:get_property
    def get_property(self, name, default=None):
        try:
            return self._find_property(name)
        except KeyError:
            if default is not None:
                return default
            raise
    #@-node:get_property
    #@+node:set_gc
    def set_gc(self, gc, name=""):
        prop = self.get_property
        if gc:
            gc.set_foreground(prop(name + ".edgecolor"))
            gc.set_linewidth(prop(name + ".linewidth"))
            gc.set_linestyle(prop(name + ".linestyle"))
            gc.set_antialiased(prop(name + ".antialiased"))
            gc.set_alpha(prop(name + ".alpha"))
        else:
            prop(name + ".edgecolor")
            prop(name + ".linewidth")
            prop(name + ".linestyle")
            prop(name + ".antialiased")
            prop(name + ".alpha")
    #@-node:set_gc
    #@+node:get_patch
    def get_patch(self, name=""):
        kwargs = {}
        for a in self.patch_attribs:
            kwargs[a] = self.get_property(name + "." + a)

        return kwargs
    #@-node:get_patch
    #@-others
#@-node:class _PropertyAware
#@+node:class Widget
class Widget(artist.Artist, _PropertyAware):
    #@	<< declarations >>
    #@+node:<< declarations >>
    properties = {
        "weight" : "normal",
        "size" : "medium",
        "style" : "normal",
        "variant" : "normal", 
        "color": 'black',
        "facecolor" : 'black',
        "edgecolor" : 'black',
        "linewidth" : 1,
        "joinstyle" : 'miter',
        "linestyle" : 'solid',
        "fill" : 1,
        "antialiased" : True,
        "alpha" : 1.0 }

    search_chain = (chart_properties,)

    bbox = mtrans.unit_bbox()
    fobj = None

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, properties=None):
        _PropertyAware.__init__(self, properties)
        artist.Artist.__init__(self)
        self.artists = []
    #@-node:__init__
    #@+node:_extend_text_properties
    def _extend_text_properties(self, kwargs):
        fp = kwargs.get("fontproperties", "")
        if not isinstance(fp, font.FontProperties):
            kwargs["fontproperties"] = self.get_font(fp)

        if not kwargs.has_key("color") and isinstance(fp, basestring):
            kwargs["color"] = self.get_property(fp + ".color")

        return kwargs
    #@-node:_extend_text_properties
    #@+node:clear
    def clear(self):
        """
        Clears all decorations of the widget.
        """
        self.artists = []

    clear.__call_completion__ = "clear()"
    #@-node:clear
    #@+node:text
    def text(self, txt, x, y, **kwargs):
        """
        Adds a text decoration to the widget.
        """
        kwargs = self._extend_text_properties(kwargs)
        artist = LazyText(x, y, txt, **kwargs)
        self.artists.append(artist)
        return artist

    text.__call_completion__ = """text("|",
    HCENTER, TOP + VSEP,
    horizontalalignment="center",
    verticalalignment="bottom",
    fontproperties="center")
    """    
    #@-node:text
    #@+node:set_figure
    def set_figure(self, figure):
        artist.Artist.set_figure(self, figure)
        for t in self.all_artists():
            t.set_figure(figure)
    #@-node:set_figure
    #@+node:set_transform
    def set_transform(self, transform):
        artist.Artist.set_transform(self, transform)
        for t in self.all_artists():
            t.set_transform(transform)
    #@-node:set_transform
    #@+node:set_clip_box
    def set_clip_box(self, clipbox):
        artist.Artist.set_clip_box(self, clipbox)
        for t in self.all_artists():
            t.set_clip_box(clipbox)
    #@-node:set_clip_box
    #@+node:all_artists
    def all_artists(self):
        return self.artists
    #@-node:all_artists
    #@+node:add_artist
    def add_artist(self, artist):
        self.artists.insert(0, artist)

    add_artist.__call_completion__ = "add_artist(|)"
    #@-node:add_artist
    #@+node:set_font_factor
    def set_font_factor(self, point_to_pixel, fig_point_to_pixel):
        """
        Change the fontsize, if the canvas is zoomed
        """
        font_factor = Lazy(point_to_pixel / fig_point_to_pixel)
        for t in filter(lambda t: isinstance(t, dtext.Text), self.artists):
            size = t.get_size()
            t.set_size(font_factor * t.get_size())
    #@-node:set_font_factor
    #@+node:prepare_draw
    def prepare_draw(self, renderer, point_to_pixel, fig_point_to_pixel):
        """
        returns a pair of boolean values:
        The first value means horizontal data_limits should be updated)
        The second value means vertical data_limits should be updated
        """
        raise NotImplementedError()
    #@-node:prepare_draw
    #@+node:overlaps
    def overlaps(self, bbox):
        return bbox.overlaps(self.bbox)
    #@-node:overlaps
    #@+node:contains
    def contains(self, x, y):
        return self.bbox.contains(x, y)
    #@-node:contains
    #@+node:get_bounds
    def get_bounds(self, renderer):
        raise NotImplementedError()
    #@-node:get_bounds
    #@-others
#@-node:class Widget
#@+node:class Row
class Row(Widget):
    """
    This class represents a row within a chart

    @var top_sep:
    Top space between row content and the row's
    top edge in VSEP units.

    @var bottom_sep:
    Bottom space between row content and the row's
    bottom edge in VSEP units.
    """
    #@	<< class Row declarations >>
    #@+node:<< class Row declarations >>
    properties = { "edgecolor" : 'gray',
                   "linewidth" : 1,
                   "linestyle" : 'solid',
                   "alpha" : 1.0,
                   "antialiased" : True }

    top_sep = 2
    bottom_sep = 2
    show_rowline = False
    zorder = -100

    #@-node:<< class Row declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, properties=None):
        Widget.__init__(self, properties)
        self.y = Lazy(0)
        self.height = Lazy(0)
        self.show_rowline = self.__class__.show_rowline

        #fetch line properties
        if self.show_rowline: self.set_gc(None, "row")
    #@-node:__init__
    #@+node:update_height
    def update_height(self, height):
        self.height.set(max(self.height.get(), height))
    #@-node:update_height
    #@+node:draw
    def draw(self, renderer, data_box):
        data_box = self.get_transform().get_bbox1()
        if not self.get_visible() or not self.overlaps(data_box): return False

        all_artists = self.all_artists()
        if all_artists:
            set_helpers(self.bbox, self.bbox)
            for a in self.all_artists(): a.draw(renderer)

        if not self.show_rowline: return False
        def prop(name): return self.get_property(name)
        transform = self.get_transform()

        gc = renderer.new_gc()
        if self.get_clip_on():
            gc.set_clip_rectangle(self.clipbox.get_bounds())

        left, right = self.bbox.intervalx().get_bounds()
        self.set_gc(gc, "row")
        y = self.bottom - self.bottom_sep * VSEP
        y = y.get()
        draw_line(renderer, gc, left, y, right, y, transform)
        return bool(self.fobj)
    #@-node:draw
    #@+node:set_y
    def set_y(self, y):
        self.y = Lazy(y)
        self.bottom = self.y - self.height - self.top_sep * VSEP
        return self.next_y()
    #@-node:set_y
    #@+node:full_height
    def full_height(self):
        return self.height + (self.top_sep + self.bottom_sep) * VSEP
    #@-node:full_height
    #@+node:next_y
    def next_y(self):
        return self.y - self.full_height()
    #@-node:next_y
    #@+node:reset_height
    def reset_height(self):
        self.height.set(0)
    #@-node:reset_height
    #@+node:contains
    def contains(self, x, y):
        return bool(self.fobj) and self.bbox.contains(x, y)
    #@-node:contains
    #@+node:prepare_draw
    def prepare_draw(self, renderer, point_to_pixel, fig_point_to_pixel):
        self.set_font_factor(point_to_pixel, fig_point_to_pixel)

        data_box = self.get_transform().get_bbox1()
        all_artists = self.all_artists()
        if all_artists:
            bbox = mtrans.unit_bbox()
            set_helpers(bbox, bbox)
            extent = lambda t: t.get_window_extent(renderer)
            bb_all = mtrans.bbox_all(map(extent, all_artists))
            bbox = mtrans.transform_bbox(self.get_transform(), bbox)
            height = (bb_all.ymax() - bbox.ymin()) / fig_point_to_pixel.get()
            self.update_height(height)

        Point = mtrans.Point
        Value = mtrans.Value

        t = self.y.val
        b = self.bottom - self.bottom_sep * VSEP
        b = b.val
        self.bbox = mtrans.Bbox(Point(data_box.ll().x(), b),
                                Point(data_box.ur().x(), t))

        return False, True
    #@-node:prepare_draw
    #@+node:get_bounds
    def get_bounds(self, renderer):
        return self.bbox
    #@-node:get_bounds
    #@-others
#@-node:class Row
#@+node:class Column
class Column(Widget):
    #@	<< class Column declarations >>
    #@+node:<< class Column declarations >>
    properties = { "edgecolor" : 'gray',
                   "linewidth" : 1,
                   "linestyle" : 'solid',
                   "alpha" : 1.0,
                   "antialiased" : True }

    left_sep = 1
    right_sep = 1
    show_colline = False
    zorder = -100

    #@-node:<< class Column declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, properties=None):
        Widget.__init__(self, properties)
        self.x = Lazy(0)
        self.width = Lazy(0)
        self.show_colline = self.__class__.show_colline

        #fetch line properties
        if self.show_colline: self.set_gc(None, "col")
    #@-node:__init__
    #@+node:update_width
    def update_width(self, width):
        self.width.set(max(self.width.get(), width))
    #@-node:update_width
    #@+node:draw
    def draw(self, renderer, data_box):
        data_box = self.get_transform().get_bbox1()
        if not self.get_visible() or not self.overlaps(data_box): return False

        all_artists = self.all_artists()
        if all_artists:
            set_helpers(self.bbox, self.bbox)
            for a in self.all_artists(): a.draw(renderer)

        if not self.show_colline: return
        def prop(name): return self.get_property(name)
        transform = self.get_transform()

        gc = renderer.new_gc()
        if self.get_clip_on():
            gc.set_clip_rectangle(self.clipbox.get_bounds())

        bottom, top = self.bbox.intervaly().get_bounds()
        self.set_gc(gc, "col")
        x = self.x + self.width + (self.left_sep + self.right_sep) * HSEP
        x = x.get()
        draw_line(renderer, gc, x, bottom, x, top, transform)
        return False
    #@-node:draw
    #@+node:set_x
    def set_x(self, x):
        self.x = Lazy(x)
        return self.next_x()
    #@-node:set_x
    #@+node:full_width
    def full_width(self):
        return self.width + (self.left_sep + self.right_sep) * HSEP
    #@-node:full_width
    #@+node:next_x
    def next_x(self):
        return self.x + self.full_width()
    #@-node:next_x
    #@+node:reset_width
    def reset_width(self):
        self.width.set(0)
    #@-node:reset_width
    #@+node:contains
    def contains(self, x, y):
        return False
    #@-node:contains
    #@+node:prepare_draw
    def prepare_draw(self, renderer, point_to_pixel, fig_point_to_pixel):
        self.set_font_factor(point_to_pixel, fig_point_to_pixel)

        Point = mtrans.Point
        Value = mtrans.Value
        data_box = self.get_transform().get_bbox1()
        HSEP.set(VSEP.get())

        l = self.x.val
        r = self.x + self.width + (self.left_sep + self.right_sep) * HSEP
        r = r.val
        self.bbox = mtrans.Bbox(Point(l, data_box.ll().y()),
                                Point(r, data_box.ur().y()))
        return True, False
    #@-node:prepare_draw
    #@+node:get_bounds
    def get_bounds(self, renderer):
        return self.bbox
    #@-node:get_bounds
    #@-others
#@-node:class Column
#@+node:class CellWidget
_two = Lazy(2)

class CellWidget(Widget):
    #@	<< declarations >>
    #@+node:<< declarations >>
    min_height = 0
    min_width = 0
    vert_sep = 2
    horz_sep = 2

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, row, col, fobj, properties=None):
        Widget.__init__(self, properties)
        self.row = row
        self.col = col
        self.fobj = fobj
    #@-node:__init__
    #@+node:get_bounds
    def get_bounds(self, renderer):
        return self.bbox
    #@-node:get_bounds
    #@+node:prepare_draw
    def prepare_draw(self, renderer, point_to_pixel, fig_point_to_pixel):
        self.set_font_factor(point_to_pixel, fig_point_to_pixel)

        #calculate cell bounding box
        Point = mtrans.Point
        Bbox = mtrans.Bbox
        HSEP.set(VSEP.get())
        left = self.col.x + self.col.left_sep * HSEP
        right = left + self.col.width
        top = self.row.y - self.row.top_sep * VSEP
        bottom = self.row.bottom
        self.bbox = Bbox(Point(left.val, bottom.val), Point(right.val, top.val))
        self.row.update_height(self.min_height)
        self.col.update_width(self.min_width)

        #get height and width
        set_helpers(self.bbox, self.bbox)
        extent = lambda t: t.get_window_extent(renderer)
        text_artists = filter(lambda t: isinstance(t, dtext.Text), self.artists)
        bb_all = mtrans.bbox_all(map(extent, text_artists))

        self.row.update_height(bb_all.height() / fig_point_to_pixel.get()\
                               + self.vert_sep * VSEP.get())
        self.col.update_width(bb_all.width() / fig_point_to_pixel.get() \
                              + self.horz_sep * HSEP.get())

        return True, True
    #@-node:prepare_draw
    #@+node:draw
    def draw(self, renderer, data_box):
        data_box = self.get_transform().get_bbox1()
        if not self.get_visible() or not self.overlaps(data_box): return False
        set_helpers(self.bbox, self.bbox)
        #print "draw cell", self.artists[0].get_text(), self.bbox.get_bounds()
        for a in self.all_artists(): a.draw(renderer)
        return True
    #@-node:draw
    #@-others
#@-node:class CellWidget
#@+node:class BoxedTextWidget
class BoxedTextWidget(Widget):
    """
    A boxed text widget. The constructor accepts the following
    arguments:

    Why check_font_factor and all the complicated stuff:
    The text width of LazyText does not scale linear, resulting
    in text overlapping boxes. check_font_factor calculates a
    newbounding box, for a new font_factor

    """

    #@	@+others
    #@+node:__init__
    def __init__(self, text, fobj, properties=None,
                 fattrib=None, left=4, right=4,
                 top=4, bottom=4, **kwargs):
        super(BoxedTextWidget, self).__init__(properties)

        self.fobj = fobj
        self.fattrib  = fattrib
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        kwargs = self._extend_text_properties(kwargs)
        self.text = LazyText(LEFT + self.left, BOTTOM + self.bottom, 
                             text, **kwargs)
        self.artists.append(self.text)


    #@-node:__init__
    #@+node:get_bounds
    def get_bounds(self, renderer):
        self.check_font_factor(renderer)
        return self.bbox
    #@-node:get_bounds
    #@+node:prepare_draw (stage2)
    def prepare_draw_stage2(self, renderer, point_to_pixel, fig_point_to_pixel):
        self.set_font_factor(point_to_pixel, fig_point_to_pixel)
        self.font_factor = Lazy(point_to_pixel / fig_point_to_pixel)
        return True, True
    #@-node:prepare_draw (stage2)
    #@+node:prepare_draw (stage1)
    def prepare_draw(self, renderer, point_to_pixel, fig_point_to_pixel):
        self.set_font_factor(point_to_pixel, fig_point_to_pixel)

        bbox = self.calc_bounding_box(renderer)
        Point = mtrans.Point
        BBox = mtrans.Bbox
        x = Lazy(0)
        y = Lazy(0)
        self.width = w = Lazy(0)
        self.height = h = Lazy(0)
        self.bbox = BBox(Point(x.val, y.val), Point(x.val + w.val, y.val + h.val))
        self.width.set(bbox.width())
        self.height.set(bbox.height())
        self.prepare_draw = self.prepare_draw_stage2
        return True, True
    #@nonl
    #@-node:prepare_draw (stage1)
    #@+node:calc_bounding_box
    def calc_bounding_box(self, renderer):
        inverse = mtrans.inverse_transform_bbox
        bbox = mtrans.unit_bbox()

        #@    << calculate bbox based on self.text >>
        #@+node:<< calculate bbox based on self.text >>
        set_helpers(bbox, bbox)
        bbox = self.text.get_window_extent(renderer)
        bbox = inverse(self.get_transform(), bbox)

        xmin, xmax = bbox.intervalx().get_bounds()
        bbox.intervalx().set_bounds(xmin, xmax + self.left + self.right)
        ymin, ymax = bbox.intervaly().get_bounds()
        bbox.intervaly().set_bounds(ymin, ymax + self.top + self.bottom)
        #@-node:<< calculate bbox based on self.text >>
        #@nl
        #@    << calculate bbox with all artists >>
        #@+node:<< calculate bbox with all artists >>
        set_helpers(bbox, bbox)
        extends = [ t.get_window_extent(renderer) for t in self.artists ]
        if extends:
            bb_all = mtrans.bbox_all(extends)
            bb_all = inverse(self.get_transform(), bb_all)
            bbox = mtrans.bbox_all((bb_all, bbox))
        #@nonl
        #@-node:<< calculate bbox with all artists >>
        #@nl
        return bbox
    #@nonl
    #@-node:calc_bounding_box
    #@+node:set_pos
    def set_pos(self, x, y):
        Point = mtrans.Point
        BBox = mtrans.Bbox
        x = Lazy(x)
        y = Lazy(y)
        w = self.width
        h = self.height
        self.bbox = BBox(Point(x.val, y.val), Point(x.val + w.val, y.val + h.val))
    #@-node:set_pos
    #@+node:draw
    def draw(self, renderer, data_box):
        if not self.get_visible() or not self.overlaps(data_box): return False
        self.check_font_factor(renderer)
        set_helpers(self.bbox, self.bbox)
        for a in self.all_artists(): a.draw(renderer)
        return True
    #@-node:draw
    #@+node:check_font_factor
    __last_font_factor = 0    
    def check_font_factor(self, renderer):
        font_factor = self.font_factor.get()
        if self.__last_font_factor != font_factor:
            self.__last_font_factor = font_factor
            bbox = self.calc_bounding_box(renderer)
            self.width.set(bbox.width())
            self.height.set(bbox.height())
    #@-node:check_font_factor
    #@-others
#@nonl
#@-node:class BoxedTextWidget
#@+node:class TableWidget
class TableWidget(Widget):
    """
    A table widget, that can have other widgets in its cells
    """

    #@	@+others
    #@+node:__init__
    def __init__(self, rows, cols, properties=None):
        super(TableWidget, self).__init__(properties)
        self.cells = [ [ None ] * cols for r in range(rows) ]
    #@-node:__init__
    #@+node:set_cell
    def set_cell(self, row, col, widget, valign="center", halign="center"):
        self.cells[row][col] = widget
        widget._valign = valign
        widget._halign = halign
    #@nonl
    #@-node:set_cell
    #@+node:get_bounds
    def get_bounds(self, renderer):
        self.check_font_factor(renderer)
        return self.bbox
    #@-node:get_bounds
    #@+node:prepare_draw (stage1)
    def prepare_draw(self, renderer, point_to_pixel, fig_point_to_pixel):
        self.set_font_factor(point_to_pixel, fig_point_to_pixel)

        zero = mtrans.zero
        Point = mtrans.Point
        BBox = mtrans.Bbox

        widest_cells = self.widest_cells = [ None ] * len(self.cells[0])
        max_widths = [ 0 ] * len(widest_cells)

        highest_cells = self.highest_cells = [ ]

        zorder = sys.maxint
        for row in self.cells:
            max_height = 0
            highest_cell = None
            for c, cell in enumerate(row):
                cell.prepare_draw(renderer, point_to_pixel, fig_point_to_pixel)

                w = cell.bbox.width()
                h = cell.bbox.height 
                if w > max_widths[c]:
                    widest_cells[c] = cell
                    max_widths[c] = w

                if h > max_height:
                    highest_cell = cell
                    max_height = h

                zorder = min(zorder, cell.zorder)

            highest_cells.append(highest_cell)

        self.zorder = zorder - 1

        self.width = w = sum([c.width for c in self.widest_cells])
        self.height = h = sum([c.height for c in self.highest_cells])

        x = y = Lazy(0)
        self.bbox = BBox(Point(x.val, y.val), 
                         Point(x.val + w.val, y.val + h.val))

        self.prepare_draw = self.prepare_draw_stage2
        return True, True
    #@-node:prepare_draw (stage1)
    #@+node:prepare_draw (stage2)
    def prepare_draw_stage2(self, renderer, point_to_pixel, fig_point_to_pixel):
        self.set_font_factor(point_to_pixel, fig_point_to_pixel)

        registry = {}
        for cell in self.widest_cells:
            self.axes.add_widget(cell)
            registry[cell] = True

        for r, row in enumerate(self.cells):
            for c, cell in enumerate(row):
                if not cell or cell in registry: continue
                self.axes.add_widget(cell)

        return True, True
    #@-node:prepare_draw (stage2)
    #@+node:set_pos
    def set_pos(self, x, y):
        Point = mtrans.Point
        BBox = mtrans.Bbox
        left = x = Lazy(x)
        y = Lazy(y)
        w = self.width
        h = self.height
        bbox = self.bbox = BBox(Point(x.val, y.val), Point(x.val + w.val, y.val + h.val))

        ry = Lazy(bbox.ur().y())

        widest_cells = self.widest_cells
        highest_cells = self.highest_cells

        for r, row in enumerate(self.cells):
            height = highest_cells[r].height
            ry -= height
            cx = Lazy(left)
            for c, cell in enumerate(row):
                width = widest_cells[c].width
                ocx = cx
                cx += width

                if not cell: continue
                w, h  = cell.width, cell.height 
                if cell._valign == "top":
                    y = ry + height - h
                elif cell._valign == "center":
                    y = ry + (height - h) / 2
                else:
                    y = ry.get()

                if cell._halign == "right":
                    x = ocx + width - w
                elif cell._halign == "center":
                    x = ocx + (width - w) / 2
                else:
                    x = ocx

                cell.set_pos(x, y)

    #@-node:set_pos
    #@+node:draw
    def draw(self, renderer, data_box):
        data_box = self.get_transform().get_bbox1()
        if not self.get_visible() or not self.overlaps(data_box): return False

        self.check_font_factor(renderer)
        set_helpers(self.bbox, self.bbox)
        for a in self.all_artists(): a.draw(renderer)

        transform = self.get_transform()

        l = self.bbox.ll().x()
        r = self.bbox.ur().x()
        b = self.bbox.ll().y()
        t = self.bbox.ur().y()

        lf = l.get()
        rf = r.get()
        tf = t.get()
        bf = b.get()

        gc = renderer.new_gc()
        self.set_gc(gc, "rowlines")
        ry = t

        for c in self.highest_cells:
            ry -= c.height
            ryf = ry.get()
            draw_lines(renderer, gc, (lf, rf), (ryf, ryf), transform)

        rx = l
        for c in self.widest_cells:
            rxf = rx.get()
            draw_lines(renderer, gc, (rxf, rxf), (bf, tf), transform)
            rx += c.width

        return True

    #@-node:draw
    #@+node:check_font_factor
    def check_font_factor(self, renderer):
        for c in self.widest_cells:
            c.check_font_factor(renderer)

    #@-node:check_font_factor
    #@-others

#@-node:class TableWidget
#@+node:class TimeWidget
class TimeWidget(Widget):
    #@	<< declarations >>
    #@+node:<< declarations >>
    properties = {
        "inside.color" : "white",
        "valign" : 'center',
        "magnification" : 1.0 }

    shape_height = 8
    start = sys.maxint
    end = 0
    row = Row
    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, start, end, fobj, row=None, properties=None):
        Widget.__init__(self, properties)
        self.start = start
        self.end = end
        self.row = row or Row()
        self.fobj = fobj
        self.text_inside = ()
        self.shape = ()
    #@-node:__init__
    #@+node:set_shape
    def set_shape(self, shape, *args, **kwargs):
        """
        Sets the widgetes shape.

        @args: (shape, shape_arg1, ...)
        """
        self.shape_func = (shape, args, kwargs)

    set_shape.__call_completion__ = "set_shape(|)"
    #@-node:set_shape
    #@+node:all_artists
    def all_artists(self):
        return tuple(self.artists) + self.shape
    #@-node:all_artists
    #@+node:finalized_row
    def finalized_row(self):
        #now the row is fixed: it is time to get the shape
        factor = Lazy(self.shape_height)
        self.height = mtrans.Value(0)
        self.depth = mtrans.Value(0)

        bb_bottom = self.row.bottom
        dh = self.row.height - self.height

        valign = self.get_property("valign")
        if valign == "center":
            bb_bottom += dh / _two
        elif valign == "top":
            bb_bottom += dh

        bottom = bb_bottom + self.depth
        top = bottom + factor * VSEP
        vcenter = (top + bottom) / _two

        left = Lazy(self.start)
        right = Lazy(self.end)
        hcenter = (left + right) / _two

        globs = self.shape_func[0].func_globals
        old_globs = {}
        def set_glob(name, value):
            old_globs[name] = globs.get(name)
            globs[name] = value

        set_glob("LEFT", left)
        set_glob("RIGHT", right)
        set_glob("TOP", top)
        set_glob("BOTTOM", bottom)
        set_glob("HCENTER", hcenter)
        set_glob("VCENTER", vcenter)
        set_glob("FACTOR", factor)
        self.shape = self.shape_func[0](self.get_property,
                                        *self.shape_func[1],
                                        **self.shape_func[2])
        globs.update(old_globs)

        bb_top = bottom + self.height
        self.shape_bbox = mtrans.Bbox(mtrans.Point(left.val, bb_bottom.val),
                                      mtrans.Point(right.val, bb_top.val))

        for s in self.shape:
            s.set_figure(self.get_figure())
            s.set_clip_box(self.get_clip_box())
            s.set_transform(self.get_transform())

        del self.shape_func
    #@-node:finalized_row
    #@+node:inside_text
    def inside_text(self, txt, x=None, y=None,
                    inside_properties="inside",
                    **kwargs):
        """
        Adds a text decoration inside the widget.
        If x and y are not None, the text will be
        placed at that position, if the text is larger
        than the widget's width.
        """

        if not txt: return

        def prop(name): return self.get_property(name)
        inside = LazyText(HCENTER, VCENTER,
                          txt, prop(inside_properties + ".color"),
                          "center", "center",
                          fontproperties=self.get_font(inside_properties))

        if x is None:
            self.text_inside = ( inside, )
        else:
            kwargs = self._extend_text_properties(kwargs)
            self.text_inside = ( LazyText(x, y, txt, **kwargs), inside )

        self.artists.extend(self.text_inside)
        return self.text_inside

    inside_text.__call_completion__ = """inside_text("|",
    RIGHT + HSEP, VCENTER,
    horizontalalignment="left",
    verticalalignment="center",
    fontproperties="right")"""
    #@-node:inside_text
    #@+node:get_bounds
    def get_bounds(self, renderer):
        show = self.fobj.name in ("Outer", "inner")

        transform = self.get_transform()
        extent = lambda t: t.get_window_extent(renderer)

        # calc shape bounding (in data coords)
        bb_shape = mtrans.bound_vertices(self.shape[0].get_verts())
        bb_shape_view = mtrans.transform_bbox(transform, bb_shape) # in view coords

        set_helpers(bb_shape, bb_shape)

        if self.text_inside:
            #@        << check if inside text fits into the shape >>
            #@+node:<< check if inside text fits into the shape >>

            inside_ext = map(extent, self.text_inside)
            contains = bb_shape_view.contains

            inside = inside_ext[-1]
            inside_text = self.text_inside[-1]
            outside_text = self.text_inside[0] 

            mid = (inside.ymin() + inside.ymax()) / 2
            if contains(inside.xmin(), mid) and contains(inside.xmax(), mid):
                outside_text.set_visible(False)
                inside_text.set_visible(True)
            else:
                outside_text.set_visible(True)
                inside_text.set_visible(False)
            #@nonl
            #@-node:<< check if inside text fits into the shape >>
            #@nl

        bb_text = map(extent, filter(lambda t: t.get_visible(), self.artists))
        bb_text.append(bb_shape_view)

        #complete bounding box
        bb_all = mtrans.bbox_all(bb_text)

        inverse = mtrans.inverse_transform_bbox
        self.bbox = inverse(self.get_transform(), bb_all)

        return self.bbox
    #@-node:get_bounds
    #@+node:overlaps
    def overlaps(self, bbox):
        return bbox.overlaps(self.shape_bbox)
    #@-node:overlaps
    #@+node:prepare_draw
    def prepare_draw(self, renderer, point_to_pixel, fig_point_to_pixel):
        self.finalized_row()

        if not isinstance(self.artists, tuple):
            self.artists = tuple(self.artists)

        #calc bounding box
        trans = self.get_transform()
        bb_shape = mtrans.bound_vertices(self.shape[0].get_verts())
        bb_shape_view = mtrans.transform_bbox(trans, bb_shape)

        set_helpers(bb_shape, bb_shape)

        bottom = sys.maxint
        top = -sys.maxint

        for te in [ t for t in self.artists if isinstance(t, dtext.Text) ]:
            b, t = te.get_bottom_top(renderer)
            bottom = min(b, bottom)
            top = max(t, top)

        bb_all = bb_shape_view
        bb_all.intervaly().set_bounds(min(bb_all.ymin(), bottom),
                                      max(bb_all.ymax(), top))

        #calc height and depth
        pxl_height = bb_all.height()
        pxl_depth = bb_shape_view.ymin() - bb_all.ymin()

        self.depth.set(pxl_depth / fig_point_to_pixel.get())
        self.height.set(pxl_height / fig_point_to_pixel.get())
        self.row.update_height(self.height.get())
        self.set_font_factor(point_to_pixel, fig_point_to_pixel)
        self.bbox = self.shape_bbox
        return True, True
    #@-node:prepare_draw
    #@+node:draw
    def draw(self, renderer, data_box):
        if not self.get_visible() or not self.overlaps(data_box): return False

        transform = self.get_transform()
        bb_shape = mtrans.bound_vertices(self.shape[0].get_verts())
        bb_data = transform.get_bbox1()
        set_helpers(bb_shape, bb_data)

        bbox = mtrans.transform_bbox(transform, bb_shape.deepcopy())
        if not self.prepare_inside_text(renderer, bbox): return False

        for s in self.shape:
            s.draw(renderer)

        for t in self.artists:
            if t.get_visible() and t.draw(renderer):
                bb = t.get_window_extent()
                bbox.update(((bb.xmin(), bb.ymin()),
                             (bb.xmax(), bb.ymax())), False)

        self.bbox = mtrans.inverse_transform_bbox(transform, bbox)
        return True
    #@-node:draw
    #@+node:prepare_inside_text
    def prepare_inside_text(self, renderer, bb_shape):
        if not self.text_inside: return True

        contains = bb_shape.contains

        al_text = self.text_inside[0]
        in_text = self.text_inside[-1]
        in_text.set_visible(True)

        inside = in_text.get_window_extent(renderer)
        mid = (inside.ymin() + inside.ymax()) / 2

        if contains(inside.xmin(), mid) and contains(inside.xmax(), mid):
            al_text.set_visible(False)
            in_text.set_visible(True)
        else:
            al_text.set_visible(True)
            in_text.set_visible(False)

        return True
    #@-node:prepare_inside_text
    #@-others
#@-node:class TimeWidget
#@+node:class GanttWidget
class GanttWidget(TimeWidget):
    """
    A Widget for gantt charts

    @var shape_height:
    Specifies the height of the widget in VSEPS

    @var row:
    Specifies the row of the widget within the chart.
    """
#@-node:class GanttWidget
#@+node:class ResourceBarWidget
class ResourceBarWidget(TimeWidget):
    """
    A widget for resource charts

    @var row:
    Specifies the row of the widget within the chart.
    """
    #@	<< class ResourceBarWidget declarations >>
    #@+node:<< class ResourceBarWidget declarations >>
    load_factor = 12
    zorder = -10

    #@-node:<< class ResourceBarWidget declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, task, row, start, end, load, offset, properties=None):
        props = { "valign" : "bottom" }
        if properties: props.update(properties)
        TimeWidget.__init__(self, start, end, task, row, props)

        self.zorder = -offset
        self.offset = offset
        self.load = load

        def shape(props):
            import shapes
            kwargs = make_properties(props, "bar")
            l = self.load_factor * font.fontManager.get_default_size()
            return (patches.Rectangle((LEFT, BOTTOM), 
                                      RIGHT - LEFT, round(l * load, 3),
                                      **kwargs),)

        self.set_shape(shape)
    #@-node:__init__
    #@+node:prepare_draw
    def prepare_draw(self, renderer, point_to_pixel, fig_point_to_pixel):
        result = TimeWidget.prepare_draw(self, renderer, point_to_pixel,
                                         fig_point_to_pixel)

        l = self.load_factor * font.fontManager.get_default_size()
        self.row.update_height(l * (self.offset + self.load))
        self.row.update_height(l)
        self.depth.set(round(l * self.offset, 3))
        for t in self.text_inside:
            t.max_size = t._fontproperties.get_size()

        return result
    #@-node:prepare_draw
    #@+node:prepare_inside_text
    __last_size = (0, 0)
    def prepare_inside_text(self, renderer, bb_shape):
        if not self.text_inside: return True

        if bb_shape.width() / self.get_figure().get_dpi() <= 0.08:
            for s in self.shape:
                s.draw(renderer)

            self.bbox = mtrans.inverse_transform_bbox(self.get_transform(),
                                                      bb_shape)
            return False

        view_box = self.get_transform().get_bbox2()

        width = min(view_box.xmax(), bb_shape.xmax())\
                - max(view_box.xmin(), bb_shape.xmin())

        height = min(view_box.ymax(), bb_shape.ymax())\
                - max(view_box.ymin(), bb_shape.ymin())


        if self.__last_size == (width, height): return True

        self.__last_size = (width, height)
        in_text = self.text_inside[-1]
        in_text.set_visible(True)
        in_text.set_size(in_text.max_size)
        in_text.set_rotation(0)
        tbbox = in_text.get_window_extent(renderer)

        sep = 0.07 * self.get_figure().get_dpi() # 0.1 inch
        width -= sep
        height -= sep

        wfactor = min(width / tbbox.width(), height / tbbox.height())

        if wfactor < 1:
            hfactor = min(width / tbbox.height(), height / tbbox.width(), 1.0)
            if hfactor > wfactor:
                wfactor = hfactor
                in_text.set_rotation(90)
            else:
                in_text.set_rotation(0)

            size = wfactor * float(in_text.max_size)
            in_text.set_visible(size > 1)
            in_text.set_size(wfactor * float(in_text.max_size))

        return True
    #@-node:prepare_inside_text
    #@+node:get_bounds
    def get_bounds(self, renderer):
        self.bbox = mtrans.bound_vertices(self.shape[0].get_verts())
        return self.bbox
    #@-node:get_bounds
    #@-others
#@-node:class ResourceBarWidget
#@-others
#@-node:@file charting/widgets.py
#@-leo
