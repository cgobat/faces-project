#@+leo-ver=4
#@+node:@file __init__.py
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
    faces project management in python

    @var LEFT:
    The left border position of a graphical widget.

    @var RIGHT:
    The right border position of a graphical widget.

    @var TOP:
    The top border position of a graphical widget.

    @var BOTTOM:
    The bottom border position of a graphical widget.

    @var VCENTER:
    The vertical center position of a graphical widget.

    @var HCENTER:
    The horizontal center position of a graphical widget.

    @var VSEP:
    Specifies the vertical space equivalent to 1/4 of the height of
    the character 'I'.

    @var HSEP:
    Specifies the horizontal space equivalent to 1/4 of the height of
    the character 'I'.

    @var FACTOR:
    Specifies the height of a graphical widget in units of VSEP.

"""
from __future__ import absolute_import

__version__ = "0.11.7"

from .pcalendar import Calendar, WorkingDate, StartDate, EndDate, Minutes

from .task import Project, BalancedProject, AdjustedProject, Task, \
    STRICT, SLOPPY, SMART, Multi, YearlyMax, WeeklyMax, MonthlyMax, \
    DailyMax, VariableLoad

from .resource import Resource
from .operators import intersect, unify, difference
from .charting.tools import VSEP, HSEP, LEFT, RIGHT, BOTTOM, \
     TOP, VCENTER, HCENTER, FACTOR, \
     set_default_size as set_default_chart_font_size,\
     set_encoding as set_chart_encoding, \
     chart_encoding

from .charting.patches import Arrow, Circle, Polygon, RegularPolygon, \
     Shadow, Wedge, Rectangle

from .charting.taxis import alt_week_locator

gui_controller = None

__all__ = ("Arrow", "Circle", "Polygon", "RegularPolygon", \
           "Shadow", "Wedge", "Rectangle", \
           "VSEP", "HSEP", "LEFT", "RIGHT", "BOTTOM", \
           "TOP", "VCENTER", "HCENTER", "FACTOR", \
           "set_default_chart_font_size",\
           "set_chart_encoding", "chart_encoding", "Resource",
           "Project", "BalancedProject", "AdjustedProject", "Task", \
           "STRICT", "SLOPPY", "SMART", "Multi", \
           "YearlyMax", "WeeklyMax", "MonthlyMax", "DailyMax", \
           "intersect", "unify", "difference", "Calendar", "gui_controller",
           "WorkingDate", "StartDate", "EndDate", "Minutes", "VariableLoad",
           "alt_week_locator")


_is_source = True
_DEBUGGING = True
_PROFILING = False
#@-node:@file __init__.py
#@-leo
