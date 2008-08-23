#@+leo-ver=4
#@+node:@file gui/print_chart.py
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
import metapie
import metapie.dbtransient as db
import metapie.gui.views as views
import faces.charting.printer as prnt
import faces.charting.charts as charts
import faces.gui.patches as patches
import faces.plocale
import tempfile
import os
import os.path
import utils



#@-node:<< Imports >>
#@nl

_is_source_ = True
_ = faces.plocale.get_gettext()


papersize = {\
         "Letter" : ( 612, 792 ),
         "Legal" : ( 612, 1008 ),
         "Tabloid" :  ( 792, 1224 ),
         "Ledger" :   ( 792, 1224 ),
         "Executive" :( 540, 720 ),
         "Monarch" :  ( 279, 540 ),
         "Statement" :( 396, 612 ),
         "Folio" :    ( 612, 936 ),
         "Quarto" :   ( 610, 780 ),
         "C5" :       ( 459, 649 ),
         "B4" :       ( 729, 1032 ),
         "B5" :       ( 516, 729 ),
         "Dl" :       ( 312, 624 ),
         "A0" :	      ( 2380, 3368 ),
         "A1" :	      ( 1684, 2380 ),
         "A2" :	      ( 1190, 1684 ),
         "A3" :	      ( 842, 1190 ),
         "A4" :       ( 595, 842 ),
         "A5" :	      ( 420, 595 ),
         "A6" :	      ( 297, 421 ),
         "custom" :   None }

paper_choices = dict(zip(papersize.keys(), papersize.keys()))
scale_choices = { "no_scale" : _("no scaling") }
scale_choices.update(paper_choices)



