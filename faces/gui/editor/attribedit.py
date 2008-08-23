#@+leo-ver=4
#@+node:@file gui/editor/attribedit.py
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
A collection of classes and functions for editing attributes
"""
#@<< Imports >>
#@+node:<< Imports >>
import wx
import context
import re
import sys
import operator
import faces.plocale
import faces.pcalendar as pcalendar
import faces.task as ftask
import faces.charting
import metapie.dbtransient as db
import metapie.gui.views as views
import metapie.gui.grid as grid
import metapie.gui.widgets as widgets
import metapie.gui.pyeditor as pyeditor
import inspect
import textwrap
import classifiers
import datetime
from metapie.gui import controller
import editorlib
try:
    set
except NameError:
    from sets import Set as set
#@-node:<< Imports >>
#@nl

_is_source_ = True
_ = faces.plocale.get_gettext()

#@+others
#@+node:Token definitions
tok_identifier = r"([a-zA-Z_][a-zA-Z0-9_]*)"
tok_path = r"(ident(\.ident)*)".replace("ident", tok_identifier)
tok_assignment = r"^(path)\s*=".replace("path", tok_path)
tok_identifier_assignment = r"%s\s*(?P<project>%s)\(" % (tok_assignment, tok_identifier)

reg_assignment = re.compile(tok_assignment)
reg_identifier_assignment = re.compile(tok_identifier_assignment)
reg_identifier = re.compile(tok_identifier + "$")
reg_path = re.compile(tok_path + "$")
#@-node:Token definitions
#@+node:get_code_root
def get_code_root(code_item):
    item = code_item
    while item:
        last = item
        item = item.get_parent()

    return last
#@nonl
#@-node:get_code_root
#@+node:class Evaluator
class Evaluator(object):
    def __init__(self, expression, context):
        try:
            editor = context.code_item.editor
            self.attributes = editor.eval_expression(expression, context=context)
        except Exception, e:
            self.error = e




#@-node:class Evaluator
#@+node:Types
#@+node:class ResourceNames
class ResourceNames(db.Enumerate):
    def __init__(self):
        super(ResourceNames, self).__init__({"" : ""})


    def fill(self, model):
        encoding = model.get_encoding()
        self.choices.clear()

        for d, r in model.resources.iteritems():
            if r.name != "Resource":
                self.choices[d] = r.title.decode(encoding)


#@-node:class ResourceNames
#@+node:class EvaluationNames
class EvaluationNames(db.Enumerate):
    def __init__(self):
        super(EvaluationNames, self).__init__({"" : ""})


    def fill(self, model):
        self.choices.clear()

        for k, v in model.evaluations.iteritems():
            self.choices[k] = k
#@-node:class EvaluationNames
#@-node:Types
#@+node:Widgets
#@+node:class SymbolCombo
class SymbolCombo(widgets.Combo):
    def __init__(self, *args, **kwargs):
        widgets.Combo.__init__(self, *args, **kwargs)
        map(self.Append, faces.charting.shapes.symbols)
#@nonl
#@-node:class SymbolCombo
#@+node:class ShapeCombo
class ShapeCombo(widgets.Combo):
    def __init__(self, *args, **kwargs):
        widgets.Combo.__init__(self, *args, **kwargs)

        symbols = faces.charting.shapes.symbols
        shapes = ["%s_bar_%s" % (i, j) for i in symbols for j in symbols]
        shapes.append("bar")
        shapes.append("brace")
        shapes.sort()
        map(self.Append, shapes)
#@nonl
#@-node:class ShapeCombo
#@+node:class BoolEnum
class BoolEnum(widgets.Enumerate):
    __type__ = db.Boolean

    def get_choices(self, itype):
        return { False : _("False"), True : _("True") }

#@-node:class BoolEnum
#@-node:Widgets
#@+node:Models and Views
#@+node:SimpleContainer
#@+node:class SimpleContainer
class SimpleContainer(db.Model):
    attrib_name = db.Text()
    child = db.Model.type()
    error = db.Text()
    #@    @+others
    #@+node:__init__
    def __init__(self, child_model, context, attrib_name, evaluator, default):
        self.attrib_name = attrib_name
        self.code_item = code_item = context.code_item
        #@    << calculate attribute value >>
        #@+node:<< calculate attribute value >>
        attribs = code_item.editor.get_attribs(self.code_item)
        if self.attrib_name in attribs:
            line = attribs[self.attrib_name]
            expression = code_item.editor.get_expression(line)
        else:
            expression = ""

        evaluation = evaluator(expression, context)
        try:
            self.error = "%s: %s" % (evaluation.error.__class__.__name__, \
                                     str(evaluation.error))
            value = default
        except AttributeError:
            if expression:
                value = evaluation.attributes.get(attrib_name) 
            else:
                value = default

        #@-node:<< calculate attribute value >>
        #@nl
        self.child = child_model(code_item, attrib_name, value)

    #@-node:__init__
    #@+node:show
    def show(self):
        #no wizzard while processing
        if controller().is_processing(): return

        dlg = editorlib.PatchedDialog(controller().frame,  -1, 
                _("Edit %s") % self.attrib_name,
                style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        dlg.SetClientSize((10, 10))
        view = self.constitute()(dlg)
        view.layout()
        dlg.simulate_modal(self.code_item.editor)
    #@nonl
    #@-node:show
    #@+node:code
    def code(self):
        return "%s = %s" % (self.attrib_name, unicode(self.child))
    #@nonl
    #@-node:code
    #@+node:realize
    def realize(self):
        editor = self.code_item.editor
        attribs = editor.get_attribs(self.code_item)
        if self.attrib_name in attribs:
            editor.replace_expression(self.code(), attribs[self.attrib_name])
        else:
            editor.insert_expression(self.code_item, self.code())
    #@-node:realize
    #@-others
#@nonl
#@-node:class SimpleContainer
#@+node:class SimpleView
class SimpleView(editorlib.MainView):
    __model__ = SimpleContainer
    __view_name__ = "default"
    vgap = 0

    format = _("""
