#@+leo-ver=4
#@+node:@file lib/report.py
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
A library of different reports.
"""
#@<< imports >>
#@+node:<< imports >>
import faces.report as _report
import faces.pcalendar as _pcalendar
import faces.task as _task
import datetime as _datetime
import bisect as _bisect
import faces.plocale
import locale


#@-node:<< imports >>
#@nl

_is_source_ = True
Cell = _report.Cell
_ = faces.plocale.get_gettext()

__all__ = ("Standard", "Titles", "Critical", "Calendar")


#@+others
#@+node:class Standard
class Standard(_report.Report):
    """
    A standard report
    """

    #@	@+others
    #@+node:register_editors
    def register_editors(cls, registry):
        super(Standard, cls).register_editors(registry)
        registry.Evaluation(_("Report/data..."))
        registry.Column(_("Report/make_report..."), "data")

    register_editors = classmethod(register_editors)

    #@-node:register_editors
    #@+node:make_report
    def make_report(self, data):
        for t in data:
            yield (t.indent_name(), t.start, t.end, t.effort, t.length)

    #@-node:make_report
    #@-others
#@-node:class Standard
#@+node:class Titles
class Titles(Standard):
    #@	<< declarations >>
    #@+node:<< declarations >>
    __attrib_completions__ = Standard.__attrib_completions__.copy()
    del __attrib_completions__["def modify_row"]

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:modify_row
    def modify_row(self, row):
        task = row[0].get_ref()[0]
        if not isinstance(task, _task.Task):
            return row

        if task.children:
            ds = { 
                0 : "xx-large",
                1 : "x-large",
                2 : "large",
                }.get(int(task.depth))

            for c in row:
                c.font_bold = True
                c.font_size = ds

        return row
    #@-node:modify_row
    #@-others
#@-node:class Titles
#@+node:class Critical
class Critical(Standard):
    #@	<< declarations >>
    #@+node:<< declarations >>
    colors = { 0 : "red" }

    __attrib_completions__ = Standard.__attrib_completions__.copy()
    __attrib_completions__.update({\
        "colors" : 'colors = { |0 : "red" }' })
    del __attrib_completions__["def modify_row"]


    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self):
        self._colors = []

        to_minutes = _pcalendar._default_calendar.Minutes
        self._colors = map(lambda i: (to_minutes(i[0]), i[1]),
                           self.colors.items())
        self._colors.sort()
        self._colors.reverse()

        Standard.__init__(self)
    #@-node:__init__
    #@+node:register_editors
    def register_editors(cls, registry):
        super(Critical, cls).register_editors(registry)
        registry.ColorMap(_("Shape/colors..."), { "0d" : "red" })

    register_editors = classmethod(register_editors)

    #@-node:register_editors
    #@+node:modify_row
    def modify_row(self, row):
        task = row[0].get_ref()[0]
        if not isinstance(task, _task.Task):
            return row

        color = None
        for v, c in self._colors:
            if task.buffer <= v: color = c

        if color:
            for c in row:
                c.back_color = color

        return row
    #@-node:modify_row
    #@-others
#@-node:class Critical
#@+node:class Calendar
class Calendar(Standard):
    #@	<< declarations >>
    #@+node:<< declarations >>
    __type_image__ = "calendar"

    show_start = True
    show_end = True
    start = None
    end = None

    __attrib_completions__ = Standard.__attrib_completions__.copy()
    __attrib_completions__.update({\
        "show_start" : 'show_start = True',
        "show_end" : 'show_end = True',
        "start" : 'start = None',
        "end" : 'end = None',
        "def modify_cell" : "def modify_cell(self, cell):\npass" })

    del __attrib_completions__["def modify_row"]
    del __attrib_completions__["def make_report"]


    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:instrument_data
    def instrument_data(self, data):
        data = tuple(data)
        self.dates = dates = {}

        mind = _datetime.datetime.max
        maxd = _datetime.datetime.min

        #@    << define insert_task >>
        #@+node:<< define insert_task >>
        def insert_task(index, date, soe, min_date, max_date):
            date = date.to_datetime()
            day = dates.setdefault(date.date(), [])
            _bisect.insort_right(day, (date.time(), soe, index))
            return min(date, min_date), max(date, max_date)
        #@nonl
        #@-node:<< define insert_task >>
        #@nl

        for i, t in enumerate(data):
            if self.show_start:
                mind, maxd = insert_task(i, t.start, 0, mind, maxd)

            if self.show_end:
                mind, maxd = insert_task(i, t.end, 1, mind, maxd)

        if not self.start:
            self.start = mind
        else:
            self.start = _pcalendar.WorkingDate(self.start).to_datetime()

        if not self.end:
            self.end = maxd
        else:
            self.end = _pcalendar.WorkingDate(self.end).to_datetime()

        self._create_columns(self.start, self.end)
        self._create_headers()

        return Standard.instrument_data(self, data)
    #@-node:instrument_data
    #@+node:get_dates
    def get_dates(self, date):
        result = self.dates.get(date, ())
        return map(lambda i: (self.data[i[2]], i[1]), result)
    #@-node:get_dates
    #@+node:make_cell
    def make_cell(self, value, **kwargs):
        cell = Cell(value, **kwargs)
        date = kwargs["date"]
        is_header = kwargs.get("header", False)

        if date and date.weekday() in (5, 6) and not is_header:
            cell.back_color = "gray"

        self.modify_cell(cell)
        return cell
    #@-node:make_cell
    #@+node:modify_cell
    def modify_cell(self, cell):
        pass

    modify_cell.args = (Cell,)
    #@nonl
    #@-node:modify_cell
    #@+node:make_report
    def make_report(self, data):
    	day_header = None
    	day_rows =  None

        #@    << define add_row >>
        #@+node:<< define add_row >>
        def add_row():
            row = map(lambda c: self.make_cell("", 
                                               right_border=c.right_border,
                                               font_size="small",
                                               header=False,
                                               bottom_border=False,
                                               date=c.date),\
                      day_header)

            day_rows.append(row)
        #@nonl
        #@-node:<< define add_row >>
        #@nl
        #@    << define add_date >>
        #@+node:<< define add_date >>
        def add_date(col, date):
            if day_rows[-1][col].value:
                add_row()
                day_rows[-1][col].value = date
                return

            for r in day_rows:
                if not r[col].value:
                    r[col].value = date
                    break
        #@nonl
        #@-node:<< define add_date >>
        #@nl

    	col_range = range(len(self.columns))
    	for d in range(1, 32):
            #iterate through all days
    	    day_header = []
    	    day_rows = []

            #@        << create day header cells >>
            #@+node:<< create day header cells >>
            for month in self.columns:
                try:
                    date = month.replace(day=d).date()
                    c = self.make_cell(date.strftime("%d. %A"),
                                       back_color="gold",
                                       bottom_border=False,
                                       header=True,
                                       date=date)
                    if day_header: day_header[-1].right_border = True
                    day_header.append(c)
                except:
                    #the day does not exist at tha month
                    c = self.make_cell("", 
                                       right_border=False,
                                       bottom_border=False,
                                       header=False,
                                       date=None)
                    day_header.append(c)
            #@nonl
            #@-node:<< create day header cells >>
            #@nl
    	    add_row()

            #@        << create day data cells >>
            #@+node:<< create day data cells >>
            for c in col_range:
                date = day_header[c].date
                if not date: continue
                tasks = self.get_dates(date)
                for t, soe in tasks:
                    if soe == 0:
                        text = self.get_start_text(t)
                    else:
                        text = self.get_end_text(t)

                    if text:
                        add_date(c, text)
            #@nonl
            #@-node:<< create day data cells >>
            #@nl
    	    day_rows.insert(0, day_header)

            #@        << adjust borders >>
            #@+node:<< adjust borders >>
            for c in col_range:
                date = day_header[c].date
                if date:
                    day_rows[-1][c].bottom_border = True

            left_frame_border = bool(day_header[0].date)
            #@nonl
            #@-node:<< adjust borders >>
            #@nl

    	    for r in day_rows:
                r[0].left_border = left_frame_border
                yield r
    #@-node:make_report
    #@+node:get_start_text
    def get_start_text(self, task):
        text = task.to_string["%H:%M"].start + " " + task.title + " (start)"
        if task.booked_resource:
            text += "\n     " + task.to_string.booked_resource
        return text
    #@-node:get_start_text
    #@+node:get_end_text
    def get_end_text(self, task):
        text = task.to_string["%H:%M"].end + " " + task.title + " (end)"
        if task.booked_resource:
            text += "\n     " + task.to_string.booked_resource
        return text
    #@-node:get_end_text
    #@+node:_create_columns
    def _create_columns(self, start, end):
        start = start.year * 12 + start.month - 1
        end = end.year * 12 + end.month
        def to_date(month):
            return _datetime.datetime(month / 12, 1 + (month % 12), 1)
        self.columns = map(to_date, range(start, end))
    #@-node:_create_columns
    #@+node:_create_headers
    def _create_headers(self):
        encoding = locale.getlocale()[1] or "ascii"
        self.headers = map(lambda d: d.strftime("%B %y").decode(encoding),
                           self.columns)
    #@-node:_create_headers
    #@-others
#@-node:class Calendar
#@-others
#@-node:@file lib/report.py
#@-leo
