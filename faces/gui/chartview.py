#@+leo-ver=4
#@+node:@file gui/chartview.py
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
import faces.observer
import wx
import matplotlib.backends.backend_wxagg as wxagg
import matplotlib.backend_bases as bases
import matplotlib.transforms as mtrans
import matplotlib.numerix as numerix
import matplotlib.font_manager as font
import matplotlib.figure as figure
import matplotlib.numerix as numerix
import metapie.navigator as navigator
from metapie.gui import controller
import datetime
import faces.task
import faces.charting.tools as tools
import faces.charting.charts as charts
import faces.gui.editor.context as context
import faces.plocale
import taskfuncs
import sys
import matplot_patches as mpatch
import math
from tipwindow import TipWindow
import print_chart



#@-node:<< Imports >>
#@nl
_is_source_ = True
_ = faces.plocale.get_gettext()

#@+others
#@+node:_cint
def _cint(x):
    return int(math.ceil(x))
#@-node:_cint
#@+node:_nop
def _nop():
    pass
#@-node:_nop
#@+node:_chart_factory
tools.set_default_size(6)

def _chart_factory(title, chart, model):
    return lambda parent: ChartView(parent, chart, model, title)
#@-node:_chart_factory
#@+node:_timechart_factory
def _timechart_factory(title, chart, model):
    return lambda parent: TimeChartView(parent, chart, model, title)
#@-node:_timechart_factory
#@+node:class _ErrorChart


faces.observer.factories["matplot_chart"] = _chart_factory
faces.observer.factories["matplot_pointchart"] = _chart_factory
faces.observer.factories["matplot_timechart"] = _timechart_factory


cursord = {
    bases.cursors.MOVE : wx.CURSOR_HAND,
    bases.cursors.HAND : wx.CURSOR_HAND,
    bases.cursors.POINTER : wx.CURSOR_ARROW,
    bases.cursors.SELECT_REGION : wx.CURSOR_CROSS,
    }


class _ErrorChart(charts.TimeAxisWidgetChart):
    #@	<< class _ErrorChart declarations >>
    #@+node:<< class _ErrorChart declarations >>
    data = True
    scroll_bars = False

    #@-node:<< class _ErrorChart declarations >>
    #@nl
    #@	@+others
    #@+node:create
    def create(self):
        self.set_time_axis()
        fig = self.figure
        fig.clf()        
        fig.text(0.5, 0.5, 'Error in chart',
                 fontsize='xx-large',
                 color='red',
                 horizontalalignment='center',
                 verticalalignment='center')

        pprop = self.get_patch
        self.axes.set_frame_on(False)
        self.time_axis.time_scale = self.time_scale
        self.time_axis.show_scale = False
        self.time_axis.show_grid = False
        self.axes.set_time_axis(self.time_axis)
        self.axes.xaxis_timescale(self.time_scale)
        self.axes.set_marker(pprop("focused.marker"), pprop("marker"))

        xmin = self.time_scale.to_num("1.1.2005")
        xmax = self.time_scale.to_num("10.1.2005")
        self.axes.set_time_lim(xmin, xmax)
        self.axes.dataLim.intervalx().set_bounds(xmin, xmax)
        self.axes.dataLim.intervaly().set_bounds(0, 1)
    #@-node:create
    #@-others
