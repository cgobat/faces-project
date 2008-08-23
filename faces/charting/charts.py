#@+leo-ver=4
#@+node:@file charting/charts.py
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
Matplotlib-based charts
"""
#@<< imports >>
#@+node:<< Imports >>
import matplotlib.figure as figure
import matplotlib.backends
import matplotlib.font_manager as font
import matplotlib.backend_bases as bases
import matplotlib.ticker as ticker
import matplotlib.axes as axes
import matplotlib.transforms as mtrans
import matplotlib.pylab as pylab
import faces
import faces.pcalendar as pcal
import faces.utils as utils
import faces.observer
import faces.plocale
import patches
import widgets as widget
import printer
import faxes
import taxis
import timescale
from tools import *



#@-node:<< Imports >>
#@nl

_is_source_ = True
_ = faces.plocale.get_gettext()

__all__ = ("TimeWidgetChart", "TableChart", "TimeAxisWidgetChart",
           "TimeAxisPlotChart", "TimeAxisMultiChart",
           "TimeAxisTabledChart")
#@+others
#@+node:Matplotlib Redirections
def _dumy(): return None, None, None

matplotlib.backends.pylab_setup = _dumy

def _wrong_pylab_function(*args, **kwargs):
    raise RuntimeError("this function may not be called inside faces")

def _new_figure_manager(*args, **kwargs):
    return _figure_manager

pylab.switch_backend = _wrong_pylab_function
pylab.subplot_tool = _wrong_pylab_function
pylab.close = _wrong_pylab_function
pylab.show = _wrong_pylab_function
pylab.draw_if_interactive = _dumy
pylab.new_figure_manager = _new_figure_manager

class _DumyFigureManager(bases.FigureManagerBase):
    def __init__(self):
        self.canvas = None
        self.num = -1

    def key_press(self, event):
        pass

_figure_manager = _DumyFigureManager()
#@-node:Matplotlib Redirections
#@+node:class MatplotChart
class MatplotChart(faces.observer.Observer, widget._PropertyAware):
    """
    Base Class for all charts.

    @var properties:
    Specifies a dictionary of display properties.

    @var show_tips:
    Specifies a boolean value, wether the charts should display tool tips.

    @var scroll_bars:
    Specifies a boolean value, wether the charts should display scroll bars.

    """
    #@	<< declarations >>
    #@+node:<< declarations >>
    __type_name__ = "matplot_chart"
    properties = {
        "family" : "sans-serif",
        #"family": [ "Arial", "Verdana", "Bitstream Vera Sans" ] ,        
        "background.facecolor" : "w",
        "fill" : 1,
        "alpha" : 1,
        "marker.edgecolor" : "blue",
        "marker.linewidth" : 2,
        "marker.antialiased" : True,
        "marker.facecolor" : "green",
        "marker.alpha" : "0.4",
        "focused.marker.edgecolor" : "red" }

    __attrib_completions__ = faces.observer.Observer.__attrib_completions__.copy()
    __attrib_completions__.update({\
        "properties" : 'properties = { | }',
        "show_tips" : 'show_tips = False',
        "scroll_bars" : 'scroll_bars = False',
        "def add_decorations" : """def add_decorations(self, axes):
    pass
    """
        })


    show_tips = True    
    scroll_bars = True

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:printer
    def printer(cls, **kwargs):
        return printer.FreePrinter(cls, **kwargs)

    printer = classmethod(printer)
    #@nonl
    #@-node:printer
    #@+node:register_editors
    def register_editors(cls, registry):
        super(MatplotChart, cls).register_editors(registry)
        registry.Boolean(_("Shape/show_tips..."))
        registry.Boolean(_("Chart/scroll_bars..."))
        registry.Property(_("Chart/properties..."), cls.create_property_groups)

    register_editors = classmethod(register_editors)

    def create_property_groups(cls, property):
        property.set_default_groups()

    create_property_groups = classmethod(create_property_groups)
    #@nonl
    #@-node:register_editors
    #@+node:__init__
    def __init__(self, paint_to=None, rect=None, **kwargs):
        faces.observer.Observer.__init__(self)
        widget._PropertyAware.__init__(self)

        self.figure = None
        self.axes = None

        back_face = self.get_property("background.facecolor")
        if isinstance(paint_to, figure.Figure):
            self.figure = paint_to
            self.axes = self.create_axes(rect, **kwargs)
            self.axes.set_axis_bgcolor(back_face)
            self.setup_axes_interface(self.axes)

        if isinstance(paint_to, axes.Axes):
            self.axes = paint_to
            self.figure = self.axes.get_figure()
            self.axes.set_axis_bgcolor(back_face)
            self.setup_axes_interface(self.axes)

        if self.figure:
            self.create()
            self._add_decorations()
    #@-node:__init__
    #@+node:_add_decorations
    def _add_decorations(self):
        self.add_decorations(self.axes)
    #@-node:_add_decorations
    #@+node:add_decorations
    def add_decorations(self, axes):
        """
        Overwrite this method to add decorations to the chart
        """
        pass

    add_decorations.args = (faxes.WidgetAxes,)
    #@-node:add_decorations
    #@+node:create_axes
    def create_axes(self, rect=None, **kwargs):
        """
        creates the default axes for the chart
        """
        raise RuntimeError("abstract")
    #@-node:create_axes
    #@+node:create
    def create(self):
        """
        create the chart
        """

        raise RuntimeError("abstract")
    #@-node:create
    #@+node:get_tip
    def get_tip(self, tipobj):
        return None
    #@-node:get_tip
    #@+node:setup_axes_interface
    def setup_axes_interface(self, axes):
        """
        Setup interface for chartview and printer
        """
        def dumy(*args): return None
        self._set_frame_on = axes.set_frame_on
        self._axes_patch = axes.axesPatch
        self._left_margin = getattr(axes, "left_margin", None)
        self._right_margin = getattr(axes, "right_margin", None)
        self._top_margin = getattr(axes, "top_margin", None)
        self._bottom_margin = getattr(axes, "bottom_margin", None)
        self._trans_data = axes.transData
        self._data_lim = axes.dataLim
        self._view_lim = axes.viewLim
        self._bbox = getattr(axes, "content_bbox", self.axes.bbox)
        self._set_xlim = axes.set_xlim
        self._set_ylim = axes.set_ylim
        self._get_xlim = axes.get_xlim
        self._get_ylim = axes.get_ylim
        self._set_autoscale_on = axes.set_autoscale_on
        self._autoscale_view = axes.autoscale_view
        self._set_auto_scale_y =getattr(axes, "set_auto_scale_y", dumy) 
        self._zoomx = axes.zoomx
        self._zoomy = axes.zoomy
        self._widget_at = getattr(axes, "widget_at", dumy)
        self._find_widget = getattr(axes, "find_widget", dumy)
        self._set_focused_on = getattr(axes, "set_focused_on", dumy)
        self._set_focused_off = getattr(axes, "set_focused_off", dumy)
        self._speed_up = getattr(axes, "speed_up", dumy) 
        self._clear_speed_cache = getattr(axes, "clear_speed_cache", dumy)
        self._widget_x_visible = getattr(axes, "widget_x_visible", dumy)
        self._widget_y_visible = getattr(axes, "widget_y_visible", dumy)
        self._share_axes = axes
        self._mark_widget = getattr(axes, "mark_widget", dumy)
        self._check_limits = getattr(axes, "check_limits", dumy)
        self._get_time_lim = getattr(axes, "get_time_lim", dumy)
        self._set_time_lim = getattr(axes, "set_time_lim", dumy)
        self._widgets = getattr(axes, "widgets", ())
    #@-node:setup_axes_interface
    #@-others
#@-node:class MatplotChart
#@+node:class TimeWidgetChart
class TimeWidgetChart(MatplotChart):
    """
    Base class for all charts that have a horizontal time axes.

    @var sharex:
    Specifies a group of charts that share their time axis. All charts
    with the same attribute will be synchronized within the gui.

    @var show_rowlines:
    Specifies wether the chart should display row lines.

    @var auto_scale_y:
    Specifies wether the chart should be also autoscaled in the y axis
    to fit in a window.

    """
    #@	<< declarations >>
    #@+node:<< declarations >>
    __type_name__ = "matplot_timechart"
    __type_image__ = "gantt"
    data = None
    sharex = None
    show_rowlines = False
    auto_scale_y = False

    __attrib_completions__ = MatplotChart.__attrib_completions__.copy()
    __attrib_completions__.update({\
        "data" : 'data = ',
        "sharex" : 'sharex = "time_share"',
        "show_rowlines" : "show_rowlines = False",
        "auto_scale_y" : 'auto_scale_y = False',
        "#data" : "get_evaluation_completions" })


    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:register_editors
    def register_editors(cls, registry):
        super(TimeWidgetChart, cls).register_editors(registry)
        registry.String(_("Chart/sharex..."), "time_share")
        registry.Boolean(_("Chart/show_rowlines..."), False)
        registry.Boolean(_("Chart/auto_scale_y..."), True)


    register_editors = classmethod(register_editors)
    #@nonl
    #@-node:register_editors
    #@+node:__init__
    def __init__(self, *args, **kwargs):
        self.calendar = pcal._default_calendar
        self.time_scale = timescale._default_scale

        if not self.data:
            raise RuntimeError("no data attribute specified")

        MatplotChart.__init__(self, *args, **kwargs)
    #@-node:__init__
    #@+node:to_date
    def to_date(self, date):
        """
        converts a date to a x value
        """
        return self.time_scale.to_num(date)
    #@-node:to_date
    #@+node:create_axes
    def create_axes(self, rect=None, **kwargs):
        pprop = self.get_patch
        rect = rect or [ 0, 0, 1, 1 ]

        ax = self.figure.add_axes(faxes.TimeWidgetAxes(self.figure,
                                                       rect, **kwargs))
        ax.auto_scale_y = self.auto_scale_y
        ax.cla()
        ax.set_marker(pprop("focused.marker"), pprop("marker"))
        return ax
    #@-node:create_axes
    #@+node:create
    def create(self):
        if not isinstance(self.axes, faxes.TimeWidgetAxes):
            raise RuntimeError("axes has to be an instance "\
                               "of TimeWidgetAxes but is %s" \
                               % self.axes.__class__.__name__)

        row_widgets = filter(lambda w: hasattr(w, "row"), self.axes.widgets)
        if row_widgets:
            rows = map(lambda w: (w.row.y.get(), w.row), row_widgets)
            row = min(rows)[1]
        else:
            row = None

        push_active(self)
        widget.Row.show_rowline = self.show_rowlines

        all_widgets = self.create_all_widgets(row)

        utils.progress_start(_("create widgets for %s") \
                             % self.__class__.__name__,
                             len(all_widgets))

        for count, w in enumerate(all_widgets):
            self.axes.add_widget(w)
            utils.progress_update(count)

        utils.progress_end()
        self.axes.xaxis_timescale(self.time_scale)
        pop_active()
    #@-node:create
    #@+node:create_all_widgets
    def create_all_widgets(self, start_row):
        raise RuntimeError("abstract")
    #@-node:create_all_widgets
    #@+node:_finalize_row_widgets
    def _finalize_row_widgets(self, row_widgets, start_row):
        rows = enumerate(map(lambda w: w.row, row_widgets)) #get rows

        rows = map(lambda r: (r[1], r), rows) # save row order
        rows.reverse() # to elimnate duplicates with higher row numbers
        rows = dict(rows)     #eliminate duplicates
        rows = rows.values()
        rows.sort()           #restore row order
        rows = map(lambda r: r[1], rows) # back to sequence

        if start_row:
            y = start_row.next_y()
        else:
            y = mtrans.zero()

        for r in rows: y = r.set_y(y)
        return rows
    #@-node:_finalize_row_widgets
    #@-others
#@-node:class TimeWidgetChart
#@+node:class TimePlotChart
class TimePlotChart(MatplotChart):
    #@	<< class TimePlotChart declarations >>
    #@+node:<< class TimePlotChart declarations >>
    __type_name__ = "matplot_timechart"
    __type_image__ = "plot"
    calendar = None
    sharex = None

    __attrib_completions__ = MatplotChart.__attrib_completions__.copy()
    __attrib_completions__.update({\
        "calendar" : 'calendar = ',
        "sharex" : 'sharex = "time_share"',
        "def create_plot" : """def create_plot(self, to_x):
    pass
    """})

    #@-node:<< class TimePlotChart declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, *args, **kwargs):
        if not self.calendar:
            raise RuntimeError("no calendar specified")

        self.time_scale = timescale.TimeScale(self.calendar)
        MatplotChart.__init__(self, *args, **kwargs)
    #@-node:__init__
    #@+node:create_axes
    def create_axes(self, rect=None, **kwargs):
        pprop = self.get_patch
        rect = rect or [ 0, 0, 1, 1 ]

        ax = self.figure.add_axes(faxes.TimePlotAxes(self.figure,
                                                     rect, **kwargs))
        ax.cla()
        return ax
    #@-node:create_axes
    #@+node:create
    def create(self):
        push_active(self)
        self.create_plot(self.time_scale.to_num)
        self.axes.xaxis_timescale(self.time_scale)
        pop_active()
    #@-node:create
    #@+node:create_plot
    def create_plot(self, to_x):
        pass
    #@-node:create_plot
    #@-others
#@-node:class TimePlotChart
#@+node:class TimeMultiChart
class TimeMultiChart(MatplotChart):
    #@	<< class TimeMultiChart declarations >>
    #@+node:<< class TimeMultiChart declarations >>
    __type_name__ = "matplot_timechart"
    __type_image__ = "gantt"
    sharex = None
    auto_scale_y = False

    __attrib_completions__ = MatplotChart.__attrib_completions__.copy()
    __attrib_completions__.update({\
        "auto_scale_y" : 'auto_scale_y = True',
        "sharex" : 'sharex = "time_share"'})


    #@-node:<< class TimeMultiChart declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, *args, **kwargs):
        self.charts = []
        self.time_scale = timescale._default_scale
        self.main_axes = None
        MatplotChart.__init__(self, *args, **kwargs)
    #@-node:__init__
    #@+node:create_axes
    def create_axes(self, rect=None, **kwargs):
        pprop = self.get_patch
        rect = rect or [ 0, 0, 1, 1 ]

        ax = self.figure.add_axes(faxes.TimeWidgetAxes(self.figure,
                                                       rect, **kwargs))
        ax.auto_scale_y = self.auto_scale_y
        ax.cla()
        ax.set_navigate(False)
        ax.set_marker(pprop("focused.marker"), pprop("marker"))
        ax.set_frame_on(True)
        ax.axesPatch.set_fill(True)
        return ax
    #@-node:create_axes
    #@+node:create
    def create(self):
        push_active(self)
        self.create_chart()

        #find a better timescale
        for ax in self.figure.get_axes():
            if ax is not self.axes and isinstance(ax, faxes.TimeAxes):
                self.time_scale = ax.time_scale
                ax.time_axis.set_visible(False)
                ax.update_time_axis()

        self.axes.xaxis_timescale(self.time_scale)
        self.axes.update_time_axis()
        self.setup_axes_interface(self.main_axes)

        pop_active()
    #@-node:create
    #@+node:add_TimeWidgetAxes
    def add_TimeWidgetAxes(self, **kwargs):
        pprop = self.get_patch
        kwargs["sharex"] = self.axes
        if not kwargs.has_key("rect"): kwargs["rect"] = (0, 0, 1, 1)
        rect = kwargs["rect"]
        if rect[1] + rect[3] >= 1:
            kwargs["top_margin"] = self.axes.top_margin

        ax = faxes.TimeWidgetAxes(self.figure, **kwargs)
        self.figure.add_axes(ax)
        ax.auto_scale_y = self.auto_scale_y
        ax.cla()
        ax.set_frame_on(False)
        ax.set_marker(pprop("focused.marker"), pprop("marker"))
        ax.set_frame_on(False)
        ax.axesPatch.set_fill(False)
        self.main_axes = ax
        return ax
    #@-node:add_TimeWidgetAxes
    #@+node:add_TimePlotAxes
    def add_TimePlotAxes(self, **kwargs):
        kwargs["sharex"] = self.axes
        if not kwargs.has_key("rect"): kwargs["rect"] = (0, 0, 1, 1)
        rect = kwargs["rect"]
        if rect[1] + rect[3] >= 1:
            kwargs["top_margin"] = self.axes.title_height

        ax = faxes.TimePlotAxes(self.figure, **kwargs)
        self.figure.add_axes(ax)
        ax.cla()
        ax.set_frame_on(False)
        return ax
    #@-node:add_TimePlotAxes
    #@+node:add_chart
    def add_chart(self, chart):
        push_active(self)
        try:
            self.charts.append(chart)
        finally:
            pop_active()
    #@-node:add_chart
    #@+node:get_tip
    def get_tip(self, tipobj):
        if not self.show_tips: return
        for c in self.charts:
            info = c.get_tip(tipobj)
            if info: return info

        return None
    #@-node:get_tip
    #@+node:create_chart
    def create_chart(self):
        pass
    #@-node:create_chart
    #@-others
#@-node:class TimeMultiChart
#@+node:class TimeAxisChart
class TimeAxisChart(object):
    """
    A Mixin for Charts with a Time Axis

    @var time_axis_properties:
    Specifies a dictionary of display properties for the time axis.

    @var show_grid:
    A boolean value that specifies wether to display a horizontal grid.

    @var show_scale:
    A boolean value that specifies wether to display the time scale.

    @var show_free_time:
    A boolean value that specifies wether to distinguish between free
    times and working times.

    @var show_now:
    A boolean value that specifies wether to display a line at now.
    """
    #@	<< declarations >>
    #@+node:<< declarations >>
    time_axis_properties = None
    show_grid = True
    show_scale = True
    show_free_time = True
    show_now = True

    __attrib_completions__ = {\
        "time_axis_properties" : 'time_axis_properties = { | }',
        "show_grid": "show_grid = False",
        "show_scale": "show_scale = False",
        "show_free_time": "show_free_time = False",
        "show_now": "show_now = False" }

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:register_editors
    def register_editors(cls, registry):
        #"time_axis_properties" : 'time_axis_properties = { | }',
        super(TimeAxisChart, cls).register_editors(registry)
        registry.Boolean(_("Axis/show_grid..."), True)
        registry.Boolean(_("Axis/show_scale..."), True)
        registry.Boolean(_("Axis/show_free_time..."), True)
        registry.Boolean(_("Axis/show_now..."), True)
        registry.Property(_("Axis/time_axis_properties..."), cls.create_time_axis_property_groups)

    register_editors = classmethod(register_editors)

    def create_time_axis_property_groups(cls, property):
        property.fill_gc_group("")
        property.fill_font_group("")
        property.fill_gc_group("now")
        property.fill_gc_group("grid")
        property.fill_font_group("0")
        property.name_groups.append("0.facecolor")
        property.name_groups.append("tickers")
        property.name_groups.append("facecolor")
        property.name_groups.append("free.facecolor")
        for t in range(3):
            property.fill_font_group(str(t))
            property.name_groups.append("%s.facecolor" % str(t))


    create_time_axis_property_groups = classmethod(create_time_axis_property_groups)
    #@nonl
    #@-node:register_editors
    #@+node:create
    def create(self):
        super(TimeAxisChart, self).create()
        self.set_time_axis()
    #@-node:create
    #@+node:set_time_axis
    def set_time_axis(self):
        self.time_axis = taxis.TimeAxis(self.time_axis_properties)
        self.time_axis.show_grid = self.show_grid
        self.time_axis.show_scale = self.show_scale
        self.time_axis.show_free_time = self.show_free_time
        self.time_axis.show_now = self.show_now
        self.time_axis.time_scale = self.time_scale
        self.axes.set_time_axis(self.time_axis)
    #@-node:set_time_axis
    #@-others
#@-node:class TimeAxisChart
#@+node:class TimeAxisWidgetChart
class TimeAxisWidgetChart(TimeAxisChart, TimeWidgetChart):
    #@	<< class TimeAxisWidgetChart declarations >>
    #@+node:<< class TimeAxisWidgetChart declarations >>
    __attrib_completions__ = TimeAxisChart.__attrib_completions__.copy()
    __attrib_completions__.update(TimeWidgetChart.__attrib_completions__)

    #@-node:<< class TimeAxisWidgetChart declarations >>
    #@nl
    #@	@+others
    #@+node:printer
    def printer(cls, **kwargs):
        return printer.TimeWidgetPrinter(cls, **kwargs)

    printer = classmethod(printer)
    #@-node:printer
    #@-others
#@-node:class TimeAxisWidgetChart
#@+node:class TimeAxisPlotChart
class TimeAxisPlotChart(TimeAxisChart, TimePlotChart):
    #@	<< class TimeAxisPlotChart declarations >>
    #@+node:<< class TimeAxisPlotChart declarations >>
    __attrib_completions__ = TimeAxisChart.__attrib_completions__.copy()
    __attrib_completions__.update(TimePlotChart.__attrib_completions__)

    #@-node:<< class TimeAxisPlotChart declarations >>
    #@nl
    #@	@+others
    #@+node:printer
    def printer(cls, **kwargs):
        return printer.TimePlotPrinter(cls, **kwargs)

    printer = classmethod(printer)
    #@-node:printer
    #@-others
#@-node:class TimeAxisPlotChart
#@+node:class TimeAxisMultiChart
class TimeAxisMultiChart(TimeAxisChart, TimeMultiChart):
    #@	<< class TimeAxisMultiChart declarations >>
    #@+node:<< class TimeAxisMultiChart declarations >>
    __attrib_completions__ = TimeAxisChart.__attrib_completions__.copy()
    __attrib_completions__.update(TimeMultiChart.__attrib_completions__)

    #@-node:<< class TimeAxisMultiChart declarations >>
    #@nl
    #@	@+others
    #@+node:printer
    def printer(cls, **kwargs):
        return printer.TimeWidgetPrinter(cls, **kwargs)

    printer = classmethod(printer)    
    #@-node:printer
    #@-others
#@-node:class TimeAxisMultiChart
#@+node:class TableChart
class TableChart(MatplotChart):
    #@	<< class TableChart declarations >>
    #@+node:<< class TableChart declarations >>
    __type_name__ = "matplot_pointchart"
    show_rowlines = True
    show_collines = True

    __attrib_completions__ = MatplotChart.__attrib_completions__.copy()
    __attrib_completions__.update({\
        "show_collines" : 'show_collines = True',
        "show_rowlines" : 'show_rowlines = True' })


    #@-node:<< class TableChart declarations >>
    #@nl
    #@	@+others
    #@+node:register_editors
    def register_editors(cls, registry):
        super(TableChart, cls).register_editors(registry)
        registry.Boolean(_("Chart/show_rowlines..."), False)
        registry.Boolean(_("Chart/show_collines..."), False)


    register_editors = classmethod(register_editors)
    #@nonl
    #@-node:register_editors
    #@+node:printer
    def printer(cls, **kwargs):
        return printer.PointPrinter(cls, **kwargs)

    printer = classmethod(printer)
    #@-node:printer
    #@+node:__init__
    def __init__(self, *args, **kwargs):
        self.cols = {}
        self.rows = {}
        self.widgets = []
        MatplotChart.__init__(self, *args, **kwargs)
    #@-node:__init__
    #@+node:create_axes
    def create_axes(self, rect=None, **kwargs):
        pprop = self.get_patch
        rect = rect or [0, 0, 1, 1]
        fig = self.figure
        ax = fig.add_axes(faxes.PointAxes(fig, rect, **kwargs))
        ax.cla()
        ax.set_marker(pprop("focused.marker"), pprop("marker"))
        return ax
    #@-node:create_axes
    #@+node:create
    def create(self):
        if not isinstance(self.axes, faxes.PointAxes):
            raise RuntimeError("axes has to be an instance "\
                               "of PointAxes but is %s" \
                               % self.axes.__class__.__name__)

        push_active(self)

        header_transform = self.axes.build_margin_transform(top=False)
        def dumy(*args): pass

        try:
            self.create_all_widgets()
            self._finalize_row_widgets()
            self._finalize_col_widgets()

            utils.progress_start(_("create widgets for %s") \
                                 % self.__class__.__name__,
                                 len(self.widgets))

            count = 0
            for w in self.widgets:
                self.axes.add_widget(w)
                utils.progress_update(count)
                count += 1

            utils.progress_end()

            for r in self.rows.itervalues(): self.axes.add_widget(r)
            for c in self.cols.itervalues(): self.axes.add_widget(c)
        finally:
            pop_active()
    #@-node:create
    #@+node:get_col
    def get_col(self, col_no):
        col = self.cols.get(col_no)
        if not col:
            widget.Column.show_colline = self.show_collines
            col = self.cols[col_no] = widget.Column()

        return col
    #@-node:get_col
    #@+node:get_row
    def get_row(self, row_no=None):
        if row_no is None:
            if self.rows: 
                row_no = max(self.rows.keys()) + 1
            else:
                row_no = 0

        row = self.rows.get(row_no)
        if not row:
            widget.Row.show_rowline = self.show_rowlines
            row = self.rows[row_no] = widget.Row()

        return row
    #@-node:get_row
    #@+node:add_cell
    def add_cell(self, row_no, col_no, fobj, properties=None):
        row = self.get_row(row_no)
        col = self.get_col(col_no)
        cell = widget.CellWidget(row, col, fobj, properties)
        self.widgets.append(cell)
        return cell
    #@-node:add_cell
    #@+node:create_all_widgets
    def create_all_widgets(self):
        pass
    #@-node:create_all_widgets
    #@+node:_finalize_row_widgets
    def _finalize_row_widgets(self):
        row_widgets = filter(lambda w: hasattr(w, "row"), self.axes.widgets)
        if row_widgets:
            rows = map(lambda w: (w.row.y.get(), w.row), row_widgets)
            y = min(rows)[1].next_y()
        else:
            y = mtrans.zero()

        rows = self.rows.items()
        rows.sort()           #restore row order
        for rno, row in rows:
            y = row.set_y(y)
    #@-node:_finalize_row_widgets
    #@+node:_finalize_col_widgets
    def _finalize_col_widgets(self):
        col_widgets = filter(lambda w: hasattr(w, "col"), self.axes.widgets)
        if col_widgets:
            cols = map(lambda w: (w.col.x.get(), w.col), col_widgets)
            x = max(cols)[1].next_x()
        else:
            x = mtrans.zero()

        cols = self.cols.items()
        cols.sort()
        for cno, col in cols:
            x = col.set_x(x)

    #@-node:_finalize_col_widgets
    #@-others
#@-node:class TableChart
#@+node:class _DescriptionTable
class _DescriptionTable(TableChart):
    #@	<< class _DescriptionTable declarations >>
    #@+node:<< class _DescriptionTable declarations >>
    properties = { "edgecolor" : "black",
                   "title.facecolor" : "darkgray",
                   "title.antialiased" : True,
                   "title.linewidth" : 1 }

    #@-node:<< class _DescriptionTable declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, report, src_axes, paint_to=None, rect=None,
                 property_prefix="", properties=None, **kwargs):
        self.src_axes = src_axes
        self.report = report
        self.property_prefix = property_prefix
        self.properties = properties or  { }
        TableChart.__init__(self, paint_to, rect, **kwargs)
    #@-node:__init__
    #@+node:get_col
    def get_col(self, col_no):
        col = self.cols.get(col_no)
        if not col:
            class TitleColumn(widget.Column):
                def set_transform(self, transform):
                    transform = self.axes.build_margin_transform(top=False)
                    widget.Column.set_transform(self, transform)
                    widget.Column.set_clip_box(self, transform.get_bbox2())

            TitleColumn.show_colline = self.show_collines
            col = self.cols[col_no] = TitleColumn()

        return col
    #@-node:get_col
    #@+node:create_all_widgets
    def create_all_widgets(self):
        rows = { }
        cells = { }

        report = self.report()
        self.create_header(report)
        rows[-1] = self.header_row

        for r in report:
            for c in r:
                task, attrib = c.get_ref()[:2]
                if task: break
            else:
                continue

            src_widget = self.src_axes.find_widget(task)
            if not src_widget: continue

            for i, c in enumerate(r):
                col = self.get_col(i)
                row = rows.get(src_widget.row)
                if not row:
                    row = rows[src_widget.row] = widget.Row()
                    row.show_rowline = self.show_rowlines
                    row.height = src_widget.row.height
                    row.top_sep = src_widget.row.top_sep
                    row.bottom_sep = src_widget.row.bottom_sep
                    row.set_y(src_widget.row.y)

                task, attrib = c.get_ref()[:2]
                cell = cells.get((row, col))
                if not cell:
                    cell = cells[(row, col)] = widget.CellWidget(row, col, task)
                    cell.fattrib = attrib
                    self.widgets.append(cell)

                #cell.vert_sep = row.top_sep + row.bottom_sep
                #row.top_sep = row.bottom_sep = 0
                self.modify_widget(cell, task, c)

        self.rows = rows
    #@-node:create_all_widgets
    #@+node:create_header
    def create_header(self, report):
        class TitleWidget(object):
            def set_transform(self, transform):
                Point = mtrans.Point
                Bbox = mtrans.Bbox
                zero = mtrans.zero()

                point_to_pixel = self.axes.fig_point_to_pixel
                bbox = self.axes.bbox
                dbox = transform.get_bbox1()
                top_margin = self.axes.top_margin
                left = self.axes.left_margin * point_to_pixel
                right = self.axes.right_margin * point_to_pixel
                mheight = point_to_pixel * top_margin
                bheight = bbox.ur().y() - bbox.ll().y()
                offset = bheight - mheight

                view_box = Bbox(Point(bbox.ll().x() + left, 
                                      bbox.ll().y() + offset),
                                Point(bbox.ur().x() - right, 
                                      bbox.ur().y()))

                data_box = Bbox(Point(dbox.ll().x() , zero - top_margin),
                                Point(dbox.ur().x(), zero))

                transform = mtrans.get_bbox_transform(data_box, view_box)
                super(TitleWidget, self).set_transform(transform)
                super(TitleWidget, self).set_clip_box(bbox)


            def contains(self, x, y):
                return False


        class TitleRow(TitleWidget, widget.Row):
            def update_height(self, height): pass

        class TitleCell(TitleWidget, widget.CellWidget): pass

        self.header_row = TitleRow()
        self.header_row.axes = self.axes
        self.header_row.show_rowline = True
        self.header_row.top_sep = self.header_row.bottom_sep = 0
        self.header_row.height = Lazy(self.axes.top_margin)
        self.header_row.set_y(0)
        self.header_row._is_header = True
        kwargs = make_properties(self.get_property,
                                 self.property_prefix+"title")
        back = patches.Polygon(((LEFT, TOP), (LEFT, BOTTOM),
                                (RIGHT, BOTTOM), (RIGHT, TOP)), **kwargs)
        self.header_row.add_artist(back)
        for i, header in enumerate(report.headers):
            col = self.get_col(i)
            col._is_header = True
            cell = TitleCell(self.header_row, col, None)
            cell._is_header = True
            self.modify_header_widget(cell, header)
            self.widgets.append(cell)
    #@-node:create_header
    #@+node:_finalize_row_widgets
    def _finalize_row_widgets(self):
        pass
    #@-node:_finalize_row_widgets
    #@+node:modify_header_widget
    def modify_header_widget(self, cell, title):
        cell.horz_sep = 6
        cell.text(title, 
                  HCENTER, VCENTER,
                  horizontalalignment ="center",
                  verticalalignment="center",
                  fontproperties=self.property_prefix+"title")
    #@-node:modify_header_widget
    #@+node:modify_widget
    def modify_widget(self, widget, obj, cell):
        if widget.artists: return

        if cell.back_color:
            back = patches.Polygon(((LEFT, TOP), (LEFT, BOTTOM),
                                    (RIGHT, BOTTOM), (RIGHT, TOP)),
                                   facecolor=cell.back_color,
                                   linewidth=0)
            widget.add_artist(back)


        halign = { cell.LEFT : "left",
                   cell.RIGHT : "right",
                   cell.CENTER : "center" }[cell.align]

        t = widget.text(str(cell), 
                        LEFT + 2 * HSEP, VCENTER,
                        horizontalalignment=halign,
                        verticalalignment="center",
                        fontproperties=self.property_prefix+"row")

        if cell.back_color: t.set_backgroundcolor(cell.back_color)
        if cell.text_color: t.set_color(cell.text_color)
        if cell.font_bold: t.set_weight("bold")
        if cell.font_italic: t.set_style("italic")
        if cell.font_size: t.set_size(cell.font_size)
        #if cell.left_border = None
        #if cell.top_border = False
        #if cell.right_border = True
        #if cell.bottom_border = True
        widget.horz_sep = 6
    #@-node:modify_widget
    #@-others
#@-node:class _DescriptionTable
#@+node:class TimeTabledChart
class TimeTabledChart(MatplotChart):
    #@	<< class TimeTabledChart declarations >>
    #@+node:<< class TimeTabledChart declarations >>
    __type_name__ = "matplot_timechart"
    __type_image__ = "gantt"

    properties = { "background.facecolor" : "white" }

    sharex = None
    auto_scale_y = False
    content_charts = ()
    plot_chart = None
    left_report = None
    right_report = None

    __attrib_completions__ = MatplotChart.__attrib_completions__.copy()
    __attrib_completions__.update({\
        "sharex" : 'sharex = "time_shared"',
        "auto_scale_y" : 'auto_scale_y = True',
        "content_charts" : 'content_charts = ()',
        "plot_chart" : 'plot_chart = None',
        "left_report" : 'left_report = None',
        "right_report" : 'right_report = None'})


    #@-node:<< class TimeTabledChart declarations >>
    #@nl
    #@	@+others
    #@+node:printer
    def printer(cls, **kwargs):
        return printer.TimeWidgetPrinter(cls, **kwargs)
    #@-node:printer
    #@+node:__init__
    printer = classmethod(printer)


    def __init__(self, *args, **kwargs):
        self.charts = []
        self.time_scale = timescale._default_scale
        MatplotChart.__init__(self, *args, **kwargs)
    #@-node:__init__
    #@+node:setup_axes_interface
    def setup_axes_interface(self, axes):
        super(TimeTabledChart, self).setup_axes_interface(self.content_axes)
        self._share_axes = axes
        del self._check_limits
        del self._widget_at
        del self._mark_widget
    #@-node:setup_axes_interface
    #@+node:_check_limits
    def _check_limits(self, cut=True):
        self.left_axes.check_limits(cut)
        self.axes.check_limits(cut)
        self.right_report and self.right_axes.check_limits(cut)
    #@-node:_check_limits
    #@+node:_widget_at
    def _widget_at(self, x, y):
        try:
            return self.content_axes.widget_at(x, y) \
                   or self.left_axes.widget_at(x, y) \
                   or self.right_axes.widget_at(x, y)
        except AttributeError:
            return None
    #@-node:_widget_at
    #@+node:_mark_widget
    def _mark_widget(self, widget):
        changed = 0
        changed += self.content_axes.mark_widget(widget)
        changed += self.left_axes.mark_widget(widget)
        try:
            changed += self.right_axes.mark_widget(widget)
        except AttributeError:
            pass

        return bool(changed)
    #@-node:_mark_widget
    #@+node:create_axes
    def create_axes(self, rect=None, **kwargs):
        rect = ( 0, 0, 1, 1 )

        #be carefully the order of the following
        #is very important (and unfortunatly quite complicated)
        #A fine tuned use of lazy values...

        top_margin = kwargs["top_margin"] = mtrans.Value(0)
        self.left_axes = faxes.PointAxes(self.figure, ( 0, 0, 1, 1 ), **kwargs)
        self.figure.add_axes(self.left_axes).cla()

        #self.left_axes.point_to_pixel and self.left_axes.fig_point_to_pixel
        #have new lazy values after add_axes

        font_factor = self.left_axes.point_to_pixel \
                      / self.left_axes.fig_point_to_pixel

        right_data_lim = mtrans.unit_bbox()
        right_offset = self.figure.figwidth * mtrans.Value(72 / 2)\
                       - right_data_lim.ur().x() * font_factor

        self.right_axes = faxes.PointAxes(self.figure, ( 0.5, 0, 0.5, 1 ),
                                          left_margin=right_offset,
                                          sharey=self.left_axes,
                                          **kwargs)

        self.figure.add_axes(self.right_axes).cla()
        self.right_axes.dataLim = right_data_lim

        kwargs["left_margin"] = self.left_axes.dataLim.ur().x() * font_factor
        kwargs["right_margin"] = self.right_axes.dataLim.ur().x() * font_factor

        class MainAxes(faxes.TimeWidgetAxes):
            def update_time_axis(self):
                self.time_axis.show_scale = True #this axes must always have a scale
                faxes.TimeWidgetAxes.update_time_axis(self)

        main_axes = MainAxes(self.figure, rect, **kwargs)
        main_axes.auto_scale_y = self.auto_scale_y
        main_axes.set_navigate(False)

        kwargs["sharex"] = main_axes
        kwargs["sharey"] = self.left_axes
        self.content_axes = faxes.TimeWidgetAxes(self.figure, rect, **kwargs)
        self.content_axes.set_frame_on(False)

        self.figure.add_axes(main_axes).cla()
        self.figure.add_axes(self.content_axes).cla()

        #correct the axespatch of mainaxes
        dtrans = main_axes.build_margin_transform(top=False)
        atrans = mtrans.get_bbox_transform(mtrans.unit_bbox(),
                                           dtrans.get_bbox2())
        main_axes.axesPatch.set_transform(atrans)
        return main_axes
    #@-node:create_axes
    #@+node:create
    def create(self):
        push_active(self)
        self.charts = map(lambda c: c(self.content_axes), self.content_charts)

        if self.left_report:
            _DescriptionTable(self.left_report,
                              self.content_axes,
                              self.left_axes,
                              property_prefix="left.",
                              properties=self.properties)


        if self.right_report:
             _DescriptionTable(self.right_report,
                               self.content_axes,
                               self.right_axes,
                               property_prefix="right.",
                               properties=self.properties)

        prop = self.get_property
        pprop = self.get_patch
        self.figure.set_facecolor(prop("background.facecolor"))

        if self.left_axes.widgets:
            self.left_axes.set_axis_bgcolor(prop("left.background.facecolor"))
            self.left_axes.set_marker(pprop("left.focused.marker"),
                                      pprop("left.marker"))

        if not self.right_axes.widgets:
            self.figure.delaxes(self.right_axes)
            del self.right_axes
        else:
            self.right_axes.set_axis_bgcolor(prop("right.background.facecolor"))    
            self.right_axes.set_marker(pprop("right.focused.marker"),
                                       pprop("right.marker"))

        self.time_scale = self.content_axes.time_scale
        self.axes.xaxis_timescale(self.time_scale)
        self.content_axes.time_axis.set_visible(False)
        self.content_axes.update_time_axis()
        self.content_axes.set_axis_bgcolor(prop("content.background.facecolor"))
        self.content_axes.set_marker(pprop("focused.marker"), pprop("marker"))
        pop_active()
    #@-node:create
    #@+node:get_tip
    def get_tip(self, tipobj):
        if not self.show_tips: return
        for c in self.charts:
            info = c.get_tip(tipobj)
            if info: return info

        return None
    #@-node:get_tip
    #@+node:create_chart
    def create_chart(self):
        pass
    #@-node:create_chart
    #@-others
#@-node:class TimeTabledChart
#@+node:class TimeAxisTabledChart
class TimeAxisTabledChart(TimeAxisChart, TimeTabledChart):
    #@	<< class TimeAxisTabledChart declarations >>
    #@+node:<< class TimeAxisTabledChart declarations >>
    __attrib_completions__ = TimeAxisChart.__attrib_completions__.copy()
    __attrib_completions__.update(TimeTabledChart.__attrib_completions__)



    #@-node:<< class TimeAxisTabledChart declarations >>
    #@nl
#@-node:class TimeAxisTabledChart
#@-others
#@nonl
#@-node:@file charting/charts.py
#@-leo
