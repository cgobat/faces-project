#@+leo-ver=4
#@+node:@file gui/repview.py
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
import wx
import wx.grid
import metapie.navigator as navigator
from metapie.gui import controller
import taskfuncs
import faces.observer
import faces.plocale
import faces.report
import faces.gui.editor.context as context
import matplotlib.colors as colors
import matplotlib.font_manager as font
import weakref
import faces.charting.tools as chart_tools
import metapie.dbtransient as db
import metapie.gui.views as views
import csv
try:
    import Cheetah.Template as CHTemplate
    import webbrowser
    import os.path
    import tempfile
    import faces.utils as utils
    _cheetah_is_installed = True
except ImportError:
    _cheetah_is_installed = False


#@-node:<< Imports >>
#@nl
_is_source_ = True
#@+others
#@+node:convert_color
def convert_color(color):
    color = colors.colorConverter.to_rgb(color)
    return map(lambda i: int(i * 255), color)
#@-node:convert_color
#@+node:_report_factory
def _report_factory(title, data, model):
    return lambda parent: ReportView(parent, data, model, title)
#@nonl
#@-node:_report_factory
#@+node:encode
def encode(text):
    if type(text) is unicode:
        return str(text.encode(chart_tools.chart_encoding))
    return str(text)
#@nonl
#@-node:encode
#@+node:class _ErrorReport

faces.observer.factories["report"] = _report_factory


_ = faces.plocale.get_gettext()


_LEFT = 1
_RIGHT = 2
_TOP = 4
_BOTTOM = 8
_DEFAULT = _RIGHT + _BOTTOM

_align_map = { faces.report.Cell.LEFT : wx.ALIGN_LEFT,
               faces.report.Cell.RIGHT : wx.ALIGN_RIGHT,
               faces.report.Cell.CENTER : wx.ALIGN_CENTER }


class _ErrorReport(faces.report.Report):
    #@	<< class _ErrorReport declarations >>
    #@+node:<< class _ErrorReport declarations >>
    data = ("Error in Report",)

    #@-node:<< class _ErrorReport declarations >>
    #@nl
    #@	@+others
    #@+node:make_report
    def make_report(self, data):
        for s in data:
            yield faces.report.Cell(s)
    #@-node:make_report
    #@-others
#@-node:class _ErrorReport
#@+node:class CellRenderer


class CellRenderer(wx.grid.PyGridCellRenderer):
    #@	@+others
    #@+node:__init__
    def __init__(self, report_view):
        wx.grid.PyGridCellRenderer.__init__(self)
        self.default = wx.grid.GridCellStringRenderer()
        self.report_view = report_view
    #@-node:__init__
    #@+node:Draw
    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        self.default.Draw(grid, attr, dc, rect, row, col, isSelected)
        dc.SetPen(wx.BLACK_PEN)

        border_val = getattr(attr, "border_val", _DEFAULT)
        if border_val & _LEFT: 
            dc.DrawLine(rect.left, rect.top, rect.left, rect.bottom + 1)

        if border_val & _TOP: 
            dc.DrawLine(rect.left, rect.top, rect.right + 1, rect.top)

        if border_val & _RIGHT: 
            dc.DrawLine(rect.right, rect.top, rect.right, rect.bottom + 1)

        if border_val & _BOTTOM: 
            dc.DrawLine(rect.left, rect.bottom, rect.right + 1, rect.bottom)
    #@-node:Draw
    #@+node:GetBestSize
    def GetBestSize(self, grid, attr, dc, row, col):
        return self.default.GetBestSize(grid, attr, dc, row, col)
    #@-node:GetBestSize
    #@+node:Clone
    def Clone(self):
        return CellRenderer(self.report_view)
    #@-node:Clone
    #@-others
#@-node:class CellRenderer
#@+node:class ReportView



