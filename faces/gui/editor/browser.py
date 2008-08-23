#@+leo-ver=4
#@+node:@file gui/editor/browser.py
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
Project Browser
"""
#@<< Imports >>
#@+node:<< Imports >>
import wx
import wx.stc
import wx.gizmos
import metapie.gui.pyeditor as pyeditor
import itertools
import faces.task as ftask
import faces.resource as fresource
import faces.observer as fobserver
import locale
import weakref
import metapie.gui.pyeditor as pyeditor
import context
from metapie.gui.controller import controller, ResourceManager
import faces.plocale
from classifiers import *


#@-node:<< Imports >>
#@nl

_is_source_ = True
_ = faces.plocale.get_gettext()

#@+others
#@+node:class Browser
class Browser(wx.gizmos.TreeListCtrl):
    #@	<< declarations >>
    #@+node:<< declarations >>
    img_size = (16, 16)
    left_sep = 4 # a work around for the wrong indent
    last_item = None
    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    #@+doc
    # displayed_eval_map:
    #   maps a project._idendity_() to the currently displayed evaluation data
    #@-doc
    #@@code
    def __init__(self, parent):
        wx.gizmos.TreeListCtrl.__init__(self, parent, -1,
                                        style= wx.TR_SINGLE | \
                                        wx.TR_HAS_BUTTONS | \
                                        wx.TR_HIDE_ROOT | \
                                        wx.LC_NO_HEADER |\
                                        wx.TR_FULL_ROW_HIGHLIGHT)

        self.Hide()
        self.idle_item = None
        self.drag_item = None
        self.image_map = {}
        self.displayed_eval_map = {} 
        self.init_tree()
        self.update_menus()

    #@-node:__init__
    #@+node:wxPython Methods
    #@+node:get_prev_visible
    #@+at 
    # Workarround for not implemented GetPrevVisible
    #@-at
    #@@c
    def get_prev_visible(self, item):
        before = item
        next = self.GetItemParent(item)
        while next.IsOk() and next != item:
            before = next
            next = self.GetNextVisible(next)

        if before == self.GetRootItem(): return item
        return before
    #@nonl
    #@-node:get_prev_visible
    #@+node:_on_change
    def _on_change(self, event):
        editor = self.GetParent().editor

        #@    << define internal insert function >>
        #@+node:<< define internal insert function >>
        def insert(item):
            prev, next = editor.code_items_near(item.get_line() - 1)

            def get_parent(item):
                parent = self.GetItemParent(item.tree_obj)
                return self.GetPyData(parent)

            parent = prev
            prev = None

            while parent and not parent.is_parent(item):
                prev = parent
                parent = get_parent(parent)

            if not parent: 
                parent = self.get_section(item)
                prev = None
            else: 
                parent = parent.tree_obj

            if prev:
                child = self.InsertItem(parent, prev.tree_obj, item.name)
            else:
                child = self.PrependItem(parent, item.name)

            item.tree_obj = child
            self.SetPyData(child, item)
            self.modify_item(child)
        #@nonl
        #@-node:<< define internal insert function >>
        #@nl
        #@    << split and sort changed items list >>
        #@+node:<< split and sort changed items list >>
        changed = event.changed
        removed = [ (-ci.get_line(), ci) for op, ci in changed if op == "removed" ]
        inserted = [ (ci.get_line(), ci) for op, ci in changed if op == "inserted" ]
        changed = [ (ci.get_line(), ci) for op, ci in changed if op == "changed" ]
        removed.sort()
        inserted.sort()
        changed.sort()
        #@nonl
        #@-node:<< split and sort changed items list >>
        #@nl

        for l, code_item in removed:
            #@        << remove item >>
            #@+node:<< remove item >>
            if code_item.tree_obj.IsOk():
                parent = self.GetItemParent(code_item.tree_obj)
                self.Delete(code_item.tree_obj)
                #@    << reinsert still existing children under new parent >>
                #@+node:<< reinsert still existing children under new parent >>
                first_child = None
                for c in code_item.get_children(True):
                    first_child = first_child or c
                    insert(c)

                if first_child:
                    self.modify_item(self.GetItemParent(first_child.tree_obj))
                #@nonl
                #@-node:<< reinsert still existing children under new parent >>
                #@nl
                self.modify_item(parent)
            #@nonl
            #@-node:<< remove item >>
            #@nl

        for l, code_item in inserted:
            #@        << insert item >>
            #@+node:<< insert item >>
            try:
                if code_item.tree_obj.IsOk():
                    tree_parent = self.GetItemParent(code_item.tree_obj)
                    item_parent = code_item.get_parent()
                    if tree_parent == item_parent.tree_obj:
                        #this can happen, in drag operations
                        continue
            except AttributeError: pass

            insert(code_item)
            #@<< insert children and modify their old parent >>
            #@+node:<< insert children and modify their old parent >>
            last_parent = None
            for c in code_item.get_children(True):
                try:
                    tree_obj = c.tree_obj
                except AttributeError: pass
                else:
                    if tree_obj.IsOk():
                        parent = self.GetItemParent(tree_obj)
                        if not last_parent: last_parent = parent
                        self.Delete(tree_obj)

                insert(c)

            if last_parent:
                self.modify_item(last_parent)
                self.modify_item(code_item.tree_obj)
            #@nonl
            #@-node:<< insert children and modify their old parent >>
            #@nl
            self.modify_item(self.GetItemParent(code_item.tree_obj))    
            #@nonl
            #@-node:<< insert item >>
            #@nl

        for l, code_item in changed:
            #@        << change item >>
            #@+node:<< change item >>
            expanded = self.IsExpanded(code_item.tree_obj)
            last_parent = self.GetItemParent(code_item.tree_obj)

            #remove item
            self.Delete(code_item.tree_obj)

            #reinsert with children
            insert(code_item)
            for c in code_item.get_children(True):
                insert(c)

            self.modify_item(self.GetItemParent(code_item.tree_obj))
            self.modify_item(last_parent)
            if expanded:
                self.Expand(code_item.tree_obj)
            #@nonl
            #@-node:<< change item >>
            #@nl

        if self.idle_item:
            self.idle_item = self.imports
    #@-node:_on_change
    #@+node:_on_idle
    def _on_idle(self, event):
        event.Skip()
        if not self.idle_item:
            return

        if not self.idle_item.IsOk():
            self.idle_item = None
            self.calc_column_widths()
            return

        if controller().is_processing(): 
            #dont't block another task
            return

        self.modify_item(self.idle_item)
        self.idle_item = self.GetNext(self.idle_item)
        event.RequestMore()

        if (self.idle_item and self.idle_item.IsOk()):
            code_item = self.GetPyData(self.idle_item)
        else:
            code_item = None

    #@-node:_on_idle
    #@+node:_on_size
    def _on_size(self, event):
        w, h = self.GetClientSize()
        self.GetMainWindow().SetDimensions(0, 0, w, h)
        self.SetColumnWidth(0, self.left_sep)

        if w > self.width:
            self.SetColumnWidth(1, self.width)
            sw = self.width
            fit_col = 1
            fit_width = sw
            for i, cw in enumerate(self.col_width):
                sw += cw
                if sw < w:
                    fit_col = i + 1
                    fit_width += cw
                else:
                    self.SetColumnWidth(i + 2, 0)

            additional = (w - fit_width) / fit_col
            for i in range(fit_col):
                cw = self.col_width[i]
                self.SetColumnWidth(i + 2, cw + additional)
                sw += cw


        else:
            self.SetColumnWidth(1, w)
            for i in range(2, self.GetColumnCount()):
                self.SetColumnWidth(i, 0)
    #@-node:_on_size
    #@+node:_on_refresh
    def _on_refresh(self, event):
        self.Refresh()
    #@-node:_on_refresh
    #@+node:_on_sel_changed
    def _on_sel_changed(self, event):
        if not self.drag_item:
            self.select_item(event.GetItem())
    #@-node:_on_sel_changed
    #@+node:_on_right_click
    def _on_right_click(self, event):
        menu = controller().make_menu()
        self.create_context_menu(menu, event.GetItem())
        if menu:    
            self.PopupMenu(menu.wxobj, event.GetPoint())
    #@nonl
    #@-node:_on_right_click
    #@+node:_on_begin_drag
    def _clean_up_dragging(self, e=None):
        self.ReleaseMouse()
        self.SetCursor(wx.NullCursor)

        self.Unbind(wx.EVT_KEY_DOWN)
        self.Unbind(wx.EVT_RIGHT_DOWN)
        self.Unbind(wx.EVT_LEFT_UP)
        self.drag_item = None


    def _on_begin_drag(self, event):
        item = event.GetItem()
        code_item = self.GetPyData(item)

        if is_task(code_item):  
            self.drag_item = code_item
            hand_cursor = wx.StockCursor(wx.CURSOR_HAND)
            self.SetCursor(hand_cursor)
            self.CaptureMouse()
            drag_item = self.drag_item
            #@        << define temporary event handlers >>
            #@+node:<< define temporary event handlers >>
            def on_key_down(evt):
                if evt.GetKeyCode() == wx.WXK_ESCAPE:
                    self._clean_up_dragging()

            #@-node:<< define temporary event handlers >>
            #@nl
            self.SetFocus()
            self.Bind(wx.EVT_KEY_DOWN, on_key_down)
            self.Bind(wx.EVT_LEFT_UP, self._on_end_drag)
            self.Bind(wx.EVT_RIGHT_DOWN, self._clean_up_dragging)


    def _on_end_drag(self, event):
        if not self.drag_item: return
        drag_item = self.drag_item    

        self._clean_up_dragging()

        pos = event.GetPosition()
        item, flag, col = self.HitTest(pos)
        #@    << check if drag_item is moved to a valid position >>
        #@+node:<< check if drag_item is moved to a valid position >>
        if not flag & (wx.TREE_HITTEST_ONITEMICON | wx.TREE_HITTEST_ONITEMLABEL):
            return

        ci = self.GetPyData(item)
        if not is_task(ci): return
        #@nonl
        #@-node:<< check if drag_item is moved to a valid position >>
        #@nl

        children = tuple(drag_item.get_children(True))
        editor = self.GetParent().editor
        editor.BeginUndoAction()
        #@    << move drag_item >>
        #@+node:<< move drag_item >>
        l, t, w, h = self.GetBoundingRect(item)
        q = t + h / 2

        if pos.y < q:
            new_line = drag_item.move_before(ci)
        else:
            if self.IsExpanded(item):
                item = self.GetNextVisible(item)
                ci = self.GetPyData(item)
                new_line = drag_item.move_before(ci)
            else:
                new_line = drag_item.move_after(ci)
        #@-node:<< move drag_item >>
        #@nl
        #@    << copy extended CodeItem attributes to new items >>
        #@+node:<< copy extended CodeItem attributes to new items >>
        new_item = editor.code_item_at(new_line)
        try:
            new_item.obj = drag_item.obj
            new_item.task_path = drag_item.task_path
            new_item.obj._function.code_item = weakref.proxy(new_item)
        except AttributeError: pass

        tasks_to_check = list(new_item.get_children(True))
        for i, c in enumerate(tasks_to_check):
            old = children[i]
            try:
                c.obj = old.obj
                c.task_path = old.task_path
                c.obj._function.code_item = weakref.proxy(c)
            except AttributeError: pass

        tasks_to_check.append(new_item)
        #@nonl
        #@-node:<< copy extended CodeItem attributes to new items >>
        #@nl

        editor.should_be_corrected = True

        editor.EndUndoAction()
        wx.CallAfter(self.update_selection, new_item)
    #@-node:_on_begin_drag
    #@-node:wxPython Methods
    #@+node:Internal Tool Methods
    #@+node:init_tree
    def init_tree(self):
        img = self.get_image_index
        append = self.AppendItem
        self.Freeze()

        self.width = 0
        self.image_list = wx.ImageList(*self.img_size)
        self.get_image_index("move")
        self.AssignImageList(self.image_list)
        self.GetHeaderWindow().Hide()

        #@    << Create Columns >>
        #@+node:<< Create Columns >>
        self.AddColumn(_(""))
        self.AddColumn(_("Name"))
        self.AddColumn(_("Start"))
        self.AddColumn(_("End"))
        self.AddColumn(_("Length"))
        self.AddColumn(_("Effort"))
        self.SetMainColumn(1)
        self.col_width = [ 0 ] * (self.GetColumnCount() - 2)
        #@nonl
        #@-node:<< Create Columns >>
        #@nl
        #@    << Insert Header Nodes >>
        #@+node:<< Insert Header Nodes >>
        root = self.AddRoot("root")
        imports = append(root, _("Imports"), img("import16"))
        miscellaneous = append(root, _("Miscellaneous"), img("misc16"))
        resources = append(root, _("Resources"), img("resources16"))
        tasks = append(root, _("Tasks"))
        evaluations = append(root, _("Evaluations"), img("evaluations16"))
        observers = append(root, _("Observers"), img("camera16"))#
        #@nonl
        #@-node:<< Insert Header Nodes >>
        #@nl
        #@    << Set Header Node Fonts >>
        #@+node:<< Set Header Node Fonts >>
        header_font = self.get_item_font(imports)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)

        self.SetItemFont(imports, header_font)
        self.SetItemFont(miscellaneous, header_font)
        self.SetItemFont(resources, header_font)
        self.SetItemFont(tasks, header_font)
        self.SetItemFont(evaluations, header_font)
        self.SetItemFont(observers, header_font)
        #@nonl
        #@-node:<< Set Header Node Fonts >>
        #@nl
        #@    << Set Header Node Titles >>
        #@+node:<< Set Header Node Titles >>
        self.SetItemText(resources, _("Efficiency"), 2)
        self.calc_column_widths(resources)

        self.set_image(tasks, "tasks16", "tasks_open16")
        self.SetItemText(tasks, _("Start"), 2)
        self.SetItemText(tasks, _("End"), 3)
        self.SetItemText(tasks, _("Length"), 4)
        self.SetItemText(tasks, _("Effort"), 5)
        self.calc_column_widths(tasks)
        #@nonl
        #@-node:<< Set Header Node Titles >>
        #@nl

        self.imports = imports
        self.miscellaneous = miscellaneous
        self.resources = resources
        self.tasks = tasks
        self.evaluations = evaluations
        self.observers = observers

        self.SelectItem(imports)
        self.Thaw()

    #@-node:init_tree
    #@+node:create_context_menu
    def create_context_menu(self, menu, item):
        editor = self.GetParent().editor

        try:
            first_item = editor.code_items[0]
        except IndexError:
            #at least one code item has to be there
            return

        if item == self.imports:
            context.CImport(first_item).make_browser_menu(menu, ("create",))

        elif item == self.resources:
            context.CResource(first_item).make_browser_menu(menu, ("create",))

        elif item == self.tasks:
            context.CProjectDeclaration(first_item).make_browser_menu(menu, ("create",))

        elif item == self.evaluations:
            context.CEvaluation(first_item).make_browser_menu(menu, ("create",))

        elif item == self.observers:
            context.CObserver(first_item).make_browser_menu(menu, ("create",))

        else:
            code_item = self.GetPyData(item)
            action_filter = ("add", "edit", "extra")

            for c in context.Context.context_list:
                c = c.__class__(code_item)
                if c.make_browser_menu(menu, action_filter):
                    break

            if is_project(code_item):
                self.append_display_eval_data_menu(code_item, item, menu)
    #@-node:create_context_menu
    #@+node:append_display_eval_data_menu
    def append_display_eval_data_menu(self, code_item, item, menu):
        session = controller().session
        editor = self.GetParent().editor

        try:
            id_ = code_item.obj._idendity_()
        except AttributeError: return

        evals = [ (k, v) for k, v in session.evaluations.items() 
                  if v._idendity_() == id_ ]
        if not evals: return

        displayed_eval_name = self.displayed_eval_map.get(id_)
        show_menu = menu.make_menu(_("&Displayed Evaluation Data"))
        menu.make_separator(_("&Displayed Evaluation Data"), True)

        def change_data_call(varname):
            def change_data(): 
                self.displayed_eval_map[id_] = varname
                self.idle_item = item

            return change_data

        for varname, eval in evals:
            check_item = False
            try:
                if displayed_eval_name == varname:
                    check_item = True
            except AttributeError: pass

            mi = show_menu.make_temp_item(varname, 
                                          change_data_call(varname),
                                          check_item=check_item)
            if check_item: mi.check()
    #@-node:append_display_eval_data_menu
    #@+node:get_display_eval_data
    def get_display_eval_data(self, task):
        id_ = task.root._idendity_()
        evaluations = controller().session.evaluations
        try:
            eval_name = self.displayed_eval_map[id_]
            try:
                return evaluations[eval_name].get_task(task.path)
            except KeyError:
                del self.displayed_eval_map[id_]
        except KeyError: pass

        evaluations = evaluations.items()
        evaluations.sort()

        for varname, eval in evaluations:
            if eval._idendity_() == id_: 
                self.displayed_eval_map[id_] = varname
                return eval.get_task(task.path) or task

        return task
    #@nonl
    #@-node:get_display_eval_data
    #@+node:get_image_index
    def get_image_index(self, path):
        try:
            return self.image_map[path]
        except KeyError:
            if path is None: return -1
            bmp = ResourceManager.load_bitmap(path, self.img_size)
            r = self.image_map[path] = self.image_list.Add(bmp)
            return r
    #@-node:get_image_index
    #@+node:set_image
    def set_image(self, item, closed=None, opened=None):
        if closed:
            self.SetItemImage(item, self.get_image_index(closed),
                              which=wx.TreeItemIcon_Normal)

        if opened:
            self.SetItemImage(item, self.get_image_index(opened),
                              which=wx.TreeItemIcon_Expanded)
    #@-node:set_image
    #@+node:get_item_font
    def get_item_font(self, item):
        font = self.GetItemFont(item)
        if not font.Ok(): font = self.GetFont()
        return font
    #@-node:get_item_font
    #@+node:get_section
    def get_section(self, code_item):
        if is_import(code_item): return self.imports
        if is_resource(code_item): return self.resources
        if is_project(code_item): return self.tasks
        if is_evaluation(code_item): return self.evaluations
        if is_observer(code_item): return self.observers
        return self.miscellaneous
    #@nonl
    #@-node:get_section
    #@+node:calc_column_widths
    def calc_column_widths(self, item=None):
        item = item or self.GetFirstChild(self.tasks)[0]
        if not item.IsOk(): return

        hidden_window = self.GetHeaderWindow()
        extent = hidden_window.GetTextExtent

        hidden_window.SetFont(self.get_item_font(item))
        for i, cw in enumerate(self.col_width):
            width = extent(self.GetItemText(item, i + 2))[0]
            self.col_width[i] = max(cw, width + 10)
    #@-node:calc_column_widths
    #@+node:modify_item
    def modify_item(self, tree_item):
        item = self.GetPyData(tree_item)
        if not item: return

        iclosed = None
        iopened = None

        if is_project(item) or is_task(item):
            #@        << make task >>
            #@+node:<< make task >>
            try:
                task = item.obj
            except AttributeError:
                if item.has_children():
                    iclosed = "folderstar16"
                    iopened = "folder_openstar16"
                else:
                    iopened = iclosed = "leafstar16"
            else:
                if item.has_children():
                    iclosed = "folder16"
                    iopened = "folder_open16"
                else:
                    iopened = iclosed = "leaf16"

                task = self.get_display_eval_data(task)
                str_obj = task.to_string
                self.SetItemText(tree_item, str_obj.start, 2)
                self.SetItemText(tree_item, str_obj.end, 3)
                self.SetItemText(tree_item, str_obj.length, 4)
                self.SetItemText(tree_item, str_obj.effort, 5)

            #@-node:<< make task >>
            #@nl

        elif is_resource(item):
            #@        << make resource >>
            #@+node:<< make resource >>
            try:
                self.SetItemText(tree_item,
                                 locale.format("%.2f", item.obj.efficiency),
                                 2)
                iclosed = item.obj.__type_image__
            except AttributeError:
                iclosed = get_resource_base(item).__type_image__
            #@nonl
            #@-node:<< make resource >>
            #@nl

        elif is_observer(item):
            #@        << make observer >>
            #@+node:<< make observer >>
            try:
                iclosed = item.obj.__type_image__
            except AttributeError:
                iclosed = get_observer_base(item).__type_image__
            #@nonl
            #@-node:<< make observer >>
            #@nl

        if not iclosed:
            if item.obj_type == pyeditor.FUNCTION:
                iopened = iclosed = "exec16"
            elif item.obj_type == pyeditor.CLASS:
                iopened = iclosed = "class16"

        self.set_image(tree_item, iclosed, iopened)
    #@-node:modify_item
    #@+node:select_item
    def select_item(self, item):
        try:
            editor = self.GetParent().editor
            item = self.GetPyData(item)
            if editor.context.code_item is item: return

            line = item.get_line()
            editor.LineScroll(0, line - editor.GetFirstVisibleLine())
            editor.GotoPos(editor.PositionFromLine(line))
            wx.CallAfter(editor.SetFocus)
        except: pass
    #@-node:select_item
    #@+node:move_caret_to_end
    def move_caret_to_end(self, treeitem):
        editor = self.GetParent().editor
        last = treeitem
        code_item = None
        while last.IsOk():
            code_item = self.GetPyData(last) or code_item
            last = self.GetLastChild(last)

        if code_item:
            line = code_item.get_last_line()
        else:
            #the section has no child ==> set the caret before the first child
            #of the next section
            next = treeitem
            line = -1
            while True:
                next = self.GetNextSibling(next)
                if next.IsOk():
                    child = self.GetFirstChild(next)
                    if not child.IsOk(): continue
                    code_item = self.GetPyData(child)
                    if code_item:
                        line = code_item.get_line() - 1
                        break
                else:
                    break

            if line < 0: line = editor.GetLineCount() - 1

        editor.LineScroll(0, line - editor.GetFirstVisibleLine())
        editor.GotoLine(line)
    #@nonl
    #@-node:move_caret_to_end
    #@-node:Internal Tool Methods
    #@+node:Public Methods
    #@+node:bind_events
    def bind_events(self):
        editor = self.GetParent().editor
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self._on_sel_changed)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self._on_refresh)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self._on_refresh)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self._on_right_click)
        self.Bind(wx.EVT_SIZE, self._on_size)
        self.Bind(wx.EVT_IDLE, self._on_idle)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self._on_begin_drag)
        editor.Bind(pyeditor.EVT_CODE_ITEM_CHANGED, self._on_change)
    #@-node:bind_events
    #@+node:on_make_menu
    def on_make_menu(self, menu_title):
        if menu_title == _("&Project"):
            top = controller().get_top_menu()
            project_menu = top.make_menu(_("&Project"), pos=110)
            item = self.GetSelection()
            if item.IsOk():
                self.create_context_menu(project_menu, item)
    #@nonl
    #@-node:on_make_menu
    #@+node:update_menus
    def update_menus(self):
        top = controller().get_top_menu()
        project_menu = top.make_menu(_("&Project"), pos=110)
        view = controller().find_view_of(self)
        menu = lambda *args, **kw: project_menu.make_item(view, *args, **kw)


        def expand(): self.Expand(self.GetSelection())
        def collapse(): self.Collapse(self.GetSelection())
        def next(): 
            next = self.GetNextVisible(self.GetSelection())
            if next.IsOk():
                self.SelectItem(next)
                self.EnsureVisible(next)

        def prev():
            prev = self.get_prev_visible(self.GetSelection())
            if prev.IsOk():
                self.SelectItem(prev)
                self.EnsureVisible(prev)

        menu(_("Collapse Item\tALT-LEFT"), collapse, "left16", pos=10)
        menu(_("Expand Item\tALT-RIGHT"), expand, "right16", pos=20)
        menu(_("Move Item Up\tALT-UP"), prev, "up16", pos=30)
        menu(_("Move Item Down\tALT-DOWN"), next, "down16", pos=40)

        project_menu.make_separator(_("Move Item Down"), False)        
    #@nonl
    #@-node:update_menus
    #@+node:refresh
    def refresh(self):
        #optimization the module has not changed the browser will not change
        editor = self.GetParent().editor
        self.idle_item = None
        self.Freeze()

        #@    << Delete children >>
        #@+node:<< Delete children >>
        self.DeleteChildren(self.imports)
        self.DeleteChildren(self.miscellaneous)
        self.DeleteChildren(self.resources)
        self.DeleteChildren(self.tasks)
        self.DeleteChildren(self.evaluations)
        self.DeleteChildren(self.observers)
        #@nonl
        #@-node:<< Delete children >>
        #@nl

        #@    << Declarations >>
        #@+node:<< Declarations >>
        img = self.get_image_index
        append = self.AppendItem

        hidden_window = self.GetHeaderWindow()
        extent = hidden_window.GetTextExtent

        font = self.GetFont()
        hidden_window.SetFont(font)

        triangle = 12
        space = 6
        offset = self.GetIndent() + triangle \
                 + 2 * space + self.img_size[0] \
                 + self.left_sep

        depth_width = self.GetIndent() + triangle
        #@nonl
        #@-node:<< Declarations >>
        #@nl
        #@    << Insert Nodes >>
        #@+node:<< Insert Nodes >>
        hierachy = []
        width = 0

        for item in editor.code_items:
            item_line = item.get_line()

            while hierachy:
                parent, last_line = hierachy[-1]
                if last_line > item.get_line(): break
                hierachy.pop()
            else:
                parent = self.get_section(item)

            child = append(parent, item.name)
            width = max(width, extent(item.name)[0] \
                        + len(hierachy) * depth_width)

            item.tree_obj = child
            self.SetPyData(child, item)

            hierachy.append((child, item.get_last_line()))
        #@nonl
        #@-node:<< Insert Nodes >>
        #@nl

        self.Thaw()

        self.width = width + offset
        #start idleing at self.imports
        self.idle_item = self.imports

        item = editor.current_code_item()
        if item: self.update_selection(item)
    #@-node:refresh
    #@+node:update_selection
    def update_selection(self, item):
        try:
            if not item.tree_obj:
                print "error no item.tree_obj", item.name
                return

            if item.tree_obj.IsOk():
                self.SelectItem(item.tree_obj)
            return
        except AttributeError: pass
    #@-node:update_selection
    #@-node:Public Methods
    #@-others
#@nonl
#@-node:class Browser
#@-others
#@-node:@file gui/editor/browser.py
#@-leo
