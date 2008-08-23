#@+leo-ver=4
#@+node:@file charting/faxes.py
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
"""
A special axes for faces charts
"""
#@<< Imports >>
#@+node:<< Imports >>
import matplotlib.axes as axes
import matplotlib.artist as artist
import matplotlib.transforms as mtrans
import matplotlib.ticker as ticker
import matplotlib._image as mimage
import matplotlib.font_manager as font
import widgets
import sys
import tools
import patches
import renderer as prend
import math


#@-node:<< Imports >>
#@nl
#@+others
#@+node:_cint
def _cint(val): return int(math.ceil(val))
#@-node:_cint
#@+node:cut_canvas
def cut_canvas(axes, reset=False):
    try:
        bbox = axes.content_bbox
    except AttributeError:
        bbox = axes.bbox

    try:
        if not reset and axes._last_viewbounds != bbox.get_bounds():
            #when the size has changed, don't scale
            old_bbox = mtrans.lbwh_to_bbox(*axes._last_viewbounds)
            trans = mtrans.get_bbox_transform(axes.viewLim, old_bbox)
            data_box = mtrans.inverse_transform_bbox(trans, bbox)
            xmin = axes.viewLim.xmin()
            ymax = axes.viewLim.ymax()

            if not axes._sharey: 
                axes.set_ylim(ymax - data_box.height(), ymax, emit=True)

            if not axes._sharex: 
                axes.set_xlim(xmin, xmin + data_box.width(), emit=True)
    except AttributeError:
        pass

    axes._last_viewbounds = bbox.get_bounds()
#@-node:cut_canvas
#@+node:class _WidgetCollection



class _WidgetCollection(artist.Artist):
    #@	<< class _WidgetCollection declarations >>
    #@+node:<< class _WidgetCollection declarations >>
    # a dummy to avoid a complete rewrite of axes draw
    zorder = -1

    #@-node:<< class _WidgetCollection declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, draw_forward):
        artist.Artist.__init__(self)
        self.draw_forward = draw_forward
    #@-node:__init__
    #@+node:draw
    def draw(self, renderer):
        if self.get_visible():
            self.draw_forward(renderer)
    #@-node:draw
    #@-others
#@-node:class _WidgetCollection
#@+node:_get_margin
            #time_it(self.draw_forward, renderer)



def _get_margin(name, kwargs):
    margin = kwargs.get(name + "_margin")
    if margin is not None:
        del kwargs[name + "_margin"]
    else:
        margin = mtrans.Value(0)

    return margin
#@-node:_get_margin
#@+node:class MarginAxes
class MarginAxes(axes.Axes):
    """
    An axes with a title bar inside the axes
    """
    #@	@+others
    #@+node:__init__
    def __init__(self, *args, **kwargs):
        self.top_margin = _get_margin("top", kwargs)
        self.bottom_margin = _get_margin("bottom", kwargs)
        self.left_margin = _get_margin("left", kwargs)
        self.right_margin = _get_margin("right", kwargs)
        axes.Axes.__init__(self, *args, **kwargs)
    #@-node:__init__
    #@+node:build_margin_transform
    def build_margin_transform(self, left=True, bottom=True,
                               right=True, top=True):
        Bbox = mtrans.Bbox
        Point = mtrans.Point
        get_bbox_transform = mtrans.get_bbox_transform

        if left:
            left_margin = self.left_margin * self.fig_point_to_pixel
            left = self.bbox.ll().x() + left_margin
        else:
            left = self.bbox.ll().x()

        if right:
            right_margin = self.right_margin * self.fig_point_to_pixel
            right = self.bbox.ur().x() - right_margin
        else:
            right = self.bbox.ur().x()

        if top:
            top_margin = self.top_margin * self.fig_point_to_pixel
            top = self.bbox.ur().y() - top_margin
        else:
            top = self.bbox.ur().y()

        if bottom:
            bottom_margin = self.bottom_margin * self.fig_point_to_pixel
            bottom = self.bbox.ll().y() + bottom_margin
        else:
            bottom = self.bbox.ll().y()

        bbox = Bbox(Point(left, bottom), Point(right, top))

        transform = get_bbox_transform(self.viewLim, bbox)
        transform.set_funcx(self.transData.get_funcx())
        transform.set_funcy(self.transData.get_funcy())
        return transform
    #@-node:build_margin_transform
    #@+node:_set_lim_and_transforms
    def _set_lim_and_transforms(self):
        axes.Axes._set_lim_and_transforms(self)
        self.fig_point_to_pixel = self.get_figure().dpi / mtrans.Value(72)

        self.org_transData = self.transData
        self.org_transAxes = self.transAxes

        self.transData = self.build_margin_transform()
        self.content_bbox = self.transData.get_bbox2()
        #self.content_bbox is self.bbox reduced by the margins

        self.transAxes = mtrans.get_bbox_transform(mtrans.unit_bbox(),
                                                   self.content_bbox)
    #@-node:_set_lim_and_transforms
    #@+node:in_axes
    def in_axes(self, xwin, ywin):
        return self.content_bbox.contains(xwin, ywin)
    #@-node:in_axes
    #@+node:cla
    def cla(self):
        axes.Axes.cla(self)
        self.axesPatch.set_transform(self.org_transAxes)
    #@-node:cla
    #@+node:draw
    def draw(self, renderer, inframe=False):
        axes.Axes.draw(self, renderer, inframe)
        if self.axison and self._frameon:
            fill = self.axesPatch.get_fill()
            self.axesPatch.set_fill(False)
            self.axesPatch.draw(renderer)
            self.axesPatch.set_fill(fill)
    #@-node:draw
    #@-others