error(Static)
lbl_error
child>
(0,3)>
-->
(0,3)
(buttons)>
""")

    #@    @+others
    #@+node:prepare
    def prepare(self):
        self.grow_col(-1)
        self.grow_row(2)
        self.buttons.grow_col(0)
        self.error.Hide()
        self.error.SetForegroundColour(self.error_colour)
    #@nonl
    #@-node:prepare
    #@+node:constitute
    def constitute(self, imodel):
        super(SimpleView, self).constitute(imodel)
        if imodel.error: self.error.Show()
    #@-node:constitute
    #@-others
#@nonl
#@-node:class SimpleView
#@-node:SimpleContainer
#@+node:Values
#@+node:Delta
#@+node:class Delta
class Delta(db.Model):
    days = db.Float(width=5, precision=1)
    hours = db.Float(width=4, precision=1) 
    minutes = db.Int()
    is_duration = False

    #@    @+others
    #@+node:__init__
    def __init__(self, code_item, attrib, value):
        super(Delta, self).__init__()
        try:
            self.to_delta = code_item.obj._to_delta
        except AttributeError:
            self.to_delta = pcalendar.Minutes

        #@    << find best value >>
        #@+node:<< find best value >>
        try:
            value = self.to_delta(value).to_timedelta(self.is_duration)
        except ValueError:
            try:
                value = getattr(code_item.obj, attrib).to_timedelta(self.is_duration)
            except AttributeError:
                value = datetime.timedelta()
        #@nonl
        #@-node:<< find best value >>
        #@nl
        self.minutes = (value.seconds / 60) % 60
        self.hours = value.seconds / 3600
        self.days = value.days
    #@nonl
    #@-node:__init__
    #@+node:__str__
    def __str__(self):
        td = datetime.timedelta(days=self.__days, 
                                hours=self.__hours, 
                                minutes=self.__minutes)
        return '"%s"' % self.to_delta(td, self.is_duration)\
                            .strftime(is_duration=self.is_duration)
    #@nonl
    #@-node:__str__
    #@-others
#@-node:class Delta
#@+node:class Duration
class Duration(Delta):
    is_duration = True
#@nonl
#@-node:class Duration
#@+node:class DeltaView
class DeltaView(views.FormView):
    __model__ = Delta
    __view_name__ = "default"
    vgap = 0

    format = _("""
days|[Days ]|hours|[Hours ]|minutes|[Minutes]
""")
#@nonl
#@-node:class DeltaView
#@-node:Delta
#@+node:Date
#@+node:class Date
class Date(db.Model):
    value = db.DateTime()

    #@    @+others
    #@+node:__init__
    def __init__(self, code_item, attrib, value):
        super(Date, self).__init__()

        to_date = pcalendar.to_datetime

        try:
            value = to_date(value)
        except ValueError:
            #@        << try alternatives >>
            #@+node:<< try alternatives >>
            try:
                value = to_date(getattr(code_item.obj, attrib))
            except AttributeError:
                value = datetime.datetime.now()
            #@nonl
            #@-node:<< try alternatives >>
            #@nl
        except TypeError:
            #@        << try alternatives >>
            #@+node:<< try alternatives >>
            try:
                value = to_date(getattr(code_item.obj, attrib))
            except AttributeError:
                value = datetime.datetime.now()
            #@nonl
            #@-node:<< try alternatives >>
            #@nl

        self.value = value
    #@nonl
    #@-node:__init__
    #@+node:__str__
    def __str__(self):
        return '"%s"' % self.__value.strftime("%x %H:%M")
    #@-node:__str__
    #@-others
#@nonl
#@-node:class Date
#@+node:class DateView
class DateView(views.FormView):
    __model__ = Date
    __view_name__ = "default"
    vgap = 0
    format = "value"
#@nonl
#@-node:class DateView
#@-node:Date
#@+node:Float
#@+node:class Float
class Float(db.Model):
    value = db.Float()

    #@    @+others
    #@+node:__init__
    def __init__(self, code_item, attrib, value):
        super(Float, self).__init__()
        self.value = float(value or 0.0)
    #@nonl
    #@-node:__init__
    #@+node:__str__
    def __str__(self):
        return '%.02f' % self.__value
    #@-node:__str__
    #@-others
#@nonl
#@-node:class Float
#@+node:class FloatView
class FloatView(views.FormView):
    __model__ = Float
    __view_name__ = "default"
    vgap = 0
    format = "value"
#@nonl
#@-node:class FloatView
#@-node:Float
#@+node:Int
#@+node:class Int
class Int(db.Model):
    value = db.Int()

    #@    @+others
    #@+node:__init__
    def __init__(self, code_item, attrib, value):
        super(Int, self).__init__()
        self.value = int(value or 0)
    #@nonl
    #@-node:__init__
    #@+node:__str__
    def __str__(self):
        return '%i' % self.__value
    #@-node:__str__
    #@-others
#@nonl
#@-node:class Int
#@+node:class IntView
class IntView(views.FormView):
    __model__ = Int
    __view_name__ = "default"
    vgap = 0
    format = "value"
#@nonl
#@-node:class IntView
#@-node:Int
#@+node:Boolean
#@+node:class Boolean
class Boolean(db.Model):
    value = db.Boolean()

    #@    @+others
    #@+node:__init__
    def __init__(self, code_item, attrib, value):
        super(Boolean, self).__init__()
        self.value = bool(value)

    #@-node:__init__
    #@+node:__str__
    def __str__(self):
        return self.__value and "True" or "False"
    #@-node:__str__
    #@-others
#@nonl
#@-node:class Boolean
#@+node:class BooleanView
class BooleanView(views.FormView):
    __model__ = Boolean
    __view_name__ = "default"
    vgap = 0
    format = "value(BoolEnum)"

#@-node:class BooleanView
#@-node:Boolean
#@+node:String
#@+node:class String
class String(db.Model):
    value = db.Text()

    #@    @+others
    #@+node:__init__
    def __init__(self, code_item, attrib, value):
        super(String, self).__init__()
        self.value = value
    #@nonl
    #@-node:__init__
    #@+node:__str__
    def __str__(self):
        return '"%s"' % self.value
    #@-node:__str__
    #@-others
#@nonl
#@-node:class String
#@+node:class StringView
class StringView(views.FormView):
    __model__ = String
    __view_name__ = "default"
    vgap = 0
    format = "value>"

    def prepare(self):
        self.grow_col(0)
#@-node:class StringView
#@-node:String
#@+node:Symbol
class Symbol(String): pass
class SymbolView(StringView):
    __model__ = Symbol
    __view_name__ = "default"
    format = "value(SymbolCombo)>"

#@-node:Symbol
#@+node:Shape
class Shape(String): pass
class ShapeView(StringView):
    __model__ = Shape
    __view_name__ = "default"
    format = "value(ShapeCombo)>"

#@-node:Shape
#@+node:MultiText
#@+node:class MultiText
class MultiText(db.Model):
    value = db.Text(multi_line=True)

    #@    @+others
    #@+node:__init__
    def __init__(self, code_item, attrib, value):
        super(MultiText, self).__init__()
        self.value = textwrap.dedent(value or "").strip("\n").decode("utf8")
    #@nonl
    #@-node:__init__
    #@+node:__str__
    def __str__(self):
        return '"""\n%s\n"""' % self.__value
    #@nonl
    #@-node:__str__
    #@-others
#@nonl
#@-node:class MultiText
#@+node:class MultiTextView
class MultiTextView(views.FormView):
    __model__ = MultiText
    __view_name__ = "default"
    vgap = 0
    format = "value>"

    #@    @+others
    #@+node:prepare
    def prepare(self):
        self.grow_col(0)
        self.grow_row(0)
        self.value.set_width("X" * 50)
        self.value.set_height(20)
    #@nonl
    #@-node:prepare
    #@-others
#@nonl
#@-node:class MultiTextView
#@-node:MultiText
#@+node:DateTimeRanges
#@+node:class DateTimeRange
class DateTimeRange(db.Model):
    start = db.DateTime(format="HHMM")
    end = db.DateTime(format="HHMM")

    #@    @+others
    #@+node:__init__
    def __init__(self, **kwargs):
        super(DateTimeRange, self).__init__(**kwargs)
        if not kwargs.has_key("start"):
            self.start = datetime.datetime.now()
    #@nonl
    #@-node:__init__
    #@+node:_set_start
    def _set_start(self, value):
        self.end = value.replace(hour=0, minute=0) \
                   + datetime.timedelta(days=1)
        return value
    #@nonl
    #@-node:_set_start
    #@+node:__str__
    def __str__(self):
        return '("%s", "%s")' \
                % (self.start.strftime("%x %H:%M"), 
                   self.end.strftime("%x %H:%M"))
    #@nonl
    #@-node:__str__
    #@-others
#@nonl
#@-node:class DateTimeRange
#@+node:class DateTimeRanges
class DateTimeRanges(db.Model):
    #@    @+others
    #@+node:__init__
    def __init__(self, code_item, attrib, value):
        super(DateTimeRanges, self).__init__()
        to_datetime = pcalendar.to_datetime
        for start, end in value or ():
            self.ranges.insert(DateTimeRange(start=to_datetime(start), 
                                             end=to_datetime(end)))
    #@nonl
    #@-node:__init__
    #@+node:__str__
    def __str__(self):
        ranges = map(str, self.ranges)
        return "[%s]" % ",\n".join(ranges)
    #@nonl
    #@-node:__str__
    #@-others

db.Relation("tr",
            db.End(DateTimeRange, "ranges", multi='*'),
            db.End(DateTimeRanges))
#@nonl
#@-node:class DateTimeRanges
#@+node:class TimeRangesView
class DateTimeRangeGrid(grid.EditGrid, views.GridView):
    __model__ = DateTimeRange
    columns = ((__model__.start, _("From")),
               (__model__.end, _("To")))
    resize_col = 0


class DateTimeRangesView(views.FormView):
    __model__ = DateTimeRanges
    __view_name__ = "default"
    vgap = 0
    format = """
