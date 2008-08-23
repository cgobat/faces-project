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
import wx.grid

class GridAutoWidthMixin(object):
    """ A mix-in class that automatically resizes the last column to take up
        the remaining width of the grid.

        This causes the wx.Grid to automatically take up the full width of
        the list, without either a horizontal scroll bar (unless absolutely
        necessary) or empty space to the right of the last column.

        WARNING: If you override the EVT_SIZE event in your wx.ListCtrl, make
                 sure you call event.Skip() to ensure that the mixin's
                 _on_resize method is called.
    """
   
    def __init__(self):
        self._resize_col_min_width = None
        self._resize_col = -1
        self._scroll_rate = None

        wx.EVT_SIZE(self, self._on_resize)
        #wx.grid.EVT_GRID_COL_SIZE(self, self._on_resize)


    def set_resize_column(self, col):
        """
        Specify which column that should be autosized.  Pass either
        -1 or the column number.  Default is -1.
        """
        self._resize_col = col
        

    def resize_last_columns(self, min_width):
        self.resize_column(min_width)


    def resize_column(self, min_width):
        self._resize_col_min_width = min_width
        self._do_resize()
        

    def _on_resize(self, event):
        self._do_resize()
        event.Skip()


    def _do_resize(self):
        if not self:  # avoid a PyDeadObject error
            return

        if not self._scroll_rate:
            self._scroll_rate = self.GetScrollPixelsPerUnit()
        
        num_cols = self.GetNumberCols()
        if num_cols == 0: return # Nothing to resize.

        resize_col = self._resize_col
        if resize_col < 0: resize_col = num_cols + resize_col

        if self._resize_col_min_width == None:
            self._resize_col_min_width = self.GetColSize(resize_col)

        resize_col_width = self.GetColSize(resize_col)
        tot_col_width = sum(map(lambda i: self.GetColSize(i), range(num_cols)))
        tot_col_width -= resize_col_width

        list_width = self.GetClientSize().width
##        if wx.Platform != '__WXMSW__':
##            if self.GetItemCount() > self.GetCountPerPage():
##                scroll_width = wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X)
##                list_width -= scroll_width


        if tot_col_width + self._resize_col_min_width > list_width:
            self.SetColSize(resize_col, self._resize_col_min_width)
            self.SetScrollRate(*self._scroll_rate)
            return

        # Resize the last column to take up the remaining available space.
        self.SetColSize(resize_col, list_width - tot_col_width)
        self.SetScrollRate(0, self._scroll_rate[1])
        



class CellComboEditor(wx.grid.PyGridCellEditor):
    def __init__(self, choices_func):
        wx.grid.PyGridCellEditor.__init__(self)
        self._choices_func = choices_func
        

    def Create(self, parent, id, evt_handler):
        self._tc = masked.Ctrl(parent, -1, "",
                               controlType=masked.controlTypes.COMBO,
                               choices=(),
                               choiceRequired=True,
                               autoSelect=True)
       
        self.SetControl(self._tc)
        self._evt_handler = evt_handler
        if evt_handler:
            wx.EVT_KEY_DOWN(self._tc, evt_handler.ProcessEvent)
            wx.EVT_CHAR(self._tc, evt_handler.ProcessEvent)
            self._tc.PushEventHandler(evt_handler)
            

    def SetSize(self, rect):
        self._tc.SetDimensions(rect.x, rect.y, rect.width+4, rect.height+4,
                               wx.SIZE_ALLOW_MINUS_ONE)


    def BeginEdit(self, row, col, grid):
        #A hack, preventing the grid_handler to end_edit
        #the control looses it's focus to the popup
        #drawback: a seqfault at program exit when the
        #          dialog is closed while editing
        if self._evt_handler: self._tc.PopEventHandler()

        self.start_value = grid.GetTable().GetValue(row, col)
        self._tc.SetCtrlParameters(choices=self._choices_func(),
                                   choiceRequired=True,
                                   autoSelect=True)
        self._tc.SetValue(self.start_value)
        self._tc.SetFocus()
                


    def EndEdit(self, row, col, grid):
        if self._evt_handler: self._tc.PushEventHandler(self._evt_handler)

        changed = False

        val = self._tc.GetValue()
        if val != self.start_value and self._tc.IsValid():
            changed = True
            grid.GetTable().SetValue(row, col, val) 

        self.start_value = ''
        return changed


    def Reset(self):
        self._tc.SetValue(self.start_value)


    def Clone(self):
        return DynamicCellChoiceEditor(self.choices_func)



class CellChoicesEditor(wx.grid.PyGridCellEditor):
    def __init__(self):
        wx.grid.PyGridCellEditor.__init__(self)
       

    def Create(self, parent, id, evt_handler):
        self._tc = wx.Choice(s)
       
        self.SetControl(self._tc)
        self._evt_handler = evt_handler
        if evt_handler:
            wx.EVT_KEY_DOWN(self._tc, evt_handler.ProcessEvent)
            wx.EVT_CHAR(self._tc, evt_handler.ProcessEvent)
            self._tc.PushEventHandler(evt_handler)
            

    def SetSize(self, rect):
        self._tc.SetDimensions(rect.x, rect.y, rect.width+4, rect.height+4,
                               wx.SIZE_ALLOW_MINUS_ONE)


    def BeginEdit(self, row, col, grid):
        if self._evt_handler: self._tc.PopEventHandler()

        self.start_value = grid.GetTable().GetValue(row, col)
        self._tc.SetCtrlParameters(choices=self._choices_func(),
                                   choiceRequired=True,
                                   autoSelect=True)
        self._tc.SetValue(self.start_value)
        self._tc.SetFocus()
                


    def EndEdit(self, row, col, grid):
        if self._evt_handler: self._tc.PushEventHandler(self._evt_handler)

        changed = False

        val = self._tc.GetValue()
        if val != self.start_value and self._tc.IsValid():
            changed = True
            grid.GetTable().SetValue(row, col, val) 

        self.start_value = ''
        return changed


    def Reset(self):
        self._tc.SetValue(self.start_value)


    def Clone(self):
        return DynamicCellChoiceEditor(self.choices_func)





