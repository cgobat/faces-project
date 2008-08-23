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
import os.path
import sys
import types
import weakref
from menupanel import MenuPanel
from stacker import Stacker
import metapie.tools as tools
import metapie.navigator as navigator


try:
    import gc
    collect_garbage = gc.collect
    #gc.set_debug(gc.DEBUG_LEAK)
except:
    def collect_garbage(): pass


_ = tools.get_gettext()



_SIBLING_COMPLEMENT = {\
    False : False,
    navigator.SIBLING_BELOW : navigator.SIBLING_ABOVE,
    navigator.SIBLING_ABOVE : navigator.SIBLING_BELOW,
    }


def _tagged_owner(owner):
    """
    if owner is a window, it will be tagged, for a more
    efficent menu handling in case of MetaApp._on_destroy_
    """
    if isinstance(owner, wx.Window):
        owner._metapie_has_menu = True
        
    return owner

def _labelize(title):
    label = ""
    do_remove = False
    for c in title:
        if do_remove:
            do_remove = False
        elif c == '&':
            do_remove = True
            continue

        if c == "\t":
            break

        label += c

    return label


class _MenuItem:
    def __init__(self, parent, title, id, callback, owner, pos, wxobj):
        self.parent = parent
        self.id = id
        self.title = title
        self.pos = pos
        self.owner = _tagged_owner(owner)
        self.callback = callback
        self.wxobj = wxobj


    def remove(self):
        self.parent.remove_by_title(self.title)


    def _clear(self):
        ctrl = controller()
        del ctrl.callback_menus[self.callback]
        del ctrl.menu_id_callbacks[self.id]


    def enable(self, enable=True):
        self.wxobj.Enable(enable)


    def check(self, check=True):
        self.wxobj.Check(check)



class Macro:
    def __init__(self):
        self.commands = []


    def add_command(self, function, *args, **kwargs):
        self.commands.append((function, args, kwargs))


    def execute(self):
        try:
            for func, args, kwargs in self.commands:
                func(*args, **kwargs)

            return True
        except:
            return False


    def pop(self):
        if self.commands:
            self.commands.pop()


