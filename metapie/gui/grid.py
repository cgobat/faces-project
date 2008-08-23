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
import wx.grid as wxg
import wxcontrols.grid as cxg
import metapie.dblayout as dblayout
import metapie
import widgets
from metapie.mtransaction import Transaction
import metapie.events as events
import weakref
import bisect
import sys
import textwrap


class _MetaGrid(type):
    def __init__(cls, name, bases, dict_):
        super(_MetaGrid, cls).__init__(name, bases, dict_)
        cls.create_columns()


    def create_columns(cls):
        if not cls.columns: return

        #after that function the exist a _columns_ attribute
        #with the following tuple for each coloumn
        #header, type instance, get function, attrib name


        #maps the property get_value method to attributes
        prop_to_attrib = dict(map(lambda kv: (kv[1]._get_value, kv[1]),
                                  cls.__model__.__attributes_map__.iteritems()))

        def parse_col_spec(cs):
            header = None
            
            if isinstance(cs, (tuple, list)):
                if len(cs) == 2:
                    cs, header = cs
                else:
                    ctype, gfunc, header = cs
                    ctype.name = gfunc.__name__
                    if not header: header = gfunc.__name__
                    return header, ctype, gfunc, None
                
            #from now on cs is always an dblayout.Type instance
            if isinstance(cs, property):
                cs = prop_to_attrib[cs.fget]
                cs_name = cs.name
                
            elif isinstance(cs, basestring):
                try:
                    bpos = cs.index("(")
                    cs_name = cs[bpos + 1:-1]
                    cs = cls.__model__.__attributes_map__[cs[:bpos]]
                except:
                    cs = cls.__model__.__attributes_map__[cs]
                    cs_name = cs.name

            if not header: header = cs.name
            return header, cs, cs._get_value, cs_name

        cls._columns_ = tuple(map(parse_col_spec, cls.columns))
                            
        

# no multiple inheritance with wx python classes
class TableDelegator(wxg.PyGridTableBase):
    def __init__(self, view):
        wxg.PyGridTableBase.__init__(self)
        self.delegate = weakref.proxy(view)


    def GetNumberRows(self):
        self.delegate.check_dead()
        return self.delegate.GetNumberRows()
            
    def GetNumberCols(self):
        self.delegate.check_dead()
        return self.delegate.GetNumberCols()

    def IsEmptyCell(self, row, col):
        self.delegate.check_dead()
        return False

    def GetColLabelValue(self, col):
        self.delegate.check_dead()
        return self.delegate.GetColLabelValue(col)
    
    def GetTypeName(self, row, col):
        self.delegate.check_dead()
        return self.delegate.GetTypeName(row, col)

    def CanGetValueAs(self, row, col, type_name):
        self.delegate.check_dead()
        return True

    def GetValue(self, row, col):
        self.delegate.check_dead()
        return self.delegate.GetValue(row, col)
    

    def DeleteRows(self, pos=0, num_rows=1):
        self.delegate.check_dead()
        return self.delegate.DeleteRows(pos, num_rows)
        


def create_text_type(itype):
    return (wxg.GridCellStringRenderer(), itype.to_string)


def create_float_type(itype):
    return (wxg.GridCellFloatRenderer(itype.width, itype.precision), float)


def create_int_type(itype):
    return (wxg.GridCellNumberRenderer(), int)


def create_boolean_type(itype):
    return (wxg.GridCellBoolRenderer(), bool)



renderers = { \
    dblayout.Int : create_int_type,
    dblayout.Float : create_float_type,
    dblayout.Boolean : create_boolean_type,
    }


   