ranges>
delete
"""

    #@    @+others
    #@+node:create_controls
    def create_controls(self):
        self.ranges = self.get_control("ranges(DateTimeRangeGrid)")
        self.delete = self.ranges.get_delete_button(self)
    #@nonl
    #@-node:create_controls
    #@+node:prepare
    def prepare(self):
        self.grow_col(0)
        self.grow_row(0)
    #@nonl
    #@-node:prepare
    #@-others
#@nonl
#@-node:class TimeRangesView
#@-node:DateTimeRanges
#@+node:WorkingTimes
#@+node:WorkingTime
def weekdays():
    dt = faces.pcalendar.Calendar.EPOCH
    return dict(map(lambda d: (d - 1, dt.replace(day=d).strftime("%A")),
                    range(1, 8)))


class WorkingTime(db.Model):
    day = db.Enumerate(weekdays())
    start = db.Time(format="HHMM")
    end = db.Time(format="HHMM")
#@nonl
#@-node:WorkingTime
#@+node:WorkingTimes
class WorkingTimes(db.Model):
    #@    @+others
    #@+node:__init__
    def __init__(self, code_item, attrib, value):
        super(WorkingTimes, self).__init__()

        cal = pcalendar.Calendar()
        for item in value or ():
            cal.set_working_days(*item)

        default = pcalendar.DEFAULT_WORKING_DAYS
        for d in range(0, 7):
            slots = cal.working_times.get(d, default[d])
            for start, end in slots:
                start = datetime.time(start / 60, start % 60)
                end = datetime.time(end / 60, end % 60)
                self.workingtimes.insert(\
                    WorkingTime(day = d, start=start, end=end))
    #@nonl
    #@-node:__init__
    #@+node:__str__
    def __str__(self):
        day_names = ("mon",  "tue", "wed", "thu", "fri", "sat", "sun")
        day_times = {}
        for t in self.workingtimes:
            start, end = t.start.strftime("%H:%M"), t.end.strftime("%H:%M")
            day_times.setdefault(t.day, []).append('"%s-%s"' % (start, end))

        tr = []
        def make_day(day):
            try:
                return '("%s", %s)' % (day_names[day], 
                                       ", ".join(day_times[day]))
            except KeyError:
                return '("%s", ())' % day_names[day]

        tr = map(make_day, range(0, 7))
        return '[%s]' % ",\n".join(tr)
    #@nonl
    #@-node:__str__
    #@-others

db.Relation("workingtime",
            db.End(WorkingTime, "workingtimes", multi='*'),
            db.End(WorkingTimes))
#@nonl
#@-node:WorkingTimes
#@+node:WorkingTimesView
class WorkingTimesView(views.FormView):
    __model__ = WorkingTimes
    __view_name__ = "default"
    vgap = 0
    format = """