#@+others
#@+node:class ChartPrinter
class ChartPrinter(db.Model):
    #@	<< declarations >>
    #@+node:<< declarations >>
    filename = db.Text(none=True, default="")
    unit = db.Enumerate({ 'cm' : _('cm'),
                          'mm' : _('mm'),
                          'inch' : _('inch'),
                          'point' : _('point'),
                          'pixel' : _('pixel') },
                        default="pixel")

    scale = db.Enumerate(scale_choices, default="no_scale")
    media = db.Enumerate(paper_choices, default="custom")
    media_size = db.Text("test")
    dpi = db.Int(default=72)
    command = db.Text(multi_line=True)
    edgecolor = db.Text(default="black")
    linewidth = db.Float(1.0)
    width = db.Float(width=7)
    height = db.Float(width=7)
    poster = db.Boolean()
    print_out_number = 0

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, printer):
        super(ChartPrinter, self).__init__()
        self.filename = None
        self.chart_name = printer._chart.__name__
        self.printer = printer
        self.printer.type = "eps"
        self.printer.unit = "mm"
        self.refresh()
        self.calc_command()
        self.attach_weak(self)
        self.calc_media_size()
    #@-node:__init__
    #@+node:refresh
    def refresh(self):
        self.printer.refresh()
        self._chart_instance = self.printer._chart_instance
    #@-node:refresh
    #@+node:reset_valid
    def reset_valid(self):
        if not self.printer.valid:
            self.printer._chart_instance = self._chart_instance
    #@-node:reset_valid
    #@+node:__call__
    def __call__(self, attrib):
        if attrib != "command":
            self.calc_command()

        self._fire_others(attrib)

        if attrib in ("unit", "media", "width", "height"):
            self.calc_media_size()

        if attrib in ("unit", "dpi", "font_size"):
            #if the unit changes the size changes also
            self.fire("width", "width")
            self.fire("height", "height")
            return
    #@-node:__call__
    #@+node:_fire_others
    def _fire_others(self, attrib):
        pass
    #@-node:_fire_others
    #@+node:_get_filename
    def _get_filename(self, org):
        if org: return self.printer.filename
        return org
    #@-node:_get_filename
    #@+node:_set_filename
    def _set_filename(self, value):
        if value:
            dpi = self.dpi
            self.printer.filename = value
            if dpi != self.dpi:
                self.dpi = self.dpi

        return value
    #@-node:_set_filename
    #@+node:_get_unit
    def _get_unit(self, org):
        return self.printer.unit
    #@-node:_get_unit
    #@+node:_set_unit
    def _set_unit(self, value):
        self.printer.unit = value
        return value
    #@-node:_set_unit
    #@+node:_get_width
    def _get_width(self, org):
        self.reset_valid()
        return self.printer.width
    #@-node:_get_width
    #@+node:_set_width
    def _set_width(self, value):
        self.reset_valid()
        self.printer.width = value
        return value
    #@-node:_set_width
    #@+node:_get_height
    def _get_height(self, org):
        self.reset_valid()
        return self.printer.get_height()
    #@-node:_get_height
    #@+node:_set_height
    def _set_height(self, value):
        self.reset_valid()
        self.printer.height = value
    #@-node:_set_height
    #@+node:_get_dpi
    def _get_dpi(self, org):
        self.reset_valid()
        return int(self.printer.dpi)
    #@-node:_get_dpi
    #@+node:_set_dpi
    def _set_dpi(self, value):
        self.printer.dpi = value
        return self.printer.dpi
    #@-node:_set_dpi
    #@+node:calc_media_size
    def calc_media_size(self):
        unit = self.unit
        if unit == "pixel": unit = "point"
        size = papersize.get(self.media)
        if not size:
            size = (self.width, self.height)
        else:
            point_factor = prnt.ChartPrinter._point_factor
            size = map(lambda s: s / point_factor[unit], size)

        if self.printer.width < self.printer.height:
            w, h = size
        else:
            h, w = size

        self.media_size = "%0.2f x %0.2f %s" % (w, h, unit)

    #@-node:calc_media_size
    #@+node:calc_command
    def calc_command(self):
        command = "printer = %s.printer()" % self.chart_name

        if self.filename is not None:
            command += '\nprinter.filename = "%s"' % self.filename

        command += '\nprinter.linewidth = %.2f' % self.linewidth
        command += '\nprinter.edgecolor = "%s"' % self.edgecolor
        command += '\nprinter.unit = "%s"' % self.unit

        if self.printer.type != "eps":
            command += '\nprinter.dpi = %i' % self.dpi

        command = self.add_command_attributes(command)

        if self.filename is not None:
            command += '\nprinter.save()'

        command += '\nprinter.end()'
        self.command = command.strip()
    #@-node:calc_command
    #@+node:add_command_attributes
    def add_command_attributes(self, command):
        return command
    #@-node:add_command_attributes
    #@+node:check_constraints
    def check_constraints(self):
        error = db.ConstraintError()

        if self.filename: 
            for e in prnt.ChartPrinter._extensions:
                if self.filename.endswith(e): return
            else:
                error.message["filename"] = _("""File name must have one of the following extensions:
    %s""") % str(prnt.ChartPrinter._extensions)

        elif self.poster and self.media == "custom":
            error.message["media"] = _("""For poster printing, you have to set
    a standard output media""")

        if error.message:
            raise error
    #@-node:check_constraints
    #@+node:save
    def save(self):
        self.printer.edgecolor = self.edgecolor
        self.printer.linewidth = self.linewidth

        if self.filename is None:
            tmpdir = tempfile.gettempdir()
            number = self.__class__.print_out_number
            self.__class__.print_out_number += 1

            #make shure the temp filename is an 8.3 name
            #poster doesn't like larger names under windows
            eps_path = os.path.join(tmpdir, "fpr%05i.eps" % number)
            self.printer.filename = eps_path
            self.printer.refresh()
            if self.printer.width < self.printer.height:
                self.printer.orientation = "portrait"
            else:
                self.printer.orientation = "landscape"

            to_remove = metapie.controller().session.tmp_files_to_remove
            pdf_path = eps_path.replace(".eps", ".pdf")
            size = self.printer._figure.get_size_inches()

            if self.poster:
                to_remove.append(eps_path)
                self.printer.save()

                if self.scale == "no_scale":
                    scale = "%.2fx%.2fi" % size
                else:
                    scale = self.scale

                ps_path = eps_path.replace(".eps", ".ps")
                to_remove.append(ps_path)

                media = self.media
                if media == "custom":
                    raise ValueError("media may not be custom")

                arguments = ("-p%s" % scale,
                             "-m%s" % media,
                             "-o%s" % ps_path,
                             eps_path)

                utils.call_command("poster", arguments,
                                   "Poster",
                                   "http://www.geocities.com/SiliconValley/5682/poster.html")

                self.call_ps2pdf(ps_path, pdf_path)
            else:
                to_remove.append(eps_path)
                self.printer.save()
                if self.media == "custom":
                    args = ('-dDEVICEWIDTHPOINTS=%i' % (size[0] * 72),
                            '-dDEVICEHEIGHTPOINTS=%i' % (size[1] * 72),
                            '-dEPSFitPage')
                else:
                    args = ('-sPAPERSIZE=%s' % self.media.lower(),)
                self.call_ps2pdf(eps_path, pdf_path, args)

                #the next two lines would be the easier an cleaner implementation
                #but the pdf_backend cannot handle unicode
                #self.printer.filename = pdf_path
                #self.printer.save()

            to_remove.append(pdf_path)

            import webbrowser
            webbrowser.open("file://%s" % pdf_path, True, False)
        else:
            self.printer.save()
    #@-node:save
    #@+node:call_ps2pdf
    def call_ps2pdf(self, input, output, args=()):
        arguments = ('-dCompatibilityLevel=1.4',
                     "-dQUIET",
                     '-dNOPAUSE',
                     '-dBATCH',
                     '-sDEVICE=pdfwrite',
                     '-sOutputFile=%s' % output,
                     '-c.setpdfwrite',
                     '-f%s' % input) + args
        utils.call_command("gs", arguments,
                           "Ghostscript",
                           "http://www.cs.wisc.edu/~ghost/doc/GPL/index.htm")
    #@-node:call_ps2pdf
    #@-others