class ReportView(wx.Panel, navigator.View):
    #@	@+others
    #@+node:__init__
    def __init__(self, parent, report, model, title):
        wx.Panel.__init__(self, parent, -1, style=wx.SUNKEN_BORDER)
        self.grid = None
        self.code_info = {}
        self.task_info = {}
        self.model = model
        self.link_view = True
        self.replace_data(report)
        self.make_menu()
    #@-node:__init__
    #@+node:make_menu
    def make_menu(self, popup=False, task=None):
        def find_in_source():
            self.model.find_in_source(self.report.__class__)

        ctrl = controller()
        if popup:
            report_menu = ctrl.make_menu()
        else:
            top = ctrl.get_top_menu()
            report_menu = top.make_menu(_("&Report"), pos=300)

        menu = lambda *args, **kw: report_menu.make_item(self, *args, **kw)

        if _cheetah_is_installed:
            menu(_("Print Report..."), self.menu_print_report, "print16", pos=100)

        menu(_("Export to CSV..."), self.menu_export_csv, "export16", pos=101)
        if not popup:
            def nav(func):
                def function(): self.navigate(func)
                return function

            menu(_("Move Left\tCTRL-ALT-LEFT"), nav("MoveCursorLeft"), "left16", pos=10)
            menu(_("Move Right\tCTRL-ALT-RIGHT"), nav("MoveCursorRight"),
                 "right16", pos=20)
            menu(_("Move Up\tCTRL-ALT-UP"), nav("MoveCursorUp"), "up16", pos=30)
            menu(_("Move Down\tCTRL-ALT-DOWN"), nav("MoveCursorDown"), "down16", pos=40)

        menu = lambda *args, **kw: report_menu.make_item(self, *args, **kw)
        menu(_("Find in Source"), find_in_source, "findsource16", pos=110)
        self.link_menu = menu(_("&Link Report"), self.change_link,
                              check_item=True, pos=120)
        self.link_menu.check(self.link_view)

        if popup and task:
            taskfuncs.make_menu_task_clipboard(ctrl, task, report_menu, 500)
            code_item = task._function.code_item
            action_filter = ("add", "edit", "extra")
            context.CTask(code_item).make_browser_menu(report_menu, action_filter)

        return report_menu
    #@-node:make_menu
    #@+node:navigate
    def navigate(self, function):
        method = getattr(self.grid, function)
        method(False)
    #@-node:navigate
    #@+node:set_grid_notifications
    def set_grid_notifications(self):
        grid = self.grid
        wx.grid.EVT_GRID_SELECT_CELL(grid, self.OnCellSelect)
        wx.grid.EVT_GRID_CELL_RIGHT_CLICK(grid, self.OnRightDown)
        wx.grid.EVT_GRID_CELL_LEFT_CLICK(grid, self.OnLeftDown)
    #@-node:set_grid_notifications
    #@+node:change_link
    def change_link(self):
        self.link_view = not self.link_view
        self.link_menu.check(self.link_view)
    #@-node:change_link
    #@+node:OnLeftDown
    def OnLeftDown(self, event):
        event.Skip()
        self.grid.SetFocus()
    #@-node:OnLeftDown
    #@+node:OnRightDown
    def OnRightDown(self, event):
        top = controller().get_top_menu()

        row = event.GetRow()
        col = event.GetCol()
        task, name = self.code_info.get((row, col), (None, None))
        menu = self.make_menu(True, task)

        self.PopupMenu(menu.wxobj, event.GetPosition())
    #@-node:OnRightDown
    #@+node:OnCellSelect
    def OnCellSelect(self, event):
        event.Skip()
        row = event.GetRow()
        col = event.GetCol()
        self.grid.MakeCellVisible(row, col)
        self.grid.SelectBlock(row, col, row, col)

        task, name = self.code_info.get((row, col), (None, None))
        if task:
            taskfuncs.make_menu_task_clipboard(controller(), task)
            if self.link_view:
                self.model.show_object(self, task, name)
        else:
            taskfuncs.remove_menu_task_clipboard(controller())
    #@-node:OnCellSelect
    #@+node:menu_print_report
    def menu_print_report(self):
        path = utils.get_template_path()
        path = os.path.join(path, "printing", "report.tmpl")
        template = CHTemplate.Template(file=path)

        template.report = self.report
        template.Cell = faces.report.Cell
        template.encoding = chart_tools.chart_encoding
        template.compile(file=path)
        template.encode = encode 

        fh, tmpfile = tempfile.mkstemp(".html")
        os.close(fh)
        out = file(tmpfile, "w")
        print >> out, str(template)
        out.close()
        webbrowser.open("file://%s" % tmpfile, True, False)
        controller().session.tmp_files_to_remove.append(tmpfile)

    #@-node:menu_print_report
    #@+node:menu_export_csv
    def menu_export_csv(self):
        dlg = ExportCSV_Dialog(controller().frame,
                               self.report.__class__.__name__)
        if dlg.ShowModal() == wx.ID_OK:
            exporter = dlg.data.exporter()
            exporter.writerow(map(encode, self.report.headers))
            for row in self.report:
                exporter.writerow(map(encode, row))

        dlg.Destroy()
    #@-node:menu_export_csv
    #@+node:Destroy
    def Destroy(self):
        taskfuncs.remove_menu_task_clipboard(controller())
        wx.Panel.Destroy(self)
    #@-node:Destroy
    #@+node:show_object
    def show_object(self, task, attrib, caller=None):
        if not self.link_view or not hasattr(task, "_function"): return

        rc = (self.grid.GetGridCursorRow(), self.grid.GetGridCursorCol())
        cursor_task, cursor_attrib = self.code_info.get(rc, (None, None))

        # don't move if the cursor is at the correct position
        if cursor_task == task and (not attrib or cursor_attrib == attrib):
            return

        taskid = task._idendity_()
        rc = self.task_info.get((taskid, attrib),
                                self.task_info.get((taskid, None)))

        if rc: self.set_cursor(*rc)
    #@-node:show_object
    #@+node:set_cursor
    def set_cursor(self, row, col, link=True):
        row = max(0, row)
        col = max(0, col)
        row = min(row, self.grid.GetNumberRows() - 1)
        col = min(col, self.grid.GetNumberCols() - 1)

        link_view = self.link_view
        self.link_view &= link
        self.grid.SetGridCursor(row, col)
        self.grid.MakeCellVisible(row, col)
        self.link_view = link_view
    #@-node:set_cursor
    #@+node:replace_data
    def replace_data(self, report):
        if self.grid:
            rc = (self.grid.GetGridCursorRow(), self.grid.GetGridCursorCol())
            self.GetSizer().Remove(self.grid)
            self.grid.Destroy()
        else:
            sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(sizer)
            rc = (0, 0)

        save_execute = controller().session.save_execute
        self.report = save_execute(report)

        if not self.report: self.report = _ErrorReport()
        save_execute(self.__fill_grid)
        wx.CallAfter(self.set_cursor, rc[0], rc[1], False)
        self.link_view = self.report.link_view
    #@-node:replace_data
    #@+node:__fill_grid
    def __fill_grid(self):
        self.code_info.clear()
        self.task_info.clear()

        cols = len(self.report.headers)
        col_range = range(cols)

        grid = self.grid = wx.grid.Grid(self, -1)
        grid.SetDefaultRenderer(CellRenderer(weakref.proxy(self)))
        grid.EnableGridLines(wx.VERSION[:2] == (2,4))
        grid.SetRowLabelSize(0)
        grid.CreateGrid(0, cols)

        grid.BeginBatch()
        try:
            r = 0
            for row in self.report:
                grid.AppendRows(1)

                for c in col_range:
                    try:
                        val = row[c]
                    except IndexError:
                        val = faces.report.Cell("cell not defined")
                        val.back_color = "red"

                    try:
                        strval = val.unicode(chart_tools.chart_encoding)
                    except AttributeError:
                        if isinstance(val, str):
                            strval = unicode(val, chart_tools.chart_encoding)
                        else:
                            strval = unicode(val)

                    grid.SetCellValue(r, c, strval)
                    grid.SetReadOnly(r, c)

                    ref = val.get_ref()
                    self.code_info[(r, c)] = ref[:2]
                    if ref[0]:
                        taskid = ref[0]._idendity_()
                        self.task_info[(taskid, ref[1])] = (r, c)
                        last_info = self.task_info.get((taskid, None), (r,9999))
                        self.task_info[(taskid, None)] = min((r, c), last_info)

                    align = _align_map.get(val.align, wx.ALIGN_LEFT)
                    grid.SetCellAlignment(r, c, align, wx.ALIGN_TOP)

                    if val.back_color:
                        back_color = convert_color(val.back_color)
                        grid.SetCellBackgroundColour(\
                            r, c, wx.Colour(*back_color))
                    else:
                        grid.SetCellBackgroundColour(\
                            r, c, grid.GetDefaultCellBackgroundColour())

                    if val.text_color:
                        text_color = convert_color(val.text_color)
                        grid.SetCellTextColour(r, c, wx.Colour(*text_color))
                    else:
                        grid.SetCellTextColour(\
                            r, c, grid.GetDefaultCellTextColour())

                    is_bold = val.font_bold
                    is_italic = val.font_italic
                    is_underline = val.font_underline
                    font_size = val.font_size

                    font = grid.GetDefaultCellFont()
                    if is_bold or is_italic or is_underline or font_size:
                        style = is_italic and wx.ITALIC or font.GetStyle()
                        weight = is_bold and wx.BOLD or font.GetWeight()
                        fsize = self.calc_font_size(font_size)

                        new_font = wx.Font(\
                            fsize, font.GetFamily(), style, weight,\
                            is_underline, font.GetFaceName())

                        grid.SetCellFont(r, c, new_font)
                    else:
                        grid.SetCellFont(r, c, font)


                    border_val = 0
                    if val.left_border: border_val += _LEFT
                    if val.top_border: border_val += _TOP
                    if val.right_border: border_val += _RIGHT
                    if val.bottom_border: border_val += _BOTTOM
                    if border_val != _DEFAULT and wx.VERSION[:2] != (2,4):
                        attr = grid.GetOrCreateCellAttr(r, c) #bug in 2.4
                        attr.border_val = border_val

                r += 1

            try:
                for c in col_range:
                    grid.SetColLabelValue(c, self.report.headers[c])
            except:
                pass

            grid.AutoSizeColumns()
            grid.AutoSizeRows()
            self.set_grid_notifications()


        finally:
            grid.EndBatch()
            sizer = self.GetSizer()
            sizer.Add(grid, 1, wx.EXPAND)
            sizer.Layout()
    #@-node:__fill_grid
    #@+node:calc_font_size
    def calc_font_size(self, font_size):
        grid_font_size = self.grid.GetDefaultCellFont().GetPointSize()
        if not font_size: return grid_font_size

        old_size = font.fontManager.get_default_size()
        font.fontManager.set_default_size(grid_font_size)
        fp = font.FontProperties(size=font_size)
        fsize = fp.get_size_in_points()
        font.fontManager.set_default_size(old_size)
        return fsize
    #@-node:calc_font_size
    #@+node:accept_sibling
    def accept_sibling(self, new_view):
        import editor

        if isinstance(new_view, editor.PlanEditorProxy):
            return navigator.SIBLING_BELOW

        if isinstance(new_view, ReportView):
            return navigator.SIBLING_BELOW

        return False
    #@-node:accept_sibling
    #@-others