class _Menu:
    def __init__(self, parent, wxobj, title, id, pos):
        self.parent = parent
        self.wxobj = wxobj
        self.pos = pos
        self.id = id
        self.title = title
        self.items = {}
        self.separators = { }


    def __len__(self):
        if self.wxobj:
            return len(self.wxobj.GetMenuItems())

        return 0


    def __iter__(self):
        id_item_map = dict([ (item.id, item)
                             for item in self.items.values() ])
        for wxitem in self.wxobj.GetMenuItems():
            try:
                yield id_item_map[wxitem.GetId()]
            except KeyError: pass


    def get(self, title):
        return self.items.get(title)


    def make_temp_item(self, *args, **kwargs):
        return self.make_item(_MenuManager.TEMP_OWNER, *args, **kwargs)


    def make_item(self, owner, title, callback, bitmap=None,
                  help="", pos=10000, check_item=False, id=-1):
        ctrl = controller()
        try:
            item = self.items[title]
        except KeyError:
            insert_pos = self._find_insert_pos(pos)
            if id == -1:
                id = wx.NewId()

            kind = wx.ITEM_NORMAL
            if check_item: kind = wx.ITEM_CHECK
            wxitem = wx.MenuItem(self.wxobj, id, title, help, kind=kind)

            bmp = ResourceManager.load_bitmap(bitmap)
            if bmp:
                wxitem.SetBitmap(bmp)

            self.wxobj.InsertItem(insert_pos, wxitem)
            item = _MenuItem(self, title, id, callback, owner, pos, wxitem)
            self.items[title] = item

            ctrl.menu_id_callbacks[id] = callback
            ctrl.callback_menus[callback] = item
            self._check_separators()
        else:
            old_callback = item.callback
            del ctrl.callback_menus[old_callback]
            item.owner = owner
            item.callback = callback
            ctrl.menu_id_callbacks[item.id] = callback
            ctrl.callback_menus[callback] = item

        return item


    def make_menu(self, title, bitmap=None, help="", pos=10000, id=-1):
        try:
            menu = self.items[title]
        except KeyError:
            insert_pos = self._find_insert_pos(pos)
            wxmenu = wx.Menu()
            if id == -1:
                id = wx.NewId()

            self.wxobj.InsertMenu(insert_pos, id, title, wxmenu, help=help)
            menu = _Menu(self, wxmenu, title, id, pos)
            self.items[title] = menu
            self._check_separators()

        return menu


    def find_item(self, title):
        return self.items.get(title)


    def make_separator(self, title, before=False):
        label = _labelize(title) #a wxwindow patch
        self.separators[label] = before
        self._check_separators()


    def remove_by_owner(self, owner):
        for m in self.items.values():
            if isinstance(m, _MenuItem):
                if m.owner is owner: m.remove()
            else:
                m.remove_by_owner(owner)

        if not self.items:
            try:
                self.parent.remove_by_title(self.title)
            except AttributeError: pass


    def remove_by_title(self, title):
        try:
            item = self.items[title]
            item._clear()
            self._realize_remove_item(item)
            del self.items[title]
        except KeyError:
            return

        label = _labelize(title)
        if self.separators.has_key(label):
            del self.separators[label]

        self._check_separators()

        if not self.items:
            try:
                self.parent.remove_by_title(self.title)
            except AttributeError: pass


    def _find_insert_pos(self, pos):
        id_item_map = dict([ (item.id, item)
                             for item in self.items.values() ])
        index = -1
        for index, wxitem in enumerate(self.wxobj.GetMenuItems()):
            try:
                cmp_pos = id_item_map[wxitem.GetId()].pos
            except KeyError:
                continue

            if cmp_pos > pos: break
        else:
            index += 1

        return index


    def _realize_remove_item(self, item):
        self.wxobj.Remove(item.id)


    def _clear(self):
        ctrl = controller()
        for m in self.items.values():
            m._clear()
            self.wxobj.Remove(item.wxobj)
            del self.items[title]

    def _check_separators(self):
        self.__check_separators_call_count += 1
        wx.FutureCall(100, self.__check_separators)


    __check_separators_call_count = 0
    def __check_separators(self):
        self.__check_separators_call_count -= 1
        if self.__check_separators_call_count > 0: return
        self.__check_separators_call_count = 0

        #remove all separators
        remove_item = self.wxobj.DestroyItem
        sep = wx.ID_SEPARATOR
        for item in self.wxobj.GetMenuItems():
            if item.GetId() == sep: remove_item(item)

        #reinsert separators:
        if not self.separators: return

        pos_labels = [ (i, item.GetLabel())
                       for i, item in enumerate(self.wxobj.GetMenuItems()) ]
        pos_labels.reverse()
        count = len(pos_labels) - 1

        last_separator_pos = 0
        for p, l in pos_labels:
            try:
                if self.separators[l]:
                    if p > 0:
                        self.wxobj.InsertSeparator(p)
                        last_separator_pos = p
                else:
                    if p < count and last_separator_pos != p + 1:
                        self.wxobj.InsertSeparator(p + 1)
                        last_separator_pos = p + 1
            except KeyError: pass


class _TopMenu(_Menu):
    def __init__(self, wxobj):
        _Menu.__init__(self, None, wxobj, "root", -1, -1)


    def make_menu(self, title, bitmap=None, pos=10000, id=-1):
        try:
            menu = self.items[title]
        except KeyError:
            if id == -1:
                id = wx.NewId()

            insert_pos = self._find_insert_pos(pos)
            wxmenu = wx.Menu()
            self.wxobj.Insert(insert_pos, wxmenu, title)
            menu = _Menu(self, wxmenu, title, id, pos)
            self.items[title] = menu

        return menu


    def remove_by_owner(self, owner):
        for m in self.items.values():
            m.remove_by_owner(owner)


    def _realize_remove_item(self, item):
        index = self.wxobj.FindMenu(item.title)
        self.wxobj.Remove(index)


    def _check_separators(self):
        pass


    def _find_insert_pos(self, pos):
        menus = [ (item.pos, item) for item in self.items.values() ]
        menus.sort()

        index = -1
        for index, pos_item in enumerate(menus):
            cmp_pos, item = pos_item
            if cmp_pos > pos: break
        else:
            index += 1

        return index