workingtimes>
delete
"""
    def create_controls(self):
        self.workingtimes = self.get_control("workingtimes(WorkingTimeGrid)")
        self.delete = self.workingtimes.get_delete_button(self)

    def prepare(self):
        self.grow_col(0)
        self.grow_row(0)
#@nonl
#@-node:WorkingTimesView
#@+node:WorkingTimeGrid
class WorkingTimeGrid(grid.EditGrid, views.GridView):
    __model__ = WorkingTime
    columns = ((__model__.day, _("Day")),
               (__model__.start, _("From")),
               (__model__.end, _("To")))
    resize_col = 0
#@nonl
#@-node:WorkingTimeGrid
#@-node:WorkingTimes
#@+node:Resources
#@+node:class Resource
class Resource(db.Model):
    name = ResourceNames()
    load = db.Float(precision=2, default=1.0)
    efficiency = db.Float(precision=2, default=1.0)

    def __init__(self, resource=None):
        super(Resource, self).__init__()
        if resource is None:
            self.load = 1.0
            self.efficiency = 1.0
            self.name = self.__attributes_map__["name"].default()
        else:
            self.name = resource.name
            self.load = getattr(resource, "load", 1.0)
            self.efficiency = resource.efficiency


    def __str__(self):
        src = self.parent.model.resources[self.name]

        args = []
        if self.load != 1.0:
            args.append("load=%.02f" % self.load)

        if self.efficiency != src.efficiency:
            args.append("efficiency=%.02f" % self.efficiency)

        if args: return "%s(%s)" % (self.name, ", ".join(args))
        return self.name
#@nonl
#@-node:class Resource
#@+node:class ResourceSet
class ResourceSet(db.Model):
    #@    @+others
    #@+node:__init__
    def __init__(self, code_item, attrib, value):
        super(ResourceSet, self).__init__()
        self.model = code_item.editor.model
        Resource.__attributes_map__["name"].fill(self.model)

        for r in value and value()._get_resources(0) or ():
            self.resources.insert(Resource(r))
    #@nonl
    #@-node:__init__
    #@+node:__str__
    def __str__(self):
        return " & ".join(map(str, self.resources))
    #@nonl
    #@-node:__str__
    #@+node:check_constraints
    def check_constraints(self):
        error = db.ConstraintError()

        res = { }
        for r in self.resources:
            if r.name in res:
                error.message["resources"] = \
                      _("Resource '%s' is specified twice.") \
                      % r.name
                break

            res[r.name] = True

        if error.message:
            raise error
    #@nonl
    #@-node:check_constraints
    #@-others

db.Relation("resources",
            db.End(Resource, "resources", multi='*'),
            db.End(ResourceSet, "parent", multi=1))
#@nonl
#@-node:class ResourceSet
#@+node:class ResourceSetView
class ResourceSetView(views.FormView):
    __model__ = ResourceSet
    __view_name__ = "default"
    vgap = 0
    format = """
resources>
delete
"""
    def create_controls(self):
        self.resources = self.get_control("resources(ResourceGrid)")
        self.delete = self.resources.get_delete_button(self)

    def prepare(self):
        self.grow_col(0)
        self.grow_row(0)
#@nonl
#@-node:class ResourceSetView
#@+node:class ResourceGrid
class ResourceGrid(grid.EditGrid, views.GridView):
    __model__ = Resource
    columns = ((__model__.name, _("Resource")),
               (__model__.load, _("Load")),
               (__model__.efficiency, _("Efficiency")))
    resize_col = 0
#@nonl
#@-node:class ResourceGrid
#@-node:Resources
#@+node:ColorSet
#@+node:class Color
class Color(db.Model):
    value = db.Text()

    def __str__(self):
        return '"%s"' % self.value

#@-node:class Color
#@+node:class ColorGrid
class ColorGrid(grid.EditGrid, views.GridView):
    __model__ = Color
    columns = (("value(Color)", _("Value")),)
    resize_col = 0
#@nonl
#@-node:class ColorGrid
#@+node:class ColorSet
class ColorSet(db.Model):
    def __init__(self, code_item, attrib, value):
        super(ColorSet, self).__init__()
        for c in value or ():
            self.colors.insert(Color(value=c))


    def __str__(self):
        return "[%s]" % ", ".join(map(str, self.colors))


db.Relation("colors",
            db.End(Color, "colors", multi='*'),
            db.End(ColorSet))
#@nonl
#@-node:class ColorSet
#@+node:class ColorSetView
class ColorSetView(views.FormView):
    __model__ = ColorSet
    __view_name__ = "default"
    vgap = 0
    format = """
colors>
delete
"""
    def create_controls(self):
        self.colors = self.get_control("colors(ColorGrid)")
        self.delete = self.colors.get_delete_button(self)

    def prepare(self):
        self.grow_col(0)
        self.grow_row(0)
#@nonl
#@-node:class ColorSetView
#@-node:ColorSet
#@+node:TwoColorSet
#@+node:class TwoColor
class TwoColor(db.Model):
    face = db.Text()
    text = db.Text()

    def __str__(self):
        return '("%s", "%s")' % (self.face, self.text)

#@-node:class TwoColor
#@+node:class TwoColorGrid
class TwoColorGrid(grid.EditGrid, views.GridView):
    __model__ = TwoColor
    columns = (("face(Color)", _("Face")),
               ("text(Color)", _("Text")))
    resize_col = 1
#@nonl
#@-node:class TwoColorGrid
#@+node:class TwoColorSet
class TwoColorSet(db.Model):
    def __init__(self, code_item, attrib, value):
        super(TwoColorSet, self).__init__()
        for face, text in value or ():
            self.colors.insert(TwoColor(face=face, text=text))


    def __str__(self):
        return "[%s]" % ",\n".join(map(str, self.colors))


db.Relation("colors",
            db.End(TwoColor, "colors", multi='*'),
            db.End(TwoColorSet))
#@nonl
#@-node:class TwoColorSet
#@+node:class ColorSetView
class TwoColorSetView(views.FormView):
    __model__ = TwoColorSet
    __view_name__ = "default"
    vgap = 0
    format = """