#@-node:class ReportView
#@+node:class ExportCSV_Model
class ExportCSV_Model(db.Model):
    #@	<< class ExportCSV_Model declarations >>
    #@+node:<< class ExportCSV_Model declarations >>
    filename = db.Text(default="test.csv")
    delimiter = db.Text(";")
    quotechar = db.Text('"')
    quoting = db.Enumerate({ csv.QUOTE_ALL : _("All"),
                             csv.QUOTE_MINIMAL : _("Minimal"),
                             csv.QUOTE_NONNUMERIC : _("Non Numeric"),
                             csv.QUOTE_NONE : _("None") } )
    escapechar = db.Text("")

    #@-node:<< class ExportCSV_Model declarations >>
    #@nl
    #@	@+others
    #@+node:check_constraints
    def check_constraints(self):
        if not self.filename: 
            error = db.ConstraintError()
            error.message["filename"] = _("A filename must be specified")
            raise error
    #@-node:check_constraints
    #@+node:exporter
    def exporter(self):
        return csv.writer(file(self.filename, "w"),
                          delimiter=str(self.delimiter),
                          quoting=self.quoting,
                          quotechar=str(self.quotechar),
                          escapechar=str(self.escapechar) or None,
                          lineterminator="\n")
    #@-node:exporter
    #@-others
