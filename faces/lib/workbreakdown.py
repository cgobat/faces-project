############################################################################
#   Copyright (C) 2005,2006 by Reithinger GmbH
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
import faces.charting.charts as charts
import faces.charting.widgets as widget
import faces.charting.patches as patches
import faces.charting.connector as connector
import faces.plocale
import sys
import textwrap
from faces.charting.tools import *

_is_source_ = True
_ = faces.plocale.get_gettext()


__all__ = ("Standard",)



class Standard(charts.TableChart):
    """
    A Standard workbreakdown chart
    """
    
    __type_image__ = "wbk"
    __editor__ = ("faces.gui.edit_chart", "WorkBreakDown")
    
    data = None
    box_width = 100
    show_rowlines = False
    show_collines = False
    separate_leafes = True
    max_depth = sys.maxint
    title_attrib = "title"

    properties = { "leaf.facecolor" : "lightgrey",
                   "facecolor" : "white",
                   "edgecolor" : "black",
                   "linewidth" : 1.0,
                   "antialiased" : True,
                   }


    __attrib_completions__ = charts.TableChart.__attrib_completions__.copy()
    __attrib_completions__.update({\
        "#data" : "get_evaluation_completions", 
        "data" : 'data = ',
        "box_width" : 'box_width = 100',
        "show_rowlines" : 'show_rowlines = False',
        "show_collines" : 'show_collines = False',
        "separate_leafes" : 'separate_leafes = True',
        "max_depth" : 'max_depth = sys.maxint',
        "title_attrib" : 'title_attrib = "title"',
        "def modify_widget" : """def modify_widget(self, cell_widget, task):
pass""",
        "def create_objects" : """def create_objects(self, data):
for t in data:
yield t
""" })


    def __init__(self, *args, **kwargs):
        self.task_to_widget = {}
        if not self.data:
            raise RuntimeError("no data attribute specified for chart %s"\
                               % getattr(self, "__name__",
                                         self.__class__.__name__))

        charts.TableChart.__init__(self, *args, **kwargs)


    def create_objects(self, data):
        return list(data)


    def create_all_widgets(self):
        objects = self.create_objects(self.data)
        objects = filter(lambda t: t.depth <= self.max_depth, objects)
        widget.Row.show_rowline = self.show_rowlines

        for t in objects:
            if t.children and t.depth < self.max_depth:
                #y of row will be calculated by _calc_y_pos
                row = widget.Row()
            else:
                row = self.get_row()

            col = self.calc_column(t)
            cell = widget.CellWidget(row, col, t)
            self.make_widget(cell, t)
            self.task_to_widget[t] = cell
            self.widgets.append(cell)


    def calc_column(self, task):
        if task.children or not self.separate_leafes:
            col = self.get_col(task.depth)
        else:
            col = self.get_col(1000)

        return col


    def get_property_group(self, task):
        if task.children and task.depth < self.max_depth:
            return "parent"

        return "leaf"


    def modify_widget(self, cell_widget, task):
        pass
    

    def make_widget(self, cell_widget, task):
        if task.depth == 0:
            cell_widget.col.left_sep = 5
            
        cell_widget.col.right_sep = 15
        cell_widget.row.top_sep = cell_widget.row.bottom_sep = 2
        cell_widget.min_height = 14

        group = self.get_property_group(task)
        kwargs = make_properties(self.get_property, group)
        cell_widget.add_artist(patches.Rectangle((LEFT, BOTTOM),
                                                 RIGHT-LEFT,
                                                 TOP-BOTTOM,
                                                 **kwargs))

        title = getattr(task, self.title_attrib)
        title = textwrap.fill(title, self.box_width)
        cell_widget.text(title, 
                         HCENTER, VCENTER,
                         horizontalalignment ="center",
                         verticalalignment="center",
                         fontproperties=group)

        self.modify_widget(cell_widget, task)


    def _finalize_col_widgets(self):
        charts.TableChart._finalize_col_widgets(self)
        HSEP.set(10) #just to have difference of x + HSEP and x
        self._calc_y_pos(self.data)
        

    def create(self):
        self.connectors = []
        charts.TableChart.create(self)

        for c in self.connectors:
            self.axes.add_widget(c)

        del self.connectors


    def _calc_y_pos(self, task):
        if not task.children or task.depth >= self.max_depth: return
        me = self.task_to_widget.get(task)
        if not me: return

        ymin = sys.maxint
        ymax = -sys.maxint
        for c in task.children:
            dst = self.task_to_widget.get(c)
            if not dst: continue
            self._calc_y_pos(c)

            bottom = dst.row.y - dst.row.full_height()
            if float(ymax) < float(dst.row.y): ymax = dst.row.y
            if float(ymin) > float(bottom): ymin = bottom
                
            self.connectors.append(self.create_connector(me, dst))

        me.row.set_y((ymin + ymax + me.row.full_height()) / 2)


    def create_connector(self, src, dest):
        return connector.WBKConnector(src, dest)
                        

    def get_tip(self, tipobj):
        if isinstance(tipobj, widget.CellWidget):
            return self.get_task_tip(tipobj.fobj)

        return None
    

    def get_task_tip(self, task):
        lines = [
            (_("Name"), task.title),
            (_("Timeframe"), "%s - %s" % (task.to_string.start,\
                                          task.to_string.end)),
            (_("Effort"), task.to_string.effort),
            (_("Length"), task.to_string.length),
            (_("Complete"), task.to_string.complete) ]

        append = lines.append
        if task.booked_resource:
            append((_("Resources"), task.to_string.booked_resource))
        elif task.performed_resource:
            append((_("Resources"), task.to_string.performed_resource))
            

        append((_("Buffer"), task.to_string.buffer))

        if getattr(task, "note", None):
            append((_("Note"), task.note))
            
        return lines



    