#@-node:class MarginAxes
#@+node:class WidgetAxes
class WidgetAxes(MarginAxes):
    """
    An axes which is optimized to display widgets.
    If widgets are not inside the current view they will not
    be drawn.
    """
    #@	@+others
    #@+node:__init__
    def __init__(self, *args, **kwargs):
        self._first_draw = True
        self._fobj_map = {}
        self.widgets = []
        self._visible_widgets = []
        self.widget_artist = _WidgetCollection(self._draw_widgets)
        MarginAxes.__init__(self, *args, **kwargs)
    #@-node:__init__
    #@+node:cla
    def cla(self):
        MarginAxes.cla(self)

        self.dataLim.intervalx().set_bounds(sys.maxint, -sys.maxint)
        self.dataLim.intervaly().set_bounds(sys.maxint, -sys.maxint)
        self._fobj_map.clear()
        self.widgets = []
        self.marker = patches.Rectangle((0,0), 0, 0)
        self.marker.widget = None
        self.marker.set_visible(False)
        self.add_artist(self.marker)
        self.marker.set_clip_box(self.content_bbox)
        self.xaxis.set_major_locator(ticker.NullLocator())
        self.xaxis.set_minor_locator(ticker.NullLocator())
        self.yaxis.set_major_locator(ticker.NullLocator())
        self.yaxis.set_minor_locator(ticker.NullLocator())
        self.reset_limits()
        self.add_collection(self.widget_artist)
    #@-node:cla
    #@+node:check_limits
    def check_limits(self, cut=True):
        """
        Changes the viewLimits to reasonable values
        """
        if cut: cut_canvas(self)
    #@-node:check_limits
    #@+node:reset_limits
    def reset_limits(self, cut=True):
        """
        Sets the data width and data size to the default values.
        e.g. reset the y axis to display the fonts in the original size
        """
        self.check_limits(cut)
        vmin, vmax = self.get_ylim()
        height = self.content_bbox.height() / self.fig_point_to_pixel.get()
        self.set_ylim(vmax - height, vmax, emit=True)
    #@-node:reset_limits
    #@+node:_get_renderer
    def _get_renderer(self):
        if not self._cachedRenderer:
            Renderer = prend.PatchedRendererAgg
            self._cachedRenderer = Renderer(10, 10, self.get_figure().dpi)

        return self._cachedRenderer
    #@-node:_get_renderer
    #@+node:add_widget
    def add_widget(self, widget):
        if widget.fobj:
            idendity = widget.fobj._idendity_()
            self._fobj_map.setdefault(idendity, []).append(widget)

        self.widgets.append(widget)
        widget.axes = self
        widget.set_figure(self.figure)
        widget.set_clip_box(self.content_bbox)
        widget.set_transform(self.transData)

        tools.HSEP.set(5)
        horz, vert = widget.prepare_draw(self._get_renderer(),
                                         self.point_to_pixel,
                                         self.fig_point_to_pixel)
        #update data lim
        if horz:
            set_bounds = self.dataLim.intervalx().set_bounds
            set_bounds(min(widget.bbox.xmin(), self.dataLim.xmin()),
                       max(widget.bbox.xmax(), self.dataLim.xmax()))


        if vert:
            set_bounds = self.dataLim.intervaly().set_bounds
            extra = tools.VSEP.get() * 4
            set_bounds(min(widget.bbox.ymin() - extra, self.dataLim.ymin()), 0)

    #@-node:add_widget
    #@+node:mark_widget
    def mark_widget(self, widget=None):
        ow = self.marker.widget
        self.marker.widget = widget
        if not widget: self.marker.set_visible(False)
        return ow != widget
    #@-node:mark_widget
    #@+node:find_widget
    def find_widget(self, fobj):
        if fobj is str:
            return self._fobj_map.get(fobj)

        idendity = fobj._idendity_()
        widgets = self._fobj_map.get(idendity, ())

        #first try to find visible widgets 
        identicals = filter(lambda w: w.fobj is fobj, widgets)
        for w in identicals:
            if w in self._visible_widgets: return w

        if identicals: return identicals[0]

        for w in widgets:
            if w in self._visible_widgets: return w

        return widgets and widgets[0] or None
    #@-node:find_widget
    #@+node:widget_at
    def widget_at(self, x, y):
        self._calc_hsep()
        found = filter(lambda w: w.contains(x, y), self._visible_widgets)
        if found: return found[-1]
        return None
    #@-node:widget_at
    #@+node:set_focused_on
    def set_focused_on(self):
        self.marker.update(self.focused_props)
    #@-node:set_focused_on
    #@+node:set_focused_off
    def set_focused_off(self):
        self.marker.update(self.marker_props)
    #@-node:set_focused_off
    #@+node:set_marker
    def set_marker(self, focused_props, normal_props):
        self.focused_props = focused_props
        self.marker_props = normal_props
        self.marker.update(normal_props)
    #@-node:set_marker
    #@+node:widget_x_visible
    def widget_x_visible(self, widget):
        self._calc_hsep()
        bbox = widget.get_bounds(self._get_renderer())
        xmin, xmax = self.get_xlim()
        width = xmax - xmin
        wxmin, wxmax = bbox.intervalx().get_bounds()
        wwidth = wxmax - wxmin

        vwidth = min(wwidth, width)

        if wxmax <= xmin + vwidth:
            xmin = wxmax - vwidth
            xmax = xmin + width

        if wxmin >= xmax - vwidth:
            xmax = wxmin + vwidth
            xmin = xmax - width

        self.set_xlim(xmin, xmax)
    #@-node:widget_x_visible
    #@+node:widget_y_visible
    def widget_y_visible(self, widget):
        ymin, ymax = self.get_ylim()
        height = ymax - ymin
        wymin, wymax = widget.bbox.intervaly().get_bounds()
        if wymax <= ymin + height / 2:
            ymin = wymax - height / 2
            ymax = ymin + height

        if wymin >= ymax - height / 2:
            ymax = wymin + height / 2
            ymin = ymax - height

        self.set_ylim(ymin, ymax)
    #@-node:widget_y_visible
    #@+node:zoomx
    def zoomx(self, numsteps):
        MarginAxes.zoomx(self, numsteps)
        if self.marker.get_visible():
            self.widget_x_visible(self.marker.widget)
            self.widget_y_visible(self.marker.widget)
    #@-node:zoomx
    #@+node:zoomy
    def zoomy(self, numsteps):
        MarginAxes.zoomy(self, numsteps)

        if self.marker.get_visible():
            self.widget_x_visible(self.marker.widget)
            self.widget_y_visible(self.marker.widget)

    #@-node:zoomy
    #@+node:_calc_hsep
    def _calc_hsep(self):
        trans = self.transData
        vsep = tools.VSEP.get() * self.point_to_pixel.get()
        origin = trans.inverse_xy_tup((0, 0))
        seps = trans.inverse_xy_tup((vsep, vsep))
        tools.HSEP.set(seps[0] - origin[0])
    #@-node:_calc_hsep
    #@+node:_draw_widgets
    def _draw_widgets(self, renderer):
        trans = self.transData
        data_box = mtrans.inverse_transform_bbox(trans, self.content_bbox)
        self._calc_hsep()

        if self._speed_cache:
            l, b, w, h = self._speed_bbox.get_bounds()
            l, b = self.transData.xy_tup((l, b))
            renderer.draw_image(l, b, self._speed_cache, self.content_bbox)

            for w in self.widgets:
                if isinstance(w, (widgets.Row, widgets.Column)):
                    w.draw(renderer, data_box)

            self._visible_widgets = self.widgets
        else:
            self._visible_widgets = [ w for w in self.widgets
                                      if w.draw(renderer, data_box) ]

        #print "widgets drawn", len(self._visible_widgets)
        if self.marker.widget:
            if self.marker.widget.overlaps(data_box):
                bbox = self.marker.widget.bbox
                self.marker.set_bounds(*bbox.get_bounds())
                self.marker.set_visible(True)
            else:
                self.marker.set_visible(False)
    #@-node:_draw_widgets
    #@+node:clear_speed_cache
    def clear_speed_cache(self):
        self._speed_cache = None
    #@-node:clear_speed_cache
    #@+node:speed_up
    _speed_cache = None
    def speed_up(self, max_size):
        self._speed_cache = None

        if not self.widgets: return

        self._calc_hsep()
        renderer = self._get_renderer()
        all_data = self.dataLim.deepcopy()

        xmin = ymin = sys.maxint
        xmax = ymax = -sys.maxint

        for w in self.widgets:
            bounds = w.get_bounds(renderer)
            xmin = min(xmin, bounds.xmin())
            xmax = max(xmax, bounds.xmax())
            ymin = min(ymin, bounds.ymin())
            ymax = max(ymax, bounds.ymax())

        all_data.intervalx().set_bounds(xmin, xmax)
        all_data.intervaly().set_bounds(ymin, ymax)

        all_view = mtrans.transform_bbox(self.transData, all_data)

        # increase view because of rounding mistakes
        xmin, xmax = all_view.intervalx().get_bounds()
        ymin, ymax = all_view.intervaly().get_bounds()
        all_view.intervalx().set_bounds(xmin - 1, xmax + 1) 
        all_view.intervaly().set_bounds(ymin - 1, ymax + 1)

        if all_view.width() * all_view.height() * 4 > max_size:
            return

        #adjust all_data to increased all_view
        all_data = mtrans.inverse_transform_bbox(self.transData, all_view)

        Renderer = prend.SpeedupRenderer
        cache = Renderer(_cint(all_view.width()), _cint(all_view.height()),
                         self.get_figure().dpi)


        render_bbox = mtrans.lbwh_to_bbox(0, 0, all_view.width(), all_view.height())
        all_trans = mtrans.get_bbox_transform(all_data, render_bbox)

        for w in self.widgets:
            if isinstance(w, (widgets.Row, widgets.Column)): continue
            w.set_transform(all_trans)
            w.set_clip_box(render_bbox)
            w.draw(cache, all_data)
            w.set_transform(self.transData)
            w.set_clip_box(self.content_bbox)

        self._speed_cache = mimage.frombuffer(cache.buffer_rgba(0, 0),
                                              cache.width, cache.height, 1)
        if self._speed_cache:
            self._speed_cache.flipud_out()
            self._speed_bbox = all_data
    #@-node:speed_up
    #@+node:draw
    def draw(self, renderer, inframe=False):
        if self._first_draw:
            self._first_draw = False
            widgets = map(lambda w: (w[1].zorder, w[0], w[1]),
                          enumerate(self.widgets))
            widgets.sort()
            self.widgets = map(lambda ziw: ziw[2], widgets)

        MarginAxes.draw(self, renderer, inframe)
    #@-node:draw
    #@+node:_set_lim_and_transforms
    def _set_lim_and_transforms(self):
        Bbox = mtrans.Bbox
        Point = mtrans.Point

        MarginAxes._set_lim_and_transforms(self)
        dtop = self.viewLim.ur().y()
        dbottom = self.viewLim.ll().y()

        vtop = self.content_bbox.ur().y()
        vbottom = self.content_bbox.ll().y()
        self.point_to_pixel = (vtop - vbottom) / (dtop - dbottom)
        cut_canvas(self, True)
    #@-node:_set_lim_and_transforms
    #@-others
