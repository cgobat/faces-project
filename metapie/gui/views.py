############################################################################
#   Copyright (C) 2005 by Reithinger GmbH
#   mreithinger@web.de
#
#   This file is part of metapie.
#                                                                         
#   metapie is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   pyplan is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the
#   Free Software Foundation, Inc.,
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
############################################################################

import wx
import tablesizer
import metapie.events as events
import metapie.dblayout as dblayout
import widgets
import grid
from metapie.mtransaction import Transaction
import textwrap
import metapie
import tools
import metapie.tools

_ = metapie.tools.get_gettext()
    
class _MetaView(type):
    def __init__(cls, name, bases, dict_):
        super(_MetaView, cls).__init__(name, bases, dict_)
        if cls.__model__:
            vname = dict_.get("__view_name__", name)
            
            views = cls.__model__.__dict__.get("_views_", {})
            try:
                #also register all _views_ of base classes
                views.update(cls.__model__._views_)
            except AttributeError:
                pass
            
            views[vname] = cls
            cls.__model__._views_ = views


class ModelView(widgets.IView):
    __model__ = None
    error_colour = wx.RED
    


class _MetaGridView(_MetaView, grid._MetaGrid): pass
#    def __init__(cls, name, bases, dict_):
#        super(_MetaGridView, cls).__init__(name, bases, dict_)


class GridView(grid.GridView, ModelView):
    __name_view_class__ = "RowView"
    __metaclass__ = _MetaGridView
    str = (None, dblayout.Text, "id")

    def prepare(self, name):
        pass

    def begin_edit(self, name):
        pass

    def inserted(self, imodel):
        return True


