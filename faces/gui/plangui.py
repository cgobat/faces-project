#! /usr/bin/python
#@+leo-ver=4
#@+node:@file gui/plangui.py
#@@first
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
import sys

try:
    if sys.frozen:
        import encodings
except AttributeError:
    import wxversion
    wxversion.select(['2.6', '2.8'])
    #wxPython 2.4 is not support since version 0.7.0

import wx.html
import os
import time
import locale

try:
    #threading can cause problems when reloaded,
    #causing nasty error messages at exit if generator module is used
    #importing it here will avoid a reload when refreshing a project
    import threading
except:
    pass


try:
    import gc
    collect_garbage = gc.collect
    #gc.set_debug(gc.DEBUG_LEAK)
except:
    def collect_garbage(): pass

from metapie.gui import controller, MetaApp, ResourceManager    
import faces.plocale
import os.path
import re
import faces as _faces

_faces.set_default_chart_font_size(8)
_faces.gui_controller = controller

import faces.observer as _observer
import faces.generator # see threading
from faces.gui.editor import PlanEditor, PlanEditorProxy
import faces.gui.repview
import faces.gui.chartview
import faces.gui.graphview
import faces.gui.utils as gutils
import metapie.navigator as navigator
import metapie.gui.session as session
import inspect
import linecache
import stat
import new
import types
import traceback
import warnings
import faces.utils
import ConfigParser
from wx.lib.fancytext import RenderToBitmap
#@-node:<< Imports >>
#@nl
#@<< Setting Globals >>
#@+node:<< Setting Globals >>
_is_source_ = True

if not wx.USE_UNICODE:
    def null_gettext(): return lambda x: x
    faces.plocale.get_gettext = null_gettext

_ = faces.plocale.get_gettext()

current_directory = ""
_warning_registry = { }
_installation_path = faces.utils.get_installation_path()
_resource_path = faces.utils.get_resource_path()
_template_path = os.path.join(_resource_path, "templates")
#@nonl
#@-node:<< Setting Globals >>
#@nl