#@-node:class ExportCSV_Model
#@+node:class ExportCSV_View
class ExportCSV_View(views.FormView):
    __model__ = ExportCSV_Model
    __view_name__ = "default"
    format = _("""
[File: ]      |filename(SaveFile)>
[Delimiter: ] |delimiter
[Quoting:]    |quoting
[Quote Char:] |quotechar
[Escape Char:]|escapechar
(0,0)
--
(buttons)>
""")

    format_buttons = "btn_ok{r}|(0,5)|btn_cancel"

    #@	@+others
    #@+node:prepare
    def prepare(self):
        self.grow_col(1)
        self.grow_row(-3)
        self.buttons.grow_col(0)
        self.filename.set_filter(_("CSV (*.csv)|*.csv"))
        self.delimiter.set_width("8")
        self.delimiter.SetMaxLength(1)
        self.quotechar.set_width("8")
        self.quotechar.SetMaxLength(1)
        self.escapechar.set_width("8")
        self.escapechar.SetMaxLength(1)
    #@-node:prepare
    #@+node:constitute
    def constitute(self, imodel):
        views.FormView.constitute(self, imodel)
        self.state_changed("quoting")
    #@-node:constitute
    #@+node:state_changed
    def state_changed(self, attrib):
        if attrib == "quoting":
            has_escape = self.imodel.quoting == csv.QUOTE_NONE
            self.quotechar.Enable(not has_escape)
            self.escapechar.Enable(has_escape)
    #@-node:state_changed
    #@+node:button_cancel
    def button_cancel(self):
        self.rollback()
        self.GetParent().GetParent().EndModal(wx.ID_CANCEL)
    #@-node:button_cancel
    #@+node:button_ok
    def button_ok(self):
        if self.save():
            self.GetParent().GetParent().EndModal(wx.ID_OK)
    #@-node:button_ok
    #@-others
#@-node:class ExportCSV_View
#@+node:class ExportCSV_Dialog
class ExportCSV_Dialog(wx.Dialog):
    #@	@+others
    #@+node:__init__
    def __init__(self, parent, name):
        wx.Dialog.__init__(self, parent, -1, _("Export CSV"),
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.name = name
    #@-node:__init__
    #@+node:ShowModal
    def ShowModal(self):
        container = views.ScrollViewContainer(self)
        self.data = ExportCSV_Model(filename=self.name + ".csv")
        self.data.constitute("default")(container)
        container.fit_size()
        self.SetClientSize(container.GetSize())
        result = wx.Dialog.ShowModal(self)
        return result

    #@-node:ShowModal
    #@-others
#@-node:class ExportCSV_Dialog
#@-others
#@-node:@file gui/repview.py
#@-leo
