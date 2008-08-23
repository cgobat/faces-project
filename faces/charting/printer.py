############################################################################
#   Copyright (C) 2005 by Reithinger GmbH
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

import matplotlib.figure as figure
import matplotlib.font_manager as font
import renderer
import tools
import widgets
import tempfile
import os.path


class ChartPrinter(object):
    """
    Prints out a chart to a specific format
    """

    _point_factor = { "cm" : 72.0/2.54,
                      "mm" : 72.0/25.4,
                      "inch" : 72.0,
                      "point" : 1.0 }

    _extensions = ( "eps", "svg", "bmp", "png", "pdf" )

    def __init__(self, chart, **kwargs):
        self.unit = kwargs.get("unit", 'point')
        self._type = kwargs.get("type", "eps")
        self.linewidth = kwargs.get("linewidth", 1.0)
        self.edgecolor = kwargs.get("edgecolor", 'black')
        dpi = kwargs.get("dpi", 72)
        size = kwargs.get("size", (10, 10))
        self._figure = figure.Figure(size, dpi, linewidth=0.0)
        self._chart = chart
        self._chart_instance = None
        self._default_font_size = font.fontManager.get_default_size()
        self._filename = ""
        self.orientation = "portrait"
        

    def flipy(self):
        return True
    

    def __del__(self):
        self._figure.set_canvas(None)
        self.end()


    def to_point(self, value):
        if self.unit == "pixel":
            return (72 * value) / self.dpi
        
        return value * self._point_factor[self.unit]


    def from_point(self, value):
        if self.unit == "pixel": return (value * self.dpi) / 72
        return value / self._point_factor[self.unit]


    def get_dpi(self):
        return self._figure.get_dpi()


    def set_dpi(self, dpi):
        if self._type == "eps": dpi = 72
        self._figure.set_dpi(dpi)
        widgets.LazyText.height_cache.clear()
        
        
    dpi = property(get_dpi, set_dpi)


    def set_filename(self, filename):
        self._filename = filename

        for e in self._extensions:
            if self._filename.endswith(e) \
                   or self._filename.endswith(e.upper()):
                if e != self._type:
                    self.type = e
                    
                return
        
        if not self._filename.endswith(self._type) \
               and not self._filename.endswith(self._type.upper()):
            self._filename += "." + self._type
        

    def get_filename(self):
        return self._filename

    filename = property(get_filename, set_filename)


    def set_type(self, type):
        if type not in self._extensions:
            raise ValueError("type '%s' not known" % type)
        
        self._type = type

        if type == "eps" and self.dpi != 72:
            self.dpi = 72

        self._chart_instance = None
            

    def get_type(self):
        return self._type

    type = property(get_type, set_type)
        

    def set_font_size(self, font_size):
        tools.set_default_size(font_size)
        self._chart_instance = None


    def get_font_size(self):
        return font.fontManager.get_default_size()

    font_size = property(get_font_size, set_font_size)


    def get_valid(self):
        return bool(self._chart_instance)


    valid = property(get_valid)

    def refresh(self):
        canvas = renderer.PatchedFigureCanvasAgg
        from charts import _figure_manager
        self._figure.clf()
        _figure_manager.canvas = canvas(self._figure)
        self._figure.set_canvas(_figure_manager.canvas)
        self._chart_instance = self._chart(self._figure)


    def save(self):
        if not self.valid: self.refresh()
        self._chart_instance._check_limits(False)
        self._set_frame()
        self._figure.figurePatch.set_linewidth(self.linewidth)
        canvas = self._figure.canvas

        if self.type == "pdf":
            from matplotlib.backends.backend_pdf import FigureCanvasPdf
            canvas = canvas.switch_backends(FigureCanvasPdf)

        canvas.print_figure(self.filename, self.dpi,
                            facecolor=self._figure.get_facecolor(),
                            edgecolor=self.edgecolor,
                            orientation=self.orientation)
        

    def check_valid(self):
        if self.valid: return
        raise RuntimeError("The printer state is invalid call 'refresh' "\
                           "to make it valid")


    def end(self):
        tools.set_default_size(self._default_font_size)
        widgets.LazyText.height_cache.clear()


    def get_margins(self):
        return 0, 0, 0, 0


    def _set_frame(self):
        pass