#@-node:class WidgetAxes
#@+node:class PointAxes
class PointAxes(WidgetAxes):
    """
    An axes which scales x, y proportional to points
    """
    #@	@+others
    #@+node:__init__
    def __init__(self, *args, **kwargs):
        WidgetAxes.__init__(self, *args, **kwargs)
        self.zoomx = self.zoomy
    #@-node:__init__
    #@+node:cla
    def cla(self):
        WidgetAxes.cla(self)
        self.dataLim.intervalx().set_bounds(0, 0)
        self.dataLim.intervaly().set_bounds(0, 0)
    #@-node:cla
    #@+node:check_limits
    __last_size = (0, 0)
    def check_limits(self, cut=True):
        WidgetAxes.check_limits(self, cut)
        size = (self.viewLim.width(), self.viewLim.height())
        if size != self.__last_size:
            prop = self.content_bbox.width() / self.content_bbox.height()
            pwidth = size[1] * prop
            if pwidth != size[0]:
                #we have to correct x
                size = (pwidth, size[1])
                xmin = self.viewLim.xmin()
                self.set_xlim(xmin, xmin + pwidth)

            self.__last_size = size
    #@-node:check_limits
    #@+node:autoscale_view
    def autoscale_view(self, cut=True):
        if not self._autoscaleon: return
        self.check_limits(cut)

        width = self.dataLim.width()
        height = self.dataLim.height()

        prop = self.content_bbox.width() / self.content_bbox.height()
        pwidth = height * prop

        xmin = self.dataLim.xmin()
        ymax = self.dataLim.ymax()

        if pwidth > width:
            self.set_xlim(xmin, xmin + pwidth)
            self.set_ylim(ymax - height, ymax)
        else:
            self.set_xlim(xmin, xmin + width)
            self.set_ylim(ymax - width / prop, ymax)

        self.__last_size = (self.viewLim.width(), self.viewLim.height())
    #@-node:autoscale_view
    #@-others
