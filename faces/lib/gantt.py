#@+leo-ver=4
#@+node:@file lib/gantt.py
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
import faces
import faces.pcalendar as pcal
import faces.charting.charts as charts
import faces.charting.widgets as widget
import faces.charting.shapes as shapes
import faces.charting.timescale as timescale
import faces.charting.connector as connector
import faces.task as task
import faces.plocale
from faces.charting.tools import *
from faces.charting.shapes import *
#@-node:<< Imports >>
#@nl
#@<< Declarations >>
#@+node:<< Declarations >>
_is_source_ = True
_ = faces.plocale.get_gettext()

_color_index = ( "navy",
                 "seagreen",
                 "indianred",
                 "violet",
                 "skyblue",
                 "purple",
                 "limegreen",
                 "darkgray" )


GanttWidget = widget.GanttWidget

__all__ = ("Standard", "Compare", "Critical") + shapes.__all__
#@nonl
#@-node:<< Declarations >>
#@nl

#@+others
#@+node:class Gantt
class Gantt(charts.TimeAxisWidgetChart):
    """
    A standard gantt chart

    @var show_connectors:
    A boolean value that specifies wether to display connectors between tasks.

    @var show_complete:
    A boolean value that specifies wether to display a completion bar
    inside the gantt bars.

    @var row_attrib:
    A string value specifying the name of the row attribute inside the
    project definitions.  With this attribute you can control in which
    row a task will be displayed.

    @var accumulate_attrib:
    A string value specifying the name of the accumulate attribute
    inside the project definitions.  If a parent task defines the
    accumulate attribute as True it will be displayed as
    leaf, and all child tasks will not be displayed.

    @var shape_attrib:
    A string value specifying the name of the shape attribute inside
    the project definitions.  The shape attribute controls the
    displayed shape of the gantt object.

    @var shape_properties_attrib:
    A string value specifying the name of the shape properties
    attribute inside the project definitions.  The shape properties
    attribute controls the style properties of the gantt object.

    @var parent_shape:
    A string value specifying the name of the general shape for parent tasks.

    @var milestone_shape:
    A string value specifying the name of the general shape for milestone tasks.

    @var leaf_shape:
    A string value specifying the name of the general shape for leaf tasks.

    @var title_attrib:
    A string value specifying the name of the task attribute that 
    should be displayed at the gantt object, to identify the task.

    @var show_resource:
    A boolean value that specifies wether to display the allocated
    resources after the title.
    """
    #@	<< declarations >>
    #@+node:<< declarations >>
    __editor__ = ("faces.gui.edit_gantt", "Standard")

    show_connectors = True
    show_complete = True
    row_attrib = "gantt_same_row"
    accumulate_attrib = "gantt_accumulate"
    shape_attrib = "gantt_shape"
    shape_properties_attrib = "gantt_properties"
    parent_shape = "brace"
    milestone_shape = "diamond"
    leaf_shape = "bar"
    title_attrib = "title"
    show_resource = True
    properties = { "parent.facecolor": "black",
                   "complete.facecolor" : "black",
                   "connector.end.facecolor" : "darkslategray",
                   "connector.end.edgecolor" : "darkslategray",
                   "connector.edgecolor" : "darkslategray",
                   "facecolor" : "blue",
                   "milestone.facecolor" : "black",
                   "background.facecolor" : "w",
                   "height" : 4, "complete.height" : 2 }

    __attrib_completions__ = charts.TimeAxisWidgetChart\
                             .__attrib_completions__.copy()
    __attrib_completions__.update({\
        "show_resource" : 'show_resource = False',
        "show_connectors" : 'show_connectors = True',
        "show_complete" : 'show_complete = True',
        "row_attrib" : 'row_attrib = "gantt_same_row"',
        "accumulate_attrib" : 'accumulate_attrib = "gantt_accumulate"',
        "shape_attrib" : 'shape_attrib = "gantt_shape"',
        "shape_properties_attrib" : 'shape_properties_attrib = "gantt_properties"',
        "parent_shape" : 'parent_shape = "brace"',
        "milestone_shape" : 'milestone_shape = "diamond"',
        "leaf_shape" : 'leaf_shape = "bar"',
        "title_attrib" : 'title_attrib = "title"',
        "def create_objects" : """def create_objects(self, data):
    for t in data:
    yield t
    """,
        "def modify_widget" : """def modify_widget(self, gantt_widget, task):
    gantt_widget.text(task.to_string["%x"].start, 
    LEFT, BOTTOM - 1.5 * VSEP, 
    verticalalignment = "top",
    horizontalalignment = "center") 
    """,
        "def modify_connector" : """def modify_connector(self, src, dest, connector):
    return True
    """
        })



    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:register_editors
    def register_editors(cls, registry):
        super(Gantt, cls).register_editors(registry)
        registry.Boolean(_("Shape/show_resource..."), True)
        registry.Boolean(_("Chart/show_connectors..."), True)
        registry.Boolean(_("Shape/show_complete..."), True)
        registry.String(_("Chart/row_attrib..."), "gantt_same_row")
        registry.String(_("Chart/accumulate_attrib..."), "gantt_accumulate")
        registry.String(_("Chart/shape_attrib..."), "gantt_shape")
        registry.String(_("Chart/shape_properties_attrib..."), "gantt_properties")
        registry.Shape(_("Shape/parent_shape..."), "brace")
        registry.Symbol(_("Shape/milestone_shape..."), "diamond")
        registry.Shape(_("Shape/leaf_shape..."), "bar")
        registry.String(_("Shape/title_attrib..."), "title")

    register_editors = classmethod(register_editors)

    def create_property_groups(cls, property):
        property.set_default_groups()
        property.name_groups.append("bar.height")
        property.name_groups.append("complete.height")
        property.name_groups.append("magnification")
        property.name_groups.append("up")

        def add_group(group):
            property.fill_font_group(group)

            shape = getattr(cls, group + "_shape", "")
            if shape.find("_bar_") > 0:
                property.name_groups.append(group + ".bar.height")
                property.name_groups.append(group + ".complete.height")
                property.name_groups.append(group + ".start.magnification")
                property.name_groups.append(group + ".end.magnification")
                property.name_groups.append(group + ".start.up")
                property.name_groups.append(group + ".end.up")
                property.fill_patch_group(group + ".complete")
                property.fill_patch_group(group + ".bar")
                property.fill_patch_group(group + ".start")
                property.fill_patch_group(group + ".end")
            else:
                property.fill_patch_group(group)

            if shape == "bar":
                property.fill_patch_group(group + ".complete")
                property.fill_font_group(group + ".inside")

            elif shape in faces.charting.shapes.symbols:
                property.name_groups.append(group + ".magnification")

        add_group("parent")
        add_group("leaf")
        add_group("milestone")



    create_property_groups = classmethod(create_property_groups)
    #@nonl
    #@-node:register_editors
    #@+node:create_all_widgets
    def create_all_widgets(self, start_row):
        widgets = map(self.create_widget, self.create_objects(self.data))
        task_map = dict(map(lambda w: (w.fobj, w), widgets))

        if self.calendar is pcal._default_calendar:
            self.calendar = task_map.keys()[0].root.calendar

        self.time_scale = timescale.TimeScale(self.calendar)
        to_num = self.time_scale.to_num

        for w in widgets:
            w.start = to_num(w.start)
            w.end = to_num(w.end)

            row_task = getattr(w.fobj, self.row_attrib, None)
            if row_task and not w.fobj.is_inherited(self.row_attrib):
                row_widget = task_map.get(row_task)
                if row_widget: w.row = row_widget.row

        rows = self._finalize_row_widgets(widgets, start_row)
        if not self.show_rowlines:
            rows = filter(lambda t: t.all_artists(), rows)

        widgets.extend(rows)
        if not self.show_connectors: return widgets

        # make connectors
        connectors = []
        for w in widgets:
            if not w.fobj: continue

            try:
                sources = w.fobj._sources.iteritems()
            except AttributeError:
                sources = {}

            for dattrib, sources in sources:
                for s in sources:
                    path, sattrib = faces.task._split_path(s)
                    src_task = w.fobj.get_task(path)
                    src_widget = task_map.get(src_task)
                    if not src_widget: continue

                    connectors.append((src_widget, sattrib, w, dattrib))

        widgets.extend(self.create_connectors(connectors))
        return widgets
    #@-node:create_all_widgets
    #@+node:create_objects
    def create_objects(self, data):
        for t in data:
            if getattr(t, self.accumulate_attrib, False) \
               and t.is_inherited(self.accumulate_attrib):
                continue

            yield t
    #@-node:create_objects
    #@+node:get_property_group
    def get_property_group(self, task):
        if task.children and not getattr(task, self.accumulate_attrib, False):
            return "parent"

        if task.milestone:
            return "milestone"

        return "leaf"
    #@-node:get_property_group
    #@+node:calc_title
    def calc_title(self, task):
        """
        Calculate the task title.
        """
        if self.title_attrib:
            title = getattr(task, self.title_attrib)
        else:
            title = ""

        if self.show_resource:
            if task.booked_resource:
                title += " ("+ task.to_string.booked_resource + ")"
            elif task.performed_resource:
                title += " ("+ task.to_string.performed_resource + ")"

        return title
    #@-node:calc_title
    #@+node:create_widget
    def create_widget(self, task):
        """
        Create a gantt widget for a task.
        """
        if isinstance(task, widget.Widget): return task

        title = self.calc_title(task)
        shape_name = self.get_shape_name(task)
        props = task.__dict__.get(self.shape_properties_attrib, None)
        gantt_widget = widget.GanttWidget(task.start, task.end,
                                          task, properties=props)
        gantt_widget.row.top_sep = gantt_widget.row.bottom_sep = 3
        self.make_shape(shape_name, gantt_widget, title)
        self.modify_widget(gantt_widget, task)
        return gantt_widget
    #@-node:create_widget
    #@+node:modify_widget
    def modify_widget(self, widget, task):
        """
        Overwrite this method to decorate a widget.
        """

    modify_widget.args = (widget.GanttWidget, task.Task)
    #@nonl
    #@-node:modify_widget
    #@+node:Shape Methods
    #@+node:get_shape_name
    def get_shape_name(self, task):
        if task.children and not getattr(task, self.accumulate_attrib, False):
            shape_name = self.parent_shape
        else:
            if task.milestone:
                shape_name = self.milestone_shape
            else:
                shape_name = self.leaf_shape

        return task.__dict__.get(self.shape_attrib, shape_name)
    #@-node:get_shape_name
    #@+node:make_shape
    def make_shape(self, shape_name, gantt_widget, title, propname=None):
        """
        Assigns a shape to gantt_widget.
        """
        try:
            shape_func = getattr(self, "make_%s_shape" % shape_name)
        except AttributeError:
            if shape_name in shapes.symbols:
                self.make_symbol_shape(shape_name, gantt_widget,
                                       title, propname)
            else:
                self.make_combined_shape(shape_name, gantt_widget,
                                         title, propname)
        else:
            try:
                shape_func(gantt_widget, title, propname)
            except TypeError:
                shape_func(gantt_widget, title)
    #@-node:make_shape
    #@+node:make_combined_shape
    def make_combined_shape(self, shape_name, widget, title, propname=None):
        end_shapes = shape_name.split("_bar_")
        if len(end_shapes) != 2:
            raise ValueError("Cannot find a shape %s" % shape_name)

        left, right = end_shapes
        left = getattr(shapes, left)
        right = getattr(shapes, right)

        try:
            complete = self.show_complete and widget.fobj.complete or 0
        except AttributeError:
            complete = 0

        propname = propname or self.get_property_group(widget.fobj)
        widget.set_shape(shapes.combibar, propname, left, right, complete)
        widget.text(title, HCENTER, TOP + VSEP,
                    horizontalalignment ="center",
                    verticalalignment="bottom",
                    fontproperties=propname)
    #@-node:make_combined_shape
    #@+node:make_symbol_shape
    def make_symbol_shape(self, shape_name, widget, title, propname=None):
        propname = propname or self.get_property_group(widget.fobj)
        widget.set_shape(getattr(shapes, shape_name), propname)
        widget.text(title, RIGHT + HSEP, VCENTER,
                    horizontalalignment ="left",
                    verticalalignment="center",
                    fontproperties=propname)
    #@-node:make_symbol_shape
    #@+node:make_bar_shape
    def make_bar_shape(self, widget, title, propname=None):
        try:
            complete = self.show_complete and widget.fobj.complete or 0
        except AttributeError:
            complete = 0

        propname = propname or self.get_property_group(widget.fobj)
        widget.set_shape(shapes.bar, propname, complete)
        widget.inside_text(title, RIGHT + HSEP, VCENTER,
                           verticalalignment="center",
                           inside_properties=propname+".inside",
                           fontproperties=propname)
    #@-node:make_bar_shape
    #@+node:make_brace_shape
    def make_brace_shape(self, widget, title, propname=None):
        propname = propname or self.get_property_group(widget.fobj)
        widget.set_shape(shapes.brace, propname)
        widget.text(title, HCENTER, TOP + VSEP,
                    horizontalalignment ="center",
                    verticalalignment="bottom",
                    fontproperties=propname)
    #@-node:make_brace_shape
    #@-node:Shape Methods
    #@+node:Connector Methods
    #@+node:find_path
    def find_path(self, sa, da):
        aamap = {
            ("start", "start") : connector.StartStartPath,
            ("end", "start") : connector.EndStartPath,
            ("start", "end") : connector.StartEndPath,
            ("end", "end") : connector.EndEndPath }

        return aamap.get((sa, da)) #connector.ShortestPath
    #@-node:find_path
    #@+node:create_connectors
    def create_connectors(self, connectors):
        cws = []
        for src, sa, dest, da in connectors:
            path = self.find_path(sa, da)
            if path:
                cw = connector.GanttConnector(src, dest, path)
                if self.modify_connector(src, dest, cw):
                    cws.append(cw)

        return cws
    #@-node:create_connectors
    #@+node:modify_connector
    def modify_connector(self, src, dest, connector):
        return True

    modify_connector.args = (task.Task, task.Task, connector.GanttConnector)
    #@nonl
    #@-node:modify_connector
    #@-node:Connector Methods
    #@+node:get_tip
    def get_tip(self, tipobj):
        if not self.show_tips: return
        try:
            if isinstance(tipobj.fobj, task.Task):
                return self.get_task_tip(tipobj.fobj)
        except AttributeError:
            pass

        return None
    #@-node:get_tip
    #@+node:get_task_tip
    def get_task_tip(self, tsk):
        lines = [
            (_("Name"), tsk.title),
            (_("Timeframe"), "%s - %s" % (tsk.to_string.start,\
                                          tsk.to_string.end)),
            (_("Effort"), tsk.to_string.effort),
            (_("Length"), tsk.to_string.length),
            (_("Load"), tsk.to_string.load),
            (_("Complete"), tsk.to_string.complete),
            (_("Done"), tsk.to_string.done),
            (_("Todo"), tsk.to_string.todo)  ]

        append = lines.append
        if tsk.booked_resource:
            append((_("Resources"), tsk.to_string.booked_resource))
        elif tsk.performed_resource:
            append((_("Resources"), tsk.to_string.performed_resource))

        try:
            append((_("Buffer"), tsk.to_string.buffer))
        except task.RecursionError:
            pass

        return lines
    #@-node:get_task_tip
    #@-others