#@-node:class _ErrorChart
#@+node:class Toolbar
class Toolbar(bases.NavigationToolbar2):
    #@	@+others
    #@+node:_init_toolbar
    def _init_toolbar(self):
        view = self.canvas.GetParent()
        self.create_menus()
    #@-node:_init_toolbar
    #@+node:create_menus
    def create_menus(self):
        view = self.canvas.GetParent()
        ctrl = controller()
        toolbar = ctrl.get_toolbar()

        def hzin(): view.horz_zoom(2)
        def hzout(): view.horz_zoom(-2)
        def vzin(): view.vert_zoom(2)
        def vzout(): view.vert_zoom(-2)

        toolbar.make_tool(view, "home", self.home, "home",
                          short=_("Home"))
        self.back_tool = toolbar.make_tool(view, "back",
                                           self.back, "back",
                                           short=_("Back"))
        self.fore_tool = toolbar.make_tool(view, "forward",
                                           self.forward, 'forward',
                                          short=_("Forward"))
        self.pan_tool = toolbar.make_tool(view, "move", self.pan, "move",
                                          kind=wx.ITEM_CHECK,
                                          short=_("Move Tool"))
        self.zoom_tool = toolbar.make_tool(view, "zoom", self.zoom,
                                           "zoom_to_rect",
                                           kind=wx.ITEM_CHECK,
                                          short=_("Zoom Tool"))
        toolbar.make_separator("home", True)
        toolbar.make_tool(view, "x-fit", view.zoom_to_fit, "viewmagfit22",
                          short=_("zoom to fit"))
        toolbar.make_tool(view, "x-zoomout", hzout, "mag-horz22",
                          short=_("zoom out horizontally"))
        toolbar.make_tool(view, "x-zoomin", hzin, "mag+horz22",
                          short=_("zoom in horizontally"))
        toolbar.make_tool(view, "y-zoomout", vzout, "mag-vert22",
                          short=_("zoom out vertically"))
        toolbar.make_tool(view, "y-zoomin", vzin, "mag+vert22",
                          short=_("zoom in vertically"))
        toolbar.make_separator("x-fit", True)
        self.refresh_buttons()
        self.make_menu()
    #@-node:create_menus
    #@+node:make_menu
    def make_menu(self, popup=False):
        ctrl = controller()
        view = self.canvas.GetParent()

        if popup:
            chart_menu = ctrl.make_menu()
        else:
            top = ctrl.get_top_menu()
            chart_menu = top.make_menu(_("&Chart"), pos=200)

        menu = lambda *args, **kw: chart_menu.make_item(view, *args, **kw)

        def find_in_source(): view.model.find_in_source(view.chart.__class__)

        def menu_print_chart():
            dlg = print_chart.PrintChart(controller().frame,
                                         self.canvas.GetParent().chart)
            dlg.simulate_modal(self.canvas.GetParent())


        menu(_("Print Chart..."), menu_print_chart, "print16", pos=100)

        if not popup:
            def hzin(): view.horz_zoom(2)
            def hzout(): view.horz_zoom(-2)
            def vzin(): view.vert_zoom(2)
            def vzout(): view.vert_zoom(-2)
            menu(_("Horizontal Zoom In\tCTRL-."), hzin, "mag+horz16", pos=10)
            menu(_("Horizontal Zoom Out\tCTRL-,"), hzout, "mag-horz16", pos=20)
            menu(_("Fit in Window"), view.zoom_to_fit, pos=30)
            chart_menu.make_separator(_("Fit in Window"))

        menu(_("Duplicate Chart"), view.duplicate, "duplicate_view16", pos=120)\
                          .enable(not hasattr(view, "_original"))
        menu(_("Find in Source"), find_in_source, "findsource16", pos=130)
        self.link_menu = menu(_("&Link Chart"), view.change_link, 
                              check_item=True, pos=140)
        self.link_menu.check(view.link_view)

        chart_menu.make_separator(_("&Link Chart"))
        return chart_menu

    #@-node:make_menu
    #@+node:refresh_buttons
    def refresh_buttons(self):
        if self.pan_tool.is_pressed() != (self._active == 'PAN'):
            self.pan_tool.toggle(self._active == 'PAN')

        if self.zoom_tool.is_pressed() != (self._active == 'ZOOM'):
            self.zoom_tool.toggle(self._active == 'ZOOM')
    #@-node:refresh_buttons
    #@+node:set_history_buttons
    def set_history_buttons(self):
        can_backward = (self._views._pos > 0)
        can_forward = (self._views._pos < len(self._views._elements) - 1)
        self.back_tool.enable(can_backward)
        self.fore_tool.enable(can_forward)
    #@-node:set_history_buttons
    #@+node:set_cursor
    def set_cursor(self, cursor):
        cursor = wx.StockCursor(cursord[cursor])
        self.canvas.SetCursor(cursor)
    #@-node:set_cursor
    #@+node:draw_rubberband
    __last_rect = None
    def draw_rubberband(self, event, x0, y0, x1, y1):
        #take from backend_wx
        canvas = self.canvas
        dc = wx.ClientDC(canvas)

        # Set logical function to XOR for rubberbanding
        dc.SetLogicalFunction(wx.XOR)

        wbrush = wx.Brush(wx.Colour(255,255,255), wx.TRANSPARENT)
        wpen = wx.Pen(wx.Colour(200, 200, 200), 1, wx.SOLID)
        dc.SetBrush(wbrush)
        dc.SetPen(wpen)

        dc.ResetBoundingBox()
        dc.BeginDrawing()
        height = self.canvas.figure.bbox.height()
        y1 = height - y1
        y0 = height - y0

        if y1 < y0: y0, y1 = y1, y0
        if x1 < y0: x0, x1 = x1, x0

        w = x1 - x0
        h = y1 - y0

        rect = (int(x0), int(y0), int(w), int(h))
        if self.__last_rect: dc.DrawRectangle(*self.__last_rect) #erase last
        self.__last_rect = rect
        dc.DrawRectangle(*rect)
        dc.EndDrawing()
    #@-node:draw_rubberband
    #@+node:release
    def release(self, event):
        self.__last_rect = None
    #@-node:release
    #@+node:mouse_move
    def mouse_move(self, event):
        bases.NavigationToolbar2.mouse_move(self, event)
        self.canvas.GetParent().mouse_over(event)
    #@-node:mouse_move
    #@-others