#@-node:class ChartPrinter
#@+node:class LimitsPrinter
#different printers for the type of the widget_axes of the chart

class LimitsPrinter(ChartPrinter):
    #@	<< declarations >>
    #@+node:<< declarations >>
    xmin = db.Float(width=7)
    xmax = db.Float(width=7)
    ymin = db.Float(width=7)
    ymax = db.Float(width=7)


    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, printer):
        super(LimitsPrinter, self).__init__(printer)
    #@-node:__init__
    #@+node:zoom
    def zoom(self):
        self.printer.autoscale()
        self.fire("width", "width")
        self.fire("height", "height")
        self.fire("xmin", "xmin")
        self.fire("ymin", "ymin")
        self.fire("tmin", "tmin")
        self.fire("xmax", "xmax")
        self.fire("ymax", "ymax")
        self.fire("tmax", "tmax")
    #@-node:zoom
    #@+node:_fire_others
    def _fire_others(self, attrib):
        super(LimitsPrinter, self)._fire_others(attrib)

        if attrib == "width":
            self.fire("xmin", "xmin")
            self.fire("xmax", "xmax")
            return

        if attrib == "height":
            self.fire("ymin", "ymin")
            self.fire("ymax", "ymax")
            return

        if attrib in ("unit", "dpi", "font_size"):
            self.fire("xmin", "xmin")
            self.fire("ymin", "ymin")
            self.fire("tmin", "tmin")
            self.fire("xmax", "xmax")
            self.fire("ymax", "ymax")
            self.fire("tmax", "tmax")
            return

        if attrib in ("xmin", "xmax"):
            self.fire("width", "width")
            return

        if attrib in ("ymin", "ymax"):
            self.fire("height", "height")
            return
    #@-node:_fire_others
    #@+node:_set_xmin
    def _set_xmin(self, value):
        self.printer.set_xlimits(xmin=value)
        return value
    #@-node:_set_xmin
    #@+node:_set_xmax
    def _set_xmax(self, value):
        self.printer.set_xlimits(xmax=value)
        return value
    #@-node:_set_xmax
    #@+node:_set_ymin
    def _set_ymin(self, value):
        self.printer.set_ylimits(ymin=value)
        return value
    #@-node:_set_ymin
    #@+node:_set_ymax
    def _set_ymax(self, value):
        self.printer.set_ylimits(ymax=value)
        return value
    #@-node:_set_ymax
    #@+node:_get_xmin
    def _get_xmin(self, value):
        self.reset_valid()
        return self.printer.get_xlimits()[0]
    #@-node:_get_xmin
    #@+node:_get_xmax
    def _get_xmax(self, value):
        self.reset_valid()
        return self.printer.get_xlimits()[1]
    #@-node:_get_xmax
    #@+node:_get_ymin
    def _get_ymin(self, value):
        self.reset_valid()
        return self.printer.get_ylimits()[0]
    #@-node:_get_ymin
    #@+node:_get_ymax
    def _get_ymax(self, value):
        self.reset_valid()
        return self.printer.get_ylimits()[1]
    #@-node:_get_ymax
    #@+node:set_max_limits
    def set_max_limits(self):
        self.printer.set_xlimits()
        self.printer.set_ylimits()
        self.y_limits.min, self.y_limits.max = self.printer.get_ylimits()
    #@-node:set_max_limits
    #@+node:add_command_attributes
    def add_command_attributes(self, command):
        command = super(LimitsPrinter, self).add_command_attributes(command)
        command += "\nprinter.set_xlimits(%.2f, %.2f)" % (self.xmin, self.xmax)
        command += "\nprinter.set_ylimits(%.2f, %.2f)" % (self.ymin, self.ymax)
        return command
    #@-node:add_command_attributes
    #@-others