class GridView(wx.PyPanel, events.Subject):
    columns = None
    minimal_visible_rows = 5
    minimal_visible_cols = 4
    resize_col = -1

    
    def __init__(self, parent):
        wx.PyPanel.__init__(self, parent,
                            style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
        events.Subject.__init__(self)
        self.container = None
        self.content = ()
        self.table = TableDelegator(self)        
        self.grid = self.create_grid()
        self.grid.SetTable(self.table)
        self.grid.SetSelectionMode(self.grid.wxGridSelectRows)
        self.grid.SetRowLabelSize(0)
        self.grid.SetMargins(0, 0)
        self.grid.DisableDragGridSize()
        self.register_types()
        self.calc_sizes()
        self.calc_min_size()
        self.grid.set_resize_column(self.resize_col)
        
        wx.EVT_SIZE(self, self._on_size)
        wxg.EVT_GRID_EDITOR_SHOWN(self, self._on_editor_shown)
        wx.EVT_KEY_DOWN(self.grid, self._on_keydown)
        wxg.EVT_GRID_CELL_LEFT_DCLICK(self,
                                      lambda e: self._selected(e.GetRow()))
        

    def _on_size(self, evt):
        self.grid.SetSize(self.GetClientSize())


    def _on_keydown(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self._selected(self.grid.GetGridCursorRow())
            return

        if event.GetKeyCode() == wx.WXK_TAB:
            if event.ShiftDown():
                if self.grid.GetGridCursorCol() <= 0:
                    self.SetFocusIgnoringChildren()
                    return
            elif self.grid.GetGridCursorCol() \
                     >= self.grid.GetNumberCols() - 1:
                self.SetFocusIgnoringChildren()
                return

        event.Skip()


    def _on_editor_shown(self, event):
        #grid is read only
        event.Veto()


    def _selected(self, row):
        try:
            imodel = self.content[row]
            if imodel: self.fire("default", imodel)
        except IndexError:
            pass


    def register_types(self):
        data_types = []
        row_size = 0
        for i, cs in enumerate(self._columns_):
            itype = cs[1]
            iname = cs[3]
            creator = renderers.get(itype.__class__, create_text_type)
            trenderer, tconverter = creator(itype)
            tname = "metapie_" + str(i)
            teditor = CellEditor(itype, iname, self)

            self.grid.RegisterDataType(tname, trenderer, teditor)
            #data type for new line
            self.grid.RegisterDataType(tname + "_new",
                                       wxg.GridCellStringRenderer(),
                                       teditor.Clone())
            
            data_types.append((tname, tconverter))

        self.data_types = tuple(data_types)
        

    def create_grid(self):
        grid = cxg.AutoSizeGrid(self)
        return grid


    def inspect(self, imodel, attrib):
        self.imodel = imodel
        self.attrib = attrib
        #self.imodel.attach(self.refresh_content, attrib)
        self.set_container(getattr(imodel, attrib))


    def end_inspect(self):
        try:
            self.imodel
        except AttributeError:
            pass
        else:
            #self.imodel.detach(self.refresh_content)
            self.set_container(None)
            del self.imodel
            del self.attrib


    def set_container(self, container):
        self.container = container
        if container is not None:
            self.set_content(container.sequence())
        else:
            self.set_content(())


    def check_dead(self):
        try:
            if self.content.is_dead():
                self.refresh_content()
        except AttributeError:
            pass
        

    def refresh_content(self, attrib=None):
        new_container = getattr(self.imodel, self.attrib)
        self.container = new_container
        self.set_content(self.container.sequence())


    def refresh(self):
        #self.refresh_content()
        #self.grid.ForceRefresh()
        #print "self.content", list(self.content)
        #print "            ", list(iter(self.container))

        print "check"
        print "    ", getattr(self.imodel, self.attrib)
        print "    ", self.container
        print "    ", len(self.container)
        print "    ", len(self.content)

        

    def set_content(self, content):
        rows_before = self.GetNumberRows()
        self.content = content

        def refresh_grid():
            try:
                grid = self.grid
            except wx.PyDeadObjectError:
                return

            grid.BeginBatch()
            row, col = grid.GetGridCursorRow(), grid.GetGridCursorCol()
            try:
                msg = wxg.GridTableMessage\
                      (self.table, wxg.GRIDTABLE_NOTIFY_ROWS_DELETED,
                       0, rows_before)
        
                grid.ProcessTableMessage(msg)

                msg = wxg.GridTableMessage\
                      (self.table, wxg.GRIDTABLE_NOTIFY_ROWS_APPENDED,
                       self.GetNumberRows())

                grid.ProcessTableMessage(msg)
            finally:
                grid.EndBatch()

            row = min(row, self.GetNumberRows() - 1)
            col = min(col, self.GetNumberCols() - 1)
            if row >= 0 and col >= 0:
                grid.SetGridCursor(row, col)
            grid.MakeCellVisible(row, col)
            grid.AdjustScrollbars()

        wx.CallAfter(refresh_grid)


    def GetNumberRows(self): return len(self.content)
    def GetNumberCols(self): return len(self._columns_)
    def GetColLabelValue(self, col): return self._columns_[col][0]
    def GetTypeName(self, row, col): return self.data_types[col][0]
    def DeleteRows(self, pos=0, num_rows=1): pass
    
    def CanGetValueAs(self, row, col, type_name):
        return True


    def GetValue(self, row, col):
        imodel = self.content[row]
        try:
            return self.data_types[col][1](self._columns_[col][2](imodel))
        except TypeError:
            return ""


    def set_width(self, col, width_string):
        w, h = self.grid.GetTextExtent(width_string)
        self.grid.SetColMinimalWidth(col, w)
        self.grid.SetColSize(col, w)
        self.calc_min_size()


    def calc_sizes(self):
        labelwin = self.grid.GetGridColLabelWindow()
        labelwin.SetFont(self.grid.GetLabelFont())
        for i, cs  in enumerate(self._columns_):
            itype = cs[1]
            w, h = self.grid.GetTextExtent(itype.width_format())
            w1, h = labelwin.GetTextExtent(cs[0] + 'i')
            w = max(w, w1)
            self.grid.SetColMinimalWidth(i, w)
            self.grid.SetColSize(i, w)


    def calc_min_size(self):
        col_count = min(self.grid.GetNumberCols(), self.minimal_visible_cols)
        width = sum(map(self.grid.GetColSize, range(col_count)))
        width += 2 * col_count
        height = self.grid.GetColLabelSize() * (self.minimal_visible_rows + 1)
        self.SetMinSize((width, height))


    def DoGetBestSize(self):
        return (0, 0)



class EditGrid(object):
    def __init__(self, *args, **kwargs):
        self.editors = {}
        self.errors = []
        super(EditGrid, self).__init__(*args, **kwargs)

        #abuse my font for calculating the error fonts
        font = self.grid.GetDefaultCellFont()
        font.SetPointSize(max(int(font.GetPointSize() * 0.7), 7))
        self.SetFont(font)


    def set_content(self, content):
        super(EditGrid, self).set_content(content)
        self.errors = []


    def GetValue(self, row, col):
        if row >= self.GetNumberRows() - 1: return ""

        pos = bisect.bisect_left(self.errors, row)
        index = row - pos #map grid rows to content index

        try:
            if self.errors[pos] == row:
                proxy = Transaction.get_proxy(self.content[index - 1])
                return proxy.error.message.get(self._columns_[col][1].name, "")
        except IndexError:
            pass

        imodel = self.content[index]
        self.insert_or_delete_error_row(imodel, row, pos)
        return self.data_types[col][1](self._columns_[col][2](imodel))
        

    def GetNumberRows(self):
        if isinstance(self.content, tuple): return len(self.content)
        return len(self.content) + len(self.errors) + 1


    def GetTypeName(self, row, col):
        if row >= self.GetNumberRows() - 1:
            return self.data_types[col][0] + "_new"

        pos = bisect.bisect_left(self.errors, row)
        try:
            if self.errors[pos] == row: return wxg.GRID_VALUE_STRING
        except IndexError:
            pass
        
        
        return self.data_types[col][0]


    def DeleteRows(self, row=0, num_rows=1):
        end = row + num_rows

        try:
            eepos = bisect.bisect_left(self.errors, end)
            if self.errors[eepos] == end: end += 1
        except IndexError: pass

        if end >= self.GetNumberRows():
            end = self.GetNumberRows() - 1

        if row >= end: return

        spos = bisect.bisect_left(self.errors, row)
        epos = bisect.bisect_left(self.errors, end)

        #disable set_content
        def dummy(*args, **kwargs): pass
        self.set_content = dummy

        del self.errors[spos:epos]
        index = row - spos
        eindex = index + (end - row - epos + spos)
        for r in range(index, eindex):
            del self.content[index]

        #enable set_content again
        del self.set_content

        for i in range(epos, len(self.errors)):
            self.errors[i] -= (epos - spos)

        del self.errors[spos:epos]
        msg = wxg.GridTableMessage(self.table,
                                   wxg.GRIDTABLE_NOTIFY_ROWS_DELETED,
                                   row, end - row)
        self.grid.ProcessTableMessage(msg)
        return True


    def insert_or_delete_error_row(self, imodel, row, epos):
        proxy = Transaction.get_proxy(imodel)
        row += 1
        try:
            error = proxy.error
            message = error.message
        except AttributeError:
            #no error defined
            try:
                if self.errors[epos] == row:
                    self.DeleteRows(row)

                return
            except IndexError:
                return


        #an error is defined
        try:
            if self.errors[epos] == row:
                #There is already an error line
                return
        except IndexError: pass
        self.errors.insert(epos, row)

        for i in range(epos + 1, len(self.errors)):
            self.errors[i] += 1

        grid = self.grid
        msg = wxg.GridTableMessage(self.table,
                                   wxg.GRIDTABLE_NOTIFY_ROWS_INSERTED,
                                   row, 1)
        grid.ProcessTableMessage(msg)
        height = 0
        for c in range(self.GetNumberCols()):
            grid.SetReadOnly(row, c)
            grid.SetCellTextColour(row, c, self.error_colour)
            grid.SetCellFont(row, c, self.GetFont())
            msg = message.get(self._columns_[c][1].name, "")

            if msg:
                w, h = self.GetTextExtent("X")
                w = grid.GetColSize(c) / w
                msg = textwrap.fill(msg, w)
                message[self._columns_[c][1].name] = msg
                if wx.Platform == '__WXMSW__':
                    height = h * (len([c for c in msg if c == "\n"]) + 1)
                else:
                    w, h = self.GetTextExtent(msg)
                    height = max(height, h)

        grid.SetRowSize(row, height + 2)
        grid.AdjustScrollbars()



    def end_inspect(self):
        super(EditGrid, self).end_inspect()
        for e in self.editors.iterkeys():
            e.end_inspect()

        self.editors.clear()

    
    def get_delete_button(self, parent):
        try:
            return self.delete_button
        except AttributeError:
            self.delete_button = wx.Button(parent, wx.ID_REMOVE)#wx.ID_DELETE)
            wx.EVT_BUTTON(self.delete_button, -1, self._on_delete)
            return self.delete_button


    def _on_delete(self, event):
        try:
            start_row = self.grid.GetSelectionBlockTopLeft()[0][0]
            end_row = self.grid.GetSelectionBlockBottomRight()[0][0]
        except IndexError:
            start_row = end_row = self.grid.GetGridCursorRow()

        self.grid.DeleteRows(start_row, end_row - start_row + 1)



    def Enable(self, flag):
        super(EditGrid, self).Enable(flag)
        try:
            self.delete_button.Enable(flag)
        except AttributeError:
            pass


    def _on_editor_shown(self, event):
        if not self._columns_[event.GetCol()][3]:
            #no attrib => no edit
            event.Veto()


    def calc_sizes(self):
        grid = self.grid

        hidden_parent = wx.Window(grid, -1, (0,0), (0,0))
        hidden_parent.Hide()

        labelwin = self.grid.GetGridColLabelWindow()
        labelwin.SetFont(self.grid.GetLabelFont())

        h = self.grid.GetDefaultRowSize()
        for i, cs in enumerate(self._columns_):
            itype = cs[1]
            attrib = cs[3]

            w, h1 = self.grid.GetTextExtent(itype.width_format())
            w1, h1 = labelwin.GetTextExtent(cs[0] + "i")
            w = max(w1, w)
                        
            if attrib:
                widget = itype.create_widget(hidden_parent, attrib)
                bw, bh = widget.GetBestSize()
                w = max(w, bw)
                h = max(h, bh)
                wx.CallAfter(widget.Destroy)

            grid.SetColMinimalWidth(i, w)
            grid.SetColSize(i, w)
            
        wx.CallAfter(hidden_parent.Destroy)
        self.grid.SetDefaultRowSize(h, True)



def isparent(child, parent):
    while child and child is not parent:
        child = child.GetParent()

    return bool(child)

        

class PatchEvtHandler(wx.EvtHandler):
    def __init__(self, editor):
        wx.EvtHandler.__init__(self)
        wx.EVT_KEY_DOWN(self, self._on_keydown)
        wx.EVT_KILL_FOCUS(self, self._on_kill_focus)
        self.editor = weakref.proxy(editor)

    
    def _on_keydown(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.editor.Reset()
            wx.CallAfter(self.editor.iview.grid.DisableCellEditControl)
            return

        elif event.GetKeyCode() == wx.WXK_RETURN:
            wx.CallAfter(self.editor.iview.grid.DisableCellEditControl)
            return
        
        event.Skip()


    def _on_kill_focus(self, event):
        grid = self.editor.iview.grid
        def handle_focus():
            focused = wx.Window_FindFocus()

            if not focused and wx.Platform == '__WXGTK__' \
               and isinstance(self.editor.iwidget, \
                              (widgets.DateTime, widgets.Date)) \
               and self.editor.iwidget.is_open():
                #dirty hack for datepicker control, to ensure
                #that month can be choosen
                return
            
            if grid and not isparent(focused, self.editor.iwidget):
                grid.DisableCellEditControl()

        wx.CallAfter(handle_focus)
        event.Skip()
    


class CellEditor(wx.grid.PyGridCellEditor):
    class ControlWrapper(wx.PyControl):
        def __init__(self, parent, editor):
            wx.PyControl.__init__(self, parent, -1)
            wx.EVT_SIZE(self, self._on_size)
            self.editor = weakref.proxy(editor)


        def _on_size(self, event):
            child = self.GetChildren()[0]
            child.SetSize(self.GetClientSize())
                

    def __init__(self, itype, iname, iview):
        wx.grid.PyGridCellEditor.__init__(self)
        self.itype = itype
        self.iname = iname
        self.iview = iview

        
    def end_inspect(self):
        self.iwidget.end_inspect()


    def Destroy(self):
        self.end_inspect()
        wx.grid.PyGridCellEditor.Destroy(self)



    def Create(self, parent, id, evt_handler):
        wrapper = self.ControlWrapper(parent, self)
        self.iwidget = self.itype.create_widget(wrapper, self.iname)
        setattr(self.iview, self.itype.name, self.iwidget)
        self.iview.prepare(self.itype.name)
        
        self.SetControl(wrapper)

        if evt_handler:
            wrapper.PushEventHandler(evt_handler)

        #patch application crash when ESC is pressed under GTK
        def apply_handler(window):
            for c in window.GetChildren():
                apply_handler(c)
            else:
                pe = PatchEvtHandler(self)
                window.PushEventHandler(pe)

        apply_handler(self.iwidget)
    

    def SetSize(self, rect):
        self.GetControl().SetDimensions(rect.x, rect.y,
                                        rect.width+4, rect.height+4,
                                        wx.SIZE_ALLOW_MINUS_ONE)


    def BeginEdit(self, row, col, grid):
        pos = bisect.bisect_left(self.iview.errors, row)
        index = row - pos #map grid rows to content index
        try:
            self.imodel = self.iview.content[index]
            self.created = False
        except IndexError:
            self.imodel = self.iview.__model__()
            self.created = True

        setattr(self.iview, self.itype.name, self.iwidget)
        self.iview.imodel = self.imodel
        self.iview.begin_edit(self.itype.name)
        self.org_value = getattr(self.imodel, self.itype.name)
        self.reset = False
        self.iwidget.inspect(self.imodel, self.itype.name)
        self.iwidget.SetFocus()
        self.iview.editors[self] = True
        

    def EndEdit(self, row, col, grid):
        #no end_inspect because of gtk error?
        #self.iwidget.end_inspect()
        if self.reset:
            setattr(self.imodel, self.itype.name, self.org_value)
        elif self.created:
            if self.iview.inserted(self.imodel):
                self.iview.content.insert(self.imodel)
                #insert only marks the imodel for the transaction,
                #but it was already changed
                #==>include it manually to ensure that check_constraint will really
                #be called
                tr = Transaction.get_transaction(self.imodel)
                tr.include(self.imodel)

                def informgrid():
                    self.iview.grid.BeginBatch()
                    try:
                        msg = wxg.GridTableMessage\
                              (self.iview.table, wxg.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
                        self.iview.grid.ProcessTableMessage(msg)

                        msg = wxg.GridTableMessage\
                              (self.iview.table, wxg.GRIDTABLE_NOTIFY_ROWS_APPENDED, 1)
                        self.iview.grid.ProcessTableMessage(msg)
                    finally:
                        self.iview.grid.EndBatch()

                wx.CallAfter(informgrid)

        delattr(self.iview, self.itype.name)
        del self.iview.imodel
        del self.org_value


    def Reset(self):
        self.reset = True


    def Clone(self):
        return CellEditor(self.itype, self.iname, self.iview)