class FormViewBase(wx.PyPanel, ModelView):
    vgap = 2
    hgap = 2
    format = ""
    error_font_size = 0.8
    #root_view

    def __init__(self, parent, style=0):
        wx.PyPanel.__init__(self, parent, -1, style=style|wx.TAB_TRAVERSAL)
        ModelView.__init__(self)

        self.widgets = {}
        self.errors = {}
        self.imodel = None

        self.create_controls()
        sizer = tablesizer.TableSizer(self, self.format, self.get_control,
                                      self.vgap, self.hgap)

        self.SetSizer(sizer)
        self.prepare()
        self.Bind(wx.EVT_WINDOW_DESTROY, self._on_destroy)


    def _on_destroy(self, event):
        if event.GetEventObject() is self:
            self.end_inspect()


    def set_default_item(self, ctrl):
        window = self
        while window:
            try:
                window.SetDefaultItem(ctrl)
                return
            except AttributeError:
                pass

            window = window.GetParent()


    def get_default_item(self):
        window = self
        while window:
            try:
                return window.GetDefaultItem()
            except AttributeError:
                pass

            window = window.GetParent()
    
        return None


    def same_dimensions(self, src, dest):
        def on_size(event):
            dest.SetSize(src.GetSize())
            event.Skip()

        def on_move(event):
            dest.Move(event.GetPosition())
            event.Skip
        
        wx.EVT_SIZE(src, on_size)
        wx.EVT_MOVE(src, on_move)


    def prepare(self):
        pass


    def Enable(self, flag):
        for w in self.widgets.itervalues():
            w.Enable(flag)

        wx.PyPanel.Enable(self, flag)


    def layout(self):
        self.GetSizer().refresh()
        self.Layout()
        self.Refresh(False)
        try:
            self.GetParent().layout()
        except AttributeError:
            pass


    def button_save(self):
        self.save()


    def button_ok(self):
        self.save()


    def button_cancel(self):
        self.rollback()


    def create_controls(self):
        pass


    def grow_row(self, row, prop=1):
        self.GetSizer().grow_row(row, prop)
        

    def grow_col(self, col, prop=1):
        self.GetSizer().grow_col(col, prop)


    def ungrow_row(self, row):
        self.GetSizer().ungrow_row(row)
        

    def ungrow_col(self, col):
        self.GetSizer().ungrow_col(col)


    def save(self):
        if self.get_default_item():
            #if save is activated by a default item, the
            #focus has not changed, therefore give all widgets
            #the chance to save their values
            self.inspect_state() 
        
        try:
            transaction = self.transaction
        except AttributeError, e:
            return False
        else:
            ok = transaction.commit()
            self.update_errors()
            if not ok:
                self.show_main_error()
            return ok
        

    def check_constraints(self):
        try:
            self.imodel.check_constraints()
        except ConstraintError, e:
            proxy = Transaction.get_proxy(self.imodel)
            assert(proxy is not self.imodel)
            proxy.error = e

        self.update_errors()


    def rollback(self):
        try:
            self.transaction.rollback()
            self.update_errors()
        except AttributeError, e:
            pass


    def inspect(self, imodel, attrib):
        self.parent_imodel = imodel
        self.parent_attrib = attrib
        self.constitute(getattr(imodel, attrib))


    def end_inspect(self):
        for w in self.widgets.itervalues():
            try:
                w.end_inspect()
            except wx.PyDeadObjectError: pass

        try:
            self.imodel.detach(self.change_state)
        except AttributeError:
            pass
            
        self.imodel = None
            
        try:
            del self.parent_imodel
            del self.parent_attrib
        except AttributeError:
            pass

    def state_changed(self, name):
        pass


    def change_state(self, name):
        try:
            setattr(self.parent_imodel, self.parent_attrib, self.imodel)
        except AttributeError:
            pass
        
        self.hide_error(name)
        self.state_changed(name)
        

    def constitute(self, imodel):
        """
        imodel: model instance
        """

        try:
            Transaction.get_transaction(imodel)
        except RuntimeError:
            self.transaction = Transaction()
            self.transaction.include(imodel)
        else:
            try:
                del self.transaction
            except AttributeError: pass

        self.imodel = imodel
        self.imodel.attach(self.change_state)
        self.inspect_state()
        

    def get_button(self, label):
        class Button(wx.Button, events.Subject):
            def __init__(self, parent, label):
                if isinstance(label, int):
                    wx.Button.__init__(self, parent, label)
                else:
                    wx.Button.__init__(self, parent, -1, label)
                    
                events.Subject.__init__(self)
                wx.EVT_BUTTON(self, -1, lambda evt: self.fire("default"))

        return Button(self, label)


    def get_label(self, label):
        return wx.StaticText(self, -1, label)


    def get_control(self, name):
        try:
            return getattr(self, name)
        except AttributeError:
            pass

        try:
            root_view = self.root_view
        except AttributeError:
            root_view = self

        result = root_view.get_stock_control(self, name)
        if not result:
            name, result = self.create_widget(name)

        setattr(self, name, result)
        return result
    

    def get_stock_control(self, parent, name):
        if name == "btn_save":
            parent.btn_save = wx.Button(parent, wx.ID_SAVE)
            wx.EVT_BUTTON(parent.btn_save, -1, lambda ev: self.button_save())
            return parent.btn_save

        if name == "btn_ok":
            parent.btn_ok = wx.Button(parent, wx.ID_OK)
            wx.EVT_BUTTON(parent.btn_ok, -1, lambda ev: self.button_ok())
            return parent.btn_ok
        
        if name == "btn_cancel":
            parent.btn_cancel = wx.Button(parent, wx.ID_CANCEL)
            wx.EVT_BUTTON(parent.btn_cancel, -1,
                          lambda ev: self.button_cancel())
            return parent.btn_cancel
        
        if name == "lbl_error":
            parent.lbl_error = wx.StaticText(parent, -1,
                                             _("Errors in saving data."))
            parent.lbl_error.SetForegroundColour(self.error_colour)
            parent.lbl_error.Hide()
            return parent.lbl_error
            
        if name.startswith("notebook"):
            name = name.strip()
            brace_pos = name.index('(')
            class Notebook(wx.Notebook):
                def layout(self):
                    parent.InvalidateBestSize()
                    parent.GetParent().layout()
            
            notebook = Notebook(parent, -1)
            setattr(parent, name[:brace_pos], notebook)
            subviews = name[brace_pos + 1:-1]
            subviews = subviews.split(",")
            for sub in subviews:
                sub = sub.strip()
                try:
                    txt_pos = sub.index('[')
                    txt_end = sub.index(']')
                    text = sub[txt_pos + 1:txt_end]
                    sub = sub[:txt_pos].strip()
                except ValueError:
                    text = sub

                result = parent.create_subform(notebook, sub)
                parent.widgets[':' + sub] = result
                setattr(parent, sub, result)
                notebook.AddPage(result, text)

            return notebook

        return None


    def create_widget(self, name):
        try:
            pos = name.index('(')
            attrib = name[:pos]
            name = name[pos + 1:-1]
        except ValueError:
            attrib = name
            name = "default"

        if attrib:
            itype = self.__model__.__attributes_map__[attrib]
            result = itype.create_widget(self, name)
            self.widgets[attrib] = result
        else:
            result = self.create_subform(self, name)
            attrib = name
            self.widgets[':' + attrib] = result

        return attrib, result


    def create_subform(self, parent, name):
        try:
            my_root_view = self.root_view
        except AttributeError:
            my_root_view = self

        sub_format = getattr(my_root_view, "format_" + name, "")
        def dumy(*args): pass
        controls = getattr(my_root_view, "create_%s_controls" % name, dumy)

        class SubView(FormViewBase):
            format = sub_format
            __model__ = self.__model__
            root_view = my_root_view

            def create_controls(self):
                controls(self)

            def inspect(self, imodel, attrib):
                self.imodel = imodel
                self.inspect_state()
                
        SubView = my_root_view.modify_subview(SubView, name)
        if not SubView.format:
            raise AttributeError("Subform has no format: Define format_%s" % name)
        
        return SubView(parent)


    def modify_subview(self, subview_class, name):
        return subview_class


    def inspect_state(self):
        for k, w in self.widgets.iteritems():
            w.inspect(self.imodel, k)


    def update_errors(self):
        for ew in self.errors.itervalues():
            ew.Hide()

        try:
            self.lbl_error.Hide()
        except AttributeError:
            pass
            
        proxy = Transaction.get_proxy(self.imodel)
        if proxy is not self.imodel and proxy.error:
            self.show_errors(proxy.error)

        for w in self.widgets.itervalues():
            w.update_errors()

        self.layout()


    def hide_error(self, name):
        try:
            widget = self.widgets[name]
            if self.errors[widget].IsShown():
                self.errors[widget].Hide()
                self.layout()
        except KeyError:
            pass

        subviews = filter(lambda kv: kv[0][0] == ':', self.widgets.items())
        for k, s in subviews:
            s.hide_error(name)


    def show_errors(self, error):
        self.show_main_error()

        messages = error.message
        for attrib, msg in messages.iteritems():
            try:
                ctrl = self._get_error_ctrl(attrib)
                ctrl.SetLabel(msg)
                self.wrap_static(ctrl, self.widgets[attrib].GetSize()[0])
                ctrl.Show(True)
            except KeyError:
                pass


    def show_main_error(self):
        try:
            if self.GetParent().show_main_error():
                return True
        except AttributeError:
            pass

        try:
            self.lbl_error.Show()
            self.layout()
            return True
        except AttributeError:
            return False


    def wrap_static(self, ctrl, width):
        best_size = ctrl.GetBestSize
        def get_width(): return best_size()[0]

        if get_width() < width: return

        fill = textwrap.fill
        text = ctrl.GetLabel()
        max_cwidth = len(text)
        min_cwidth = 0
        while min_cwidth < max_cwidth:
            cwidth = (max_cwidth + min_cwidth) / 2
            ctrl.SetLabel(fill(text, cwidth))
            w = get_width()
            if w == width: return
            if w < width: min_cwidth = cwidth + 1
            else: max_cwidth = cwidth - 1

        if w > width:
            ctrl.SetLabel(fill(text, cwidth - 1))


    def _get_error_ctrl(self, name):
        widget = self.widgets[name]
        try:
            return self.errors[widget]
        except KeyError:
            sizer = self.GetSizer()
            ctrl = self.errors[widget] = wx.StaticText(self, -1, "")
            ctrl.SetForegroundColour(self.error_colour)
            font = ctrl.GetFont()

            if isinstance(self.error_font_size, int):
                font_size = self.error_font_size
            else:
                font_size = int(font.GetPointSize() * self.error_font_size)
            
            font.SetPointSize(font_size)
            ctrl.SetFont(font)
            sizer.add_error(widget, ctrl)
            return ctrl