colors>
delete
"""
    def create_controls(self):
        self.colors = self.get_control("colors(ColorGrid)")
        self.delete = self.colors.get_delete_button(self)

    def prepare(self):
        self.grow_col(0)
        self.grow_row(0)
#@nonl
#@-node:class ColorSetView
#@-node:TwoColorSet
#@+node:ColorMap
#@+node:class ColorLimit
class ColorLimit(db.Model):
    limit = db.Text()
    color = db.Text()

    def check_constraints(self):
        error = db.ConstraintError()
        try:
            faces.pcalendar.to_timedelta(self.limit)
        except ValueError, e:
            error.message["limit"] = str(e)
            raise error


    def __str__(self):
        return '"%s" : "%s"' % (self.limit, self.color)
#@-node:class ColorLimit
#@+node:class ColorLimitGrid
class ColorLimitGrid(grid.EditGrid, views.GridView):
    __model__ = ColorLimit
    columns = (("limit", _("< Limit")),
               ("color(Color)", _("Color")))
    resize_col = 0
#@-node:class ColorLimitGrid
#@+node:class ColorMap
class ColorMap(db.Model):
    def __init__(self, code_item, attrib, value):
        super(ColorMap, self).__init__()
        for limit, color in value.iteritems() or ():
            self.colors.insert(ColorLimit(limit=limit, color=color))


    def __str__(self):
        return "{%s}" % ",\n".join(map(str, self.colors))


db.Relation("colors",
            db.End(ColorLimit, "colors", multi='*'),
            db.End(ColorMap))
#@nonl
#@-node:class ColorMap
#@+node:class ColorMapView
class ColorMapView(views.FormView):
    __model__ = ColorMap
    __view_name__ = "default"
    vgap = 0
    format = """
colors>
delete
"""
    def create_controls(self):
        self.colors = self.get_control("colors(ColorGrid)")
        self.delete = self.colors.get_delete_button(self)

    def prepare(self):
        self.grow_col(0)
        self.grow_row(0)
#@nonl
#@-node:class ColorMapView
#@-node:ColorMap
#@-node:Values
#@-node:Models and Views
#@+node:Editors
#@+node:SingletonEditor
class SingletonEditor(db.Model, context.ItemEditor):
    title = ""

    #@    @+others
    #@+node:Editor Interface
    #@+node:apply
    def apply(self, expression, code_item):
        return False
    #@-node:apply
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        return "extra"
    #@-node:apply_browser_menu
    #@+node:activate
    def activate(self, context):
        """
        activates the editor.
        """
        if controller().is_processing(): return

        self.context = context
        self.init_attributes()
        dlg = editorlib.PatchedDialog(controller().frame,  -1, self.title,
                style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        dlg.SetClientSize((10, 10))
        view = self.constitute()(dlg)
        view.layout()
        dlg.simulate_modal(context.code_item.editor)
        return self
    #@-node:activate
    #@-node:Editor Interface
    #@+node:Internals
    #@+node:realize
    def realize(self):
        self.realize_code()
        del self.context
        self.detach_all()
    #@nonl
    #@-node:realize
    #@+node:cancel
    def cancel(self):
        del self.context
        self.detach_all()
    #@nonl
    #@-node:cancel
    #@-node:Internals
    #@+node:Overwrites
    #@+node:init_attributes
    def init_attributes(self):
        raise RuntimeError("abstract")
    #@nonl
    #@-node:init_attributes
    #@+node:realize_code
    def realize_code(self):
        raise RuntimeError("abstract")
    #@-node:realize_code
    #@-node:Overwrites
    #@-others
#@nonl
#@-node:SingletonEditor
#@+node:Evaluation Editors
#@+node:print_evaluation_references
def print_evaluation_references(code_item, outstream=None):
    outstream = outstream or sys.stdout
    ename = code_item.name
    m = code_item.editor.model
    print >> outstream, _('The following lines reference to "%s":') % ename
    for ci, line, in code_item.editor.find_evaluation_references(code_item):
        print >> outstream, _('   object: "%s", File "%s", line %i') % (str(ci), m.path, line + 1)

    print >> outstream
#@nonl
#@-node:print_evaluation_references
#@+node:class EvaluationReferencePrinter
class EvaluationReferencePrinter(object):
    __icon__ = "list16"

    #@    @+others
    #@+node:apply
    def apply(self, expression, code_item):
        return False
    #@-node:apply
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        return "extra"
    #@-node:apply_browser_menu
    #@+node:activate
    def activate(self, context):
        print_evaluation_references(context.code_item)
    #@-node:activate
    #@-others
#@-node:class EvaluationReferencePrinter
#@+node:class EvaluationRemover
class EvaluationRemover(object):
    __icon__ = "delete16"

    #@    @+others
    #@+node:apply
    def apply(self, expression, code_item):
        return False
    #@-node:apply
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        return "extra"
    #@-node:apply_browser_menu
    #@+node:activate
    def activate(self, context):
        code_item = context.code_item

        if list(code_item.editor.find_evaluation_references(code_item)):
            print_evaluation_references(context.code_item, sys.stderr)
            print >> sys.stderr, _("You have to remove those references before removing the evaluation!\n")
        else:
            code_item.remove()
    #@-node:activate
    #@-others
#@nonl
#@-node:class EvaluationRemover
#@+node:class ProjectEditorMixin
class ProjectEditorMixin(object):
    __icon__ = "edit16"

    #@    @+others
    #@+node:Attribute Manipulation
    #@+node:_set_project
    def _set_project(self, value):
        return value
    #@nonl
    #@-node:_set_project
    #@+node:_set_scenario
    def _set_scenario(self, value):
        return value
    #@nonl
    #@-node:_set_scenario
    #@-node:Attribute Manipulation
    #@+node:apply
    def apply(self, expression, code_item):
        if not expression: return False

        mo = reg_identifier_assignment.search(expression)
        if not mo: return False

        pname = mo.groupdict()["project"]
        return self.__class__.__name__.startswith(pname)


    #@-node:apply
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        if classifiers.is_evaluation(code_item): 
            expr = code_item.editor.get_expression(code_item.get_line())
            if re.search(r"\WProject\W", expr): return "extra"
        return ""
    #@nonl
    #@-node:apply_browser_menu
    #@+node:init_attributes
    def init_attributes(self):
        code_item = self.context.code_item
        self.name = code_item.name

        editor = code_item.editor
        expr = editor.get_expression(code_item.get_line())
        dict = editor.eval_expression(expr, context=self.context)

        try:
            module = editor.get_module()
            obj = eval("module.%s" % code_item.name)
        except AttributeError:
            try:
                obj = dict[code_item.name]
            except KeyError:
                obj = None


        if obj:
            self.scenario = obj.scenario
            self.project = obj._function.__name__
            self.id = obj.id
        else:
            self.scenario = "_default"
            self.project = ""

        return obj

    #@-node:init_attributes
    #@+node:realize_code
    def realize_code(self):
        code = str(self)
        code_item = self.context.code_item
        editor = code_item.editor
        editor.BeginUndoAction()
        if code_item.name != self.name:
            #name has changed ==> change the name in all references
            old_name = code_item.name

            iterator = editor.find_evaluation_references(code_item)
            refs = dict([ (line, ci) for ci, line in iterator ])
            for line in refs.keys():
                start = editor.PositionFromLine(line)
                end = editor.GetLineEndPosition(line)
                editor.SetTargetStart(start)
                editor.SetTargetEnd(end)
                text = editor.GetTextRange(start, end)
                editor.ReplaceTarget(text.replace(old_name, self.name))

        code_item.editor.replace_expression(code, code_item.get_line())

        editor.EndUndoAction()
    #@-node:realize_code
    #@-others

#@-node:class ProjectEditorMixin
#@+node:class ProjectCreator
class ProjectCreator(SingletonEditor):
    name = db.Text()
    scenario = db.Text()
    id = db.Text()
    project = db.Text()
    title = _("Create Project")

    #@    @+others
    #@+node:apply
    def apply(self, expression, code_item):
        return not expression
    #@-node:apply
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        return "create"
    #@nonl
    #@-node:apply_browser_menu
    #@+node:init_attributes
    def init_attributes(self):
        self.scenario = "_default"
        self.project = ""
        self.name = ""
        self.id = ""

    #@-node:init_attributes
    #@+node:Attribute Manipulation
    #@+node:_construct_name
    def _construct_name(self, project=None, scenario=None):
        project = project or self.project
        scenario = scenario or self.scenario
        if scenario == "_default": scenario = "default"
        if not project: return ""
        return "%s.%s" % (project, scenario)
    #@nonl
    #@-node:_construct_name
    #@+node:_set_project
    def _set_project(self, value):
        if not self.name or self.name == self._construct_name():
            self.name = self._construct_name(project=value)

        if self.id == self.project or not self.id:
            self.id = value

        return value
    #@-node:_set_project
    #@+node:_set_scenario
    def _set_scenario(self, value):
        if not self.name or self.name == self._construct_name():
            self.name = self._construct_name(scenario=value)

        return value
    #@nonl
    #@-node:_set_scenario
    #@-node:Attribute Manipulation
    #@+node:check_constraints
    def check_constraints(self):
        error = db.ConstraintError()
        if not reg_path.match(self.name):
            error.message["name"] = _("Name is not a valid identifier")

        if not reg_path.match(self.project):
            error.message["project"] = _("project is not a valid identifier")

        if not reg_identifier.match(self.id):
            error.message["id"] = _("id is not a valid identifier")

        if error.message:
            raise error
    #@nonl
    #@-node:check_constraints
    #@+node:realize_code
    def realize_code(self):
        code = str(self)
        context = self.context.__class__(self.context.get_last_code_item())
        context.append_item(code, 0, prespace="\n")
    #@nonl
    #@-node:realize_code
    #@+node:__str__
    def __str__(self):
        return '%s = Project(%s, "%s", "%s")' \
                % (self.name, self.project, self.scenario, self.id)
    #@-node:__str__
    #@-others
#@-node:class ProjectCreator
#@+node:class ProjectEditor
class ProjectEditor(ProjectEditorMixin, ProjectCreator):
    title = _("Edit Project")

    #@    @+others
    #@-others
#@nonl
#@-node:class ProjectEditor
#@+node:class ProjectView
class ProjectView(editorlib.MainView):
    __model__ = ProjectCreator
    __view_name__ = "default"

    format = _("""