class FreePrinter(ChartPrinter):
    #equally to 1024 x 786 pixels with 64 dpi
    _width = 1152 
    _height = 864

    def __init__(self, chart, **kwargs):
        ChartPrinter.__init__(self, chart, **kwargs)
        size = kwargs.get("size")
        if size:
            self._width = size[0] * 72
            self._height = size[1] * 72
            

    def flipy(self):
        return True

    
    def get_width(self):
        return self.from_point(self._width)


    def set_width(self, width):
        self._width = self.to_point(width)
        self._figure.set_figsize_inches(self._width/72.0, self._height/72.0)
        

    width = property(get_width, set_width)


    def get_height(self):
        return self.from_point(self._height)


    def set_height(self, height):
        self._height = self.to_point(height)
        self._figure.set_figsize_inches(self._width/72.0, self._height/72.0)
   
    
    height = property(get_height, set_height)



class TimePlotPrinter(FreePrinter):
    def __init__(self, chart, **kwargs):
        FreePrinter.__init__(self, chart, **kwargs)
        self.set_ylimits(*kwargs.get("ylimits", (None, None)))
        self.set_xlimits(*kwargs.get("xlimits", (None, None)))
        

    def refresh(self):
        FreePrinter.refresh(self)
        self.autoscale(False)
        self._set_limits()


    def _set_limits(self):
        if not self.valid: return False
        chart = self._chart_instance
        chart._set_ylim(ymin=self._ylimits[0], ymax=self._ylimits[1])
        chart._set_time_lim(*self._time_limits)
        return True


    def set_time_limits(self, min=None, max=None):
        self._time_limits = (min, max)
        self._set_limits()


    def get_time_limits(self):
        self.check_valid()
        return self._chart_instance._get_time_lim()


    def set_xlimits(self, min=None, max=None):
        self._time_limits = (min and int(min), max and int(max))
        self._set_limits()


    def get_xlimits(self):
        self.check_valid()
        return self._chart_instance._get_xlim()
        

    def get_ylimits(self):
        self.check_valid()
        return self._chart_instance._get_ylim()

        
    def set_ylimits(self, ymin=None, ymax=None):
        self._ylimits = (ymin, ymax)
        self._set_limits()


    def _set_frame(self):
        chart = self._chart_instance
        patch = chart._axes_patch
        chart._set_frame_on(True)
        patch.set_fill(False)
        self._figure.set_facecolor(patch.get_facecolor())
        patch.set_linewidth(self.linewidth)
        patch.set_edgecolor(self.edgecolor)

        
    def autoscale(self, set=True):
        if not self.valid: self.refresh()
        chart = self._chart_instance
        chart._set_autoscale_on(True)
        chart._autoscale_view()
        if set:
            self._ylimits = chart._get_ylim()
            self._time_limits = chart._get_time_lim()

        

class WidgetPrinter(ChartPrinter):
    def __init__(self, chart, **kwargs):
        ChartPrinter.__init__(self, chart, **kwargs)
        self._ylimits = kwargs.get("ylimits", (None, None))
        unit = self.unit
        self.unit = "point"
        self.set_xlimits(*kwargs.get("xlimits", (None, None)))
        self.unit = unit


    def flipy(self):
        return False


    def set_height(self, value):
        self.check_valid()
        value = self.to_point(value)
        chart = self._chart_instance
        ymin, ymax = chart._get_ylim()
        bottom = chart._right_margin.get()
        top = chart._top_margin.get()
        value -= (bottom + top)
        self._ylimits = (ymax - value, ymax)
        self._set_limits()
       

    def set_ylimits(self, ymin=None, ymax=None):
        ymin = ymin and -self.to_point(ymin)
        ymax = ymax and -self.to_point(ymax)
        self._ylimits = (ymax, ymin)
        self._set_limits()
        

    def get_height(self):
        self.check_valid()
        chart = self._chart_instance
        margin = chart._top_margin.get() + chart._bottom_margin.get()
        return self.from_point(chart._view_lim.height() + margin)
        
    height = property(get_height, set_height)
    

    def get_ylimits(self):
        self.check_valid()
        ymin, ymax = self._chart_instance._get_ylim()
        return self.from_point(-ymax), self.from_point(-ymin)
        

    def set_ylimits(self, ymin=None, ymax=None):
        ymin = ymin and -self.to_point(ymin)
        ymax = ymax and -self.to_point(ymax)
        self._ylimits = (ymax, ymin)
        self._set_limits()


    def refresh(self):
        ChartPrinter.refresh(self)
        self.autoscale(False)
        self._set_limits()
        self._correct_size()
                

    def get_margins(self):
        self.check_valid()
        chart = self._chart_instance
        left = chart._left_margin.get()
        right = chart._right_margin.get()
        top = chart._top_margin.get()
        bottom = chart._bottom_margin.get()
        return map(self.from_point, (left, top, right, bottom))


    def _set_frame(self):
        chart = self._chart_instance
        patch = chart._axes_patch
        chart._set_frame_on(True)
        patch.set_fill(False)
        self._figure.set_facecolor(patch.get_facecolor())
        patch.set_linewidth(self.linewidth)
        patch.set_edgecolor(self.edgecolor)


    def _set_limits(self):
        if not self.valid: return False
        chart = self._chart_instance
        chart._set_ylim(ymin=self._ylimits[0], ymax=self._ylimits[1])
        return True


    def autoscale(self, set=True):
        if not self.valid: self.refresh()
        chart = self._chart_instance
        chart._set_autoscale_on(True)
        chart._set_auto_scale_y(False)
        chart._autoscale_view(False)
        chart._set_ylim(chart._data_lim.intervaly().get_bounds())
        if set: self._ylimits = chart._get_ylim()


    def _correct_size(self):
        raise RuntimeError("abstract")
    

