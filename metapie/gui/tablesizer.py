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
import re
import sys
import math

class TableSizer(wx.PySizer):
    """
    This is a more comfortable version of a GridBagSizer.
    Instead of calculating all positions and spans by your self,
    you specify a format string and let TableSizer do it.
    The format string is an ascii table:

    '''
    #line1|ctrl1|ctrl2> |ctrl3
    #line2|ctrl4|ctrl5{cc}>
    #line3|ctrl6|  "
    -
    ctrl7[label of 7]|(20,30)|ctrl8
    '''

    ctrl1 - ctrl8 are control names that have to be specified by the
    controls dictionary in the constructor

    each line specifies a table row, each '|' specifes a column separator
    equal column separators must be have exactly the same position in each line
    A '>' specifes the cell should be expanded
    A tuple specifies a spacer
    A '"' specifes a row span with the above column
    '[xxx]' xxx is a label
    A '{xy}' specifies the cell alignment x can be l(eft), c(enter), r(ight)
             y can be t(op), c(enter), b(ottom)
    """

    class Cell(object):
        __slots__ = ("left", "right", "top", "bottom", "content")
        SPACER = re.compile(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)")
        CONTROL = re.compile(r"([^{>]*)({([lrm]?)([btc]?)})?(>?)")

        def __init__(self, left, top, right, bottom, content):
            self.left, self.top = left, top
            self.right, self.bottom = right, bottom
            self.content = content


        def constitute(self, parent, controls):
            if self.content.isdigit():
                #vertical spacer
                self.content = (int(self.content), 0)
                return

            mo = self.SPACER.match(self.content)
            if mo:
                #vertical and horizontal spacer
                self.content = (int(mo.group(1)), int(mo.group(2)))
                return

            mo = self.CONTROL.match(self.content)
            if not mo:
                raise ValueError("Wrong format '%s' at position (%i, %i)" \
                                 % (c.content, c.row, c.col))

            name = mo.group(1)
            if not name:
                self.content = (0, 0)
                return

            halign = mo.group(3) or 'l' # l, m, r
            valign = mo.group(4) or 'c' # t, c, b
            expand = bool(mo.group(5))

            if name[0] == "-":
                #horizontal separator line
                self.content = (wx.StaticLine(parent, style=wx.LI_HORIZONTAL),
                                halign, valign, True)
                return

            name = name.strip()
            if name[0] == '[' and name[-1] == ']':
                self.content = (wx.StaticText(parent, -1, name[1:-1]),
                                halign, valign, expand)
            else:
                try:
                    start = name.index('[')
                    end = name.index(']')
                    if name[end + 1:]: raise ValueError()
                    label = name[start + 1:end]
                    name = name[:start]
                    ctrl = controls(name)
                    ctrl.SetLabel(label)
                except ValueError:
                    ctrl = controls(name)

                self.content = (ctrl, halign, valign, expand)


        def set_tab_order(self, before):
            if isinstance(self.content[0], int):
                return before

            if before: self.content[0].MoveAfterInTabOrder(before)
            return self.content[0]


        def get_min_size(self, vgap, hgap):
            if isinstance(self.content[0], int):
                w, h = self.content[:2]
                if w: w += 2 * hgap
                if h: h += 2 * vgap
                return w, h
            
            if not self.content[0].IsShown(): return (0, 0)
                
            min_size = self.content[0].GetMinSize()
            best_size = self.content[0].GetBestSize()
            return max(min_size.width, best_size.width) + 2 * hgap,\
                   max(min_size.height, best_size.height) + 2 * vgap
            

        def set_dimensions(self, left, top, width, height, vgap, hgap):
            if isinstance(self.content[0], int): return
            ctrl, halign, valign, expand = self.content

            width -= 2 * hgap
            height -= 2 * vgap
            left += hgap
            top += vgap
            
            if expand:
                w, h = width, height
            else:
                w, h = self.get_min_size(0, 0)
                                
            if halign == 'm':
                left += (width - w) / 2
            elif halign == 'r':
                left += width - w
                
            if valign == 'c':
                top += (height - h) / 2
            elif valign == 'b':
                top += height - h

            self.content[0].SetDimensions(left, top, w, h)


    class SizeInfo(object):
        #__slots__ = ("min_size", "prop")
        min_size = 0
        prop = 0

    
    def __init__(self, window, format, controls, vgap=0, hgap=0):
        wx.PySizer.__init__(self)
        self.vgap = vgap
        self.hgap = hgap

        if isinstance(controls, dict):
            control_dict = controls
            controls = lambda k: control_dict[k]

        self.min_size = None
        self.cols = []
        self.rows = []
        
        self.parse_format(window, format.strip(), controls)


    def grow_col(self, col, proportion):
        if col < 0: col -= 1
        self.cols[col].prop = proportion
        self.min_size = None
        

    def grow_row(self, row, proportion):
        row *= 2
        if row < 0: row -= 1
        self.rows[row].prop = proportion
        self.min_size = None
        

    def ungrow_row(self, row):
        self.grow_row(row, 0)


    def ungrow_col(self, col):
        self.grow_col(col, 0)
        

    def add_error(self, window, ctrl):
        for c in self.cells:
            if c.content[0] is window:
                break
        else:
            raise ValueError("sizer item not found", window)

        cell = self.Cell(c.left, c.bottom, c.right, c.bottom + 1,
                         (ctrl, c.content[1], 't', c.content[3]))

        self.cells.append(cell)
        self.refresh()
        

    def parse_format(self, window, format, controls):
        lines = format.split("\n")
        self.cells = cells = []

        format_cols = {}
        format_rows = {}
        top = 0
        for l in lines:
            cols = l.split('|')
            format_rows[top] = True
            bottom = top + 1
            left = 0
            for c in cols:
                format_cols[left] = True
                right = left + len(c) + 1
                c = c.strip()
                if c.startswith('"'):
                    #found row span
                    above = [ ce for ce in cells
                              if ce.left == left and ce.top % 2 == 0]
                    
                    if not above:
                        raise ValueError("wrong row span at (%i, %i)"\
                                         % (left, top))
                    
                    above[-1].bottom = bottom
                else:
                    cells.append(self.Cell(left, top, right, bottom, c))

                left = right

            #an extra row for error messages
            cells.append(self.Cell(0, bottom, sys.maxint, bottom + 1, "0"))
            format_rows[bottom] = True
            top = bottom + 1
                
        #create controls and convert the border coordinates
        #from format-system to table-system
        format_cols = format_cols.keys()
        format_cols.sort()
        col_fo_ta = dict([ (fo, ta) for ta, fo in enumerate(format_cols) ])
        right_border = len(col_fo_ta)

        format_rows = format_rows.keys()
        format_rows.sort()
        row_fo_ta = dict([ (fo, ta) for ta, fo in enumerate(format_rows) ])
        bottom_border = len(row_fo_ta)

        last_ctrl = None
        for c in cells:
            c.left = col_fo_ta[c.left]
            c.right = col_fo_ta.get(c.right, right_border)
            c.top = row_fo_ta[c.top]
            c.bottom = row_fo_ta.get(c.bottom, bottom_border)
            
            c.constitute(window, controls)
            last_ctrl = c.set_tab_order(last_ctrl)

        self.cols = [ self.SizeInfo() for i in format_cols ]
        self.rows = [ self.SizeInfo() for i in format_rows ]
        self.cols.append(self.SizeInfo())
        self.rows.append(self.SizeInfo())


    def CalcMin(self):
        if self.min_size: return self.min_size

        cols = self.cols
        rows = self.rows
        hgap = self.hgap
        vgap = self.vgap

        col_rules = [ {} for si in cols ]
        row_rules = [ {} for si in rows ]
        cols_pos = [ 0 ] * len(col_rules)
        rows_pos = [ 0 ] * len(row_rules)

        def update_rule(rules, border, size):
            try:
                rules[border] = max(rules[border], size)
            except KeyError:
                rules[border] = size
            
        for c in self.cells:
            w, h = c.get_min_size(vgap, hgap)
            update_rule(col_rules[c.left], c.right, w)
            update_rule(row_rules[c.top], c.bottom, h)

        def calc_positions(infos, pos, rules):
            redo = True
            for _ in infos:
                redo = False
                for i, si in enumerate(infos[:-1]):
                    my_rules = rules[i]
                    if si.prop == 0 and len(my_rules) == 1:
                        index, size = my_rules.items()[0]
                        max_pos = pos[index] - size
                        if pos[i] < max_pos:
                            redo = True
                            pos[i] = max_pos
                            break

                    for index, size in my_rules.iteritems():
                        pos[index] = max(pos[index], pos[i] + size)

                if not redo:
                    break

            for i, si in enumerate(infos[:-1]):
                si.min_size = pos[i + 1] - pos[i]

        calc_positions(cols, cols_pos, col_rules)
        calc_positions(rows, rows_pos, row_rules)

        self.min_size = wx.Size(cols_pos[-1] - 2*hgap,
                                rows_pos[-1] - 2*vgap)
        return self.min_size
        

    def RecalcSizes(self):
        minsize = self.CalcMin()
        pos = self.GetPosition()
        size = self.GetSize()

        def round(x):
            return int(math.ceil(x - 0.5))

        def calc_pos(infos, add_size, max_size, offset):
            last_pos = offset
            pos = []

            prop_sum = float(sum([ si.prop for si in infos ]) or 1)
            
            for si in infos[:-1]:
                pos.append(last_pos)
                last_pos += si.min_size + round(add_size * si.prop / prop_sum)

            pos.append(max_size)
            return pos

        hgap = self.hgap
        vgap = self.vgap
        cols = calc_pos(self.cols, float(size[0] - minsize[0]),
                        size[0], pos.x - hgap)
        rows = calc_pos(self.rows, float(size[1] - minsize[1]),
                        size[1], pos.y - vgap)

        for c in self.cells:
            left = cols[c.left]
            right = cols[c.right]
            top = rows[c.top]
            bottom = rows[c.bottom]
            c.set_dimensions(left, top, right - left, bottom - top, vgap, hgap)
            

    def refresh(self):
        self.min_size = None
        