[Project: ] |project(Combo)>
[Scenario: ]|scenario(Combo)>
[Name: ]    |name>
[Id: ]      |id>
-->
(buttons)>
""")

    #@    @+others
    #@+node:prepare
    def prepare(self):
        self.grow_col(-1)
        self.grow_row(-2)
        self.buttons.grow_col(0)
    #@nonl
    #@-node:prepare
    #@+node:constitute
    def constitute(self, imodel):
        super(ProjectView, self).constitute(imodel)

        #@    << fill project combo >>
        #@+node:<< fill project combo >>
        self.project_map = {}
        editor = imodel.context.code_item.editor
        module = editor.get_module()
        ismodule = inspect.ismodule
        val_name_map = dict([ (v, k) for k, v in module.__dict__.iteritems() 
                              if ismodule(v)])

        for m in controller().get_planbuffers():
            if editor.model.path != m.path:
                import_module = m.editor.get_module()
                try:
                    # get modules import name            
                    prefix = val_name_map[import_module] + "."
                except KeyError:
                    continue
            else:
                prefix = ""

            for item in m.editor.editor.code_items:
                if item.indent == 0 \
                    and item.obj_type == pyeditor.FUNCTION \
                    and not item.get_args():
                    try:
                        if not isinstance(item.obj, ftask._ProjectBase): continue
                    except AttributeError: pass
                    self.project_map[prefix + item.name] = item

        projects = self.project_map.keys()
        projects.sort()
        self.project.Clear()
        for p in projects:
            self.project.Append(p)
        #@nonl
        #@-node:<< fill project combo >>
        #@nl

        self.scenario.Clear()
        self.scenario.Append("_default")
    #@nonl
    #@-node:constitute
    #@+node:state_changed
    def state_changed(self, attrib):
        if attrib == "project":
            self.scenario.Clear()
            try:
                item = self.project_map[self.imodel.project]
            except KeyError:
                self.scenario.Append("_default")
            else:
                try:
                    all_scenarios = list(item.obj.all_scenarios)
                except AttributeError:
                    self.scenario.Append("_default")
                else:
                    all_scenarios.sort()
                    for s in all_scenarios:
                        self.scenario.Append(s)
    #@nonl
    #@-node:state_changed
    #@-others
#@nonl
#@-node:class ProjectView
#@+node:class BalancedProjectCreator
class BalancedProjectCreator(ProjectCreator):
    balance = db.Enumerate(ftask._allocator_strings)
    performed = db.Text()
    title = _("Create BalancedProject")

    #@    @+others
    #@+node:init_attributes
    def init_attributes(self):
        super(BalancedProjectCreator, self).init_attributes()
        self.balancing = ftask.SMART
        self.performed = ""
    #@-node:init_attributes
    #@+node:__str__
    def __str__(self):
        balance = ftask._allocator_strings[self.balance]
        if self.performed:
            return '%s = BalancedProject(%s, "%s", "%s", %s, %s)' \
                    % (self.name, self.project, self.scenario, 
                       self.id, balance, self.performed)
        else:
            return '%s = BalancedProject(%s, "%s", "%s", %s)' \
                    % (self.name, self.project, self.scenario, 
                       self.id, balance)

    #@-node:__str__
    #@+node:check_constraints
    def check_constraints(self):
        try:
            super(BalancedProjectCreator, self).check_constraints()
        except db.ConstraintError, error:
            pass
        else:
            error = db.ConstraintError()

        if self.performed and not reg_path.match(self.performed):
            error.message["performed"] = _("performed is not a valid identifier")

        if error.message:
            raise error
    #@nonl
    #@-node:check_constraints
    #@-others
#@nonl
#@-node:class BalancedProjectCreator
#@+node:class BalancedProjectEditor
class BalancedProjectEditor(ProjectEditorMixin, BalancedProjectCreator):
    title = _("Edit BalancedProject")
    #@    @+others
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        if classifiers.is_evaluation(code_item): 
            expr = code_item.editor.get_expression(code_item.get_line())
            if re.search(r"\WBalancedProject\W", expr): return "extra"
        return ""
    #@nonl
    #@-node:apply_browser_menu
    #@+node:init_attributes
    def init_attributes(self):
        obj = super(BalancedProjectEditor, self).init_attributes()
        if obj:
            self.balance = obj.balance
        else:
            self.balance = ftask.SMART

        self.performed = ""
        args = self.context.code_item.get_args()
        try:
            self.performed = args[4]
        except IndexError:
            for a in args:
                if a.startswith("performed"):
                    self.performed = a.split("=")[-1].strip()
                    break
    #@-node:init_attributes
    #@-others
#@nonl
#@-node:class BalancedProjectEditor
#@+node:class BalancedProjectView
class BalancedProjectView(ProjectView):
    __model__ = BalancedProjectCreator
    __view_name__ = "default"

    format = _("""