#@<< set __all__ attribute >>
#@+node:<< set __all__ attribute >>
Gantt.__all__ = filter(lambda n: getattr(getattr(Gantt, n), "im_func", None) is None, dir(Gantt))
Gantt.__all__ += [ "calc_title", "make_shape", "create_widget"  ]
Gantt.__all__ = tuple(Gantt.__all__)
#@nonl
#@-node:<< set __all__ attribute >>
#@nl

#@-node:class Gantt
#@+node:class Standard
class Standard(Gantt):
    __doc__ = _("""
      A Standard gantt chart.
      """)

    #@    @+others
    #@+node:register_editors
    def register_editors(cls, registry):
        super(Standard, cls).register_editors(registry)
        registry.Evaluation(_("Chart/data..."))


    register_editors = classmethod(register_editors)
    #@-node:register_editors
    #@-others
#@-node:class Standard
#@+node:class Critical
class Critical(Standard):
    """
    A Gantt to visualize the critical chain.

    @var colors:
    Specify a dictionary, that defines colours for different
    buffer values.
    """
    #@	<< declarations >>
    #@+node:<< declarations >>
    __type_image__ = "critical_gantt"
    show_rowlines = False
    show_connectors = True
    colors = { "0d" : "red" }

    __editor__ = ("faces.gui.edit_gantt", "Critical")
    __attrib_completions__ = Standard.__attrib_completions__.copy()
    __attrib_completions__.update({\
        "colors" : 'colors = { |"0d" : "red" }' })
    del __attrib_completions__["def modify_widget"]


    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:register_editors
    def register_editors(cls, registry):
        super(Critical, cls).register_editors(registry)
        registry.ColorMap(_("Shape/colors..."), { "0d" : "red" })


    register_editors = classmethod(register_editors)
    #@-node:register_editors
    #@+node:__init__
    def __init__(self, *args, **kwargs):
        to_minutes = pcal._default_calendar.Minutes

        self._colors = map(lambda i: (to_minutes(i[0]), i[1]),
                           self.colors.items())
        self._colors.sort()
        self._colors.reverse()

        Standard.__init__(self, *args, **kwargs)
    #@-node:__init__
    #@+node:modify_widget
    def modify_widget(self, widget, task):
        for v, c in self._colors:
            if task.buffer <= v:
                shape_name = self.get_shape_name(task)
                group = self.get_property_group(task)
                widget.set_property("%s.facecolor" % group, c)
                widget.set_property("%s.bar.facecolor" % group, c)

        return widget
    #@-node:modify_widget
    #@-others