class _Toolbar:
    ITEM_NORMAL = wx.ITEM_NORMAL
    ITEM_CHECK = wx.ITEM_CHECK
    ITEM_RADIO = wx.ITEM_RADIO

    def __init__(self, wxobj, parent):
        self.wxobj = wxobj
        self.parent = parent
        self.tools = []
        self.separators = {}


    def make_control(self, owner, title, factory, pos=-1):
        tool = self.get(title)
        if not tool:
            id_ = wx.NewId()

            tool = _ToolbarControl(self, id_, title, owner, factory)
            tool._insert_at_toolbar(self.wxobj, pos)
            if pos <= -1:
                self.tools.append(tool)
            else:
                self.tools.insert(pos, tool)

            self._check_separators()
            self.realize()
        else:
            tool.owner = owner
            tool.factory = factory

        return tool
 

    def make_separator(self, title, before=False):
        try:
            self.separators[title] = before
            self._check_separators()
        finally:
            self.realize()


    def make_tool(self, owner, title, callback,
                  bitmap1, bitmap2=wx.NullBitmap,
                  kind=ITEM_NORMAL,
                  short="", long="",
                  pos=-1):
        ctrl = controller()
        tool = self.get(title)
        if not tool:
            id_ = wx.NewId()

            bmp1 = ResourceManager.load_bitmap(bitmap1)
            bmp2 = ResourceManager.load_bitmap(bitmap2)

            tool = _ToolbarItem(self, id_, title, owner, bmp1, bmp2,
                                kind, short, long)

            tool._insert_at_toolbar(self.wxobj, pos)
            if pos <= -1:
                self.tools.append(tool)
            else:
                self.tools.insert(pos, tool)

            ctrl.menu_id_callbacks[id_] = callback
            ctrl.callback_tools[callback] = tool
            self._check_separators()
            self.realize()
        else:
            tool.owner = owner
            old_callback = ctrl.menu_id_callbacks[tool.id]
            del ctrl.callback_tools[old_callback]
            ctrl.menu_id_callbacks[tool.id] = callback
            ctrl.callback_tools[callback] = tool

        return tool


    def remove_by_owner(self, owner):
        to_delete = []
        try:
            index = -1
            for t in self.tools:
                index += 1
                if t and t.owner == owner:
                    self.wxobj.DeleteTool(t.id)
                    to_delete.append(index)

                    if self.separators.has_key(t.title):
                        del self.separators[t.title]

                    ctrl = controller()
                    callback = ctrl.menu_id_callbacks[t.id]
                    del ctrl.menu_id_callbacks[t.id]
                    del ctrl.callback_tools[callback]

            to_delete.reverse()
            for i in to_delete:
                del self.tools[i]

            self._check_separators()
        finally:
            if to_delete:
                self.realize() #avoid flickering in windows


    def remove_by_title(self, title):
        tool = self.get(title)
        if tool:
            self.remove(tool)


    def remove(self, tool):
        for i in range(len(self.tools)):
            if self.tools[i] is tool:
                self.wxobj.DeleteTool(tool.id)
                del self.tools[i]

                if self.separators.has_key(tool.title):
                    del self.separators[tool.title]

                if isinstance(tool, _ToolbarItem):
                    ctrl = controller()
                    callback = ctrl.menu_id_callbacks[tool.id]
                    del ctrl.menu_id_callbacks[tool.id]
                    del ctrl.callback_tools[callback]

                if wx.Platform == '__WXMSW__':
                    if isinstance(tool, _ToolbarControl) and tool.control:
                        tool.control.Destroy()

                self._check_separators()
                self.realize()
                return

    __realize_call_count = 0
    if wx.Platform == '__WXMAC__':
        __realized_called = False

    def __realize(self):
        self.__realize_call_count -= 1
        if self.__realize_call_count <= 0:
            self.__realize_call_count = 0
            try:
                if wx.Platform == '__WXMAC__':
                    if self.__realized_called:
                        #mac accepts only one Realize call per tool bar 
                        #==> to change a toolbar you have to create a new one
                        self._check_separators(True)

                    self.__realized_called = True

                self.wxobj.Realize()
            except wx.PyDeadObjectError:
                pass


    def realize(self):
        self.__realize_call_count += 1
        wx.FutureCall(100, self.__realize)


    def get(self, title):
        for t in self.tools:
            if t and t.title == title:
                return t

        return None


    def _check_separators(self, rebuild_tool_bar=False):
        NONE = 0
        WAS_SEP = 1
        NEED_SEP = 2

        mode = WAS_SEP
        sep = None
        index = -1
        new_tools = []

        for t in self.tools:
            index += 1

            if t is None:
                if mode == NEED_SEP:
                    mode = NONE
                    new_tools.append(t)
                elif mode == WAS_SEP:
                    rebuild_tool_bar = True
                else:
                    mode = WAS_SEP
                    sep = index
                continue

            if mode == NEED_SEP:
                self.wxobj.InsertSeparator(index)
                new_tools.append(None)
                index += 1
                mode = WAS_SEP

            s = self.separators.get(t.title)
            if not s:
                if mode == WAS_SEP:
                    if sep:
                        rebuild_tool_bar = True

                    mode = NONE
                    sep = None

                if s == False:
                    mode = NEED_SEP
            elif s:
                if mode != WAS_SEP:
                    self.wxobj.InsertSeparator(index)
                    index += 1

                new_tools.append(None)
                mode = NONE
                sep = None

            new_tools.append(t)

        self.tools = new_tools

        if mode == WAS_SEP:
            rebuild_tool_bar = True

        if rebuild_tool_bar:
            # wxpython patch: wxPython cannot delete separators
            old_wxobj = self.wxobj
            bitmap_size = self.wxobj.GetToolBitmapSize()
            ctrl = controller()
            ctrl.freeze()
            self.wxobj = wx.ToolBar(ctrl.frame, -1)
            self.wxobj.Hide()
            self.wxobj.SetToolBitmapSize(bitmap_size)
            for t in self.tools:
                if t:
                    t._insert_at_toolbar(self.wxobj)
                    t.enable()
                else:
                    self.wxobj.AddSeparator()
            self.wxobj.Show()
            ctrl.thaw()
            ctrl.frame.SetToolBar(self.wxobj)

            if wx.Platform in ('__WXMSW__', '__WXMAC__'): 
                old_wxobj.Destroy()