[Project: ]  |project(Combo)>
[Scenario: ] |scenario(Combo)>
[Name: ]     |name>
[Balance: ]  |balance
[Id: ]       |id>
[Performed: ]|performed>
-->
(buttons)>
""")
#@-node:class BalancedProjectView
#@+node:class AdjustedProjectCreator
class AdjustedProjectCreator(SingletonEditor):
    name = db.Text()
    base = db.Text()
    title = _("Create AdjustedProject")

    #@    @+others
    #@+node:apply
    def apply(self, expression, code_item):
        return not expression
    #@-node:apply
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        return "create"
    #@nonl
    #@-node:apply_browser_menu
    #@+node:init_attributes
    def init_attributes(self):
        self.scenario = "_default"
        self.project = ""
        self.name = ""
        self.id = ""

        #code_item = self.context.code_item
        #if classifiers.is_evaluation(code_item):


    #@-node:init_attributes
    #@+node:check_constraints
    def check_constraints(self):
        error = db.ConstraintError()
        if not reg_path.match(self.name):
            error.message["name"] = _("Name is not a valid identifier")

        if not reg_path.match(self.base):
            error.message["base"] = _("base is not a valid identifier")

        if error.message:
            raise error
    #@nonl
    #@-node:check_constraints
    #@+node:realize_code
    def realize_code(self):
        code = str(self)
        context = self.context.__class__(self.context.get_last_code_item())
        context.append_item(code, 0, prespace="\n")
    #@nonl
    #@-node:realize_code
    #@+node:__str__
    def __str__(self):
        return '%s = AdjustedProject(%s)' % (self.name, self.base)
    #@-node:__str__
    #@-others
#@-node:class AdjustedProjectCreator
#@+node:class AdjustedProjectEditor
class AdjustedProjectEditor(AdjustedProjectCreator):
    title = _("Edit AdjustedProject")    
    __icon__ = "edit16"

    #@    @+others
    #@+node:apply
    def apply(self, expression, code_item):
        if not expression: return False

        mo = reg_identifier_assignment.search(expression)
        if not mo: return False

        pname = mo.groupdict()["project"]
        return self.__class__.__name__.startswith(pname)


    #@-node:apply
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        if classifiers.is_evaluation(code_item): 
            expr = code_item.editor.get_expression(code_item.get_line())
            if re.search(r"\WAdjustedProject\W", expr): return "extra"
        return ""
    #@nonl
    #@-node:apply_browser_menu
    #@+node:init_attributes
    def init_attributes(self):
        self.name = self.context.code_item.name
        try:
            self.base = self.context.code_item.get_args()[0]
        except IndexError:
            self.base = 0
    #@-node:init_attributes
    #@+node:realize_code
    def realize_code(self):
        code = str(self)
        code_item = self.context.code_item
        editor = code_item.editor
        editor.BeginUndoAction()
        if code_item.name != self.name:
            #name has changed ==> change the name in all references
            old_name = code_item.name

            iterator = editor.find_evaluation_references(code_item)
            refs = dict([ (line, ci) for ci, line in iterator ])
            for line in refs.keys():
                start = editor.PositionFromLine(line)
                end = editor.GetLineEndPosition(line)
                editor.SetTargetStart(start)
                editor.SetTargetEnd(end)
                text = editor.GetTextRange(start, end)
                editor.ReplaceTarget(text.replace(old_name, self.name))

        code_item.editor.replace_expression(code, code_item.get_line())

        editor.EndUndoAction()
    #@-node:realize_code
    #@-others
#@-node:class AdjustedProjectEditor
#@+node:class AdjustedProjectView
class AdjustedProjectView(editorlib.MainView):
    __model__ = AdjustedProjectCreator
    __view_name__ = "default"

    format = _("""