#@-node:class Critical
#@+node:class Compare
class Compare(Gantt):
    """
    A Gantt chart for comparing different projects.

    @var colors:
    Specifies a list of different colors for each project.
    """
    #@	<< declarations >>
    #@+node:<< declarations >>
    __type_image__ = "compare_gantt"
    colors = _color_index
    show_rowlines = True
    show_connectors = False

    __editor__ = ("faces.gui.edit_gantt", "Compare")
    __attrib_completions__ = Gantt.__attrib_completions__.copy()
    __attrib_completions__.update({\
        "colors" : 'colors = ( "navy", "seagreen", "indianred")' })
    del __attrib_completions__["def create_objects"]


    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:register_editors
    def register_editors(cls, registry):
        super(Compare, cls).register_editors(registry)
        registry.ColorSet(_("Shape/colors..."), ("navy", "seagreen", "indianred"))
        registry.MultiEvaluation(_("Chart/data..."))


    register_editors = classmethod(register_editors)
    #@-node:register_editors
    #@+node:create_objects
    def create_objects(self, data):
        colors = self.colors

        for task_list in data:
            if not isinstance(task_list, (tuple, list)):
                task_list = (task_list, )

            last = len(task_list) - 1
            sum_widget = None
            sum_start = 0
            sum_end = -0
            last_widget = None

            for i, task in enumerate(task_list):
                if not task: continue

                if getattr(task, self.accumulate_attrib, False) \
                       and task.is_inherited(self.accumulate_attrib):
                    break

                if task.children:
                    if not sum_widget:
                        sum_widget = self.create_widget(task)
                        sum_start = task.start
                        sum_end = task.end
                    else:
                        sum_start = min(sum_start, task.start)
                        sum_end = max(sum_end, task.end)
                else:
                    last_widget = widget = self.create_widget(task)
                    shape_name = self.get_shape_name(task)
                    widget.set_property("facecolor", colors[i % len(colors)])
                    widget.row.show_rowline = False
                    yield widget

            if last_widget:
                last_widget.row.show_rowline = self.show_rowlines

            if sum_widget:
                sum_widget.start = sum_start
                sum_widget.end = sum_end
                yield sum_widget
    #@-node:create_objects
    #@-others
#@-node:class Compare
#@-others
#@nonl
#@-node:@file lib/gantt.py
#@-leo