#@-node:class LimitsPrinter
#@+node:class WidgetPrinter
class WidgetPrinter(LimitsPrinter):
    #@	<< declarations >>
    #@+node:<< declarations >>
    font_size = db.Int()

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:_get_font_size
    def _get_font_size(self, org):
        return self.printer.font_size
    #@-node:_get_font_size
    #@+node:_set_font_size
    def _set_font_size(self, value):
        value = max(value, 2)
        self.printer.font_size = value
        self.refresh()
        return value
    #@-node:_set_font_size
    #@+node:add_command_attributes
    def add_command_attributes(self, command):
        command = super(WidgetPrinter, self).add_command_attributes(command)
        command += '\nprinter.fontsize = %i' % self.font_size
        return command
    #@-node:add_command_attributes
    #@-others
#@-node:class WidgetPrinter
#@+node:class TimePrinter
class TimePrinter(db.Model):
    #@	<< declarations >>
    #@+node:<< declarations >>
    tmin = db.DateTime()
    tmax = db.DateTime()


    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, *args, **kwargs):
        super(TimePrinter, self).__init__(*args, **kwargs)
    #@-node:__init__
    #@+node:_set_tmin
    def _set_tmin(self, value):
        self.printer.set_time_limits(min=value)
        return value
    #@-node:_set_tmin
    #@+node:_set_tmax
    def _set_tmax(self, value):
        self.printer.set_time_limits(max=value)
        return value
    #@-node:_set_tmax
    #@+node:_get_tmin
    def _get_tmin(self, value):
        self.reset_valid()
        return self.printer.get_time_limits()[0]
    #@-node:_get_tmin
    #@+node:_get_tmax
    def _get_tmax(self, value):
        self.reset_valid()
        return self.printer.get_time_limits()[1]
    #@-node:_get_tmax
    #@+node:add_command_attributes
    def add_command_attributes(self, command):
        command = super(TimePrinter, self).add_command_attributes(command)
        command += '\nprinter.width = %.2f' % self.width
        return command
    #@-node:add_command_attributes
    #@-others
#@-node:class TimePrinter
#@+node:class TimeWidgetPrinter
class TimeWidgetPrinter(TimePrinter, WidgetPrinter, ChartPrinter):
	pass
#@-node:class TimeWidgetPrinter
#@+node:class TimePlotPrinter
class TimePlotPrinter(TimePrinter, LimitsPrinter):
    #@	@+others
    #@+node:add_command_attributes
    def add_command_attributes(self, command):
        command = super(TimePlotPrinter, self).add_command_attributes(command)
        command += '\nprinter.height = %.2f' % self.height
        return command
    #@-node:add_command_attributes
    #@-others
#@-node:class TimePlotPrinter
#@+node:class PointPrinter
class PointPrinter(WidgetPrinter, LimitsPrinter):
    pass

#@-node:class PointPrinter
#@+node:class PrinterView
class PrinterView(views.FormView):
#@<< declarations >>
#@+node:<< declarations >>
    __model__ = ChartPrinter
    __view_name__ = "default"

    format = _("""
[File: ]     |filename(SaveFile)>
[Edgecolor: ]|edgecolor(Color)|[Linewidth: ]|linewidth
[Unit:]      |unit
%s
(canvas)>
--
(cmd_or_print)>
--
(buttons)>
""")

    format_cmd_or_print = """
(Command)>|(Printer)>
"""

    format_Printer = _("""
[Printer:]
(0,0)            |poster[Print as Poster]
[Scale To Size: ]|scale
[Output Media: ] |media|media_size(Static)
""")

    format_Command = _("""
[Command:]
command>
""")

    format_buttons = "btn_print{r}|btn_save{r}|(0,5)|btn_cancel"
    viewlimit = ""
    format_canvas = """
[Canvas Size:]
[ Size: ]      |(size)
[ Resolution:] |dpi|[ dpi]
"""

    format_size = "width|[ x ]|height|[ ]|unit"