[Name: ]            |name>
[Base Evaluation: ] |base(Combo)>
-->
(buttons)>
""")

    #@    @+others
    #@+node:prepare
    def prepare(self):
        self.grow_col(-1)
        self.grow_row(-2)
        self.buttons.grow_col(0)
    #@nonl
    #@-node:prepare
    #@+node:constitute
    def constitute(self, imodel):
        super(AdjustedProjectView, self).constitute(imodel)

        #@    << fill base combo >>
        #@+node:<< fill base combo >>
        balanced_projects = []
        editor = imodel.context.code_item.editor
        module = editor.get_module()
        ismodule = inspect.ismodule
        val_name_map = dict([ (v, k) for k, v in module.__dict__.iteritems() 
                              if ismodule(v)])


        for m in controller().get_planbuffers():
            if editor.model.path != m.path:
                import_module = m.editor.get_module()
                try:
                    # get modules import name
                    prefix = val_name_map[import_module] + "."
                except KeyError:
                    continue
            else:
                prefix = ""

            for item in m.editor.editor.code_items:
                if item.obj_type == classifiers.EVALUATION:
                    expr = m.editor.editor.get_expression(item.get_line())
                    try:
                        expr.index("BalancedProject")
                    except ValueError:
                        continue
                    else:
                        balanced_projects.append(prefix + item.name)

        balanced_projects.sort()
        self.base.Clear()
        for p in balanced_projects:
            self.base.Append(p)
        #@nonl
        #@-node:<< fill base combo >>
        #@nl
    #@-node:constitute
    #@-others
#@nonl
#@-node:class AdjustedProjectView
#@-node:Evaluation Editors
#@+node:Import Editors
#@+node:class ImportRemover
class ImportRemover(object):
    __icon__ = "delete16"

    #@    @+others
    #@+node:apply
    def apply(self, expression, code_item):
        return False
    #@-node:apply
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        return "extra"
    #@-node:apply_browser_menu
    #@+node:activate
    def activate(self, context):
        code_item = context.code_item.remove()
    #@-node:activate
    #@-others
#@-node:class ImportRemover
#@+node:class ImportCreator
class ImportCreator(object):
    #@    @+others
    #@+node:__init__
    def __init__(self, import_string):
        self.import_string = import_string
    #@nonl
    #@-node:__init__
    #@+node:apply
    def apply(self, expression, code_item):
        return False
    #@-node:apply
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        return "create"
    #@-node:apply_browser_menu
    #@+node:activate
    def activate(self, context):
        context = context.__class__(context.get_last_code_item())
        context.append_item(self.import_string, 0, prespace="\n")
    #@nonl
    #@-node:activate
    #@-others
#@nonl
#@-node:class ImportCreator
#@-node:Import Editors
#@+node:NameEditor
#@+node:class NameEditor
class NameEditor(SingletonEditor):
    name = db.Text()
    #@    @+others
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        return "create"
    #@-node:apply_browser_menu
    #@+node:init_attributes
    def init_attributes(self):
        self.name = ""
    #@nonl
    #@-node:init_attributes
    #@+node:check_constraints
    def check_constraints(self):
        if not reg_identifier.match(self.name):
            error = db.ConstraintError()    
            error.message["name"] = _("Name is not a valid identifier")
            raise error
    #@nonl
    #@-node:check_constraints
    #@+node:realize_code
    def realize_code(self):
        raise RuntimeError("abstract")

    #@-node:realize_code
    #@-others
#@nonl
#@-node:class NameEditor
#@+node:class NameEditorView
class NameEditorView(editorlib.MainView):
    __model__ = NameEditor
    __view_name__ = "default"

    format = _("""
[Name: ]|name>
-->
(buttons)>
""")

    def prepare(self):
        self.grow_col(-1)
        self.grow_row(1)
        self.buttons.grow_col(0)
        self.name.set_width("X"*30)
#@nonl
#@-node:class NameEditorView
#@-node:NameEditor
#@+node:class RenameEditor
class RenameEditor(NameEditor):
    #@    @+others
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        return "extra"
    #@-node:apply_browser_menu
    #@+node:init_attributes
    def init_attributes(self):
        self.name = self.context.code_item.name
    #@-node:init_attributes
    #@+node:realize_code
    def realize_code(self):
        code_item = self.context.code_item
        editor = code_item.editor
        editor.BeginUndoAction()
        code_item.rename(self.name)
        self.correct_code(editor)
        editor.EndUndoAction()

    #@-node:realize_code
    #@+node:correct_code
    def correct_code(self, editor):
        editor.correct_code()
    #@nonl
    #@-node:correct_code
    #@-others
#@-node:class RenameEditor
#@+node:class AttributeEditor
class AttributeEditor(context.ItemEditor):
    evaluator = Evaluator

    #@    @+others
    #@+node:__init__
    def __init__(self, attrib_name, edit_model, default=None):
        self.attrib_name = attrib_name
        self.edit_model = edit_model
        self.default = default
    #@nonl
    #@-node:__init__
    #@+node:apply
    def apply(self, expression, code_item):
        if not expression: return True

        mo = reg_assignment.search(expression)
        if not mo: return False

        path = mo.group(1).split(".")
        return path[-1] == self.attrib_name

    #@-node:apply
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        if self.attrib_name in existing_attribs:
            return "edit"

        return "add"
    #@nonl
    #@-node:apply_browser_menu
    #@+node:activate
    def activate(self, context):
        """
        activates the editor.
        """
        imodel = SimpleContainer(self.edit_model, context, self.attrib_name, 
                                 self.evaluator, self.default)
        imodel.show()
        return imodel
    #@-node:activate
    #@-others
#@nonl
#@-node:class AttributeEditor
#@-node:Editors
#@+node:Assign Editors
registry = context.CEvaluation.editors
registry[_("Evaluation/Create Project...(1000)")] = ProjectCreator()
registry[_("Evaluation/Create BalancedProject...(1010)")] = BalancedProjectCreator()
registry[_("Evaluation/Create AdjustedProject...(1020)")] = AdjustedProjectCreator()
registry[_("Evaluation/Edit...(1000)")] = ProjectEditor()
registry[_("Evaluation/Edit...(1001)")] = BalancedProjectEditor()
registry[_("Evaluation/Edit...(1002)")] = AdjustedProjectEditor()
registry[_("Evaluation/Show References...(1900)")] = EvaluationReferencePrinter()
registry[_("Evaluation/Remove...(1020)")] = EvaluationRemover()

registry = context.CImport.editors
registry[_("Import/Remove...(1020)")] = ImportRemover()
registry[_("Import/Import Gantt Charts(100)")] = ImportCreator("import faces.lib.gantt as gantt")
registry[_("Import/Import Workbreakdown Charts(110)")] = ImportCreator("import faces.lib.workbreakdown as workbreakdown")
registry[_("Import/Import Resource Charts(120)")] = ImportCreator("import faces.lib.resource as resource_charts")
registry[_("Import/Import Reports(130)")] = ImportCreator("import faces.lib.report as report")

del registry

#@-node:Assign Editors
#@-others
#@nonl
#@-node:@file gui/editor/attribedit.py
#@-leo
