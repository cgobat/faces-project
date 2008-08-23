#@+leo-ver=4
#@+node:@file lib/resource.py
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
import faces.charting.charts as charts
import faces.observer
import faces.task
import faces.resource
import faces.charting.timescale as timescale
import faces.charting.widgets as widget
import faces.charting.patches as patches
import faces.charting.shapes as shapes
import faces.plocale
import matplotlib.font_manager as font
import locale
from faces.charting.tools import *

#@-node:<< Imports >>
#@nl

_is_source_ = True
_ = faces.plocale.get_gettext()

__all__ = ("Standard",)

#@+others
#@+node:class Standard
class Standard(charts.TimeAxisWidgetChart):
    """
    A standard resource chart.

    @var load_factor:
    Specifies the height of a load 1.0 bar in units of
    the default font size. If the load_factor is 12 and
    the default font size is 12 pt, the height of load 1.0 bar
    will be 12 * 12 = 144 pt. The default value is 12.

    @var start:
    The left start date of the chart. If KW{None} it is calculated
    automatically.

    @var end:
    The right end date of the chart. If KW{None} it is calculated
    automatically.

    @var title_attrib:
    A string value specifying the name of the task attribute that 
    should be displayed at the gantt object, to identify the task.

    @var color_index:
    A list of tuples defining the facecolor and fontcolor for
    the booking bars.
    """
    #@	<< declarations >>
    #@+node:<< declarations >>
    __type_image__ = "resources"
    __editor__ = ("faces.gui.edit_chart", "Resource")

    color_index = ( ("navy", "white"),
                    ("seagreen", "white"),
                    ("indianred", "white"),
                    ("violet", "white"),
                    ("skyblue", "white"),
                    ("purple", "white"),
                    ("forestgreen", "white"),
                    ("limegreen", "white"),
                    ("darkorchid", "white"),
                    ("rosybrown", "white") )

    properties = { "title.weight" : "bold",
                   "title.color" : "white",
                   "row.edgecolor" : "black",
                   "title.edgecolor" : "black",
                   "title.facecolor" : "black",
                   "title.linewidth" : 1,
                   "title.fill" : 1,
                   "title.antialiased" : True }

    _color_dict = { }
    _cindex = 0
    load_factor = 12
    show_rowlines = True
    start = None
    end = None
    title_attrib = "title"

    __attrib_completions__ = charts.TimeAxisWidgetChart.__attrib_completions__.copy()
    __attrib_completions__.update({\
        "color_index" : 'color_index = [ ("navy", "white"), ("seagreen", "white") ]',
        "title_attrib" : 'title_attrib = "title"',
        "load_factor" : 'load_factor = 12',
        "show_rowlines" : 'show_rowlines = False',
        "start" : 'start = "|"',
        "end" : 'end = "|"',
        "def modify_row" : """def modify_row(self, row_widget, res):
    self.add_load_line(row_widget, 1.0, edgecolor="red")
    """,
        "def modify_bar" : \
        """def modify_bar(self, bar_widget, row_widget, task):
    bar_widget.text("effort: %s\\nlength: %s" \\
    % (task.to_string.effort,
    task.to_string.length),
    LEFT + 2*HSEP, TOP - 2*VSEP,
    horizontalalignment="left",
    verticalalignment="top",
    color="white")
    """})


    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:register_editors
    def register_editors(cls, registry):
        super(Standard, cls).register_editors(registry)
        registry.Boolean(_("Chart/show_rowlines..."), True)
        registry.Float(_("Chart/load_factor..."), 12)
        registry.Date(_("Chart/start..."))
        registry.Date(_("Chart/end..."))
        registry.String(_("Shape/title_attrib..."), "title")
        registry.Evaluation(_("Chart/data..."))
        registry.TwoColorSet(_("Chart/color_index..."), cls.color_index)


    register_editors = classmethod(register_editors)

    def create_property_groups(cls, property):
        property.set_default_groups()
        property.fill_font_group("title")
        property.fill_font_group("left.load_line")
        property.fill_font_group("right.load_line")
        property.fill_font_group("load_line")
        property.fill_font_group("bar.inside")    


    create_property_groups = classmethod(create_property_groups)
    #@nonl
    #@-node:register_editors
    #@+node:__init__
    def __init__(self, *args, **kwargs):
        charts.TimeAxisWidgetChart.__init__(self, *args, **kwargs)
    #@-node:__init__
    #@+node:create_all_widgets
    def create_all_widgets(self, start_row):
        data = self.data

        widgets = []

        try:
            if isinstance(data, faces.task.Task):
                if not self.start: self.start = self.data.start
                if not self.end: self.end = self.data.end
                self.calendar = self.data.root.calendar
                data = data.all_resources()
            elif isinstance(data, faces.resource.Resource):
                data = ( data, )
            elif issubclass(data, faces.resource.Resource):
                data = ( data(), )
        except TypeError:
            raise ValueError("the data attribute is not valid")

        if not self.start or not self.end:
            raise RuntimeError("You have to specify 'start' and 'end'")

        self.time_scale = timescale.TimeScale(self.calendar)
        self.start = self.time_scale.to_num(self.start)
        self.end = self.time_scale.to_num(self.end)

        for resource in iter(data):
            row = self.create_row(resource)
            bars = self.create_bars(resource(), row)
            if bars:
                widgets.extend(bars)
            else:
                # to ensure that the row will be there
                dumy = widget.TimeWidget(self.start, self.end, resource, row)
                dumy.set_shape(shapes.bar, "bar")
                dumy.set_visible(False)
                widgets.append(dumy)

        if not widgets:
            #no resource allocated
            raise RuntimeError("no resources defined")

        rows = self._finalize_row_widgets(widgets, start_row)
        widgets.extend(rows)
        return widgets
    #@-node:create_all_widgets
    #@+node:create_row
    def create_row(self, resource):
        row = widget.Row()
        row.top_sep = 9
        row.bottom_sep = 0
        row.fobj = resource

        name = resource.name
        if resource.title != name:
            name += "(%s)" % resource.title

        kwargs = make_properties(self.get_property, "title")
        row.add_artist(patches.Rectangle((LEFT, TOP - 8 * VSEP),
                                         RIGHT - LEFT, 7 * VSEP,
                                         **kwargs))

        row.text(name, LEFT + 2 * HSEP, TOP - 3 * VSEP,
                 verticalalignment="top",
                 horizontalalignment ="left",
                 fontproperties="title")

        row.text(name, RIGHT - 2 * HSEP, TOP - 3 * VSEP,
                 verticalalignment="top",
                 horizontalalignment ="right",
                 fontproperties="title")

        self.modify_row(row, resource)
        return row
    #@-node:create_row
    #@+node:modify_row
    def modify_row(self, row_widget, resource):
        """
        Overwrite this method, to decorate a resource row.
        """
        pass
    #@-node:modify_row
    #@+node:add_load_line
    def add_load_line(self, row_widget, load, **kwargs):
        """
        Adds a horizontal line at a specific load.
        """

        offset = self.load_offset(load)
        row_widget.add_artist(patches.Polygon(((LEFT, BOTTOM + offset),
                                               (RIGHT, BOTTOM + offset)),\
                                              **kwargs))

        row_widget.text("load %0.2f" % load, 
                        RIGHT - 2*HSEP, BOTTOM + offset - 2*VSEP,
                        horizontalalignment="right",
                        verticalalignment="top",
                        fontproperties="left.load_line")

        row_widget.text("load %0.2f" % load, 
                        LEFT + 2*HSEP, BOTTOM + offset - 2*VSEP,
                        horizontalalignment="left",
                        verticalalignment="top",
                        fontproperties="right.load_line")
    #@-node:add_load_line
    #@+node:load_offset
    add_load_line.__call_completion__ = 'add_load_line(row_widget, 1.0, edgecolor="red")'


    def load_offset(self, load):
        """
        returns the y position of a specific load.
        """
        return load * self.load_factor * font.fontManager.get_default_size()
    #@-node:load_offset
    #@+node:create_bar
    def create_bar(self, task, row, start, end, load, offset):
        widget.ResourceBarWidget.load_factor = self.load_factor
        facecolor, text_color = self.get_color(task)
        props = { "bar.inside.color" : text_color,
                  "facecolor" : facecolor }
        bar = widget.ResourceBarWidget(task, row, start, end, 
                                       load, offset, props)
        bar.inside_text("%s (%.2f)" % (getattr(task, self.title_attrib), load),
                        inside_properties="bar.inside")
        self.modify_bar(bar, row, task)
        return bar
    #@-node:create_bar
    #@+node:modify_bar
    def modify_bar(self, bar_widget, row_widget, task):
        """
        Overwrite this method, to decorate a var widget.
        """
        pass
    #@-node:modify_bar
    #@+node:get_color
    def get_color(cls, task):
        id_ = task._idendity_()
        if not id_:
            #vacations have always the same color
            return ("gold", "black")

        color = cls._color_dict.get(id_)
        if not color:
            color = cls._color_dict[id_] = cls.color_index[cls._cindex]
            cls._cindex += 1
            if cls._cindex >= len(cls.color_index):
                cls._cindex = 0

        return color
    #@-node:get_color
    #@+node:create_bars
    get_color = classmethod(get_color)


    def create_bars(self, resource, row):
        to_num = self.time_scale.to_num
        widgets = []
        dstart = self.start
        dend = self.end

        tasks = resource.get_bookings_at(dstart, dend, self.data.scenario)

        def make_item(task):
            start = to_num(min(task.start, task.book_start))
            end = to_num(max(task.end, task.book_end))
            return (start, -(end - start), -task.load, task.book_start, task)

        book_items = map(make_item, tasks)
        book_items.sort()
        load_offsets = faces.resource.ResourceCalendar()
        used_tasks = {}

        def break_booking(start, end):
            #breaks a booking into parts with different load offsets
            spos, epos, offsets = load_offsets.get_bookings(start, end)
            offsets = map(lambda o: (max(to_num(o[0]), start), o[1] / 10000.0),
                          offsets[spos:epos])
            #returns the following sequence:
            #[(offset[0], offset[1]), (offset[1], offset[2]), ...]
            return zip(offsets, offsets[1:] + [(end,0)])

        def feq(f1, f2):
            "float equal"
            return ("%.3f" % f1) == ("%.3f" % f2)

        for s, le, lo, bs, t in book_items:
            load = -lo

            start = max(to_num(t.book_start), dstart)
            end = min(to_num(t.book_end), dend)

            breaks = break_booking(start, end)
            for sl, el in breaks:
                start, offset = sl
                end = el[0]
                last = used_tasks.get(t._idendity_())

                if last and feq(last.offset, offset) and feq(last.load, load):
                    cal_last_end = self.calendar.EndDate(last.end)
                    cal_start = self.calendar.EndDate(start)
                    if cal_last_end >= cal_start:
                        #connect the two objects
                        load_offsets.add_load(last.end, end, load)
                        last.end = end
                        continue                    

                load_offsets.add_load(start, end, load)
                obj = self.create_bar(t, row, start, end, load, offset)
                widgets.append(obj)
                used_tasks[t._idendity_()] = obj

        return widgets
    #@-node:create_bars
    #@+node:get_tip
    def get_tip(self, tipobj):
        if not self.show_tips: return

        if isinstance(tipobj, widget.ResourceBarWidget):
            formats = faces.task.Task.formats
            to_minute = self.time_scale.chart_calendar.Minutes
            duration = tipobj.fobj.book_end - tipobj.fobj.book_start
            duration = to_minute(duration, True)
            work_time = to_minute(tipobj.fobj.work_time)
            lines = [
                (_("Name"), tipobj.fobj.title),
                (_("Load"), locale.format("%.2f", tipobj.load, True)),
                (_("Worktime"),  work_time.strftime(formats["length"])),
                (_("Timeframe"), "%s - %s" %
                 (tipobj.fobj.book_start.strftime(formats["start"]),
                  tipobj.fobj.book_end.strftime(formats["end"]))),
                 (_("Duration"), duration.strftime(formats["duration"], True)),
                (_("State"), tipobj.fobj.actual and _("actual") or _("planned"))
                ]

            return lines

        return None
    #@-node:get_tip
    #@-others
#@-node:class Standard
#@-others

faces.observer.clear_cache_funcs[Standard] = Standard._color_dict.clear
#@-node:@file lib/resource.py
#@-leo