#@-node:class PointAxes
#@+node:class TimeAxes
class TimeAxes(object):
    #@	<< class TimeAxes declarations >>
    #@+node:<< class TimeAxes declarations >>
    time_axis = None
    time_scale = None


    #@-node:<< class TimeAxes declarations >>
    #@nl
    #@	@+others
    #@+node:set_time_axis
    def set_time_axis(self, time_axis):
        try:
            self.collections.remove(self.time_axis)
        except ValueError:
            pass

        self.time_axis = time_axis
        self.add_collection(self.time_axis)
        axis_transform = self.build_margin_transform(top=False)
        self.time_axis.set_transform(axis_transform)
        self.time_axis.set_clip_box(axis_transform.get_bbox2())
        self.update_time_axis()
    #@-node:set_time_axis
    #@+node:xaxis_timescale
    def xaxis_timescale(self, time_scale):
        self.time_scale = time_scale
        self.xaxis.set_major_locator(ticker.NullLocator())
        self.xaxis.set_minor_locator(ticker.NullLocator())
    #@-node:xaxis_timescale
    #@+node:set_time_lim
    def set_time_lim(self, xmin=None, xmax=None, emit=False):
        xmin = xmin and self.time_scale.to_num(xmin)
        xmax = xmax and self.time_scale.to_num(xmax)
        self.set_xlim(xmin=xmin, xmax=xmax, emit=emit)
    #@-node:set_time_lim
    #@+node:get_time_lim
    def get_time_lim(self):
        xmin, xmax = self.get_xlim()
        xmin = self.time_scale.to_num(int(xmin))
        xmax = self.time_scale.to_num(int(xmax))
        return xmin.to_datetime(), xmax.to_datetime()
    #@-node:get_time_lim
    #@+node:format_coord
    def format_coord(self, x, y):
        'return a format string formatting the x, y coord'

        if self.time_scale:
            xs = self.time_scale.to_num(int(x)).strftime()
        else:
            xs = self.format_xdata(x)

        ys = self.format_ydata(y)
        return  'x=%s, y=%s'%(xs,ys)
    #@-node:format_coord
    #@+node:update_time_axis
    def update_time_axis(self):
        ah = self.time_axis \
             and self.time_axis.get_visible() \
             and self.time_axis.calc_height() or 0

        self.top_margin.set(ah)
    #@-node:update_time_axis
    #@+node:unshare
    def unshare(self):
        self._sharex = None
        self._sharey = None
    #@-node:unshare
    #@-others
