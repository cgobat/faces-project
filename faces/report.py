#@+leo-ver=4
#@+node:@file report.py
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
A report generator
"""
from __future__ import absolute_import
#@<< declarations >>
#@+node:<< declarations >>
from past.builtins import cmp
from builtins import next
from builtins import filter
from builtins import str
from builtins import map
from past.builtins import basestring
from builtins import object
from . import task
from . import observer
import datetime as datetime
import inspect
from . import pcalendar
from . import plocale
from . import utils
from .task import _ValueWrapper

_is_source_ = True
_ = plocale.get_gettext()


header_names = { "indent_name": _("Name"),
                 "name": _("Name"),
                 "index": _("Index"),
                 "title" : _("Title"),
                 "start" : _("Start"),
                 "end"  : _("End"),
                 "load" : _("Load"),
                 "estimated_effort" : _("Estimated Effort"),
                 "performed_effort" : _("Performed Effort"),
                 "performed_end" : _("Performed End"),
                 "performed_start" : _("Performed Start"),
                 "performed_work_time" : _("Worktime"),
                 "length" : _("Length"),
                 "effort" : _("Effort"),
                 "duration" : _("Duration"),
                 "real_effort" : _("Real Effort"),
                 "quotient" : _("Quotient"),
                 "complete" : _("Complete"),
                 "priority" : _("Priority"),
                 "todo" : _("Todo"),
                 "efficiency" : _("Efficiency"),
                 "buffer" : _("Buffer"),
                 "costs" : _("Costs"),
                 "sum" : _("Sum"),
                 "max" : _("Max"),
                 "min" : _("Min"),
                 "milestone" : _("Milestone"),
                 "resource" : _("Resource"),
                 "booked_resource" : _("Booked Resource") }


#@-node:<< declarations >>
#@nl
#@+others
#@+node:Private
#@+node:_val
def _val(val):
    if isinstance(val, _ReportValueWrapper):
        return val._value

    return val
#@-node:_val
#@+node:_has_ref
def _has_ref(val):
    if isinstance(val, _ReportValueWrapper):
        return val._ref

    return False
#@-node:_has_ref
#@+node:class _ReportValueWrapper
class _ReportValueWrapper(_ValueWrapper):
    #@	@+others
    #@+node:__init__
    def __init__(self, value, ref=(None, "")):
        _ValueWrapper.__init__(self, value, ref)
    #@-node:__init__
    #@+node:_vw
    def _vw(self, operand, *args):
        refs = list(map(_has_ref, args))
        refs = list(filter(bool, refs))
        vals = list(map(_val, args))
        result = operand(*vals)
        return _ReportValueWrapper(result, refs and refs[0] or (None, ""))
    #@-node:_vw
    #@+node:_cmp
    def _cmp(self, operand, *args):
        vals = list(map(_val, args))
        return operand(*vals)
    #@-node:_cmp
    #@+node:__call__
    def __call__(self, *args):
        vals = list(map(_val, args))
        other = _ReportValueWrapper(self._value(*vals),
                                    (self._ref[0], self._ref[1], args))
        return other
    #@-node:__call__
    #@+node:__repr__
    def __repr__(self):
        if isinstance(self._value, basestring):
            return self._value

        formatter = self._ref[0].formatter(self._ref[1])
        return formatter(self._value)
    #@-node:__repr__
    #@+node:type
    __str__ = __repr__

    def type(self):
        return type(self._value)
    #@-node:type
    #@+node:unicode
    def str(self, *args): 
        if isinstance(self._value, str):
            return str(self._value, *args)

        return repr(self)
    #@nonl
    #@-node:unicode
    #@-others
#@nonl
#@-node:class _ReportValueWrapper
#@+node:class _TaskWrapper


class _TaskWrapper(object):
    #@	@+others
    #@+node:__init__
    def __init__(self, task):
        self.task = task
    #@-node:__init__
    #@+node:__getattr__
    def __getattr__(self, name):
        if name == "copy_src":
            return self.task.copy_src and _TaskWrapper(self.task.copy_src)

        if name == "to_string":
            return _ToStringWrapper(self.task.to_string)

        value = getattr(self.task, name)

        if isinstance(value, task.Task):
            result = _TaskWrapper(value)
        else:
            result = _ReportValueWrapper(value, (self.task, name))

        setattr(self, name, result)
        return result
    #@-node:__getattr__
    #@+node:__iter__
    def __iter__(self):
        def wrap_iter():
            for t in self.task:
                yield _TaskWrapper(t)

        return wrap_iter()
    #@-node:__iter__
    #@+node:__str__
    def __str__(self):
        return "_TaskWrapper %s" % self.task
    #@-node:__str__
    #@-others
#@-node:class _TaskWrapper
#@+node:class _ToStringWrapper


class _ToStringWrapper(object):
    #@	@+others
    #@+node:__init__
    def __init__(self, converter):
        self.converter = converter
    #@-node:__init__
    #@+node:__getattr__
    def __getattr__(self, name):
        value = getattr(self.converter, name)
        result = _ReportValueWrapper(value, (self.converter.source, name))
        setattr(self, name, result)
        return result
    #@-node:__getattr__
    #@+node:__getitem__
    def __getitem__(self, format):
        return _ToStringWrapper(self.converter[format])
    #@-node:__getitem__
    #@-others
#@-node:class _ToStringWrapper
#@+node:class _ReportIter



class _ReportIter(object):
    #@	@+others
    #@+node:__init__
    def __init__(self, report):
        self.report = report
        try:
            self.stepper = iter(report.make_report(report.data))
        except Exception as e:
            report._raise(e)
    #@-node:__init__
    #@+node:__iter__
    def __iter__(self):
        return self
    #@-node:__iter__
    #@+node:next
    def __next__(self):
        row = next(self.stepper)
        if not isinstance(row, (tuple, list)):
            row = (row, )

        def to_cell(c):
            if isinstance(c, Cell): return c
            return Cell(c)

        row = list(map(to_cell, row))
        if row[0].left_border is None:
            row[0].left_border = True

        return self.report.modify_row(row)
    #@-node:next
    #@-others
#@-node:class _ReportIter
#@-node:Private
#@+node:Public
#@+node:class Cell
class Cell(object):
    """
    The class represents a cell within a report row

    @var back_color:
    Specifies the background color of the cell.  Valid value are any
    html hex string like '\#eeefff' or legal html names for colors,
    like 'red', 'burlywood' and 'chartreuse'.

    @var text_color:
    Specifies the text color of the cell. Valid value are any html hex
    string like '\#eeefff' or legal html names for colors, like 'red',
    'burlywood' and 'chartreuse'.

    @var font_bold:
    Specifies if the text should be displayed bold. Valid values are
    True or False.

    @var font_italic:
    Specifies if the text should be displayed italic. Valid values
    are True or False.

    @var font_underline:
    Specifies if the text should be displayed underlined. Valid
    values are True or False.

    @var font_size:
    Specifies the font size of the text. Valid values are either an
    absolute value of"xx-small", "x-small", "small", "medium", "large",
    "x-large", "xx-large"; or a relative value of"smaller" or "larger";
    or an absolute font size, e.g. 12.

    @var left_border:
    Specifies if a left border apperars. Valid values
    are True or False.

    @var top_border:
    Specifies if a top border apperars. Valid values
    are True or False.

    @var right_border:
    Specifies if a right border apperars. Valid values
    are True or False.

    @var bottom_border:
    Specifies if a bottom border apperars. Valid values
    are True or False.

    @var align:
    Specifies the alignment of the cell. Valid values are
    LEFT(0), RIGHT(1), CENTER(2)
    """
    #@	<< declarations >>
    #@+node:<< declarations >>
    LEFT = 0
    RIGHT = 1
    CENTER = 2

    back_color = None
    text_color = None
    font_bold = False
    font_italic = False
    font_underline = False
    font_size = None
    left_border = None
    top_border = False
    right_border = True
    bottom_border = True
    align = LEFT

    __all__ = ("LEFT", "RIGHT", "CENTER", "back_color",\
               "text_color", "font_bold", "font_italic",\
               "font_underline", "font_size", "left_border",\
               "top_border", "right_border", "bottom_border",\
               "align")

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, value, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.value = value
        if self.get_type() is float:
            self.align = self.RIGHT
    #@-node:__init__
    #@+node:__str__
    def __str__(self):
        return str(self.value)
    #@-node:__str__
    #@+node:__unicode__
    def __unicode__(self):
        return str(self.value)
    #@-node:__unicode__
    #@+node:__nonzero__
    def __bool__(self):
        return bool(self.value)
    #@-node:__nonzero__
    #@+node:__cmp__
    def __cmp__(self, other):
        return cmp(self.value, other.value)
    #@-node:__cmp__
    #@+node:get_label
    def get_label(self):
        if isinstance(self.value, _ReportValueWrapper):
            return self.value._ref[1]

        return ""
    #@-node:get_label
    #@+node:unicode
    def str(self, *args):
        value = self.value
        try:
            return value.str(*args)
        except AttributeError:
            pass

        if isinstance(value, str):
            return str(value, *args)

        return str(value)
    #@-node:unicode
    #@+node:get_type
    def get_type(self):
        if isinstance(self.value, _ReportValueWrapper):
            return type(self.value._value)

        return type(self.value)
    #@-node:get_type
    #@+node:get_ref
    def get_ref(self):
        if isinstance(self.value, _ReportValueWrapper):
            return self.value._ref

        return (None, "")
    #@-node:get_ref
    #@+node:native
    def native(self):
        """
        returns the native value of the cell.
        """

        if isinstance(self.value, _ReportValueWrapper):
            return self.value._value

        return self.value
    #@-node:native
    #@-others

    __repr__ = __str__
#@nonl
#@-node:class Cell
#@+node:class Report
class Report(observer.Observer):
    """
    A standart report.

    @var headers:
    A tuple specifying the report header.
    """
    #@	<< declarations >>
    #@+node:<< declarations >>
    __type_name__ = "report"
    __type_image__ = "report"
    data = None
    headers = ()

    __attrib_completions__ = observer.Observer.__attrib_completions__.copy()
    __attrib_completions__.update({\
        "#data" : "get_evaluation_completions", 
        "data" : 'data = ',
        "headers" : 'headers = ()',
        "def make_report" : "def make_report(self, data):\nfor d0 in data: \nyield (|d0.indent_name(), d0.start)",
        "def prepare_data" : "def prepare_data(self, data):\nreturn data",
        "def modify_row" : "def modify_row(self, row):\nreturn row" })

    __all__ = ("headers", "data")
    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self):
        if not self.data:
            self._raise(RuntimeError('no data attribute specified'))

        if not self.headers:
            def get_header(c):
                result = c.get_label()
                return header_names.get(result, result)

            first = next(iter(self))
            if not self.headers:
                self.headers = tuple(map(get_header, first))
    #@-node:__init__
    #@+node:_raise
    def _raise(self, exc):
        line = inspect.getsourcelines(self.__class__)[1]
        fname = inspect.getsourcefile(self.__class__)
        raise exc.__class__('%s (File "%s", line %i)' % (str(exc), fname, line))
    #@-node:_raise
    #@+node:make_report
    def make_report(self, data):
        raise RuntimeError("called base report")

    make_report.args = ("data",)
    #@nonl
    #@-node:make_report
    #@+node:prepare_data
    def prepare_data(self, data):
        return data
    #@-node:prepare_data
    #@+node:instrument_data
    def instrument_data(self, data):
        def wrap_obj(obj):
            if isinstance(obj, task.Task):
                return _TaskWrapper(obj)

            if isinstance(obj, _TaskWrapper):
                return obj

            if isinstance(obj, basestring):
                return obj

            try:
                return list(map(wrap_obj, iter(obj)))
            except TypeError:
                return obj

        return wrap_obj(data)
    #@-node:instrument_data
    #@+node:modify_row
    def modify_row(self, row):
        return row

    modify_row.args = ([Cell]*20,)

    #@-node:modify_row
    #@+node:__iter__
    __is_prepared = False
    def __iter__(self):
        if not self.__is_prepared:
            self.data = self.prepare_data(self.data)
            self.data = self.instrument_data(self.data)
            self.__is_prepeditared = True
        return _ReportIter(self)
    #@-node:__iter__
    #@-others
#@-node:class Report
#@-node:Public
#@-others
#@-node:@file report.py
#@-leo