#@-node:class Toolbar
#@+node:class ChartView
class ChartView(wx.PyScrolledWindow, navigator.View):
    #@	@+others
    #@+node:Init Methods
    #@+node:__init__
    def __init__(self, parent, chart, model, title):
        wx.PyScrolledWindow.__init__(self, parent, -1)

        tmpdc = wx.ClientDC(parent)
        dpi = tmpdc.GetPPI()[0]
        del tmpdc
        self.dpi = float(dpi)
        self.has_focus = False
        self.canvas = None
        self.chart = None
        self.model = model
        self.marked_widget = None
        self._is_ready = False
        self.timer = wx.Timer(self)
        self.deferred_func = None
        self.deferred_args = None
        self.link_view = True
        self.toolbar = None
        self.replace_data(chart)
    #@-node:__init__
    #@+node:_setup_events
    def _setup_events(self):
        wx.EVT_TIMER(self, -1, self._on_timer)
        wx.EVT_SIZE(self, self._on_size)
        wx.EVT_IDLE(self, self._on_idle)
        wx.EVT_SET_FOCUS(self, self._on_set_focus)
        wx.EVT_KILL_FOCUS(self, self._on_kill_focus)
    #@-node:_setup_events
    #@+node:init_scrolling
    def init_scrolling(self):
        get_bbox_transform = mtrans.get_bbox_transform
        unit_bbox = mtrans.unit_bbox
        dlim = self.chart._data_lim.deepcopy()
        dlim.intervalx().set_bounds(dlim.xmin(), dlim.xmax())
        dlim.intervaly().set_bounds(dlim.ymax(), dlim.ymin())
        self.scroll_trans = get_bbox_transform(dlim, unit_bbox())
    #@-node:init_scrolling
    #@+node:replace_data
    def replace_data(self, chart):
        if self.canvas:
            self.figure.clf()
            self.canvas.Destroy()

        last_trans = None
        if self.chart and not isinstance(self.chart, _ErrorChart):
            last_trans = self.chart._trans_data

        self.figure = figure.Figure(dpi=self.dpi)
        self.canvas = mpatch.FigureCanvasWx(self, -1, self.figure)
        self.canvas.mpl_connect('button_press_event', self.mouse_button)
        charts._figure_manager.canvas = self.canvas
        self.SetTargetWindow(self.canvas)
        self.create_chart(chart)

        if self.toolbar:
            views = self.toolbar._views
            self.toolbar = Toolbar(self.canvas)
            self.toolbar._views = views
        else:
            self.toolbar = Toolbar(self.canvas)

        self.show_horz_bar = self.show_vert_bar = self.chart.scroll_bars
        self.link_view = not self.chart.link_view
        self.change_link()
        self.init_scrolling()

        if self.is_visible():
            self.become_visible(last_trans)
    #@-node:replace_data
    #@+node:create_chart
    def create_chart(self, chart):
        save_execute = controller().session.save_execute
        self.chart = save_execute(chart, self.figure)
        if not self.chart: self.chart = _ErrorChart(self.figure)
    #@-node:create_chart
    #@+node:setup_scrolling
    _yscroll = 0
    _xscroll = 0
    def setup_scrolling(self):
        sdata = self.scroll_trans.get_bbox1()
        vlim = mtrans.transform_bbox(self.chart._trans_data, sdata)
        sview = self.scroll_trans.get_bbox2()

        width = _cint(vlim.width())
        height = _cint(-vlim.height())

        sview.intervalx().set_bounds(0, width)
        sview.intervaly().set_bounds(0, height)
        self.SetVirtualSize((width, height))

        xrate = self.show_horz_bar and 20 or 0
        yrate = self.show_vert_bar and 20 or 0

        vlim = self.chart._view_lim
        x, y = self.scroll_trans.xy_tup((vlim.xmin(), vlim.ymax()))
        self._xscroll = _cint(x / 20)
        self._yscroll = _cint(y / 20)
        self._scroll_adjustments = [xrate, yrate, 10+width/20, 10+height/20,
                                    self._xscroll, self._yscroll, True]

        self.SetScrollbars(*self._scroll_adjustments)
        self.AdjustScrollbars()
        self.EnableScrolling(False, False)
    #@-node:setup_scrolling
    #@-node:Init Methods
    #@+node:wxPython Methods
    #@+node:Destroy
    def Destroy(self):
        self.timer.Stop()
        wx.PyScrolledWindow.Destroy(self)
    #@-node:Destroy
    #@+node:_on_timer
    def _on_timer(self, event):
        self.timer.Stop()
        if self.deferred_func:
            self.deferred_func(*self.deferred_args)
            self.deferred_args = None
            self.deferred_func = None
    #@-node:_on_timer
    #@+node:_on_size
    def _on_size(self, event):
        if self.canvas:
            self.canvas.SetSize(self.GetClientSizeTuple())
    #@-node:_on_size
    #@+node:_on_set_focus
    def _on_set_focus(self, event):
        self.has_focus = True
        self.toolbar.create_menus()
        self.chart._set_focused_on()
        self.draw()
    #@-node:_on_set_focus
    #@+node:_on_kill_focus
    def _on_kill_focus(self, event):
        self.has_focus = False
        self.chart._set_focused_off()
        self.draw()
    #@-node:_on_kill_focus
    #@+node:_on_idle
    def _on_idle(self, event):
        try:
            if self.has_focus: self.toolbar.refresh_buttons()
            self.update_state()
        except:
            pass
    #@-node:_on_idle
    #@-node:wxPython Methods
    #@+node:Geometry Methods
    #@+node:scale_figure
    def scale_figure(self, trans):
        if trans:
            self._on_size(None)
            self.check_limits()
            vb = self.chart._bbox
            xmin, ymin = trans.inverse_xy_tup((vb.xmin(), vb.ymin()))
            xmax, ymax = trans.inverse_xy_tup((vb.xmax(), vb.ymax()))
            self.chart._set_xlim(xmin, xmax)
            self.chart._set_ylim(ymin, ymax)
        else:
            self.SetScrollbar(wx.VERTICAL, 0, 1, 10, False)
            self.SetScrollbar(wx.HORIZONTAL, 0, 1, 10, False)
            self._on_size(None)
            self.check_limits()
            self.chart._autoscale_view()

        self.setup_scrolling()
    #@-node:scale_figure
    #@+node:check_limits
    def check_limits(self):
        self.chart._check_limits()
    #@-node:check_limits
    #@+node:zoom_to_fit
    def zoom_to_fit(self):
        self.chart._autoscale_view()
        self.update_state(True)
    #@-node:zoom_to_fit
    #@+node:horz_zoom
    def horz_zoom(self, step):
        self.chart._zoomx(step)
        self.update_state(True)
    #@-node:horz_zoom
    #@+node:vert_zoom
    def vert_zoom(self, step):
        self.chart._zoomy(step)
        self.update_state(True)
    #@-node:vert_zoom
    #@+node:scroll
    def scroll(self, direction, delta):
        if direction == wx.HORIZONTAL:
            self._scroll_adjustments[4] = self.GetScrollPos(direction) + delta
        else:
            self._scroll_adjustments[5] = self.GetScrollPos(direction) + delta

        self.SetScrollbars(*self._scroll_adjustments)
    #@-node:scroll
    #@+node:update_state
        #controller().status_bar.SetStatusText("", 2)


    _last_data_bounds = (0, 0, 0, 0)
    _last_view_bounds = (0, 0, 1, 1)
    def update_state(self, push_view=False):
        if not self._is_ready: return

        def calc_scale(data, view):
            return (int(100 * float(data[2]) / (view[2] or 1.0)),\
                    int(100 * float(data[3]) / (view[3] or 1.0)))

        result = False
        trans = self.chart._trans_data
        data_box = trans.get_bbox1()

        data_bounds = map(int, data_box.get_bounds())
        view_bounds = map(int, trans.get_bbox2().get_bounds())

        if self._last_data_bounds != data_bounds or \
           self._last_view_bounds != view_bounds:
            self.check_limits()
            data_bounds = map(int, data_box.get_bounds())
            last_scale = calc_scale(self._last_data_bounds,
                                    self._last_view_bounds)
            scale = calc_scale(data_bounds, view_bounds)
            if last_scale != scale:
                try:
                    self.deferred(1000, self.chart._speed_up, 1024*1024*30)
                    self.chart._clear_speed_cache()
                except AttributeError:
                    pass

            self.draw()
            self.setup_scrolling()
            if push_view: self.toolbar.push_current()
            self._last_view_bounds = view_bounds
            self._last_data_bounds = data_bounds


        x, y = self.GetViewStart()
        if y != self._yscroll or x != self._xscroll:
            xt, yt = self.scroll_trans.inverse_xy_tup((x * 20, y * 20))
            if x != self._xscroll and self.show_horz_bar:
                self.chart._set_xlim(xt, xt + data_box.width())

            if y != self._yscroll and self.show_vert_bar:
                self.chart._set_ylim(yt - data_box.height(), yt)
    #@-node:update_state
    #@-node:Geometry Methods
    #@+node:Matplotlib Events
    #@+node:mouse_over
    def mouse_over(self, event):
        if event.xdata is None: return
        widget = self.chart._widget_at(event.xdata, event.ydata)
        if not TipWindow.get().is_widget_active(widget):
            self.deferred(1000, self._show_info)

        try:
            date = event.inaxes.time_scale.to_num(int(event.xdata))
            controller().status_bar.SetStatusText(repr(date), 2)
        except AttributeError:
            pass
    #@-node:mouse_over
    #@+node:mouse_button
    def mouse_button(self, event):
        if self.toolbar._active: return

        if event.button in (1, 3):
            #mark widget
            try:
                axes = event.inaxes
                widget = self.chart._widget_at(event.xdata, event.ydata)
                if self.mark_widget(widget, axes): self.draw()
            except AttributeError:
                widget = None

            fobj = getattr(widget, "fobj", None)
            fattrib = getattr(widget, "fattrib", None)

            if isinstance(fobj, faces.task.Task):
                taskfuncs.make_menu_task_clipboard(controller(), fobj)
            else:
                taskfuncs.remove_menu_task_clipboard(controller())

            if self.link_view and fobj:
                self.model.show_object(self, fobj, fattrib)


        if event.button == 3:
            # context menu
            self.timer.Stop()
            menu = self.toolbar.make_menu(True)

            if fobj:
                try:
                    code_item = fobj._function.code_item
                except AttributeError:
                    pass
                else:
                    taskfuncs.make_menu_task_clipboard(controller(), fobj, menu, 500)
                    action_filter = ("add", "edit", "extra")
                    for c in context.Context.context_list:
                        c = c.__class__(code_item)
                        if c.make_browser_menu(menu, action_filter):
                            break


            self.PopupMenu(menu.wxobj, (event.x,
                                        self.GetClientSizeTuple()[1] - event.y))


    #@-node:mouse_button
    #@-node:Matplotlib Events
    #@+node:Misc Methods
    #@+node:become_visible
    def become_visible(self, last_trans=None):
        if not last_trans:
            self._setup_events()
            self._is_ready = True

        self.scale_figure(last_trans)
        #force update (inclusive scrolling)
        self._last_data_bounds = (0, 0, 0, 0)             
        self.update_state()
    #@-node:become_visible
    #@+node:duplicate
    def duplicate(self):
        class Unshared(self.chart.__class__):
            sharex = datetime.datetime.today() # should never be shared

        org_chart = id(self.chart.__class__)

        def is_duplicate(view):
            return isinstance(view, ChartView) \
                   and getattr(view, "_original", 0) == org_chart

        duplicates = filter(is_duplicate, controller().get_all_views())
        if duplicates:
            duplid = max(map(lambda v: v._duplid, duplicates)) + 1
        else:
            duplid = 1

        model = self.model
        title = self._nav_title + "(%i)" % duplid
        factory_args = (self.__class__, Unshared, model, title) 
        view = controller().produce_view(model, title, factory_args)
        view._original = org_chart
        view._duplid = duplid
    #@-node:duplicate
    #@+node:change_link
    def change_link(self):
        self.link_view = not self.link_view
        self.toolbar.link_menu.check(self.link_view)
    #@-node:change_link
    #@+node:deferred
    def deferred(self, time_out, func, *args):
        self.deferred_func = func
        self.deferred_args = args
        self.timer.Start(time_out, wx.TIMER_ONE_SHOT)
    #@-node:deferred
    #@+node:mark_widget
    def mark_widget(self, widget, axes=None):
        self.marked_widget = widget
        return self.chart._mark_widget(widget)
    #@-node:mark_widget
    #@+node:_show_info
    def _show_info(self):
        x, y = self.mouse_pos_data()
        if x is None: return
        widget = self.chart._widget_at(x, y)
        if widget:
            info = self.chart.get_tip(widget)
            if info:
                TipWindow.get().set_info(info, widget)
    #@-node:_show_info
    #@+node:mouse_pos_data
    def mouse_pos_data(self):
        x, y = self.ScreenToClientXY(*wx.GetMousePosition())
        w, h = self.GetClientSizeTuple()
        if 0 <= x < w and 0 <= y < h:
            y = h - y
            return self.chart._trans_data.inverse_xy_tup((x, y))

        return None, None
    #@-node:mouse_pos_data
    #@+node:show_object
    def show_object(self, fobj, attrib=None, caller=None):
        if not self.link_view: return
        widget = self.chart._find_widget(fobj)
        self.deferred(300, self._show_widget, widget, caller)
    #@-node:show_object
    #@+node:_show_widget
    def _show_widget(self, widget, caller):
        if widget:
            if self.show_x_coord(caller):
                self.chart._widget_x_visible(widget)

            self.chart._widget_y_visible(widget)

        if self.mark_widget(widget):
            self._last_view_bounds = (0, 0, 1, 1) # force update
            self.update_state()
    #@-node:_show_widget
    #@+node:show_x_coord
    def show_x_coord(self, caller):
        return True
    #@-node:show_x_coord
    #@+node:draw
    def draw(self):
        self.check_limits()
        self.canvas.draw()
    #@-node:draw
    #@-node:Misc Methods
    #@+node:Metapie Methods
    #@+node:accept_sibling
    def accept_sibling(self, new_view):
        import editor
        if isinstance(new_view, editor.PlanEditorProxy):
            return navigator.SIBLING_BELOW

        import repview
        if isinstance(new_view, repview.ReportView):
            return navigator.SIBLING_BELOW

        if isinstance(new_view, ChartView):
            return navigator.SIBLING_BELOW

        return False
    #@-node:accept_sibling
    #@-node:Metapie Methods
    #@-others