class _ToolbarControl:
    def __init__(self, parent, id_, title, owner, factory, *args):
        self.parent = parent
        self.id = id_
        self.title = title
        self.owner = _tagged_owner(owner)
        self.factory = factory
        self.args = args


    def remove(self):
        self.parent.remove(self)


    def _insert_at_toolbar(self, wxobj, pos=-1):
        self.control = self.factory(wxobj, self.id)
        if pos <= -1:
            wxobj.AddControl(self.control)
        else:
            wxobj.InsertControl(pos, self.control)


class _ToolbarItem:
    def __init__(self, parent, id_, title, owner,
                 bmp1, bmp2, kind, short, long):
        self.parent = parent
        self.id = id_
        self.title = title
        self.owner = _tagged_owner(owner)
        self.bmp1 = bmp1
        self.bmp2 = bmp2
        self.kind = kind
        self.short = short
        self.long = long


    def remove(self):
        self.parent.remove(self)


    def enable(self, enable=True):
        try:
            self.parent.wxobj.EnableTool(self.id, enable)
        except wx.PyDeadObjectError:
            pass


    def toggle(self, toggle=True):
        try:
            self.parent.wxobj.ToggleTool(self.id, toggle)
        except wx.PyDeadObjectError:
            pass

    def is_pressed(self):
        try:
            return self.parent.wxobj.GetToolState(self.id)
        except wx.PyDeadObjectError:
            return False


    def _insert_at_toolbar(self, wxobj, pos=-1):
        if pos <= -1:
           wxobj.AddLabelTool(self.id, self.title,
                               self.bmp1, self.bmp2,
                               self.kind, self.short, self.long)
        else:
           wxobj.InsertLabelTool(pos, self.id, self.title,
                                 self.bmp1, self.bmp2,
                                 self.kind, self.short, self.long) 


class _MenuManager:
    TEMP_OWNER = object()

    def __init__(self):
        self.callback_menus = {}
        self.callback_tools = {}
        self.menu_id_callbacks = {}
        self.popup_menus = []
        self.top_menu = None
        self.toolbar = None
        self.macro = None


    def get_top_menu(self):
        if self.top_menu is None:
            wxobj = wx.MenuBar()
            self.frame.SetMenuBar(wxobj)
            self.top_menu = _TopMenu(wxobj)

        return self.top_menu


    def make_menu(self, title=""):
        self.remove_temp_menus()
        wxmenu = wx.Menu(title)
        id_ = wx.NewId()
        menu = _Menu(None, wxmenu, "", id_, -1)
        self.popup_menus.append(menu)
        return menu


    def get_menu(self, callback):
        return self.callback_menus.get(callback)


    def get_menu_by_id(self, id):
        return self.get_menu(self.menu_id_callbacks[id])


    def remove_temp_menus(self):
        try:
            self.top_menu.remove_by_owner(self.TEMP_OWNER)
        except AttributeError: pass

        for m in self.popup_menus:
            m.remove_by_owner(self.TEMP_OWNER)

        self.popup_menus = []


    def remove_menu_items(self, owner):
        self.remove_temp_menus()

        try:
            self.top_menu.remove_by_owner(owner)
        except AttributeError: pass

        try:
            self.toolbar.remove_by_owner(owner)
        except AttributeError: pass


    def _on_menu_select_(self, event):
        action = self.menu_id_callbacks.get(event.GetId(), None)
        if action:
            macro = self.macro
            if macro:
                def call_action(id):
                    action = self.menu_id_callbacks.get(id, None)
                    action()
                macro.add_command(call_action, event.GetId())

            action()
            if macro and macro != self.macro:
                macro.pop()


    def get_toolbar(self):
        if not self.toolbar:
            wxobj = wx.ToolBar(self.frame, -1)
            self.frame.SetToolBar(wxobj)
            self.toolbar = _Toolbar(wxobj, self.frame)

        return self.toolbar