class FormView(FormViewBase):
    __metaclass__ = _MetaView
    __name_view_class__ = "FormView"

    def __init__(self, parent, style=0):
        FormViewBase.__init__(self, parent, style)
        #inside prepare the size of widgets could be changed
        for k, w in self.widgets.iteritems():
            if k[0] == ':': w.GetSizer().refresh()
        
        self.GetSizer().refresh()

               
   
#ScrolledPanel does not work here
class ScrollViewContainer(wx.PyScrolledWindow):
    hborder = 5
    vborder = 5
    
    def __init__(self, *args, **kwargs):
        wx.PyScrolledWindow.__init__(self, *args, **kwargs)
        wx.EVT_SIZE(self, self._on_size)


    def fit_size(self, min_size=(0, 0)):
        children = self.GetChildren()
        if not children: return
        w, h = children[0].GetSizer().CalcMin()
        w = max(w + 2 * self.hborder, min_size[0])
        h = max(h + 2 * self.vborder, min_size[1])
        self.SetSize((w, h))


    def setup_scrolling(self, scroll_x=True, scroll_y=True, rate_x=20, rate_y=20):
        if not scroll_x: rate_x = 0
        if not scroll_y: rate_y = 0

        self.SetScrollRate(0, 0)
        child = self.GetChildren()[0]
        w, h = child.GetSizer().CalcMin()
        child.SetDimensions(self.hborder, self.vborder, w, h)
        w += 2 * self.hborder - 2
        h += 2 * self.vborder - 2
        self.SetVirtualSize( (w, h) )
        self.SetVirtualSize( (w, h) ) # don't ask me but you have to set it twice
        self.SetScrollRate(rate_x, rate_y)


    def _resize_children(self):
        child = self.GetChildren()[0]
        w, h = self.GetClientSize()
        w -= 2 * self.hborder
        h -= 2 * self.vborder

        minw, minh = child.GetSizer().CalcMin()
        child.SetDimensions(self.hborder, self.vborder,
                            max(w, minw), max(h, minh))

            
    __scrolling_setup = False
    def _on_size(self, event):
        if self.GetChildren():
            if not self.__scrolling_setup:
                tools.EVT_CHILD_SET_FOCUS(self, self._on_child_set_focus)
                self.setup_scrolling()
                self.__scrolling_setup = True
            self._resize_children()

        event.Skip()


    def layout(self):
        if self.GetChildren():
            if not self.__scrolling_setup:
                tools.EVT_CHILD_SET_FOCUS(self, self._on_child_set_focus)

            self.setup_scrolling()
            self.__scrolling_setup = True
            self._resize_children()
            
    
    def _on_child_set_focus(self, event):
        event.Skip()

        vw, vh = self.GetVirtualSize()
        cw, ch = self.GetClientSize()
        if vw <= cw and vh <= ch: return

        child = event.GetEventObject()
        sppu_x, sppu_y = self.GetScrollPixelsPerUnit()
        vs_x, vs_y = self.GetViewStart()
        cr = child.GetRect()
        parent = child.GetParent() # the child may deeper in the hierachy
        tl = parent.ClientToScreen(cr.GetTopLeft())
        br = parent.ClientToScreen(cr.GetBottomRight())

        tl = self.ScreenToClient(tl)
        br = self.ScreenToClient(br)
        cr = wx.RectPP(tl, br)

        new_vs_x, new_vs_y = -1, -1

        # is it before the left edge?
        if cr.x < 0 and sppu_x > 0:
            new_vs_x = vs_x + (cr.x / sppu_x)

        # is it above the top?
        if cr.y < 0 and sppu_y > 0:
            new_vs_y = vs_y + (cr.y / sppu_y)


        # For the right and bottom edges, scroll enough to show the
        # whole control if possible, but if not just scroll such that
        # the top/left edges are still visible

        # is it past the right edge ?
        if cr.right > cw and sppu_x > 0:
            diff = (cr.right - cw) / sppu_x
            if cr.x - diff * sppu_x > 0:
                new_vs_x = vs_x + diff + 1
            else:
                new_vs_x = vs_x + (cr.x / sppu_x)
                
        # is it below the bottom ?
        if cr.bottom > ch and sppu_y > 0:
            diff = (cr.bottom - ch) / sppu_y
            if cr.y - diff * sppu_y > 0:
                new_vs_y = vs_y + diff + 1
            else:
                new_vs_y = vs_y + (cr.y / sppu_y)


        # if we need to adjust
        if new_vs_x != -1 or new_vs_y != -1:
            #print "%s: (%s, %s)" % (self.GetName(), new_vs_x, new_vs_y)
            self.Scroll(new_vs_x, new_vs_y)


def build_view(cmodel, name):
    attribs = cmodel.__attributes_tuple__
    if not attribs:
        class BuildView(FormView):
            __view_name__ = name
            model = cmodel
            format = "[Empty]"

        return BuildView

    maxlen = max(map(lambda a: len(a.name), attribs))
    def make_cell(attrib):
        return "[%-*s]|%s" % (maxlen, attrib.name.capitalize() + ":",
                              attrib.name)

    view_format = "\n".join(map(make_cell, attribs))
    
    class BuildView(FormView):
        __view_name__ = name
        __model__ = cmodel
        format = view_format

    return BuildView

metapie._view_builders["FormView"] = build_view
