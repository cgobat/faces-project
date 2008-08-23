#@+leo-ver=4
#@+node:@file charting/taxis.py
#@@language python
"""
A timeaxis for gantt and resource charts.
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
import matplotlib.font_manager as font
import matplotlib.transforms as mtrans
import matplotlib.colors as colors
import matplotlib.artist as artist
import matplotlib._image as mimage
import datetime
import widgets
import faces.plocale
import locale
from faces.pcalendar import strftime
from tools import *


#@-node:<< Imports >>
#@nl

_is_source_ = True
_ = faces.plocale.get_gettext()

_colorConverter = colors.colorConverter

_week_name = _("Week")

def alt_week_locator(alt=True):
    """
    use an alternate week locator for gantt charts.
    """
    global _week_name
    if alt:
        _week_name = ""
    else:
        _week_name = _("Week")

#@+others
#@+node:Locators
#@+others
#@+node:class Locator
class Locator(object):
    #@	<< declarations >>
    #@+node:<< declarations >>
    can_locate_free_time = False

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self):
        self.tick_pos = (0, 0) # position is 0, the highest positon is 0
        self.sizes = {}
        self.format_cache = { }
    #@-node:__init__
    #@+node:get_marks
    def get_marks(self, intervals, scale, transform):
        xmin, xmax = transform.get_bbox1().intervalx().get_bounds()
        if intervals[0][0] < xmin:
            intervals[0] = (xmin, intervals[0][1])

        if intervals[-1][1] > xmax:
            intervals[-1] = (intervals[-1][0], xmax)

        middles = map(lambda i: (i[0] + i[1]) / 2, intervals)
        build_mark = self.build_mark
        marks = [ build_mark(i, scale, transform) for i in intervals ]
        xs = transform.seq_x_y(middles, middles)[0]
        return zip(marks, xs)
    #@-node:get_marks
    #@+node:build_mark
    def build_mark(self, interval, scale, transform):
        format = self._get_format(interval, transform)
        date = scale.to_num(int(interval[0])).to_datetime()
        quater = 1 + (date.month - 1) / 3
        decade = 10 * (date.year / 10)
        f = format.replace("%Q", str(quater))
        f = f.replace("%D", str(decade))
        return strftime(date, f)
    #@nonl
    #@-node:build_mark
    #@+node:fits
    def fits(self, transform, scale):
        delta = self._delta(scale)
        key = self.tick_pos[0] == self.tick_pos[1] and "top" or "default"
        sizes = self.sizes.get(key, self.sizes["default"])[0]
        delta = transform(delta)
        return sizes[-1][0] < delta
    #@-node:fits
    #@+node:prepare
    def prepare(self, renderer, fonts, tickers):
        "precalculates all possible marker sizes"
        self.renderer = renderer
        self.fonts = zip(tickers, fonts)
        self._calc_sizes()
        for v in self.sizes.itervalues():
            for s in v.itervalues():
                s.sort()
                s.reverse()

        del self.renderer
        del self.fonts
    #@-node:prepare
    #@+node:_calc_sizes
    def _calc_sizes(self):
        raise RuntimeError("abstract")
    #@-node:_calc_sizes
    #@+node:_delta
    def _delta(self, scale):
        raise RuntimeError("abstract")
    #@-node:_delta
    #@+node:_get_format
    def _get_format(self, interval, transform):
        delta = int(interval[0] - interval[1])
        format = self.format_cache.get(delta)
        if format: return format

        x, y = transform.seq_x_y(interval, (0, 0))
        tdelta = x[1] - x[0]
        key = self.tick_pos[0] == self.tick_pos[1] and "top" or "default"
        sizes = self.sizes.get(key, self.sizes["default"])[self.tick_pos[0]]
        for s, f in sizes:
            if s < tdelta:
                format = f
                break
        else:
            format = ""

        self.format_cache[delta] = format
        return format
    #@-node:_get_format
    #@+node:_calc_markers
    def _calc_markers(self, markers, format, key="default"):
        extent = self.renderer.get_text_width_height

        key_fonts = self.sizes.get(key)
        if not key_fonts:
            key_fonts = {}
            for i, f in self.fonts: key_fonts[i] = []

        if not isinstance(markers, (list, tuple)):
            markers = (markers,)

        for i, f in self.fonts:
            size = max([extent(m, f, False)[0] for m in markers])
            key_fonts[i].append((size, str(format)))

        self.sizes[key] = key_fonts
    #@-node:_calc_markers
    #@+node:is_free
    def is_free(self, num_date):
        #num_date is int
        return False
    #@-node:is_free
    #@-others
#@-node:class Locator
#@+node:class DecadeLocator
class DecadeLocator(Locator):
    #@	@+others
    #@+node:_delta
    def _delta(self, scale):
        return scale.week_delta * 52 * 10
    #@-node:_delta
    #@+node:_calc_sizes
    def _calc_sizes(self):
        self._calc_markers("88888", "%D")
    #@-node:_calc_sizes
    #@+node:__call__
    def __call__(self, left, right, time_scale):
        num = time_scale.to_num
        dt = datetime.datetime
        left = num(int(left))
        right = num(int(right))
        start = left.to_datetime().year / 10
        end = right.to_datetime().year / 10 + 2
        locs = map(lambda y: num(dt(y * 10, 1, 1)), range(start, end))
        return locs
    #@-node:__call__
    #@-others
#@-node:class DecadeLocator
#@+node:class YearLocator
class YearLocator(Locator):
    #@	@+others
    #@+node:_delta
    def _delta(self, scale):
        return scale.week_delta * 52
    #@-node:_delta
    #@+node:_calc_sizes
    def _calc_sizes(self):
        self._calc_markers("88888", "%IY")
    #@-node:_calc_sizes
    #@+node:__call__
    def __call__(self, left, right, time_scale):
        num = time_scale.to_num
        dt = datetime.datetime
        left = num(int(left))
        right = num(int(right))
        start = left.to_datetime().year
        end = right.to_datetime().year + 2
        locs = map(lambda y: num(dt(y, 1, 1)), range(start, end))
        return locs
    #@-node:__call__
    #@-others
#@-node:class YearLocator
#@+node:class QuaterLocator
class QuaterLocator(Locator):
    #@	@+others
    #@+node:_delta
    def _delta(self, scale):
        return scale.week_delta * 12
    #@-node:_delta
    #@+node:_calc_sizes
    def _calc_sizes(self):
        self._calc_markers("Q 8/88888", "Q %Q/%IY", "top")
        self._calc_markers("Q 88", "Q %Q")
    #@-node:_calc_sizes
    #@+node:__call__
    def __call__(self, left, right, time_scale):
        num = time_scale.to_num
        dt = datetime.datetime
        left = num(int(left))
        right = num(int(right))
        start = left.to_datetime()
        end = right.to_datetime()
        start = start.year * 4 + (start.month - 1) / 3
        end = end.year * 4 + (end.month - 1) / 3 + 2
        locs = map(lambda qy: num(dt(qy/4, (qy%4)*3+1, 1)), range(start, end))
        return locs
    #@-node:__call__
    #@-others
#@-node:class QuaterLocator
#@+node:class MonthLocator
class MonthLocator(Locator):
    #@	@+others
    #@+node:_delta
    def _delta(self, scale):
        return scale.week_delta * 4
    #@-node:_delta
    #@+node:_calc_sizes
    def _calc_sizes(self):
        dt = datetime.datetime
        def mlist(format):
            return map(lambda m: strftime(dt(2005, m, 1), format), range(1, 13))

        self._calc_markers(mlist("%B 88888"), "%B %IY", "top")
        self._calc_markers(mlist("%b 88888"), "%b %IY", "top")
        self._calc_markers(mlist("%m.88888"), "%m.%IY", "top")
        self._calc_markers(mlist("%B"), "%B")
        self._calc_markers(mlist("%b"), "%b")
        self._calc_markers("8888", "%m")
    #@-node:_calc_sizes
    #@+node:__call__
    def __call__(self, left, right, time_scale):
        num = time_scale.to_num
        dt = datetime.datetime

        left = num(int(left))
        right = num(int(right))
        start = left.to_datetime()
        end = right.to_datetime()
        start = start.year * 12 + start.month - 1
        end = end.year * 12 + end.month + 1
        locs = map(lambda my: num(dt(my/12, 1+my%12, 1)), range(start, end))
        return locs
    #@-node:__call__
    #@-others
#@-node:class MonthLocator
#@+node:class WeekLocator
class WeekLocator(Locator):
    #@	@+others
    #@+node:_delta
    def _delta(self, scale):
        return scale.week_delta
    #@-node:_delta
    #@+node:_calc_sizes
    def _calc_sizes(self):
        global _week_name

        dt = datetime.datetime
        def mlist(format):
            return map(lambda m: strftime(dt(2005, m, 1), str(format)), range(1, 13))

        if _week_name:
            self._calc_markers(mlist("%IW. " + _week_name + " %IB 88888"),
                               "%IW. " + _week_name + " %IB %IY", "top")
            self._calc_markers(mlist("%IW. " + _week_name + " %ib 88888"),
                               "%IW. " + _week_name + " %ib %IY", "top")
            self._calc_markers(mlist("%IW. " + _week_name + " %im.88888"),
                               "%IW. " + _week_name + " %m.%IY", "top")
            self._calc_markers(mlist("%IW %ib 88888"), "%IW %ib %IY", "top")
            self._calc_markers(mlist("%IW %im 88888"), "%IW %im.%IY", "top")
            self._calc_markers("888. " + _week_name, "%IW. " + _week_name)
            self._calc_markers("8888", "%IW")
        else:
            # in the US week numbers are not used
            self._calc_markers(mlist("%B 88"), "%B %d")
            self._calc_markers(mlist("%b. 88"), "%b. %d")

    #@-node:_calc_sizes
    #@+node:__call__
    def __call__(self, left, right, time_scale):
        num = time_scale.to_num
        left = num(int(left))
        right = num(int(right)) + time_scale.week_delta
        start = left.to_datetime().replace(hour=0, minute=0)
        start -= datetime.timedelta(days=start.weekday()) 
        start = num(start)
        locs = range(start, right, time_scale.week_delta)
        return locs
    #@-node:__call__
    #@-others
#@-node:class WeekLocator
#@+node:class DayLocator
class DayLocator(Locator):
    #@	<< declarations >>
    #@+node:<< declarations >>
    can_locate_free_time = True


    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:_delta
    def _delta(self, scale):
        return scale.day_delta
    #@-node:_delta
    #@+node:_calc_sizes
    def _calc_sizes(self):
        dt = datetime.datetime
        def dlist(format):
            return map(lambda d: strftime(dt(2005, 1, d), format), range(1, 8))

        self._calc_markers(dlist("%A %x88"), "%A %x", "top")
        self._calc_markers(dlist("%a %x88"), "%a %x", "top")
        self._calc_markers(dlist("%x88"), "%x", "top")
        self._calc_markers(dlist("%A 888."), "%A %d.")
        self._calc_markers(dlist("%a 888."), "%a %d.")
        self._calc_markers("8888", "%d")
    #@-node:_calc_sizes
    #@+node:__call__
    def __call__(self, left, right, time_scale):
        self.time_scale = time_scale
        num = time_scale.to_num
        date = time_scale.to_datetime
        td = datetime.timedelta
        left = date(num(int(left))).replace(hour=0, minute=0)
        right = date(num(int(right)))
        days = (right - left).days + 2
        locs = map(lambda d: num(left + td(days=d)), range(0, days))
        return locs
    #@-node:__call__
    #@+node:is_free
    def is_free(self, num_date):
        return self.time_scale.is_free_day(num_date)
    #@-node:is_free
    #@-others
#@-node:class DayLocator
#@+node:class SlotLocator
class SlotLocator(Locator):
    #@	<< declarations >>
    #@+node:<< declarations >>
    can_locate_free_time = True


    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:_delta
    def _delta(self, scale):
        return scale.slot_delta
    #@-node:_delta
    #@+node:__call__
    def __call__(self, left, right, time_scale):
        self.time_scale = time_scale
        num = time_scale.to_num
        date = time_scale.to_datetime
        td = datetime.timedelta
        left = date(num(int(left))).replace(hour=0, minute=0)
        right = date(num(int(right)))
        days = (right - left).days + 2
        days = map(lambda d: left + td(days=d), range(0, days))
        get_working_times = time_scale.chart_calendar.get_working_times

        locs = []
        for d in days:
            slots = get_working_times(d.weekday())
            locs.extend(map(lambda s: num(d + td(minutes=s[0])), slots))

        return locs
    #@-node:__call__
    #@+node:_calc_sizes
    def _calc_sizes(self):
        self._calc_markers("888:88-88:88", "%(sh)02i:%(sm)02i-%(eh)02i:%(em)02i")
        self._calc_markers("888-88", "%(sh)02i-%(eh)02i")
        self._calc_markers("888:88", "%(sh)02i:%(sm)02i")
        self._calc_markers("888", "%(sh)02i")
    #@-node:_calc_sizes
    #@+node:get_marks
    def get_marks(self, intervals, scale, transform):
        def build_mark(interval):
            format = self._get_format(interval, transform)
            start = scale.to_num(interval[0]).to_datetime()
            end = scale.to_num(interval[1]).to_datetime()
            vals = { "sh" : start.hour,
                     "sm" : start.minute,
                     "eh" : end.hour,
                     "em" : end.minute }
            return format % vals

        middles = map(lambda i: (i[0] + i[1]) / 2, intervals)
        marks = map(build_mark, intervals)
        xs = transform.seq_x_y(middles, (0,)*len(middles))[0]
        return zip(marks, xs)
    #@-node:get_marks
    #@+node:is_free
    def is_free(self, num_date):
        return self.time_scale.is_free_slot(num_date)
    #@-node:is_free
    #@-others
#@-node:class SlotLocator
#@-others

_locators = ( SlotLocator,
              DayLocator,
              WeekLocator,
              MonthLocator,
              QuaterLocator,
              YearLocator,
              DecadeLocator )
#@-node:Locators
#@+node:_zigzag_lines
def _zigzag_lines(locs, top, bottom):
    xs = locs * 2
    xs.sort()
    ys = [ top, bottom,  bottom, top ] * ((len(locs) + 1) / 2)
    if len(locs) % 2: del ys[-2:]
    return xs, ys
#@-node:_zigzag_lines
#@+node:class TimeAxis
class TimeAxis(artist.Artist, widgets._PropertyAware):
    #@	<< declarations >>
    #@+node:<< declarations >>
    properties = {
        "family": "sans-serif",
        #"family": [ "Arial", "Verdana", "Bitstream Vera Sans" ] ,
        "weight": "normal",
        "size"  : "medium",
        "style" : "normal",
        "variant" : "normal",
        "2.weight" : "bold",
        "2.size" : "x-large",
        "1.weight" : "bold",
        "1.size" : "large",
        "color": 'black',
        "0.facecolor" : 'white',
        "facecolor" : 'darkgray',
        "edgecolor" : 'black',
        "grid.edgecolor" : 'darkgray',
        "free.facecolor": "lightgrey",
        "linewidth" : 1,
        "joinstyle" : 'miter',
        "linestyle" : 'solid',
        "now.edgecolor" : "black",
        "now.linewidth" : 2,
        "now.linestyle" : "dashed",
        "antialiased" : True,
        "alpha" : 1.0,
        "tickers" : (1, ) }


    zorder = -100
    show_grid = True
    show_scale = True
    show_free_time = True
    show_now = True
    time_scale = None # must be set by Chart

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, properties=None):
        widgets._PropertyAware.__init__(self, properties)
        artist.Artist.__init__(self)
        self._locators = tuple(map(lambda l: l(), _locators))
        self._last_cache = None
        self._last_cache_state = None
        self._last_width = 0
        self.encoding = locale.getlocale()[1] or "ascii"
    #@-node:__init__
    #@+node:calc_height
    def calc_height(self):
        if not self.show_scale:
            self.height = 0
            return 0

        prop = self.get_property
        def_height = font.fontManager.get_default_size()

        sep = def_height / 3
        tickers = (0,) + prop("tickers")
        self.height = 0
        for t in tickers:
            tsize = self.get_font(str(t)).get_size_in_points()
            self.height += tsize + 2 * sep

        return self.height
    #@-node:calc_height
    #@+node:set_transform
    def set_transform(self, t):
        #a non scaled point y axis
        Value = mtrans.Value
        Point = mtrans.Point
        Bbox = mtrans.Bbox
        Transformation = mtrans.SeparableTransformation

        fig_point_to_pixel = self.get_figure().dpi / mtrans.Value(72)

        view_box = t.get_bbox2()
        top = view_box.ur().y()
        bottom = view_box.ll().y()
        point_height = (bottom - top) / fig_point_to_pixel

        bbox = t.get_bbox1()
        ll = bbox.ll()
        ur = bbox.ur()
        new_ll = Point(ll.x(), point_height)
        new_ur = Point(ur.x(), Value(0))
        data_box = Bbox(new_ll, new_ur)

        t = Transformation(data_box, view_box, t.get_funcx(), t.get_funcy())
        artist.Artist.set_transform(self, t)
    #@-node:set_transform
    #@+node:draw
    __prepared = False
    def draw(self, renderer):
        if not self.get_visible(): return

        trans = self.get_transform()
        trans.freeze()
        try:
            if not self.__prepared:
                self.__prepared = True
                tickers = (0,) + self.get_property("tickers")
                fonts = map(lambda t: self.get_font(str(t)), tickers)
                for l in self._locators:
                    l.prepare(renderer, fonts, tickers)

            data_box = trans.get_bbox1()
            view_box = trans.get_bbox2()
            width = data_box.width()

            if self._last_width != width:
                self._last_width = width
                self.find_ticker(renderer)

            cache_state = (self.show_grid + self.show_scale,
                           view_box.width(), view_box.height(),
                           renderer, data_box.xmin())

            if self._last_cache_state == cache_state and self._last_cache:
                try:
                    #not now because of memory leak
                    renderer.draw_image(0, 0, self._last_cache, view_box)
                    #renderer.restore_region(self._last_cache)
                    return
                except:
                    pass

            gc = renderer.new_gc()

            if self.get_clip_on():
                gc.set_clip_rectangle(self.clipbox.get_bounds())

            if self.show_grid: self.draw_grid(renderer, gc, trans)
            if self.show_now:
                time_scale = self.time_scale
                left, right = data_box.intervalx().get_bounds()
                if left <= time_scale.now <= right:
                    top, bottom = data_box.intervaly().get_bounds()
                    self.set_gc(gc, "now")
                    renderer.draw_lines(gc,
                                        (time_scale.now, time_scale.now),
                                        (top, bottom), trans)

            if self.show_scale: self.draw_scale(renderer, gc, trans)

            self._last_cache_state = cache_state
            #self._last_cache = renderer.copy_from_bbox(view_box)
            try:
                self._last_cache = mimage.frombuffer(\
                    renderer.buffer_rgba(0, 0),
                    renderer.width,
                    renderer.height, 1)
            except AttributeError:
                self._last_cache = None

            if self._last_cache:
                self._last_cache.flipud_out()
        finally:
            trans.thaw()
    #@-node:draw
    #@+node:find_ticker
    def find_ticker(self, renderer):
        time_scale = self.time_scale

        tickers = self.get_property("tickers")
        if not isinstance(tickers, tuple):
            tickers = tuple(tickers)

        tickers = (0,) + tickers
        highest_locator = tickers[-1]

        transform = self.get_transform()
        origin = transform.xy_tup((0, 0))[0]

        def delta_trans(x_delta):
            p = transform.xy_tup((x_delta, 0))
            return p[0] - origin

        def refresh_locators(lowest):
            self.ticker = lowest
            for t in tickers:
                loc = self._locators[lowest + t]
                loc.tick_pos = (t, highest_locator)
                loc.format_cache.clear()

        for ti in range(len(self._locators) - highest_locator):
            loc = self._locators[ti]
            loc.tick_pos = (0, highest_locator)

            if loc.fits(delta_trans, time_scale):
                refresh_locators(ti)
                break
        else:
            refresh_locators(len(self._locators) - highest_locator - 1)
    #@-node:find_ticker
    #@+node:draw_scale
    def draw_scale(self, renderer, gc, trans):
        prop = self.get_property
        time_scale = self.time_scale

        def_height = font.fontManager.get_default_size()
        sep = def_height / 3
        left, right = trans.get_bbox1().intervalx().get_bounds()
        dpi = self.get_figure().get_dpi()

        if left >= right: return

        self.set_gc(gc)
        free_face = _colorConverter.to_rgb(prop("free.facecolor"))

        def dline(x1, y1, x2, y2):
            draw_line(renderer, gc, x1, y1, x2, y2, trans)

        def draw_ticks(bottom, locator, name, show_free_time=False):
            fp = self.get_font(name)
            top = bottom - fp.get_size_in_points() - 2 * sep

            locs = locator(left, right, time_scale)
            lintervals = zip(locs[:-1], locs[1:])

            face = _colorConverter.to_rgb(prop(name + ".facecolor"))
            verts = ((left, -bottom), (left, -top),
                     (right, -top), (right, -bottom))
            verts = trans.seq_xy_tups(verts)
            renderer.draw_polygon(gc, face, verts)

            if show_free_time and locator.can_locate_free_time:
                gc.set_linewidth(0)
                for l, r in lintervals:
                    #if locator.is_free((l + r) / 2):
                    if locator.is_free(l):
                        verts = ((l, -bottom), (l, -top),
                                 (r, -top), (r, -bottom))
                        verts = trans.seq_xy_tups(verts)
                        renderer.draw_polygon(gc, free_face, verts)

            fp = self.get_font(name)
            gc.set_foreground(prop(name + ".color"))
            x, y = trans.xy_tup((0, -bottom + sep))
            markers = locator.get_marks(lintervals, time_scale, trans)
            for m, x in markers:
                self.draw_text(renderer, gc, x, y, m, fp, "bc", dpi)

            gc.set_foreground(prop(name + ".edgecolor"))
            gc.set_linewidth(prop(name + ".linewidth"))

            xs, ys = _zigzag_lines(locs, -top, -bottom)
            renderer.draw_lines(gc, xs, ys, trans)

            gc.set_linewidth(prop("linewidth"))
            dline(left, -top, right, -top)
            dline(left, -bottom, right, -bottom)

            return top

        tickers = prop("tickers")
        bottom = self.height
        ticks = self._locators[self.ticker]
        bottom = draw_ticks(bottom, ticks, "0", self.show_free_time)
        for t in tickers:
            ticks = self._locators[self.ticker + t]
            bottom = draw_ticks(bottom, ticks, str(t))
    #@-node:draw_scale
    #@+node:draw_grid
    def draw_grid(self, renderer, gc, trans):
        time_scale = self.time_scale
        prop = self.get_property        

        data_box = trans.get_bbox1()
        left, right = data_box.intervalx().get_bounds()
        top, bottom = data_box.intervaly().get_bounds()

        if left >= right: return

        locator = self._locators[self.ticker]
        locs = locator(left, right, time_scale)
        lintervals = zip(locs[:-1], locs[1:])

        self.set_gc(gc, "grid")
        if self.show_free_time and locator.can_locate_free_time:
            gc.set_linewidth(0)
            free_face = _colorConverter.to_rgb(prop("free.facecolor"))
            for l, r in lintervals:
                if locator.is_free((l + r) / 2):
                    verts = trans.seq_xy_tups(((l, bottom), (l, top),
                                               (r, top), (r, bottom)))

                    renderer.draw_polygon(gc, free_face, verts)


        gc.set_linewidth(prop("grid.linewidth"))

        xs, ys = _zigzag_lines(locs, top, bottom)
        renderer.draw_lines(gc, xs, ys, trans)
        draw_line(renderer, gc, left, bottom, right, bottom, trans)
    #@-node:draw_grid
    #@+node:draw_text
    def draw_text(self, renderer, gc, x, y, text, fp, align, dpi):
        """
        special draw_text for taxis using the locale encoding which is used by
        the strftime functions
        """

        if not text: return
        text = text.decode(self.encoding)

        w, h = renderer.get_text_width_height(text, fp, False)
        if align[0] == 'c': 
            y -= h / 2
        elif align[0] == 't':
            y -= h

        if align[1] == 'c': 
            x -= w / 2
        elif align[1] == 'r':
            x -= w

        if renderer.flipy():
            canvasw, canvash = renderer.get_canvas_width_height()
            y = canvash-y

        renderer.draw_text(gc, x, y, text, fp, 0, False)
    #@-node:draw_text
    #@-others
#@-node:class TimeAxis
#@-others
#@-node:@file charting/taxis.py
#@-leo