class ResourceManager:
    resource_path = [ ]
    loaded_bitmaps = None
    empty = None
        
    def _init_(cls):
        res_dir = None
        try:
            if sys.frozen:
                path = os.path.abspath(os.path.dirname(sys.argv[0]))
                path = os.path.join(path, "resources", "metapie")
            else:
                raise AttributeError()
        except AttributeError:
            import metapie
            path = os.path.split(metapie.__file__)[0]
            path = os.path.join(path, "resources")

        path = os.path.normcase(path)
        cls.resource_path.append(path)

    _init_ = classmethod(_init_)


    def get_bitmap_path(cls, name):
        extensions = (".png", ".gif")
        if name.find(".") > 0:
            extensions = ("",)
            
        for r in cls.resource_path:
            for e in extensions:
                path = os.path.join(r, "images", name + e)
                if os.path.exists(path):
                    return path

        return None

    get_bitmap_path = classmethod(get_bitmap_path)
    

    def load_bitmap(cls, name, size=""):
        if name is None:
            cls.empty = cls.empty or wx.EmptyBitmap(0, 0)
            return cls.empty

        if not isinstance(name, str):
            return name
       
        if cls.loaded_bitmaps is None:
            wx.InitAllImageHandlers()
            cls.loaded_bitmaps = {}

        bmp = cls.loaded_bitmaps.get(name + str(size))
        if bmp is not None:
            return bmp

        path = cls.get_bitmap_path(name)
        if path is None:
            raise ValueError('could not find bitmap: "%s"' % name,
                             cls.resource_path)

        img = wx.Image(path, wx.BITMAP_TYPE_ANY)
        
        if size: img.Rescale(*size)
            
        bmp = img.ConvertToBitmap()
        cls.loaded_bitmaps[name + str(size)] = bmp
        return bmp

    load_bitmap = classmethod(load_bitmap)

ResourceManager._init_()    


class _ModelManager:
    def __init__(self):
        self.id_to_model = {}


    def add_model(self, new_model, activate=True):
        insert_after_model_id = None
        largest_index = 0

        for id_, m in self.id_to_model.iteritems():
            result = m.accept_sibling(new_model)
            if not result:
                result = _SIBLING_COMPLEMENT[new_model.accept_sibling(m)]

            if not result:
                self.remove_model(m)
                continue
                
            if result == navigator.SIBLING_BELOW:
                index = self.navigator.index_of(id_)
                if index >= largest_index:
                    insert_after_model_id = id_
                    largest_index = index

        if insert_after_model_id:
            pos = self.navigator.index_of(insert_after_model_id) + 1
        else:
            pos = 0

        bitmap = ResourceManager.load_bitmap(navigator.get_bitmap(new_model))
        model_id = wx.NewId()
        self.navigator.insert_title(navigator.get_title(new_model),
                                    model_id,
                                    bitmap,
                                    pos=pos,
                                    active=activate)
                              
        self.adjust_navigator()
        self.id_to_model[model_id] = new_model        
        new_model.register()
        

    def remove_model(self, model):
        id_ = self.id_of_model(model)
        self.navigator.remove(id_)
        self.remove_menu_items(model)
        self.destroy_views_of_model(model)
        del self.id_to_model[id_]


    def id_of_model(self, model):
        for id_, m in self.id_to_model.iteritems():
            if m is model: return id_

        return None

    def get_model(self, title):
        id_ = self.navigator.id_of(title)
        return self.id_to_model.get(id_)


    def show_model_views(self, model):
        index = self.navigator.index_of(self.id_of_model(model))
        self.navigator.activate(index)