#@-node:class ChartView
#@+node:class TimeViewManager



class TimeViewManager(object):
    #@	<< class TimeViewManager declarations >>
    #@+node:<< class TimeViewManager declarations >>
    _managers = { }

    #@-node:<< class TimeViewManager declarations >>
    #@nl
    #@	@+others
    #@+node:get_manager
    def get_manager(view, chart_class):
        key = str(chart_class.sharex)
        if not key:
            key = chart_class.__name__

        manager = TimeViewManager._managers.get(key)
        if not manager: 
            manager = TimeViewManager(key)
            manager._managers[key] = manager

        manager.register(view)
        return manager
    #@-node:get_manager
    #@+node:__init__
    get_manager = staticmethod(get_manager)

    def __init__(self, key):
        self.key = key
        self.views = []
        self.main_axes = None
        self.xmin = sys.maxint
        self.xmax = -sys.maxint
    #@-node:__init__
    #@+node:register
    def register(self, view):
        self.views.append(view)
    #@-node:register
    #@+node:unregister
    def unregister(self, view, refresh=True):
        del self.views[self.views.index(view)]
        if not self.views:
            del self._managers[self.key]
        elif refresh:
            self.update_siblings(view)
    #@-node:unregister
    #@+node:update_siblings
    def update_siblings(self, caller_view):
        if not self.main_axes:
            self.main_axes = self.views[0].chart._share_axes

        if self.views[0] == caller_view:
            v = self.views[0]
            axes = v.chart._share_axes
            axes.unshare()

            show_scale = axes.time_axis.show_scale
            if getattr(v, "_show_scale", show_scale) != show_scale:
                axes.time_axis.show_scale = v._show_scale
                axes.update_time_axis()
                v.draw()

            v._current_show_scale = show_scale
            v.show_horz_bar = v.show_vert_bar
            self._update_scroll_info()
            return

        ctrl = controller()
        pos_views = map(lambda v: (ctrl.get_active_view_pos(v), v), self.views)
        pos_views.sort()

        first = pos_views[0][1]
        last = pos_views[-1][1]
        for p, v in pos_views:
            if not hasattr(v, "_show_scale"):
                v._show_scale = v.chart.show_scale

            axes = v.chart._share_axes
            axes.time_axis.show_scale = v == first
            axes.update_time_axis()

            v.show_horz_bar = v == last
            v.setup_scrolling()

        self._update_scroll_info()
    #@-node:update_siblings
    #@+node:_update_scroll_info
    def _update_scroll_info(self):
        for v in self.views:
            if v.show_horz_bar:
                interval = v.scroll_trans.get_bbox1().intervalx()
                interval.set_bounds(self.xmin, self.xmax)
                v.setup_scrolling()
                return
    #@-node:_update_scroll_info
    #@+node:update_xlim
    def update_xlim(self, xmin, xmax):
        self.xmin = min(self.xmin, xmin)
        self.xmax = max(self.xmax, xmax)
    #@-node:update_xlim
    #@+node:shared
    def shared(self):
        return self.main_axes
    #@-node:shared
    #@+node:get_sibling_pos
    def get_sibling_pos(self, view):
        key = view.manager.key
        if key < self.key:
            return navigator.SIBLING_ABOVE

        return navigator.SIBLING_BELOW
    #@-node:get_sibling_pos
    #@-others