class TimeWidgetPrinter(WidgetPrinter):
    _width = 1152

    def __init__(self, chart, **kwargs):
        WidgetPrinter.__init__(self, chart, **kwargs)
        size = kwargs.get("size")
        if size:
            self._width = size[0] * 72


    def get_width(self):
        return self.from_point(self._width)


    def set_width(self, width):
        self._width = self.to_point(width)
        height = self._figure.get_figheight()
        self._figure.set_figsize_inches(self._width/72.0, height)
                
    width = property(get_width, set_width)


    def set_time_limits(self, min=None, max=None):
        self._time_limits = (min, max)
        self._set_limits()


    def get_time_limits(self):
        self.check_valid()
        return self._chart_instance._get_time_lim()
       

    def set_xlimits(self, min=None, max=None):
        self._time_limits = (min and int(min), max and int(max))
        self._set_limits()


    def get_xlimits(self):
        self.check_valid()
        return self._chart_instance._get_xlim()


    def _set_limits(self):
        if WidgetPrinter._set_limits(self):
            chart = self._chart_instance
            chart._set_time_lim(*self._time_limits)
            self._correct_size()


    def _correct_size(self):
        if not self.valid: return
        chart = self._chart_instance
        margin = chart._top_margin.get() + chart._bottom_margin.get()
        height = chart._view_lim.height() + margin
        self._figure.set_figsize_inches(self._width/72.0, height/72.0)
        self._chart_instance._check_limits(False)


    def autoscale(self, set=True):
        WidgetPrinter.autoscale(self, set)
        if set:
            chart = self._chart_instance
            self._time_limits = chart._get_time_lim()
            self._correct_size()


class PointPrinter(WidgetPrinter):
    def __init__(self, chart, **kwargs):
        WidgetPrinter.__init__(self, chart, **kwargs)


    def set_width(self, value):
        self.check_valid()
        chart = self._chart_instance
        xmin, xmax = self.get_xlimits()
        left = chart._left_margin.get()
        right = chart._right_margin.get()
        value -= (left + right)
        self.set_xlimits(xmin, xmin + value)

    
    def get_width(self):
        self.check_valid()
        chart = self._chart_instance
        margin = chart._left_margin.get() + chart._right_margin.get()
        return self.from_point(chart._view_lim.width() + margin)
        
    width = property(get_width, set_width)


    def get_xlimits(self):
        self.check_valid()
        xmin, xmax = self._chart_instance._get_xlim()
        return self.from_point(xmin), self.from_point(xmax)


    def set_xlimits(self, xmin=None, xmax=None):
        xmin = xmin and self.to_point(xmin)
        xmax = xmax and self.to_point(xmax)
        self._xlimits = (xmin, xmax)
        self._set_limits()


    def _set_limits(self):
        if WidgetPrinter._set_limits(self):
            chart = self._chart_instance
            chart._set_xlim(xmin=self._xlimits[0], xmax=self._xlimits[1])
            self._correct_size()


    def _correct_size(self):
        chart = self._chart_instance
        hmargin = chart._left_margin.get() + chart._right_margin.get()
        vmargin = chart._top_margin.get() + chart._bottom_margin.get()
        width  = chart._view_lim.width() + hmargin
        height = chart._view_lim.height() + vmargin
        self._figure.set_figsize_inches(width/72.0, height/72.0)
        self._chart_instance._check_limits(False)


    def autoscale(self, set=True):
        chart = self._chart_instance
        chart._set_xlim(chart._data_lim.intervalx().get_bounds())
        chart._set_ylim(chart._data_lim.intervaly().get_bounds())
        if set:
            self._xlimits = chart._get_xlim()
            self._ylimits = chart._get_ylim()
            self._set_limits()