#@+others
#@+node:Tools
#@+node:_import_
def _import_(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod
#@-node:_import_
#@+node:title_of_path
def title_of_path(path):
    return os.path.split(path)[1]
#@-node:title_of_path
#@+node:is_project_file
def is_project_file(path, main_path=None):
    path = os.path.abspath(path)
    path = os.path.normcase(path)

    if path == main_path: return True
    if not os.access(path, os.W_OK): return False

    if current_directory and path.startswith(current_directory):
        return True

    return False
#@-node:is_project_file
#@+node:getsourcefile
def getsourcefile(obj):
    try:
        if isinstance(obj, str):
            obj = sys.modules.get(obj)

        return inspect.getabsfile(obj)
    except:
        pass

    return ""
#@-node:getsourcefile
#@+node:_generate_menu_wrapper
def _generate_menu_wrapper(executer, obj):
    msg = wx.MessageBox
    frame = controller().GetTopWindow()

    to_execute = getattr(obj, "faces_execute", obj)

    if hasattr(obj, "faces_openfile"):
        fname = obj.faces_openfile
        def wrapper():
            dlg = wx.FileDialog(frame, _("Choose a file"),
                                os.path.split(fname)[0],
                                os.path.split(fname)[1],
                                _("All Files|*"), wx.OPEN)
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                if executer.save_execute(to_execute, path):
                    obj.faces_openfile = path
                    msg(_("%s('%s') was executed successfully")\
                        % (obj.__name__, path),
                        _("Success"), style=wx.ICON_INFORMATION|wx.OK)
                collect_garbage()
            dlg.Destroy()

    elif hasattr(obj, "faces_savefile"):
        fname = obj.faces_savefile
        def wrapper():
            dlg = wx.FileDialog(frame, _("Choose a filename"),
                                os.path.split(fname)[0],
                                os.path.split(fname)[1],
                                _("All Files|*"), wx.SAVE)
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                if executer.save_execute(to_execute, path):
                    obj.faces_savefile = path
                    msg(_("%s('%s') was executed successfully")\
                        % (obj.__name__, path),
                        _("Success"), style=wx.ICON_INFORMATION|wx.OK)
                collect_garbage()
            dlg.Destroy()

    elif hasattr(obj, "faces_savedir"):
        dname = obj.faces_savedir

        def wrapper():
            dlg = wx.DirDialog(frame, _("Select Directory to save to"), dname)
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                if executer.save_execute(to_execute, path):
                    obj.faces_savedir = path
                    msg(_("%s('%s') was executed successfully")\
                        % (obj.__name__, path),
                        _("Success"), style=wx.ICON_INFORMATION|wx.OK)
                collect_garbage()
            dlg.Destroy()
    else:
        def wrapper():
            if executer.save_execute(to_execute):
                msg(_("%s() was executed successfully") % obj.__name__,
                    _("Success"), style=wx.ICON_INFORMATION|wx.OK)

    return wrapper
#@-node:_generate_menu_wrapper
#@-node:Tools
#@+node:class PlanBuffer
class PlanBuffer(navigator.Model):
    #@	@+others
    #@+node:Construct and Destroy Methods
    #@+node:__init__
    def __init__(self, path, is_main_buffer=False):
        self.text = ""
        path = os.path.abspath(path)
        path = os.path.normcase(path)
        self.path = path
        self.editor_id = None
        self.mod_time = 0
        self.is_modified = None
        self.resources = {}
        self.calendars = {}
        self.editor = PlanEditor(self)
        self.is_main_buffer = is_main_buffer
        self.active_views = {}
        self.consider_backup = True

    #@-node:__init__
    #@+node:__del__
    def __del__(self):
        self.close()
    #@-node:__del__
    #@+node:close
    def close(self):
        #try:
        #    self.editor.Destroy()
        #    self.editor = None
        #except AttributeError: pass
        self.remove_backup_file()
    #@-node:close
    #@-node:Construct and Destroy Methods
    #@+node:Metapie Methods
    #@+node:_right_click_
    def _right_click_(self, event, view):
        if not view: return

        module = controller().session.get_module(self.path)
        obj = getattr(module, view, None)
        if not obj: return

        def find_in_source(): self.find_in_source(obj)
        ctrl = controller()
        menu = ctrl.make_menu()
        menu.make_item(self, _("Find in Source"), find_in_source, "findsource16")

        button = event.GetButtonObj()
        pos = button.ScreenToClient(wx.GetMousePosition())
        button.PopupMenu(menu.wxobj, pos)
    #@-node:_right_click_
    #@+node:register
    def register(self):
        ctrl = controller()
        ctrl.freeze()

        factory = lambda parent: PlanEditorProxy(self, parent)
        title = title_of_path(self.path)
        self.editor_id = ctrl.register_view(self, title, factory, "edit")
        ctrl.thaw()
    #@-node:register
    #@+node:accept_sibling
    def accept_sibling(self, sibling):
        if isinstance(sibling, PlanBuffer):
            if str(sibling) < str(sibling):
                return navigator.SIBLING_ABOVE
            else:
                return navigator.SIBLING_BELOW

        return False
    #@-node:accept_sibling
    #@-node:Metapie Methods
    #@+node:Mediator Methods
    #@+node:goto_source
    def goto_source(self, line):
        self.get_edit_view(True).goto_line(line)
    #@-node:goto_source
    #@+node:find_in_source
    def find_in_source(self, obj):
        self.get_edit_view(True).find_in_source(obj)
    #@-node:find_in_source
    #@+node:show_object
    def show_object(self, caller, fobj, attrib=None):
        model = self._find_model(fobj)
        model._show_object(caller, fobj, attrib)

    __show_object_called = False
    def _show_object(self, caller, fobj, attrib=None):
        if self.__show_object_called: return
        self.__show_object_called = True

        try:
            edit_view = None
            views = controller().get_all_views()
            for v in views:
                if v is caller: continue

                if isinstance(v, PlanEditorProxy):
                    edit_view = v
                    continue

                try:
                    v.show_object(fobj, attrib, caller)
                except AttributeError:
                    pass

            if edit_view:
                if edit_view.model() is not self:
                    edit_view = self.get_edit_view(True)

                edit_view.show_object(fobj, attrib, caller)

        finally:
            self.__show_object_called = False

    def _find_model(self, fobj):
        """
        find the model of a task object
        """
        try:
            path = inspect.getabsfile(getattr(fobj, "_function", None))
        except TypeError:
            try:
                path = inspect.getabsfile(fobj)
            except TypeError:
                return self

        path = os.path.normcase(path)
        if path != self.path:
            for m in controller().get_planbuffers():
                if m.path == path:
                    return m

        return self        
    #@nonl
    #@-node:show_object
    #@+node:get_edit_view
    def get_edit_view(self, create_view=True):
        ctrl = controller()
        if create_view:
            view = ctrl.create_view(self.editor_id)
        else:
            view = ctrl.get_active_view_by_id(self.editor_id)

        return view
    #@-node:get_edit_view
    #@-node:Mediator Methods
    #@+node:Backup Methods
    #@+node:get_backup_file
    def get_backup_file(self):
        if self.path.startswith(_template_path): return ""
        ndir, nbase = os.path.split(self.path)
        return os.path.join(ndir, "#%s#" % nbase)
    #@-node:get_backup_file
    #@+node:remove_backup_file
    def remove_backup_file(self):
        try:
            os.unlink(self.get_backup_file())
            return True
        except OSError:
            pass
        return False
    #@-node:remove_backup_file
    #@+node:save_backup
    def save_backup(self):
        view = self.get_edit_view(False)
        if not view: return
        path = self.get_backup_file()
        if not path: return
        view.sync_text()
        f = file(path, "wb")
        f.write(self.text)
        f.close()
    #@-node:save_backup
    #@-node:Backup Methods
    #@+node:Buffer Methods
    #@+node:__deferred_save
    def __deferred_save(self):
        self.save_buffer()
        linecache.checkcache()        
        controller().session.execute_plan()
    #@-node:__deferred_save
    #@+node:refresh
    def refresh(self):
        #@    << find path and consider backups >>
        #@+node:<< find path and consider backups >>
        path = self.get_backup_file()
        if self.consider_backup and os.access(path, os.F_OK):
            result = wx.MessageBox(_('A backup copy of "%s" exists.\n'
                                     'Should I use it?') % self.path,
                                   _("Backup exists"),
                                   style=wx.YES_NO|wx.ICON_QUESTION)
            if result == wx.NO:
                path = self.path
        else:
            path = self.path

        #@-node:<< find path and consider backups >>
        #@nl

        mod_time = os.stat(path)[stat.ST_MTIME]
        if self.mod_time < mod_time:
            f = file(path, "r")
            self.text = f.read()\
                        .replace("\r\n", "\n")\
                        .replace("\r", "\n")\
                        .replace("\t", " " * 8)
            f.close()
            #@        << fix efficiency misspelling >>
            #@+node:<< fix efficiency misspelling >>
            if self.text.find("efficency") >= 0:
                answer = wx.MessageBox(_("The file %s has a misspelled efficiency attribute."\
                                         "Sould I correct it?") % path,
                                       _("Misspelling Bug"),
                                       wx.YES_NO|wx.ICON_QUESTION)
                if answer == wx.YES:
                    self.text = self.text.replace("efficency", "efficiency")
            #@nonl
            #@-node:<< fix efficiency misspelling >>
            #@nl

            self.mod_time = mod_time
            if self.is_main_buffer:
                _faces.set_chart_encoding(self.get_encoding())

            refresh_text = True
        else:
            refresh_text = False

        self.editor.refresh(refresh_text)
        if self.consider_backup and self.remove_backup_file(): self.save_buffer()
        self.consider_backup = False
    #@nonl
    #@-node:refresh
    #@+node:get_encoding
    def get_encoding(self):
        line_end = 0
        for i in range(2):
            line_end = self.text.find("\n", line_end + 1)

        mo = re.search(r"coding[:=]\s*([-\w.]+)", self.text[:line_end])
        if mo: return mo.group(1)
        return "ascii"
    #@-node:get_encoding
    #@+node:save
    def save(self):
        if self.path.startswith(_template_path): return self.menu_save_as()

        self.set_menus()
        ctrl = controller()
        ctrl.session.check_for_correction()
        ctrl.frame.SetCursor(wx.HOURGLASS_CURSOR)
        ctrl.status_bar.SetStatusText(_("Saving..."), 0)
        wx.CallAfter(self.__deferred_save)
        wx.CallAfter(ctrl.frame.SetCursor, wx.NullCursor)
        wx.CallAfter(ctrl.status_bar.SetStatusText, "", 0)
        wx.CallAfter(self.set_focus, True)
    #@-node:save
    #@+node:save_buffer
    def save_buffer(self):
        self.editor.sync_text(True)
        f = file(self.path, "wb")
        f.write(self.text)
        f.close()
        self.remove_backup_file()
        mod_time = os.stat(self.path)[stat.ST_MTIME]
        self.mod_time = mod_time

    #@-node:save_buffer
    #@+node:modified
    def modified(self, is_modified=True):
        if self.is_modified != is_modified:
            self.is_modified = is_modified
            self.set_menus()
    #@-node:modified
    #@-node:Buffer Methods
    #@+node:Misc Methods
    #@+node:__str__
    def __str__(self):
        return title_of_path(self.path)
    #@-node:__str__
    #@+node:menu_save_as
    def menu_save_as(self):
        directory = current_directory
        if not directory or directory.startswith(_template_path):
            directory = os.getcwd()

        dlg = wx.FileDialog(controller().GetTopWindow(),
                            _("Choose a filename"),
                            directory,
                            "",
                            _("Faces Files (*.py)|*.py"),
                            wx.SAVE|wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            try:
                str(dlg.GetPath())
            except UnicodeEncodeError:
                wx.MessageBox(_("Filenames may only contain ascii characters."),
                              _("Error"), style=wx.ICON_ERROR|wx.OK)
            else:
                root, ext = os.path.splitext(dlg.GetPath())
                if not root: return
                self.path = root + ".py"
                self.path = os.path.abspath(self.path)
                self.path = os.path.normcase(self.path)

                view = self.get_edit_view(False)
                if view: view.sync_text()

                ctrl = controller()
                ctrl.remove_model(self)
                ctrl.add_model(self)
                ctrl.session.add_recent_file(self.path)
                self.set_menus()
                self.save()

        dlg.Destroy()
    #@-node:menu_save_as
    #@+node:set_focus
    def set_focus(self, create_view=False):
        view = self.get_edit_view(create_view)
        if view: view.SetFocus()
    #@-node:set_focus
    #@+node:set_menus
    def set_menus(self):
        ctrl = controller()

        top = ctrl.get_top_menu()
        file_menu = top.make_menu(_("&File"))

        menu = lambda *args, **kw: \
               file_menu.make_item(self, *args, **kw)

        toolbar = ctrl.get_toolbar()
        toolbar.make_tool(self, "save", self.save,
                          "filesave22").enable(bool(self.is_modified))
        toolbar.make_tool(self, "saveas", self.menu_save_as,
                          "filesaveas22").enable(True)

        menu(_("&Save\tCTRL-S"), self.save, "filesave16",
             pos=30).enable(bool(self.is_modified))
        menu(_("&Save as..."), self.menu_save_as, "filesaveas16",
             pos=40).enable(True)
    #@-node:set_menus
    #@+node:set_observer
    def set_observer(self, observer):
        #observer is a directory of all observers of the model
        #the keys consist of a tuple of
        #(observer.__type_name__, observer.__type_image__)
        #the values are a list of tuples of (observer_title, observe_class)

        active_views = self.active_views
        all_observers = reduce(lambda x, y: x + y, observer.values(), [])
        new_views = dict(map(lambda v: (v[0], -1), all_observers))

        # unregister all observers which are not
        # in the plan file anymore
        ctrl = controller()
        for view, id_ in active_views.iteritems():
            if not new_views.has_key(view):
                ctrl.unregister_view(id_)

        self.active_views = new_views
        keys = observer.keys()
        keys.sort()
        pos = 1
        for k in keys:
            v = observer[k]
            factory = _observer.factories.get(k[0])
            if factory:
                pos = self.__set_views(k[0], factory, v, pos)
    #@-node:set_observer
    #@+node:__set_views
    def __set_views(self, name, create_factory, new_views, pos):
        ctrl = controller()
        active_views = self.active_views

        new_views.sort()
        for t, v in new_views:
            factory = create_factory(t, v, self)
            id_ = ctrl.register_view(self, t, factory, v.__type_image__, pos=pos)
            active_views[t] = id_
            view = ctrl.get_active_view_by_id(id_)
            if view: view.replace_data(v)
            pos += 1

        return pos
    #@-node:__set_views
    #@-node:Misc Methods
    #@-others
#@-node:class PlanBuffer
#@+node:class _Executer
class _Executer:
    #@	<< class _Executer declarations >>
    #@+node:<< class _Executer declarations >>
    menus_owner = "mown"

    #@-node:<< class _Executer declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self):
        self.main_buffer = None
        self.evaluations = {}
        self.loaded_modules = {}
        self.tmp_files_to_remove = []
    #@-node:__init__
    #@+node:get_module
    def get_module(self, path):
        for module in self.loaded_modules.values():
            try:
                if module._faces_source_file == path:
                    return module
            except AttributeError: pass
            except KeyError: pass        

        return None

    #@-node:get_module
    #@+node:remove_modules
    def remove_modules(self):
        for m in self.loaded_modules.keys():
            #@        << remove module >>
            #@+node:<< remove module >>
            try:
                module = sys.modules[m]
            except KeyError: continue

            try:
                module.faces_clean_up()
            except AttributeError: pass

            del sys.modules[m]
            #@nonl
            #@-node:<< remove module >>
            #@nl

        self.evaluations.clear()
        self.loaded_modules.clear()

    #@-node:remove_modules
    #@+node:clear_cache
    def clear_cache(self):
        _faces.task.clear_cache()
        for v in _observer.clear_cache_funcs.itervalues(): v()
        for p in self.tmp_files_to_remove:
            try:
                os.unlink(p)
            except OSError:
                pass

        self.tmp_files_to_remove = []
    #@-node:clear_cache
    #@+node:execute_plan
    def execute_plan(self):
        ctrl = controller()
        ctrl.progress_start(_("calculate project"), 8)

        _warning_registry.clear()
        self.clear_logs()
        self.clear_cache()

        ctrl.progress_update(1)
        collect_garbage()

        self.save_execute(self.__execute_module)
        ctrl.freeze()
        try:
            ctrl.progress_update(6)
            self.__refresh_active_buffer_list()
            self.__refresh_view_list()        
        finally:
            ctrl.thaw()

        ctrl.progress_update(7)
        self.remove_empty_logview()

        ctrl.progress_update(8)
        ctrl.progress_end()

        logger = ctrl.get_active_view_by_id(ctrl.session.logger_id)
        if logger:
            focus = logger
        else:
            focus = self.main_buffer.get_edit_view(True)

        focus.SetFocus()
    #@nonl
    #@-node:execute_plan
    #@+node:save_execute
    def save_execute(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SyntaxError, e:
            sys.stderr.write('%s %s File "%s", line %i\n'
                             % (e.__class__.__name__,
                                e.msg, e.filename, e.lineno))
        except Exception, e:
            self.traceback(e, sys.exc_info()[2])

        return None
    #@nonl
    #@-node:save_execute
    #@+node:traceback
    def traceback(self, exc, tb, string_replacement=("<string>", 1)):
        tb = traceback.extract_tb(tb)
        tb.reverse()

        print >> sys.stderr, "%s: %s" % (exc.__class__.__name__, str(exc))
        for t in tb:
            filename, line = t[:2]
            if filename == "<string>":
                filename, line = string_replacement

            if is_project_file(filename, self.main_buffer.path)\
                   or _faces._DEBUGGING:
                print >> sys.stderr, '\tFile "%s", line %i' % (filename, line)
    #@-node:traceback
    #@+node:__refresh_active_buffer_list
    def __refresh_active_buffer_list(self):
        ctrl = controller()

        #@    << get all loaded source files >>
        #@+node:<< get all loaded source files >>
        def get_source_file(module):
            try:
                path = module._faces_source_file
            except AttributeError:
                return ""

            try:
                module._is_source_
                return ""
            except AttributeError:
                pass

            if is_project_file(path, self.main_buffer.path):
                return path

            return ""

        files = filter(bool, map(get_source_file, self.loaded_modules.values()))
        files = dict(map(lambda f: (f, False), files))
        #@nonl
        #@-node:<< get all loaded source files >>
        #@nl
        for m in ctrl.get_planbuffers():
            if m.path in files:
                del files[m.path]
            else:
                #remove obsolete PlanBuffer
                ctrl.remove_model(m)

        #@    << add new plan buffers >>
        #@+node:<< add new plan buffers >>
        for f in files.keys():
            try:
                ctrl.add_model(PlanBuffer(f), False)
            except OSError:
                pass
        #@nonl
        #@-node:<< add new plan buffers >>
        #@nl
    #@-node:__refresh_active_buffer_list
    #@+node:__refresh_view_list
    def __refresh_view_list(self):
        ctrl = controller()
        #@    << init collections >>
        #@+node:<< init collections >>
        resources = {}
        calendars = {}
        observer = {}
        evaluations = {}
        functions = []
        #@nonl
        #@-node:<< init collections >>
        #@nl
        #@    << define is_valid_module >>
        #@+node:<< define is_valid_module >>
        #@+at 
        #@nonl
        # filters out modules which are definitly not faces modules
        #@-at
        #@@code
        buffer_paths = [ m.path for m in ctrl.get_planbuffers() ]

        def is_valid_module(module):
            try:
                if not module._faces_source_file: return False
            except AttributeError:
                return False

            try:
                return not module._is_source_
            except AttributeError:
                return module._faces_source_file in buffer_paths
        #@nonl
        #@-node:<< define is_valid_module >>
        #@nl

        public_attribs = lambda obj: filter(lambda n: n[0] != "_", dir(obj))
        getabsfile = inspect.getabsfile

        for module in filter(is_valid_module, self.loaded_modules.values()):
            #@        << import a possible gui part of the module >>
            #@+node:<< import a possible gui part of the module >>
            try:
                gui_module = _import_(module.faces_gui_module)
                self.loaded_modules[module.faces_gui_module] = gui_module
            except AttributeError: pass
            #@-node:<< import a possible gui part of the module >>
            #@nl
            path = module._faces_source_file

            for k in public_attribs(module):
                v = getattr(module, k)
                #@            << check if k, v is an observer >>
                #@+node:<< check if k, v is an observer >>
                try:
                    if issubclass(v, _observer.Observer) and v.visible:
                        observer.setdefault(path, {})\
                            .setdefault((v.__type_name__,
                                         v.__type_image__), [])\
                            .append((k, v))
                except TypeError: pass
                #@nonl
                #@-node:<< check if k, v is an observer >>
                #@nl
                #@            << check if k, v is an project evaluation >>
                #@+node:<< check if k, v is an project evaluation >>
                if isinstance(v, _faces.task._ProjectBase):
                    evaluations.setdefault(path, {})[k] = v
                    continue

                try:
                    #by convention evaluations are attributes of the top task function
                    if not v.task_func: continue # if v is a task function it has the task_func attribute
                    for n in public_attribs(v):
                        p = getattr(v, n)
                        if isinstance(p, _faces.task._ProjectBase):
                            evaluations.setdefault(path, {})["%s.%s" % (k, n)] = p
                    continue
                except AttributeError: pass


                #@-node:<< check if k, v is an project evaluation >>
                #@nl
                #@            << check if k, v is a resource >>
                #@+node:<< check if k, v is a resource >>
                if isinstance(v, (_faces.Resource,
                                  _faces.resource._MetaResource)):
                    resources.setdefault(path, {})[k] = v
                    continue
                #@nonl
                #@-node:<< check if k, v is a resource >>
                #@nl
                #@            << check if k, v is a calendar >>
                #@+node:<< check if k, v is a calendar >>
                if isinstance(v, _faces.Calendar):
                    calendars.setdefault(path, {})[k] = v
                    continue
                #@nonl
                #@-node:<< check if k, v is a calendar >>
                #@nl
                #@            << check if k, v has menu >>
                #@+node:<< check if k, v has menu >>
                if hasattr(v, "faces_menu"):
                    functions.append(v)
                #@nonl
                #@-node:<< check if k, v has menu >>
                #@nl

        self.evaluations.clear()
        for v in evaluations.itervalues():
            self.evaluations.update(v)

        #@    << assign collections to models >>
        #@+node:<< assign collections to models >>
        for m in ctrl.get_planbuffers():
            m.evaluations = evaluations.get(m.path, {})
            m.resources = resources.get(m.path, {})
            m.calendars = calendars.get(m.path, {})
            m.set_observer(observer.get(m.path, {}))
            m.refresh() # refresh edit view
        #@nonl
        #@-node:<< assign collections to models >>
        #@nl
        #@    << create Toolmenu >>
        #@+node:<< create Toolmenu >>
        top = ctrl.get_top_menu()
        top.remove_by_owner(self.menus_owner)

        for f in functions:
            menu_path = f.faces_menu
            menu_path = menu_path.split("/")

            menu = top.make_menu(_("&Tools"), pos=9980)
            for m in menu_path[:-1]:
                menu = menu.make_menu(m)

            menu.make_item(self.menus_owner, menu_path[-1],
                           _generate_menu_wrapper(self, f),
                           bitmap=getattr(f, "faces_menu_icon", None))
        #@nonl
        #@-node:<< create Toolmenu >>
        #@nl
    #@-node:__refresh_view_list
    #@+node:__execute_module
    def __execute_module(self):
        global current_directory

        path = self.main_buffer.path
        (current_directory, filename) = os.path.split(path)

        #@    << check filename >>
        #@+node:<< check filename >>
        try:
            module_name = str(os.path.splitext(filename)[0])
        except UnicodeEncodeError:
            print >> sys.stderr, \
                  u'filename "%s" contains non ascii chars' % unicode(filename)
            return True
        #@nonl
        #@-node:<< check filename >>
        #@nl
        #@    << remove modules that have to be reloaded >>
        #@+node:<< remove modules that have to be reloaded >>
        for name, module in self.loaded_modules.iteritems():
            try:
                mod_time = os.stat(module._faces_source_file)[stat.ST_MTIME]
                if mod_time <= module._faces_modtime: continue
            except AttributeError: continue
            except OSError: continue

            try:
                module.faces_gui_cleanup()
            except AttributeError: pass

            try:
                del sys.modules[name]
            except KeyError: pass
        #@nonl
        #@-node:<< remove modules that have to be reloaded >>
        #@nl

        actual_modules = {}
        actual_modules.update(sys.modules)

        #@    << init main_module >>
        #@+node:<< init main_module >>
        main_module = new.module(module_name)
        main_module.__file__ = path
        main_module._faces_source_file = path
        main_module.__name__ = "__faces_main__"
        #@-node:<< init main_module >>
        #@nl

        tmp_path = sys.path[0]
        sys.path[0] = current_directory
        try:
            #@        << fetch code and execute it >>
            #@+node:<< fetch code and execute it >>
            text = self.main_buffer.text
            controller().progress_update(2)
            code = compile(text, path, "exec")
            controller().progress_update(3)
            exec code in main_module.__dict__
            controller().progress_update(4)
            #@nonl
            #@-node:<< fetch code and execute it >>
            #@nl
            #@        << find imported modules >>
            #@+node:<< find imported modules >>
            new_modules = filter(lambda m: m[0] not in actual_modules and m[1],\
                                 sys.modules.iteritems())
            new_modules = dict(new_modules)                    

            def set_module_data(module):
                source_file = getsourcefile(module)
                if source_file:
                    module._faces_source_file = source_file
                    try:
                        module._faces_modtime = os.stat(source_file)[stat.ST_MTIME]
                    except OSError:
                        module._faces_modtime = 0

            map(set_module_data, new_modules.values())
            self.loaded_modules.update(new_modules)

            #@-node:<< find imported modules >>
            #@nl

            self.loaded_modules["__faces_main__"] =\
                sys.modules["__faces_main__"] = main_module
        finally:
            sys.path[0] = tmp_path
            controller().progress_update(5)
            if not "__faces_main__" in self.loaded_modules:
                self.loaded_modules["__faces_main__"] =\
                    sys.modules["__faces_main__"] = main_module    

        return True
    #@-node:__execute_module
    #@-others
#@-node:class _Executer
#@+node:class ShellView
class ShellView(session.ShellView):
    #@	@+others
    #@+node:__init__
    def __init__(self, parent, locals=None):
        session.ShellView.__init__(self, parent, locals)
        wx.EVT_SET_FOCUS(self, self._on_get_focus)
    #@-node:__init__
    #@+node:_on_get_focus
    def _on_get_focus(self, event):
        top = controller().get_top_menu()
        edit_menu = top.make_menu(_("&Edit"), pos=100)
        menu = lambda *args, **kw: edit_menu.make_item(self, *args, **kw)
        menu(_("&Undo\tCTRL-Z"), self.Undo, "undo16", pos=100)
        menu(_("&Redo\tCTRL-R"), self.Redo, "redo16", pos=200)
        menu(_("Cut\tCTRL-X"), self.Cut, "editcut16", pos=300)
        menu(_("&Copy\tCTRL-C"), self.Copy, "editcopy16", pos=400)
        menu(_("&Paste\tCTRL-V"), self.Paste, "editpaste16", pos=500)
        event.Skip()
    #@-node:_on_get_focus
    #@-others
#@-node:class ShellView
#@+node:class LoggerView
class LoggerView(session.MessageLogger):
    #@	@+others
    #@+node:__init__
    def __init__(self, parent):
        session.MessageLogger.__init__(self, parent)
        wx.EVT_SET_FOCUS(self, self._on_get_focus)
    #@-node:__init__
    #@+node:_on_get_focus
    def _on_get_focus(self, event):
        top = controller().get_top_menu()
        edit_menu = top.make_menu(_("&Edit"), pos=100)
        menu = lambda *args, **kw: edit_menu.make_item(self, *args, **kw)
        menu(_("&Copy\tCTRL-C"), self.Copy, "editcopy16", pos=400)
        event.Skip()
    #@-node:_on_get_focus
    #@-others
#@-node:class LoggerView
#@+node:class Session
class Session(session.Session, _Executer):
    #@	<< class Session declarations >>
    #@+node:<< class Session declarations >>
    LOGGER = LoggerView

    #@-node:<< class Session declarations >>
    #@nl
    #@	@+others
    #@+node:__init__
    def __init__(self):
        session.Session.__init__(self)
        _Executer.__init__(self)

        def open_shell(parent):
            try:
                dict = sys.modules["__faces_main__"].__dict__
            except KeyError:
                dict = globals()

            return ShellView(parent, dict)

        self.SHELL_FACTORY = open_shell
        self.help = None

        config = controller().config
        try:
            self.recent_files = config.get("DEFAULT", "recent_files").split(",")
            self.recent_files = map(str.strip, self.recent_files)
            self.recent_files = filter(bool, self.recent_files)
        except ConfigParser.NoOptionError:
            self.recent_files = []
    #@-node:__init__
    #@+node:end_session
    def end_session(self):
        self.clear_cache()
        controller().config.set("DEFAULT", "recent_files",
                                ",".join(self.recent_files))
    #@-node:end_session
    #@+node:get_help
    def get_help(self):
        if not self.help:
            wx.FileSystem.AddHandler(wx.ZipFSHandler())
            self.help = wx.html.HtmlHelpController()
            self.help.AddBook(os.path.join(_resource_path,
                                           "help", "faces.zip"), True)
        return self.help
    #@-node:get_help
    #@+node:jump_to_file
    def jump_to_file(self, path, line):
        path = os.path.normcase(path)
        for m in controller().get_planbuffers():
            if m.path == path:
                m.goto_source(line)
    #@-node:jump_to_file
    #@+node:set_menus
    def set_menus(self):
        top = controller().get_top_menu()

        wx.App.SetMacHelpMenuTitleName(_("&Help"))
        help_menu = top.make_menu(_("&Help"), pos=sys.maxint, id=wx.ID_HELP)
        menu = lambda *args, **kw: help_menu.make_item(self, *args, **kw)
        menu(_("&Content and Index"), self.menu_help)
        menu(_("&Send Project..."), self.menu_send_project)

        menu(_("&Howtos..."), self.menu_howtos)
        item = menu(_("&About"), controller().show_splash, id=wx.ID_ABOUT)
        wx.App.SetMacAboutMenuItemId(item.id)

        if check_memory: menu(_("Check Memory"), check_memory)

        file_menu = top.make_menu(_("&File"))

        menu = lambda *args, **kw: file_menu.make_item(self, *args, **kw)
        menu(_("&New..."), self.menu_new, "filenew16",
             help=_("New faces file"), pos=0)
        menu(_("&Open..."), self.menu_open, "fileopen16",
             help=_("Open faces file"), pos=10)

        self.recent_menu = file_menu.make_menu(\
            _("&Recent Files"), help=_("Open recently used files"), pos=15)

        self.update_recent_menu()
        self.close_menu = menu(_("&Close"), self.menu_close,
                               "fileclose16",
                               pos=20)

        menu(_("&Save\tCTRL-S"), 1, "filesave16", pos=30).enable(False)
        menu(_("&Save as..."), 2, "filesaveas16", pos=40).enable(False)
        menu(_("Recalculate\tF5"), self.menu_recalc, "rebuild16", pos=50,
             help=_("Recalculate Project"))
        self.close_menu.enable(False)

        toolbar = controller().get_toolbar()

        toolbar.make_tool(self, "new", self.menu_new, "filenew22",
                          short=_("New Project"))

        toolbar.make_tool(self, "open", self.menu_open, "fileopen22",
                          short=_("Open Project"),
                          long="open file")

        toolbar.make_tool(self, "close", self.menu_close,
                          "fileclose22",
                          short=_("Close Project"),
                          long="close file")

        toolbar.make_tool(self, "save", 1, "filesave22",
                          short=_("save"), long="save file").enable(False)

        toolbar.make_tool(self, "saveas", 2, "filesaveas22",
                          short=_("save as")).enable(False)

        toolbar.make_tool(self, "recalculate", self.menu_recalc, "rebuild22",
                          short=("Recalculate"),
                          long=_("Recalculate Project"))

        toolbar.realize()
    #@-node:set_menus
    #@+node:add_recent_file
    def add_recent_file(self, path):
        path = os.path.abspath(path)
        path = os.path.normcase(path)

        try:
            self.recent_files.remove(path)
        except ValueError:
            pass

        self.recent_files.insert(0, path)
        del self.recent_files[8:]
        self.update_recent_menu()
    #@-node:add_recent_file
    #@+node:update_recent_menu
    __recent_owner = object()
    def update_recent_menu(self):
        file_menu = controller().get_top_menu().make_menu(_("&File"))
        self.recent_menu = file_menu.make_menu(\
            _("&Recent Files"), help=_("Open recently used files"), pos=15)

        self.recent_menu.make_item(None, "dumy", None) #dummy to avoid the deletion of the menu
        self.recent_menu.remove_by_owner(self.__recent_owner)
        def make_open_file(f):
            def open_file(): self.open_file(f)
            return open_file

        for f in self.recent_files:
            self.recent_menu.make_item(self.__recent_owner, f,
                                       make_open_file(f))

        self.recent_menu.remove_by_owner(None)
    #@-node:update_recent_menu
    #@+node:register
    def register(self):
        session.Session.register(self)
        self.set_menus()
    #@-node:register
    #@+node:menu_recalc
    def menu_recalc(self):
        if not self.main_buffer: return
        view = self.main_buffer.get_edit_view(False)
        if view: view.sync_text()

        self.check_for_correction()
        self.execute_plan()
    #@nonl
    #@-node:menu_recalc
    #@+node:check_for_correction
    def check_for_correction(self):
        to_correct = [ model.editor.editor
                       for model in controller().get_planbuffers()
                       if model.editor.editor.should_be_corrected ]
        if to_correct:
            answer = wx.MessageBox(_("Should I try to correct your project?"),
                                   _("Recalc Project"),
                                   wx.YES_NO|wx.CANCEL|wx.ICON_QUESTION)
            if answer == wx.YES:
                for editor in to_correct:
                    editor.should_be_corrected = False
                    editor.correct_code()
            else:
                for editor in to_correct:
                    editor.should_be_corrected = False
    #@nonl
    #@-node:check_for_correction
    #@+node:menu_help
    def menu_help(self):
        #import webbrowser
        #webbrowser.open("http://faces.homeip.net/book/index.html")
        self.get_help().DisplayContents()
    #@-node:menu_help
    #@+node:menu_send_project
    def menu_send_project(self):
        def get_text(module):
            if not isinstance(module, PlanBuffer): return None
            view = module.get_edit_view(False)
            if view: view.sync_text()
            return (module.path, module.text)

        models = controller().id_to_model.values()
        projects = filter(bool, map(get_text, models))
        if not projects: return
        sender = gutils.ProjectSender()
        sender.add_recipient("mreithinger@web.de",
                             "Faces Project Files",
                             projects)
        sender.send()
        controller().session.tmp_files_to_remove.append(sender.path)
    #@-node:menu_send_project
    #@+node:menu_howtos
    def menu_howtos(self):
        dlg = wx.FileDialog(controller().GetTopWindow(),
                            _("Choose a howto file"),
                            faces.utils.get_howtos_path(),
                            "",
                            _("Faces Files (*.py)|*.py"),
                            wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.open_file(dlg.GetPath())
        dlg.Destroy()
    #@-node:menu_howtos
    #@+node:menu_new
    def menu_new(self):
        templates = filter(lambda f: f.endswith(".py"),
                           os.listdir(_template_path))
        dlg = wx.SingleChoiceDialog(controller().GetTopWindow(),
                                    _("The following templates are available:"),
                                    _("Choose Template"),
                                    templates)
        if dlg.ShowModal() == wx.ID_OK:
            template = dlg.GetStringSelection()
            self.open_file(os.path.join(_template_path, template), False)
        dlg.Destroy()
    #@-node:menu_new
    #@+node:menu_open
    def menu_open(self):
        dlg = wx.FileDialog(controller().GetTopWindow(),
                            _("Choose a file"),
                            current_directory or os.getcwd(),
                            "",
                            _("Faces Files (*.py)|*.py"),
                            wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.open_file(dlg.GetPath())
        dlg.Destroy()
    #@-node:menu_open
    #@+node:menu_close
    def menu_close(self):
        if not self.check_modified_buffers(): return False
        self.close_menu.enable(False)
        self.main_buffer = None
        for m in controller().get_planbuffers():
            m.close()
            controller().remove_model(m)

        self.remove_modules()
        self.clear_logs()
        return True
    #@-node:menu_close
    #@+node:open_file
    def open_file(self, path, add_recent=True):
        if not self.menu_close(): return
        self.close_menu.enable(True)
        self.main_buffer = PlanBuffer(path, True)
        self.main_buffer.refresh()

        dirname = os.path.dirname(path)
        if dirname:
            os.chdir(dirname)

        controller().add_model(self.main_buffer)
        self.execute_plan()
        self.main_buffer.set_focus(True)
        if add_recent: self.add_recent_file(self.main_buffer.path)
    #@-node:open_file
    #@+node:check_modified_buffers
    def check_modified_buffers(self):
        for m in controller().get_planbuffers():
            if m.is_modified:
                answer = wx.MessageBox(_("The file %s was modified."
                                         " Should it be saved?") % m.path,
                                       _("Close Buffer"),
                                       wx.YES_NO|wx.CANCEL|wx.ICON_QUESTION)
                if answer == wx.YES:
                    m.save_buffer()
                elif answer == wx.CANCEL:
                    return False
                else:
                    m.close()

        return True
    #@-node:check_modified_buffers
    #@-others
#@-node:class Session
#@+node:showwarning
def showwarning(message, category, filename, lineno, file=None):
    if _warning_registry.has_key((filename, lineno)):
        return

    _warning_registry[(filename, lineno)] = True
    print >> sys.stderr, warnings.formatwarning(message, category, filename, lineno)
#@-node:showwarning
#@+node:check_installation
def check_installation():
    import time
    try:
        time.strptime("1.1.2005 10:30", "%d.%m.%Y %H:%M")
    except Exception, e:
        print >> sys.stderr, "Error in installation(time.strptime):"
        print >> sys.stderr, e
#@-node:check_installation
#@+node:check_memory
if _faces._DEBUGGING:
    def check_memory():
        collect_garbage()
        objs = gc.get_objects()
        print
        print "--------------------------------------------------------------"
        print "views"
        print "--------------------------------------------------------------"
        for v in filter(lambda o: isinstance(o, navigator.View), objs):
            print v._nav_title, v.__class__.__name__
        print "--------------------------------------------------------------"

        print
        print "--------------------------------------------------------------"
        print "observers"
        print "--------------------------------------------------------------"
        for v in filter(lambda o: isinstance(o, _observer.Observer), objs):
            print v.__type_name__, v.__class__.__name__
        print "--------------------------------------------------------------"

        import matplotlib.axes as axes 
        print
        print "--------------------------------------------------------------"
        print "axes"
        print "--------------------------------------------------------------"
        for v in filter(lambda o: isinstance(o, axes.Axes), objs):
            refs = gc.get_referrers(v)
            print v.__class__.__name__, len(refs)

        print "--------------------------------------------------------------"

        import faces.charting.widgets as widgets
        print
        print "--------------------------------------------------------------"
        print "widgets"
        print "--------------------------------------------------------------"
        for v in filter(lambda o: isinstance(o, widgets.Widget), objs):
            refs = gc.get_referrers(v)
            print v.__class__.__name__, len(refs)
        print "--------------------------------------------------------------"
else:
    check_memory = None
#@-node:check_memory
#@+node:class TaskBarIcon
class TaskBarIcon(wx.TaskBarIcon):
    TBMENU_RESTORE = wx.NewId()
    TBMENU_CLOSE   = wx.NewId()

    def __init__(self, frame):
        wx.TaskBarIcon.__init__(self)
        self.frame = frame

        # Set the image
        icon = wx.IconFromBitmap(ResourceManager.load_bitmap("gantt"))
        self.SetIcon(icon, "Faces")
        self.imgidx = 1
        print "taskbar"
        # bind some events
        self.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.OnTaskBarActivate)
        self.Bind(wx.EVT_MENU, self.OnTaskBarActivate, id=self.TBMENU_RESTORE)
        self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=self.TBMENU_CLOSE)


    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(self.TBMENU_RESTORE, _("Restore Faces"))
        menu.Append(self.TBMENU_CLOSE,   _("Close Faces"))
        return menu


    def MakeIcon(self, img):
        """
        The various platforms have different requirements for the
        icon size...
        """
        if "wxMSW" in wx.PlatformInfo:
            img = img.Scale(16, 16)
        elif "wxGTK" in wx.PlatformInfo:
            img = img.Scale(22, 22)
        # wxMac can be any size upto 128x128, so leave the source img alone....
        icon = wx.IconFromBitmap(img.ConvertToBitmap() )
        return icon


    def OnTaskBarActivate(self, evt):
        if self.frame.IsIconized():
            self.frame.Iconize(False)
        if not self.frame.IsShown():
            self.frame.Show(True)
        self.frame.Raise()


    def OnTaskBarClose(self, evt):
        self.frame.Close()
#@-node:class TaskBarIcon
#@+node:class FacesApp
splash_text = """<font family="swiss" size="9">
Support <font style="slant">faces</font> and send your
project files to mreithinger@web.de.

To improve the quality of <font style="slant">faces</font>, we need more
real-world test data. Support the <font style="slant">faces</font> development
team and provide your project for use as test data.

You can use the Menu <font family="modern" weight="bold">Help->Send Project</font>
for your convenience.</font>
"""

version_text = '<font family="swiss" size="7">'\
               'faces version %s. Copyright (c) '\
               '2005,2006,2007 by Reithinger GmbH</font>' % str(_faces.__version__)


class FacesApp(MetaApp):
    #@	@+others
    #@+node:OnInit
    def OnInit(self):
        if MetaApp.OnInit(self):
            self.frame.Bind(wx.EVT_CLOSE, self._on_frame_close)
            self.frame.Bind(wx.EVT_MENU_OPEN, self._on_menu_open)
            self.status_bar.SetFieldsCount(3)
            self.status_bar.SetStatusWidths([-1, 20, 200])
            self.gauge = wx.Gauge(self.status_bar, -1, 10)
            self.gauge.Hide()
            self.show_splash(True)
            return True

        return False

    #@-node:OnInit
    #@+node:show_splash
    def show_splash(self, timeout=False):
        splash = ResourceManager.load_bitmap("splash1")

        text = RenderToBitmap(splash_text)
        dc = wx.MemoryDC()
        dc.SelectObject(splash)
        dc.DrawBitmap(text, 14, 100, True)

        version = RenderToBitmap(version_text)
        y = splash.GetHeight() - version.GetHeight() - 10
        dc.DrawBitmap(version, 14, y, True)

        dc.SelectObject(wx.NullBitmap)

        flags = wx.SPLASH_CENTRE_ON_SCREEN
        if timeout:
            flags |= wx.SPLASH_TIMEOUT
        else:
            flags |= wx.SPLASH_NO_TIMEOUT

        splash = wx.SplashScreen(splash, flags, 8000, self.frame, 
                                 style=wx.STAY_ON_TOP|wx.FRAME_NO_TASKBAR)

        self.Yield(True)
    #@-node:show_splash
    #@+node:_on_frame_close
    def _on_frame_close(self, event):
        if event.CanVeto() and not self.session.check_modified_buffers():
            event.Veto()
        else:
            event.Skip()
            self.frame.Hide() #avoid flickering in Windows
            self.frame.Destroy()
    #@-node:_on_frame_close
    #@+node:_on_menu_open
    def _on_menu_open(self, event):
        menu = event.GetMenu()
        items = self.get_top_menu().items.values()

        for item in items:
            if item.wxobj == menu:
                title = item.title
                self.remove_temp_menus()
                for v in self.get_all_views():
                    try:
                        v.on_make_menu(title)
                        break
                    except AttributeError: pass
    #@-node:_on_menu_open
    #@+node:is_processing
    def is_processing(self):
        try:
            self.gauge_title
            return True
        except AttributeError:
            return False
    #@-node:is_processing
    #@+node:progress_start
    def progress_start(self, title, maximum, message=""):
        self.gauge_title = title
        self.frame.SetStatusText(title, 0)
        w, h = self.status_bar.GetTextExtent(title + "X")
        rect = self.status_bar.GetFieldRect(0)
        self.gauge.SetDimensions(rect.x + w, rect.y,
                                 rect.width - w, rect.height)
        self.gauge.SetRange(maximum)
        self.gauge.Show()
        #self.frame.Enable(False)
        self.Yield(True)

    #@-node:progress_start
    #@+node:progress_update
    def progress_update(self, value, message=""):
        try:
            self.frame.SetStatusText(self.gauge_title, 0)
            self.gauge.SetValue(value)
            self.Yield(True)
        except AttributeError:
            pass
    #@-node:progress_update
    #@+node:progress_end
    def progress_end(self):
        try:
            self.frame.SetStatusText("", 0)
            self.gauge.Hide()
            self.Yield(True)
            del self.gauge_title
        except AttributeError:
            pass

        #self.frame.Enable()
        self.WakeUpIdle()
    #@-node:progress_end
    #@+node:get_planbuffers
    def get_planbuffers(self):
        models = self.id_to_model.values()
        for m in models:
            if isinstance(m, PlanBuffer):
                yield m
    #@nonl
    #@-node:get_planbuffers
    #@-others
#@nonl
#@-node:class FacesApp
#@+node:main
def main():
    sys.setcheckinterval(10000)
    lang = os.environ.get("LANG", "")
    try:
        locale.setlocale(locale.LC_ALL, lang)
    except locale.Error, err:
        print >> sys.stderr, err
        if wx.Platform == '__WXMSW__':
            locale.setlocale(locale.LC_ALL, "")
        else:
            locale.setlocale(locale.LC_ALL, "C")

    if not _faces._PROFILING:
        try:
            import psyco
        except ImportError:
            pass
        else:
            psyco.profile()
            #psyco.log()
            psyco.cannotcompile(re.compile)

    ResourceManager.resource_path.append(_resource_path)

    app = FacesApp(False)
    app.config = ConfigParser.SafeConfigParser()
    app.config.read(os.path.expanduser("~/.faces-cfg"))

    app.freeze()
    faces.utils.do_yield = app.Yield
    faces.utils.progress_start = app.progress_start
    faces.utils.progress_update = app.progress_update
    faces.utils.progress_end = app.progress_end

    app.get_toolbar().wxobj.SetToolBitmapSize((24, 24))
    app.set_title("faces")

    icon = wx.IconFromBitmap(ResourceManager.load_bitmap("gantt"))
    app.frame.SetIcon(icon)

    app.session = Session()
    app.add_model(app.session)
    app.session.install_logger()

    if _faces._DEBUGGING:
        sys.stdout = sys.__stdout__

    warnings.showwarning = showwarning
    warnings.filterwarnings("always")
    try:
        # used in python <= 2.3
        warnings.filterwarnings("ignore", category=OverflowWarning)
    except NameError: pass
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    check_installation()
    app.thaw()

    if len(sys.argv) > 1:
        try:
            app.session.open_file(sys.argv[1])
        except:
            pass

    app.MainLoop()
    app.session.end_session()

    try:
        outf = file(os.path.expanduser("~/.faces-cfg"), "w")
        app.config.write(outf)
    except IOError:
        pass

    return 0

#@-node:main
#@-others

if __name__ == "__main__":
    if _faces._PROFILING:
        import profile
        import pstats

        profile.run("main()", "profile_out")
        p = pstats.Stats('profile_out')
        p.strip_dirs().sort_stats('cumulative').print_stats(40)
    else:
        sys.exit(main())
#@-node:@file gui/plangui.py
#@-leo