class AutoSizeGrid(wx.grid.Grid, GridAutoWidthMixin):
    def __init__(self, parent):
        wx.grid.Grid.__init__(self, parent, -1)
        GridAutoWidthMixin.__init__(self)
        wx.grid.EVT_GRID_CELL_LEFT_DCLICK(self, self._on_left_dclick)


    def _on_left_dclick(self, evt):
        if self.CanEnableCellControl():
            self.EnableCellEditControl()

        evt.Skip()

        
class GridCtrl(wx.PyPanel):
    #to overwrite GetBestSize

    def __init__(self, parent):
        wx.PyPanel.__init__(self, parent, style=wx.SIMPLE_BORDER)
        self.create_grid()
        wx.EVT_SIZE(self, self._on_resize)



    def create_grid(self):
        self.grid = AutoSizeGrid(self)



    def SetTable(self, table):
        self.grid.SetTable(table, True)
        table.init_table()
        self.grid.SetRowLabelSize(0)
        self.grid.SetMargins(0,0)
        self.grid.AutoSizeColumns(True)
        self.grid._do_resize()
                

    def _on_resize(self, event):
        self.grid.SetSize(self.GetClientSize())


    def DoGetBestSize(self):
        return (0, 0)

        
    def Enable(self, flag):
        self.grid.Enable(flag)


    def delete_row(self, event):
        self.grid.DeleteRows(self.grid.GetGridCursorRow())




##class ObjectGridTable(wx.grid.PyGridTableBase):
##    def __init__(self, grid):
##        gridlib.PyGridTableBase.__init__(self)
        
##        self.attributes = ()
##        grid.SetTable(self)
        

        
##    def GetNumberRows(self): return len(self.data) + 1
##    def GetNumberCols(self): return len(self.attributes)
##    def IsEmptyCell(self, row, col): return False
##    def GetColLabelValue(self, col):
##        attr = self.attributes[col]
##        if isinstance(attr, (tuple, list)) n:
            

        
##    def GetTypeName(self, row, col): return self.data_type[col]


##    def GetValue(self, row, col):
##        try:
##            return getattr(self.data[row], self.col_attribs[col])
##        except IndexError:
##            return ''
        
##    def SetValue(self, row, col, value):
##        try:
##            if col == 0 and not self.GetValue(row, 0):
##                for c in range(self.GetNumberCols()):
##                    setattr(self.data[row],
##                            self.col_attribs[c],
##                            self.col_defaults[c])
                            
##                setattr(self.data[row], self.col_attribs[col], value)
##                msg = gridlib.GridTableMessage(self,
##                              gridlib.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
##            else:
##                setattr(self.data[row], self.col_attribs[col], value)
##        except IndexError:
##            class Dumy: pass
##            d = Dumy()
##            for c in range(self.GetNumberCols()):
##                setattr(d, self.col_attribs[c], "")
                
##            self.data.append(d)
##            self.SetValue(row, col, value)

##            msg = gridlib.GridTableMessage(self,
##                          gridlib.GRIDTABLE_NOTIFY_ROWS_APPENDED, 1)
##            self.GetView().ProcessTableMessage(msg)


##    def DeleteRows(self, pos=0, num_rows=1):
##        grid = self.GetView()
##        if pos < len(self.data):
##            del self.data[pos:pos + num_rows]
        
##            msg = gridlib.GridTableMessage(self,
##                          gridlib.GRIDTABLE_NOTIFY_ROWS_DELETED, pos, num_rows)
        
##            self.GetView().ProcessTableMessage(msg)

##        return True


        


def clear_events_on_destroy(window):
    from wx.lib.evtmgr import eventManager
    def deregister(event):
        if event.GetEventObject() is window:
            eventManager.DeregisterWindow(window)

    eventManager.Register(deregister, wx.EVT_WINDOW_DESTROY, window)


if __name__ == '__main__':
    import wx.lib.evtmgr
    _eventManager = wx.lib.evtmgr.eventManager
    
    app = wx.PySimpleApp()
    f = wx.Frame(None)

    
    p = wx.Panel(f)

    grid = GridCtrl(p)
    remove = wx.Button(p, wx.ID_REMOVE)
    
    _eventManager.Register(grid.delete_row, wx.EVT_BUTTON, remove)
    clear_events_on_destroy(remove)
    
    #set ticker properties here if you want
    s = wx.BoxSizer(wx.VERTICAL)
    #s = wx.BoxSizer(wx.HORIZONTAL)
    s.Add(grid, flag=wx.GROW, proportion=1)
    s.Add(remove)
    p.SetSizer(s)
    f.Show()
    app.MainLoop()