class _ViewManager:
    def __init__(self):
        self.registered_views = {}
        self.__last_view_count = -1
        self.view_menu_owner = object()

        top = self.get_top_menu()
        self.view_menu = view_menu = top.make_menu(_("&Views"), 1000)

        def mi(*args, **kwargs):
            return view_menu.make_item(self, *args, **kwargs)

        self.destroy_menu = mi(_("&Destroy\tF4"), self.destroy_active_view,
                               "window_suppressed16",
                               pos=1000)
        self.maximize_menu = mi(_("&Maximize\tF6"), self.maximize_active_view,
                                "window_fullscreen16",
                                pos=1010)
        self.increase_menu = mi(_("&Increase\tF7"), self.increase_active_view,
                                pos=1020)
        self.decrease_menu = mi(_("&Reduce\tF8"), self.decrease_active_view,
                                pos=1030)

        view_menu.make_separator(_("Destroy"), True)
        self._refresh_menu()
        self.frame.Bind(wx.EVT_IDLE, self._on_idle_)


    def init_view_manager(self):
        self.hidden_parent = wx.Window(self.frame, -1)
        self.hidden_parent.Hide()


    def find_view_of(self, window):
        while window:
            if isinstance(window, navigator.View):
                return window

            window = window.GetParent()

        return None


    def get_focused_view(self):
        return self.find_view_of(wx.Window_FindFocus())
    
    __last_focused_view = None
    def _on_idle_(self, event):
        view = self.get_focused_view()
        if view != self.__last_focused_view:
            if view:
                self.set_subtitle(view._nav_title)
            else:
                self.set_subtitle("")
            self.__last_focused_view = view

        self._refresh_menu()
        event.Skip()


    def destroy_active_view(self):
        view = self.get_focused_view()
        if view:
            self.destroy_view(view)


    def increase_active_view(self):
        view = self.get_focused_view()
        if view: self.stacker.resize(view, 10)


    def decrease_active_view(self):
        view = self.get_focused_view()
        if view: self.stacker.resize(view, -10)


    def maximize_active_view(self):
        focus_view = self.get_focused_view()
        views = self.stacker.views
        i_range = range(len(views))
        i_range.reverse()
        for i in i_range:
            v, c = views[i]
            if v is not focus_view:
                self.stacker.remove(i)

        self.stacker.adjust_layout()


    def _refresh_menu(self, force=False):
        view_count = len(self.stacker.views)
        if self.__last_view_count == view_count and not force:
            return

        self.__last_view_count = view_count
        enable = view_count > 1
        self.destroy_menu.enable(enable)
        self.increase_menu.enable(enable)
        self.decrease_menu.enable(enable)
        self.maximize_menu.enable(enable)

        self.remove_menu_items(self.view_menu_owner)

        top = self.get_top_menu()
        view_menu = self.view_menu

        i = 0
        for v, c in self.stacker.views:
            try:
                model = v._nav_model()
                title = v._nav_title

                view_menu.make_item(self.view_menu_owner,
                                    navigator.get_title(model) + "/" + title,
                                    v.SetFocus,
                                    pos=i)
                i += 1
            except: pass
        

    def register_view(self, model, title, factory_args, bitmap=None, pos=-1):
        viewid = self.navigator.id_of(navigator.get_title(model), title)
        if not viewid:
            viewid = wx.NewId()
            bitmap = ResourceManager.load_bitmap(bitmap)
            self.navigator.insert_content(title,
                                          viewid,
                                          parent_id=self.id_of_model(model),
                                          bitmap=bitmap,
                                          pos=pos,
                                          active=False)
            self.adjust_navigator()

        self.registered_views[viewid] = (model, title, factory_args)
        return viewid


    def unregister_view(self, viewid):
        if not self.registered_views.has_key(viewid):
            return

        self.navigator.remove(viewid)
        self.stacker.remove(self.get_active_view_by_id(viewid))
        del self.registered_views[viewid]
        self.stacker.adjust_layout()
        self._refresh_menu(True)


    def get_active_view_by_id(self, viewid):
        for v, c in self.stacker.views:
            if v.GetId() == viewid:
                return v

        return None


    def get_all_views(self):
        return map(lambda v: v[0], self.stacker.views)


    def get_active_view_pos(self, view):
        return self.stacker.index_of(view)
    

    def create_view(self, viewid):
        view = self.get_active_view_by_id(viewid)
        if view:
            return view

        attribs = self.registered_views.get(viewid)
        if not attribs:
            return None

        (model, title, factory_args) = attribs
        return self.produce_view(model, title, factory_args, viewid)


    def produce_view(self, model, title, factory_args, viewid=-1):
        if viewid < 0: viewid = wx.NewId()
        if isinstance(factory_args, (tuple, list)):
            factory = factory_args[0]
            args = factory_args[1:]
            new_view = factory(self.hidden_parent, *args)
        else:
            new_view = factory_args(self.hidden_parent)

        new_view.Hide()
        new_view.SetId(viewid)
        new_view._nav_title = title
        new_view._nav_model = weakref.ref(model)
        self._build_layout(new_view)
        new_view.become_visible()
        new_view.Show()
        self._refresh_menu(True)
        return new_view


    def destroy_view(self, view):
        self.stacker.remove(view)
        self.stacker.adjust_layout()
        wx.CallAfter(collect_garbage)

        
    def destroy_views_of_model(self, model):
        views = self.stacker.views
        i_range = range(len(views))
        i_range.reverse()
        for i in i_range:
            v, c = views[i]
            try:
                if v._nav_model() is model:
                    self.stacker.remove(i)
            except:
                pass

        self.stacker.adjust_layout()
        self._refresh_menu(True)


    def get_views_of_model(self, model):
        result = []
        for v, c in self.stacker.views:
            if v._nav_model() is model:
                result.append(v)

        return result
        

    def get_view(self, model_title, view_title):
        viewid = self.navigator.id_of(model_title, view_title)
        return viewid and self.create_view(viewid)
        

    def get_active_view(self, model_title, view_title):
        viewid = self.navigator.id_of(model_title, view_title)
        return viewid and self.get_active_view_by_id(viewid)


    def _build_layout(self, new_view):
        views = self.stacker.views
        i_range = range(len(views))
        i_range.reverse()
        remove_last_view = False
        to_insert = 0

        for i in i_range:
            try:
                view, c = views[i]
                result = view.accept_sibling(new_view)
                if not result:
                    result = _SIBLING_COMPLEMENT[new_view.accept_sibling(view)]

                if not result:
                    if remove_last_view:
                        self.stacker.remove(i + 1)
                        remove_last_view = False

                    remove_last_view = True
                    continue

                if result == navigator.SIBLING_ABOVE:
                    if remove_last_view:
                        self.stacker.remove(i + 1)
                        remove_last_view = False

                    continue

                if result == navigator.SIBLING_BELOW:
                    to_insert = i + 1
                    break
            except:
                pass
            
        if remove_last_view:
            self.stacker.replace(to_insert, new_view)
        else:
            self.stacker.insert(to_insert, new_view,
                                navigator.get_height(new_view))

        i_range = range(0, to_insert - 1)
        i_range.reverse()
        for i in i_range:
            view, c = views[i]
            result = view.accept_sibling(new_view)
            if not result:
                result = _SIBLING_COMPLEMENT[new_view.accept_sibling(view)]

            if not result:
                self.stacker.remove(i)

        self.stacker.adjust_layout()