if __name__ == '__main__':
    def test1(p):
        class Big(wx.PyPanel):
            def DoGetBestSize(self):
                return 150, 200
        
        format = """
[a]|(18,0)|[b]
[Name: ]      |name>
[Multi: ]                       |multi>
--                              | "
[Depth: ]{b}  |depth{rb}|(10,10)| "
              |bool[Boolean]
big>
error{r}      |[tst]|hide{r}
"""
#0 |    1 | 2 |  3  | 4 |   5   |  6   |
        controls = {}
        controls["name"] = wx.TextCtrl(p, -1)
        controls["depth"] = wx.ComboBox(p, -1, choices=["1", "2", "3"],
                                        style=wx.CB_DROPDOWN\
                                        |wx.CB_READONLY\
                                        |wx.CB_SORT)
        controls["multi"] = wx.TextCtrl(p, -1,
                                        style=wx.TE_MULTILINE|wx.SUNKEN_BORDER)
        controls["bool"] = wx.CheckBox(p, -1, "")
        controls["big"] = Big(p, -1, style=wx.SUNKEN_BORDER)
        controls["error"] = wx.Button(p, -1, "show error")
        controls["hide"] = wx.Button(p, -1, "hide error")
        controls["hide"].Hide()

        s = TableSizer(p, format, controls, 2, 2)


        def make_error(msg):
            ctrl = wx.StaticText(p, -1, msg)
            ctrl.SetForegroundColour(wx.RED)
            font = ctrl.GetFont()
            font.SetPointSize(int(font.GetPointSize() * 0.7))
            ctrl.SetFont(font)
            return ctrl


        def show_errors(event):
            controls["hide"].Show()
            controls["error"].Hide()
            controls["big_err"] = make_error("Big Error message\nyes")
            s.add_error(controls["multi"], make_error("Error message"))
            s.add_error(controls["big"], controls["big_err"])
            s.add_error(controls["depth"], make_error("depth error message"))
            p.Layout()
        

        def hide_error(event):
            controls["big_err"].Hide()
            s.refresh()
            p.Layout()


        wx.EVT_BUTTON(controls["error"], -1, show_errors)
        wx.EVT_BUTTON(controls["hide"], -1, hide_error)
    
        s.grow_col(3, 1)
        s.grow_row(1, 1)
        return s

    #print "min", s.CalcMin()

    def test2(p):
        format = """
big>   | [Multi:]
 ""    | multi>
 ""    | depth>
"""    

        class Big(wx.PyPanel):
            def DoGetBestSize(self):
                return 200, 600

        controls = {}
        controls["depth"] = wx.TextCtrl(p, -1)
        controls["multi"] = wx.TextCtrl(p, -1,
                                        style=wx.TE_MULTILINE|wx.SUNKEN_BORDER)
        controls["big"] = Big(p, -1, style=wx.SUNKEN_BORDER)

        s = TableSizer(p, format, controls, 2, 2)

        s.grow_col(1, 1)
        s.grow_row(1, 1)
        return s


    
    app = wx.PySimpleApp()
    f = wx.Frame(None)
    p = wx.Panel(f, style=wx.RAISED_BORDER)
    
    s = test1(p)

    p.SetSizer(s)

    print "p.GetMinSize", s.GetMinSize()

    size = s.GetMinSize()
    
    p.SetClientSize(s.GetMinSize())

    print "p.size", p.GetSize()
    f.SetClientSize(p.GetSize())

    print "client size 1", f.GetClientSize(), f.GetSize()
    
    f.Show()

    print "client size 2", f.GetClientSize(), f.GetSize()
    app.MainLoop()