#@-node:class TimeAxes
#@+node:class TimePlotAxes
class TimePlotAxes(TimeAxes, MarginAxes):
    #@	<< class TimePlotAxes declarations >>
    #@+node:<< class TimePlotAxes declarations >>
    first_draw = True

    #@-node:<< class TimePlotAxes declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, *args, **kwargs):
        MarginAxes.__init__(self, *args, **kwargs)
    #@-node:__init__
    #@+node:draw
    def draw(self, renderer, inframe=False):
        if self.first_draw:
            self.first_draw = False
            for a in self.lines: a.set_clip_box(self.content_bbox)
            for a in self.texts: a.set_clip_box(self.content_bbox)
            for a in self.patches: a.set_clip_box(self.content_bbox)
            for a in self.artists: a.set_clip_box(self.content_bbox)

        MarginAxes.draw(self, renderer, inframe)
        cut_canvas(self, True)
    #@-node:draw
    #@-others
#@-node:class TimePlotAxes
#@+node:class TimeWidgetAxes
class TimeWidgetAxes(TimeAxes, WidgetAxes):
    """
    An axes wich displays widgets horizontal in time. (e.g. GanttCharts)
    """
    #@	<< class TimeWidgetAxes declarations >>
    #@+node:<< class TimeWidgetAxes declarations >>
    auto_scale_y = False

    #@-node:<< class TimeWidgetAxes declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, *args, **kwargs):
        WidgetAxes.__init__(self, *args, **kwargs)
    #@-node:__init__
    #@+node:set_auto_scale_y
    def set_auto_scale_y(self, do_scale=True):
        self.auto_scale_y = do_scale
    #@-node:set_auto_scale_y
    #@+node:check_limits
    def check_limits(self, cut=True):
        WidgetAxes.check_limits(self, cut)

        vmin, vmax = self.viewLim.intervaly().get_bounds()
        if vmax > 0:
            self.viewLim.intervaly().set_bounds((vmin - vmax), 0)
    #@-node:check_limits
    #@+node:autoscale_view
    def autoscale_view(self, cut=True):
        if not self._autoscaleon: return
        self.check_limits(cut)

        all_data = self.dataLim.deepcopy()
        reduced = self.content_bbox.deepcopy()
        renderer = self._get_renderer()

        if self.auto_scale_y:
            ymin, ymax = self.dataLim.intervaly().get_bounds()
            self.set_ylim(ymin, ymax)
        else:
            self.reset_limits()

        xmin, xmax = self.dataLim.intervalx().get_bounds()
        self.set_xlim(xmin, xmax, emit=False)
        self._calc_hsep()

        #Notice: it is not correct to just get the bounds
        #in the actual data coords an set the view limits
        #This is because text on the left or right bound
        #has always the same pixel width. This means the text witdh
        #in data coord changes when the data coord scale changes.

        #find out the bounds in actual data coords
        for w in self.widgets:
            bounds = w.get_bounds(renderer)
            xmin = min(xmin, bounds.xmin())
            xmax = max(xmax, bounds.xmax())

        all_data.intervalx().set_bounds(xmin, xmax)

        #the complete bound in pixel coords
        all_view = mtrans.transform_bbox(self.transData, all_data)
        add_space = 0.08 * self.get_figure().get_dpi() #2mm margin left an right

        left_offset = self.content_bbox.xmin() - all_view.xmin() + add_space
        right_offset = all_view.xmax() - self.content_bbox.xmax() + add_space
        width = self.content_bbox.width()

        if left_offset > width / 4: left_offset = width / 4
        if right_offset > width / 4: right_offset = width / 4

        # scale down the pixel bounds
        xmin1 = self.content_bbox.xmin() + left_offset
        xmax1 = self.content_bbox.xmax() - right_offset
        reduced.intervalx().set_bounds(xmin1, xmax1)

        # create a new transformation from scaled down pixel coords to limits
        trans = mtrans.get_bbox_transform(reduced, self.viewLim)
        data_box = mtrans.transform_bbox(trans, self.content_bbox)
        self.set_xlim(data_box.xmin(), data_box.xmax(), emit=True)
        cut_canvas(self, True)
    #@-node:autoscale_view
    #@+node:widget_at
    def widget_at(self, x, y):
        return WidgetAxes.widget_at(self, x, y)
    #@-node:widget_at
    #@-others
#@-node:class TimeWidgetAxes
#@-others
#@-node:@file charting/faxes.py
#@-leo