#@-node:class TimeViewManager
#@+node:class TimeChartView



class TimeChartView(ChartView):
    #@	@+others
    #@+node:__init__
    def __init__(self, parent, chart, model, title):
        self.manager = None
        ChartView.__init__(self, parent, chart, model, title)
    #@-node:__init__
    #@+node:create_chart
    def create_chart(self, chart):
        if self.manager: self.manager.unregister(self, self.show_horz_bar)
        self.manager = TimeViewManager.get_manager(self, chart)
        save_execute = controller().session.save_execute
        self.chart = save_execute(chart, self.figure,
                                  sharex=self.manager.shared())
        if not self.chart: self.chart = _ErrorChart(self.figure)
    #@-node:create_chart
    #@+node:scale_figure
    def scale_figure(self, trans):
        try:
            self.manager.update_siblings(self)
        except AttributeError:
            #can happen in windows if you click to fast
            #for shared charts.
            self.show_horz_bar = True # make sure the view can scroll

        ChartView.scale_figure(self, trans)
    #@-node:scale_figure
    #@+node:Destroy
    def Destroy(self):
        if self.manager:
            self.manager.unregister(self)
            self.manager = None

        controller().status_bar.SetStatusText("", 2)
        ChartView.Destroy(self)
    #@-node:Destroy
    #@+node:accept_sibling
    def accept_sibling(self, new_view):
        import editor
        if isinstance(new_view, editor.PlanEditorProxy):
            return navigator.SIBLING_BELOW

        import repview
        if isinstance(new_view, repview.ReportView):
            return navigator.SIBLING_BELOW

        if isinstance(new_view, TimeChartView):
            return self.manager.get_sibling_pos(new_view)

        return False
    #@-node:accept_sibling
    #@+node:show_x_coord
    def show_x_coord(self, caller):
        return caller not in self.manager.views
    #@-node:show_x_coord
    #@+node:init_scrolling
    def init_scrolling(self):
        get_bbox_transform = mtrans.get_bbox_transform
        unit_bbox = mtrans.unit_bbox
        dlim = self.chart._data_lim.deepcopy()
        self.scroll_trans = get_bbox_transform(dlim, unit_bbox())
        dlim.intervaly().set_bounds(dlim.ymax(), dlim.ymin())
        self.manager.update_xlim(dlim.xmin() - dlim.width(),
                                 dlim.xmax() + dlim.width())
    #@-node:init_scrolling
    #@-others
#@-node:class TimeChartView
#@-others
#@-node:@file gui/chartview.py
#@-leo