#@-node:<< declarations >>
#@nl
    #@	@+others
    #@+node:__init__
    def __init__(self, *args, **kwargs):
        self.format = self.format % self.viewlimit
        super(PrinterView, self).__init__(*args, **kwargs)
    #@-node:__init__
    #@+node:create_buttons_controls
    def create_buttons_controls(self, view):
        view.btn_print = view.get_button(wx.ID_PRINT)
        def prnt():
            if self.save(): self.imodel.save()
        view.btn_print.attach(prnt)
    #@-node:create_buttons_controls
    #@+node:prepare
    def prepare(self):
        self.grow_col(1)
        self.grow_row(-3)

        self.cmd_or_print.grow_col(0)
        self.cmd_or_print.grow_col(1)
        self.cmd_or_print.grow_row(0)

        self.cmd_or_print.Printer.grow_col(-1)
        self.cmd_or_print.Command.grow_col(0)
        self.cmd_or_print.Command.grow_row(1)

        self.buttons.grow_col(0)
        self.filename.set_filter(_("EPS (*.eps)|*.eps|"  \
                                   "SVG (*.svg)|*.svg|"  \
                                   "BMP (*.bmp)|*.bmp|"  \
                                   "PNG (*.png)|*.png"))
        self.filename.set_width("X" * 20)
        self.canvas.dpi.set_width("8888")
        self.canvas.dpi.SetMaxLength(4)
        self.cmd_or_print.Command.command.set_height(6)
        self.cmd_or_print.Command.command.SetEditable(False)
        self._prepare_others()
    #@-node:prepare
    #@+node:modify_subview
    def modify_subview(self, subview, name):
        if name in ("limits", "size"):
            subview.hgap = subview.vgap = 0

        return subview
    #@-node:modify_subview
    #@+node:_prepare_others
    def _prepare_others(self):
        pass
    #@-node:_prepare_others
    #@+node:button_cancel
    def button_cancel(self):
        self.rollback()
        self.GetParent().GetParent().EndModal(wx.ID_CANCEL)
    #@-node:button_cancel
    #@+node:button_save
    def button_save(self):
        if self.save():
            self.imodel.save()
            self.GetParent().GetParent().EndModal(wx.ID_OK)
    #@-node:button_save
    #@+node:make_size_int
    def make_size_int(self):
        self.canvas.size.width.SetFractionWidth(0)
        self.canvas.size.height.SetFractionWidth(0)
        self.canvas.size.layout()
    #@-node:make_size_int
    #@+node:make_size_float
    def make_size_float(self):
        self.canvas.size.width.SetFractionWidth(2)
        self.canvas.size.height.SetFractionWidth(2)
        self.canvas.layout()
    #@-node:make_size_float
    #@+node:state_changed
    def state_changed(self, attrib):
        if attrib == "unit":
            if self.imodel.unit in ('pixel', 'mm', 'point'):
                self.make_size_int()
            else:
                self.make_size_float()
            return

        if attrib == "filename":
            value = self.imodel.filename

            if not value or value.endswith("ps"):
                self.canvas.dpi.Enable(False)
            else:
                self.canvas.dpi.Enable(True)

            if value is None:
                self.buttons.btn_save.Hide()
                self.cmd_or_print.Command.Hide()
                self.buttons.btn_print.Show()
                self.cmd_or_print.Printer.Show()
                self.cmd_or_print.ungrow_col(0)
                self.cmd_or_print.grow_col(1)
                self.cmd_or_print.Printer.layout()
            else:
                self.buttons.btn_save.Show()
                self.cmd_or_print.Command.Show()
                self.buttons.btn_print.Hide()
                self.cmd_or_print.Printer.Hide()
                self.cmd_or_print.ungrow_col(1)
                self.cmd_or_print.grow_col(0)
                self.cmd_or_print.Command.layout()

            self.buttons.layout()
            return

        if attrib == "poster":
            self.cmd_or_print.Printer.scale.Enable(self.imodel.poster)
    #@-node:state_changed
    #@+node:constitute
    def constitute(self, imodel):
        views.FormView.constitute(self, imodel)
        self.state_changed("filename")
        self.state_changed("unit")
        self.state_changed("poster")
    #@-node:constitute
    #@-others