class _MainFrame(wx.Frame):
    def __init__(self, title):
        wx.Frame.__init__(self, None, -1, title,
                          pos=(10,10), size=(1024, 768),
                          style=wx.NO_FULL_REPAINT_ON_RESIZE | \
                          wx.DEFAULT_FRAME_STYLE)


    def Destroy(self):
        #destroy all views before they can cause any harm
        #because the can refer to the frame decoration, like statusbar,
        #(and in Destroy can be any clean up code)
        
        for v in controller().get_all_views():
            v.Destroy()

        controller().toolbar = None
        wx.Frame.Destroy(self)

    

class MetaApp(wx.App, _MenuManager,
              _ModelManager, _ViewManager):
    instance = None

    def __init__(self, *args, **kwargs):
        MetaApp.instance = self
        self.__title = ""
        self.__subtitle = ""
        self.frame = None
        
        _MenuManager.__init__(self)
        _ModelManager.__init__(self)
        wx.App.__init__(self, *args, **kwargs)
        _ViewManager.__init__(self)

        self.Bind(wx.EVT_MENU, self._on_menu_select_)
        self.Bind(wx.EVT_BUTTON, self._on_menu_button_)
        self.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self._on_right_click_)
        self.Bind(wx.EVT_WINDOW_DESTROY, self._on_destroy_)
        

    __last_size = None
    def _on_size_(self, event):
        if event.GetSize() != self.__last_size:
            self.__last_size = event.GetSize()
            wx.CallAfter(self.layouter.LayoutWindow, self.frame, self.stacker)
            return True
        
        return False


    def _on_sash_drag_(self, event):
        size = event.GetDragRect().GetSize()
        if event.GetDragStatus() == wx.SASH_STATUS_OUT_OF_RANGE:
            size.SetWidth(self.stacker.sash_height)

        event.GetEventObject().SetDefaultSize(size)
        self.layouter.LayoutWindow(self.frame, self.stacker)
        self.stacker.refresh_focus()
        

    def _on_right_click_(self, event):
        model = self.id_to_model.get(event.GetId())
        if model:
            method = getattr(model, "_right_click_", None)
            if method: method(event, None)
            return

        attribs = self.registered_views.get(event.GetId())
        if attribs:
            method = getattr(attribs[0], "_right_click_", None)
            if method: method(event, attribs[1])
        

    def _on_menu_button_(self, event):
        if self.id_to_model.has_key(event.GetId()):
            self.adjust_navigator()
            event.Skip()
            return

        view = self.create_view(event.GetId())
        if view:
            view.SetFocus()


    def _on_destroy_(self, event):
        if getattr(event.GetEventObject(), "_metapie_has_menu", False):
            self.remove_menu_items(event.GetEventObject())


    def get_title(self):
        return self.__title


    def set_title(self, title):
        self.__title = title
        self.refresh_title()


    def get_subtitle(self):
        return self.__subtitle


    def set_subtitle(self, subtitle):
        self.__subtitle = subtitle
        self.refresh_title()

    title = property(get_title, set_title)
    subtitle = property(get_subtitle, set_subtitle)


    def OnInit(self):
        self.frame = _MainFrame(self.__build_title())
        self._create_children()

        def exit():
            self.frame.Destroy()

        self.init_view_manager()

        top = self.get_top_menu()
        file_menu = top.make_menu(_("&File"), pos=0)
        item = file_menu.make_item(self, _("&Exit"), exit, "exit16", pos=sys.maxint, id=wx.ID_EXIT)
        wx.App.SetMacExitMenuItemId(item.id)
        file_menu.make_separator(_("&Exit"), True)

        self.SetTopWindow(self.frame)
        self.frame.Show()

        wx.CallAfter(self.layouter.LayoutWindow, self.frame, self.stacker)
        return True


    def refresh_title(self):
        title = self.__build_title()
        if self.frame:
            self.frame.SetTitle(title)


    def adjust_navigator(self):
        navigator = self.navigator
        width = navigator.GetSizeTuple()[0]
        best_width = navigator.get_best_width()
        best_width = max(width, best_width)

        if width < best_width or True:
            sash = navigator.GetParent()
            sash.SetSize((best_width - 1, -1))
            sash.SetDefaultSize((best_width + self.stacker.sash_height, -1))
            self.layouter.LayoutWindow(self.frame, self.stacker)


    def __build_title(self):
        if not self.subtitle:
            return self.title

        return self.title + " - " + self.subtitle


    def start_recording(self):
        self.macro = Macro()
        return self.macro


    def stop_recording(self):
        macro = self.macro
        self.macro = None
        return macro


    def freeze(self):
        self.frame.Freeze()

    def thaw(self):
        self.frame.Thaw()


    def _create_children(self):
        sash = wx.SashLayoutWindow(self.frame, wx.NewId(),
                                   style=wx.NO_BORDER|wx.SW_3D)
        sash.SetDefaultBorderSize(Stacker.sash_height)
        sash.SetDefaultSize((30, -1))
        sash.SetOrientation(wx.LAYOUT_VERTICAL)
        sash.SetAlignment(wx.LAYOUT_LEFT)
        sash.SetSashVisible(wx.SASH_RIGHT, True)
        sash.SetSizeHints(Stacker.sash_height, -1)

        self.navigator = MenuPanel(sash)
        self.stacker = Stacker(self.frame)
        self.layouter = wx.LayoutAlgorithm()

        self.status_bar = wx.StatusBar(self.frame)
        self.frame.SetStatusBar(self.status_bar)

        wx.EVT_SASH_DRAGGED(self, sash.GetId(), self._on_sash_drag_)
        wx.EVT_SIZE(self.frame, self._on_size_)

    

def controller():
    return MetaApp.instance