#@-node:class PrinterView
#@+node:class LimitsPrinterView
class LimitsPrinterView(object):
    viewlimit = """
auto_scale>
(viewlimit)>
"""

    format_viewlimit = """
[View Limits:]
[Horizontal: ]|xmin|[ - ]|xmax
[Vertical: ]  |ymin|[ - ]|ymax|[]
--
"""

    #@	@+others
    #@+node:_prepare_others
    def _prepare_others(self):
        self.viewlimit.grow_col(-1)
        super(LimitsPrinterView, self)._prepare_others()
    #@-node:_prepare_others
    #@+node:create_controls
    def create_controls(self):
        super(LimitsPrinterView, self).create_controls()
        self.auto_scale = self.get_button("Zoom To Extends")
        def zoom():
            self.imodel.zoom()

        self.auto_scale.attach(zoom)
    #@-node:create_controls
    #@-others
#@-node:class LimitsPrinterView
#@+node:class WidgetPrinterView
class WidgetPrinterView(LimitsPrinterView):
    format_canvas = """
[Canvas Size:]
[Size: ]      |(size)
[Font size:]  |font_size|[  Resolution:] |dpi|[ dpi]
"""

    viewlimit = """
auto_scale>
(viewlimit)>"""

    #@	@+others
    #@+node:_prepare_others
    def _prepare_others(self):
        self.canvas.font_size.SetMaxLength(2)
        self.canvas.font_size.set_width("88")
        self.canvas.font_size.SetToolTipString(_("Size of standard font in Points"))
        super(WidgetPrinterView, self)._prepare_others()
    #@-node:_prepare_others
    #@-others
#@-node:class WidgetPrinterView
#@+node:class TimePrinterView
class TimePrinterView(object):
    format_viewlimit = """
[View Limits:]
[Horizontal: ]|tmin|[ - ]|tmax
[Vertical: ]  |ymin|[ - ]|ymax
--
"""
#@-node:class TimePrinterView
#@+node:class TimePlotPrinterView
class TimePlotPrinterView(TimePrinterView, LimitsPrinterView, PrinterView):
    __model__ = TimePlotPrinter
    __view_name__ = "default"    
#@-node:class TimePlotPrinterView
#@+node:class TimeWidgetPrinterView
class TimeWidgetPrinterView(TimePrinterView, WidgetPrinterView, PrinterView):
    __model__ = TimeWidgetPrinter
    __view_name__ = "default"    

#@-node:class TimeWidgetPrinterView
#@+node:class PointPrinterView
class PointPrinterView(WidgetPrinterView, PrinterView):
    __model__ = PointPrinter
    __view_name__ = "default"    
#@-node:class PointPrinterView
#@+node:class PrintChart
class PrintChart(patches.PatchedDialog):
    #@	@+others
    #@+node:__init__
    def __init__(self, parent, chart):
        wx.Dialog.__init__(self, parent, -1, _("Print Chart"),
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)


        if isinstance(chart, charts.MatplotChart):
            try:
                axes = chart.widget_axes()
            except AttributeError:
                axes = chart.axes

            figure = axes.get_figure()
            kwargs = { "xlimits": axes.get_xlim(),
                       "ylimits": axes.get_ylim(),
                       "dpi": figure.get_dpi(),
                       "size": figure.get_size_inches(),
                       "type": "png" }
        else:
            kwargs = {}

        printer = chart.printer(**kwargs)

        if isinstance(printer, prnt.TimePlotPrinter):
            model = TimePlotPrinter

        elif isinstance(printer, prnt.TimeWidgetPrinter):
            model = TimeWidgetPrinter

        elif isinstance(printer, prnt.PointPrinter):
            model = PointPrinter

        else:
            model = ChartPrinter

        self.data = model(printer)
    #@-node:__init__
    #@+node:ShowModal
    def simulate_modal(self, focused):
        container = views.ScrollViewContainer(self)
        view = self.data.constitute("default")(container)

        def resize():
            w, h = view.GetSize()
            container.SetClientSize((w + 10, h + 40))
            self.SetClientSize(container.GetSize())

        wx.CallAfter(resize)

        def end_dialog():
            self.data.printer.end()
            view.end_inspect()

        patches.PatchedDialog.simulate_modal(self, focused, end_dialog)
    #@-node:ShowModal
    #@-others
#@-node:class PrintChart
#@-others
#@-node:@file gui/print_chart.py
#@-leo
