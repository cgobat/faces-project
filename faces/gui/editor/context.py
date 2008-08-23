#@+leo-ver=4
#@+node:@file gui/editor/context.py
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
Different editor contexts, they depend on the 
source code environemnt of a cursor position.
"""
#@<< Imports >>
#@+node:<< Imports >>
import metapie.gui.pyeditor as pyeditor
import faces.observer as fobserver
import faces.resource as fresource
import faces.task as ftask
import faces.plocale
import weakref
import types
import inspect
from classifiers import *
from metapie.gui import controller
#@-node:<< Imports >>
#@nl

_is_source = True
_ = faces.plocale.get_gettext()

#@+others
#@+node:get_observer_pseudo
def get_observer_pseudo(code_item):
    module = code_item.editor.get_module()
    for base in code_item.get_args():
        try:
            bo = eval("module.%s" % base)
            if issubclass(bo, fobserver.Observer):
                return bo
        except AttributeError: pass
        except TypeError: pass
        except SyntaxError: pass

    return fobserver.Observer
#@nonl
#@-node:get_observer_pseudo
#@+node:create_editor_menu
def create_editor_menu(menu, context, editors):
    #editors is a pair consisting of ("path", attrib_editor)
    #@    << define improve_duplicate_names >>
    #@+node:<< define improve_duplicate_names >>
    def improve_duplicate_names(editors):
        if len(editors[0][0].split("/")) < 2: 
            #path has no group
            return editors

        counts = { }
        for path, editor in editors:
            name = path.split("/")[-1]
            counts[name] = counts.get(name, 0) + 1

        result = []    
        for path, editor in editors:
            path = path.split("/")
            name = path[-1]
            if counts[name] > 1:
                group = path[-2]
                result.append(("%s (%s)" % (name, group), editor))
            else:
                result.append((name, editor))

        return result
    #@nonl
    #@-node:<< define improve_duplicate_names >>
    #@nl
    #@    << define make_groups >>
    #@+node:<< define make_groups >>
    def make_groups(editors):
        """
        If there are more than 10 editors arange them in groups
        """
        if len(editors) <= 10:
            return improve_duplicate_names(editors)

        groups = {}
        for name, ie in editors:
            path = name.split("/")
            gl = groups.setdefault(path[0], [])
            gl.append(("/".join(path[1:]), ie))

        for g, e in groups.iteritems():
            if len(g.split("/")) > 1:
                groups[g] = make_groups(e)

        return groups.items()
    #@nonl
    #@-node:<< define make_groups >>
    #@nl
    #@    << define create_menu >>
    #@+node:<< define create_menu >>
    def make_call(item_editor):
        def call(): item_editor.activate(context)
        return call


    def create_menu(parent_menu, editors):
        editors.sort()
        was_list = False
        for name, ie in editors:
            path = name.split("/")
            menu_title = path[0]
            menu_pos = -1

            #@        << extract menu position from title >>
            #@+node:<< extract menu position from title >>
            try:
                paren_pos = menu_title.index("(")
                menu_pos = int(menu_title[paren_pos + 1:-1])
                menu_title = menu_title[:paren_pos]
            except ValueError:
                pass
            #@nonl
            #@-node:<< extract menu position from title >>
            #@nl

            if isinstance(ie, list):
                create_menu(parent_menu.make_menu(menu_title, pos=menu_pos), ie)
                if not was_list: parent_menu.make_separator(menu_title, True)
                was_list = True
            else:
                parent_menu.make_temp_item(menu_title, make_call(ie), pos=menu_pos,
                                           bitmap=getattr(ie, "__icon__", None))
                was_list = False
    #@-node:<< define create_menu >>
    #@nl
    editors = make_groups(editors)
    create_menu(menu, editors)
    if editors:
        menu.make_separator(tuple(menu)[-1].title)

#@-node:create_editor_menu
#@+node:class ItemEditor
class ItemEditor(object):
    """
    Define the Interface for Editor to 
    manipulate code_items.
    """
    attrib_name = ""

    def apply(self, expression):
        """
        returns true if the editor applies for the expression
        """
        return False


    def activate(self, code_item, context):
        """
        activates the editor.
        """

#@-node:class ItemEditor
#@+node:class PTask
class PTask(object):
    """
    A pseudo task object
    """
    __doc__ = ftask.Task.__doc__
    __attrib_completions__ = ftask.Task.__attrib_completions__.copy()
    __attrib_completions__.update({ "up" : "up", "root" : "root"})    
    #@	@+others
    #@+node:__init__
    def __init__(self, code_item=None):
        self.code_item = code_item
        self.to_string = self.me = weakref.proxy(self)

        if code_item:
            self.name = code_item.name
            self.dict_children = dict(map(lambda c: (c.name, PTask(c)), 
                                      self.code_item.get_children()))
            try:
                self.title = code_item.obj.title
            except AttributeError:
                self.title = self.name
        else:
            self.name = self.title = ""
    #@nonl
    #@-node:__init__
    #@+node:root
    def _get_root(self):
        last_parent = self.code_item
        parent = last_parent.get_parent()
        while parent:
            last_parent = parent
            parent = parent.get_parent()

        return PTask(last_parent)

    root = property(_get_root)
    #@-node:root
    #@+node:up
    def _get_up(self):
        parent = self.code_item.get_parent()
        return parent and PTask(parent) or None

    up = property(_get_up)
    #@nonl
    #@-node:up
    #@+node:__getattr__
    def __getattr__(self, name):
        if name in self.dict_children:
            return self.dict_children[name]

        return getattr(ftask.Task, name)
    #@-node:__getattr__
    #@+node:_get__all__
    def _get__all__(self):
        return dir(ftask.Task) \
               + ["up", "root", "me", "to_string", "calendar"] \
               + self.dict_children.keys()

    __all__ = property(_get__all__)
    #@nonl
    #@-node:_get__all__
    #@-others


#@-node:class PTask
#@+node:class Context
class Context(object):
    context_list = []
    code_item = None
    editors = {} # attribute editors


    def __init__(self, code_item=None):
        self.code_item = code_item


    def __repr__(self):
        return self.__class__.__name__

#@+others
#@+node:Methods
#@+node:Interface
    #@    @+others
    #@+node:get_last_code_item
    def get_last_code_item(self):
        """
        returns the last code item of the context.
        This code_item can be used for function append_item
        """
        raise RuntimeError("abstract")
    #@nonl
    #@-node:get_last_code_item
    #@+node:append_item
    def append_item(self, code, indent=-1, prespace="\n\n"):
        """
        appends a new code_item after the current item
        """
        editor = self.code_item.editor
        editor.BeginUndoAction()

        last_line = self.code_item.get_last_line()
        line_end = editor.GetLineEndPosition(last_line)
        insert_code = "%s%s" % (prespace, code)

        editor.InsertText(line_end, insert_code)

        start_line = last_line + 2
        line_pos = editor.PositionFromLine(start_line)
        if indent > -1:
            editor.SetLineIndentation(start_line, indent)
        else:
            editor.autoindent(line_pos, False)

        line_count = len(code.split("\n"))
        for line in range(start_line + 1, start_line + line_count):
            editor.autoindent(editor.PositionFromLine(line), False)
        else:
            line = start_line + line_count

        line_end = editor.GetLineEndPosition(line)        
        if editor.GetLine(line + 1).strip():
            # the next line is not empty ==> insert an extra line
            editor.InsertText(line_end, "\n")

        editor.GotoPos(line_end)
        editor.EndUndoAction()
        return start_line, start_line + line_count
    #@nonl
    #@-node:append_item
    #@+node:insert_item
    #@+doc
    # The code must bei inserted before the line marker of the code item!
    # (Therefore the insertion ahs to be done at prev_line_end)
    #@-doc
    #@@code
    def insert_item(self, code, indent):
        """
        inserts a new code_item beforte the current item
        """
        editor = self.code_item.editor
        editor.BeginUndoAction()

        line = self.code_item.get_line()
        prev_line_end = editor.GetLineEndPosition(line - 1)

        insert_code = "\n%s\n" % code
        editor.InsertText(prev_line_end, insert_code)

        start_line = line
        line_pos = editor.PositionFromLine(start_line)
        editor.SetLineIndentation(start_line, indent)

        line_count = len(code.split("\n"))
        for line in range(start_line + 1, start_line + line_count):
            editor.autoindent(editor.PositionFromLine(line), False)
        else:
            line = start_line + line_count

        line_end = editor.GetLineEndPosition(line)
        if editor.GetLine(start_line - 1).strip():
            # the before line is not empty ==> insert an extra line
            line_before_end = editor.GetLineEndPosition(start_line - 1)
            editor.InsertText(line_before_end, "\n")

        editor.GotoPos(line_end)
        editor.EndUndoAction()
        return start_line, start_line + line_count
    #@-node:insert_item
    #@+node:make_browser_menu
    def make_browser_menu(self, menu, action_filter=None):
        return False
    #@nonl
    #@-node:make_browser_menu
    #@+node:activate
    def activate(self, editor, line, prev, next, inside):
        """
        try to activate the context
        """
        if self.can_activate(editor, line, prev, next, inside):
            self.code_item = inside
            return True
        else:
            self.code_item = None
            return False
    #@nonl
    #@-node:activate
    #@+node:get_main_completion_list
    def get_main_completion_list(self):
        """
        returns the completion list of the context
        """
        return ()


    #@-node:get_main_completion_list
    #@+node:get_sub_completion_list
    def get_sub_completion_list(self, name):
        """
        returns the completions list of a specific attribute
        """
        return ()
    #@nonl
    #@-node:get_sub_completion_list
    #@+node:find_object
    def find_object(self, name):
        """
        Find an object by name.
        """
        return None
    #@nonl
    #@-node:find_object
    #@+node:make_button
    __last_expression = None
    def make_button(self, button, expression):
        if expression == self.__last_expression: return
        self.__last_expression = expression
        if not button: return

        editors = self.get_editors()
        if not editors: 
            button.hide()
            return

        try:
            attribs = self.code_item.editor.get_attribs(self.code_item)
        except AttributeError:
            attribs = ()

        if expression:
            applies = lambda ne: ne[1].apply(expression, self.code_item)
        else:        
            applies = lambda ne: ne[1].apply(expression, self.code_item) \
                                 and ne[1].attrib_name not in attribs
        editors = filter(applies, editors.iteritems())

        if not editors: 
            button.hide()
            return

        button.set_bitmap(expression and "edit16" or "new16")

        if expression:
            item_editor = editors[0][1]
            def show_popup(editor):
                item_editor.activate(self)
        else:
            def show_popup(editor):
                menu = controller().make_menu()
                create_editor_menu(menu, self, editors)
                button.PopupMenu(menu.wxobj, (0, button.GetSize().height))
                editor.SetFocus()

        button.action = show_popup
        button.Show()
    #@nonl
    #@-node:make_button
    #@-others
#@nonl
#@-node:Interface
#@+node:Methods to Overwrite
    #@    @+others
    #@+node:get_editors
    def get_editors(self):
        return self.editors
    #@nonl
    #@-node:get_editors
    #@+node:can_activate
    #@-node:can_activate
    #@-others
#@nonl
#@-node:Methods to Overwrite
#@+node:Tool Methods
    #@    @+others
    #@+node:amend_browser_menu
    def amend_browser_menu(self, menu, action_filter=None):
        code_item = self.code_item
        existing_attribs = code_item.editor.get_attribs(code_item)
        editors = self.get_editors()

        toadd = []
        toedit = []
        extra = []
        for pe in editors.iteritems():
            action = pe[1].apply_browser_menu(existing_attribs, code_item)
            if action_filter and action not in action_filter: continue
            if action == "add": toadd.append(pe)
            elif action == "edit": toedit.append(pe)
            elif action in ("extra", "create"): extra.append(pe)

        if extra:
            create_editor_menu(menu, self, extra)

        if toadd:
            #@        << insert "Add Attributes" menu >>
            #@+node:<< insert "Add Attributes" menu >>
            add = menu.make_menu(_("Add Attributes"))
            create_editor_menu(add, self, toadd)
            #@nonl
            #@-node:<< insert "Add Attributes" menu >>
            #@nl

        if toedit:
            #@        << insert "Edit Attributes" menu >>
            #@+node:<< insert "Edit Attributes" menu >>
            edit = menu.make_menu(_("Edit Attributes"))
            create_editor_menu(edit, self, toedit)
            #@nonl
            #@-node:<< insert "Edit Attributes" menu >>
            #@nl
            #@        << insert "Remove Attributes" menu >>
            #@+node:<< insert "Remove Attributes" menu >>
            remove = menu.make_menu(_("Remove Attributes"))
            editor = code_item.editor
            def create_remove(line):
                def remove_attrib(): editor.replace_expression("", line, True)
                return remove_attrib

            for p, edit in toedit:
                try:
                    attrib = edit.attrib_name
                    line = existing_attribs[attrib]
                    remove.make_temp_item(attrib, create_remove(line))
                except KeyError:
                    pass
            #@nonl
            #@-node:<< insert "Remove Attributes" menu >>
            #@nl

    #@-node:amend_browser_menu
    #@-others
#@nonl
#@-node:Tool Methods
#@-node:Methods
#@+node:Subclasses
#@+node:class CStructureContext
class CStructureContext(Context):
#@+others
#@+node:Methods
#@+node:Tool Methods
    #@    @+others
    #@+node:get_object
    def get_object(self):
        """
        retrieve a valid code or pseudo object
        """
        try:
            obj = self.code_item.obj
        except AttributeError:
            obj = self.code_item.obj = self.get_default_pseudo()

        return obj
    #@-node:get_object
    #@-others
#@nonl
#@-node:Tool Methods
#@+node:Context Interface
    #@    @+others
    #@+node:activate
    def activate(self, editor, line, prev, next, inside):
        if not super(CStructureContext, self)\
                .activate(editor, line, prev, next, inside):
            self.make_button(None, None)
            return False

        return True
    #@nonl
    #@-node:activate
    #@+node:get_main_completion_list
    def get_main_completion_list(self):
        obj = self.get_object()
        return filter(lambda kv: kv[0][0] != "#",\
                      obj.__attrib_completions__.items())
    #@-node:get_main_completion_list
    #@+node:get_sub_completion_list
    def get_sub_completion_list(self, name):
        obj = self.get_object()
        compl_dir = obj.__attrib_completions__
        try:
            compl = compl_dir["#%s" % name]
        except KeyError:
            return []
        else:
            if isinstance(compl, basestring):
                compl = getattr(self.code_item.editor, compl)(obj)
            else:
                compl = compl.items()

        return compl

    #@-node:get_sub_completion_list
    #@+node:find_object
    def find_object(self, name):
        """
        Find an object by name.
        """
        editor = self.code_item.editor
        attribs = editor.get_attribs(self.code_item)
        try:
            expression = editor.get_expression(attribs[name])
            attribs = editor.eval_expression(expression, context=self)
            return attribs[name]
        except Exception, e: pass

        obj = self.get_object()
        try:
            return getattr(obj, name)
        except AttributeError, e:
            return None
    #@-node:find_object
    #@-others
#@nonl
#@-node:Context Interface
#@+node:Methods to Overwrite
    #@    @+others
    #@+node:get_default_pseudo
    def get_default_pseudo(self):
        return None
    #@nonl
    #@-node:get_default_pseudo
    #@-others
#@nonl
#@-node:Methods to Overwrite
#@-node:Methods
#@+node:Subclasses
#@+node:class CResource
class CResource(CStructureContext):
    editors = {}
    #@    @+others
    #@+node:Context Interface
    #@+node:get_last_code_item
    def get_last_code_item(self):
        editor = self.code_item.editor
        try:
            return [ci for ci in editor.code_items if is_resource(ci) ][-1]
        except IndexError:
            return CImport(self.code_item).get_last_code_item()
    #@-node:get_last_code_item
    #@+node:make_browser_menu
    def make_browser_menu(self, menu, action_filter=()):
        if is_resource(self.code_item) or "create" in action_filter:
            self.amend_browser_menu(menu, action_filter)
            return True

        return False
    #@nonl
    #@-node:make_browser_menu
    #@-node:Context Interface
    #@+node:Overwrites (Context)
    #@+node:can_activate
    def can_activate(self, editor, line, prev, next, inside):
        return is_resource(inside)
    #@-node:can_activate
    #@-node:Overwrites (Context)
    #@+node:Overwrites (CStructureContext)
    #@+node:get_default_pseudo
    def get_default_pseudo(self):
        return fresource.Resource
    #@nonl
    #@-node:get_default_pseudo
    #@-node:Overwrites (CStructureContext)
    #@-others

Context.context_list.append(CResource())    
#@nonl
#@-node:class CResource
#@+node:class CTask
class CTask(CStructureContext):
    editors = {}
    #@    @+others
    #@+node:Context Interface
    #@+node:make_browser_menu
    def make_browser_menu(self, menu, action_filter=None):
        if not is_task(self.code_item): return False
        self.amend_browser_menu(menu, action_filter)
        return True
    #@-node:make_browser_menu
    #@+node:get_main_completion_list
    def get_main_completion_list(self):
        compl = super(CTask, self).get_main_completion_list()
        #@    << add user defined task completions >>
        #@+node:<< add user defined task completions >>
        try:
            tc = self.code_item.editor.task_completions
            if tc: compl += tc
        except AttributeError: pass
        #@nonl
        #@-node:<< add user defined task completions >>
        #@nl
        return compl    
    #@nonl
    #@-node:get_main_completion_list
    #@+node:get_sub_completion_list
    def get_sub_completion_list(self, name):
        compl = super(CTask, self).get_sub_completion_list(name)
        if not compl:
            compl = self.code_item.editor.get_session_completions()

        compl += [("up", "up"), ("root", "root")]
        return compl

    #@-node:get_sub_completion_list
    #@-node:Context Interface
    #@+node:Overwrites (Context)
    #@+node:can_activate
    def can_activate(self, editor, line, prev, next, inside):
        if is_task(inside):
            self.pseudo = PTask(inside)
            return True
        else:
            self.pseudo = None
            return False
    #@-node:can_activate
    #@-node:Overwrites (Context)
    #@+node:Overwrites (CStructureContext)
    #@+node:get_object
    def get_object(self):
        return self.pseudo
    #@-node:get_object
    #@-node:Overwrites (CStructureContext)
    #@-others

Context.context_list.append(CTask())
#@-node:class CTask
#@+node:class CProjectDeclaration
class CProjectDeclaration(CTask):
    editors = {}
    #@    @+others
    #@+node:Context Interface
    #@+node:get_last_code_item
    def get_last_code_item(self):
        try:
            editor = self.code_item.editor
            return [ci for ci in editor.code_items if is_project(ci) ][-1]
        except IndexError:
            return CResource(self.code_item).get_last_code_item()
    #@-node:get_last_code_item
    #@+node:make_browser_menu
    def make_browser_menu(self, menu, action_filter=None):
        if is_project(self.code_item) or "create" in action_filter:
            self.amend_browser_menu(menu, action_filter)
            return True

        return False
    #@-node:make_browser_menu
    #@-node:Context Interface
    #@+node:Overwrites (Context)
    #@+node:can_activate
    def can_activate(self, editor, line, prev, next, inside):
        if is_project(inside):
            self.pseudo = PTask(inside)
            return True
        else:
            self.pseudo = None
            return False
    #@-node:can_activate
    #@-node:Overwrites (Context)
    #@-others

Context.context_list.append(CProjectDeclaration())
#@-node:class CProjectDeclaration
#@+node:class CObserver
class CObserver(CStructureContext):
    editors = {}
    #@    @+others
    #@+node:Context Interface
    #@+node:get_last_code_item
    def get_last_code_item(self):
        editor = self.code_item.editor
        try:
            return [ci for ci in editor.code_items if is_observer(ci) ][-1]
        except IndexError:
            return CEvaluation(self.code_item).get_last_code_item()

    #@-node:get_last_code_item
    #@+node:make_browser_menu
    def make_browser_menu(self, menu, action_filter=None):
        if is_observer(self.code_item) or "create" in action_filter:
            self.amend_browser_menu(menu, action_filter)
            return True

        return False
    #@-node:make_browser_menu
    #@-node:Context Interface
    #@+node:Overwrites (Context)
    #@+node:can_activate
    def can_activate(self, editor, line, prev, next, inside):
        return is_observer(inside)
    #@-node:can_activate
    #@-node:Overwrites (Context)
    #@+node:Overwrites (CStructureContext)
    #@+node:get_editors
    def get_editors(self):
        import faces.gui.editor.observer as gobserver

        try:
            obj = self.code_item.obj
        except AttributeError:
            obj = self.get_default_pseudo()

        registry = gobserver.EditorRegistry()
        obj.register_editors(registry)
        registry.editors.update(self.editors)
        return registry.editors
    #@-node:get_editors
    #@+node:get_default_pseudo
    def get_default_pseudo(self):
        return get_observer_pseudo(self.code_item)
    #@-node:get_default_pseudo
    #@-node:Overwrites (CStructureContext)
    #@-others

Context.context_list.append(CObserver())
#@nonl
#@-node:class CObserver
#@-node:Subclasses
#@-others
#@nonl
#@-node:class CStructureContext
#@+node:class CObserverFunc
class CObserverFunc(Context):
    #@    @+others
    #@+node:Context Interface
    #@+node:make_button
    def make_button(self, button, expression):
        #@    << get editors >>
        #@+node:<< get editors >>
        import faces.gui.editor.observer as gobserver

        parent_item = self.code_item.get_parent()
        try:
            obj = parent_item.obj
        except AttributeError:
            try:
                obj = get_observer_pseudo(parent_item)
            except AttributeError:
                obj = None

        if obj:
            registry = gobserver.EditorRegistry()
            obj.register_editors(registry)
            editors = registry.editors
        else:
            editors = {}
        #@nonl
        #@-node:<< get editors >>
        #@nl

        applies = lambda ne: ne[1].apply("", self.code_item)
        editors = filter(applies, editors.iteritems())

        if len(editors) != 1:
            button.hide()
            return

        button.set_bitmap("edit16")
        item_editor = editors[0][1]
        def show_popup(editor):
            item_editor.activate(CObserver(self.code_item.get_parent()))

        button.action = show_popup
        button.Show()
    #@nonl
    #@-node:make_button
    #@+node:find_object
    def find_object(self, name):
        """
        Find an object by name.
        """

        #@    << define get_observer >>
        #@+node:<< define get_observer >>
        def get_observer():
            parent = self.code_item.get_parent()
            try:
                return parent.obj
            except AttributeError:
                return get_observer_pseudo(parent)
        #@nonl
        #@-node:<< define get_observer >>
        #@nl

        if name == "self":
            return get_observer()

        args = list(self.code_item.get_args())
        try:
            no = args.index(name)
        except ValueError:
            return None

        observer = get_observer()
        #@    << get argument description >>
        #@+node:<< get argument description >>
        for c in inspect.getmro(observer):
            try:
                func = getattr(c, self.code_item.name)
                arg_desc = func.args
                break
            except AttributeError: 
                pass
        else:
            return None
        #@nonl
        #@-node:<< get argument description >>
        #@nl

        try:        
            obj = arg_desc[no - 1]
        except IndexError:
            return None

        if isinstance(obj, basestring):
            # a string indicates a refrence to an attribute
            parent = CObserver(self.code_item.get_parent())
            obj = parent.find_object(obj)

        return obj
    #@nonl
    #@-node:find_object
    #@-node:Context Interface
    #@+node:Overwrites (Context)
    #@+node:can_activate
    def can_activate(self, editor, line, prev, next, inside):
        return is_observer_func(inside)
    #@-node:can_activate
    #@-node:Overwrites (Context)
    #@-others

Context.context_list.append(CObserverFunc())
#@nonl
#@-node:class CObserverFunc
#@+node:class CImport
class CImport(Context):
    editors = {}
    #@    @+others
    #@+node:Interface
    #@+node:get_last_code_item
    def get_last_code_item(self):
        editor = self.code_item.editor
        try:
            return [ci for ci in editor.code_items if is_import(ci) ][-1]
        except IndexError:
            import wx
            wx.MessageBox("At least one import has to bei in the code!", "Error")
            return None
    #@nonl
    #@-node:get_last_code_item
    #@+node:make_browser_menu
    def make_browser_menu(self, menu, action_filter=None):
        if is_import(self.code_item) or "create" in action_filter:
            self.amend_browser_menu(menu, action_filter)
            return True

        return False
    #@nonl
    #@-node:make_browser_menu
    #@+node:get_main_completion_list
    def get_main_completion_list(self):
        """
        returns the completion list of the context
        """
        fimport = lambda n: ("import faces.lib.%s" % n, 
                             "import faces.lib.%s as %s" % (n, n)) 
        ffrom = lambda n: ("from faces.lib.%s" % n, 
                           "from faces.lib.%s import %s" % (n, n))

        modules = ("report", "gantt", "resource", "generator", "workbreakdown")
        return map(fimport, modules) + map(ffrom, modules)




    #@-node:get_main_completion_list
    #@-node:Interface
    #@+node:Overwrites (Context)
    #@+node:can_activate
    def can_activate(self, editor, line, prev, next, inside):
        return is_import(prev) and line <= prev.get_last_line() + 1 \
               or is_import(next) and line >= next.get_line() - 1

    #@-node:can_activate
    #@-node:Overwrites (Context)
    #@-others

Context.context_list.append(CImport())
#@nonl
#@-node:class CImport
#@+node:class CMisc
class CMisc(Context):
    editor = None
    #@    @+others
    #@+node:Context Interface
    #@+node:activate
    def activate(self, editor, line, prev, next, inside):
        self.code_item = inside
        self.editor = editor
        if not prev:
            if next: 
                return line < next.get_line() - 1
            return True

        return False
    #@-node:activate
    #@+node:get_main_completion_list
    def get_main_completion_list(self):
        import editor
        return editor._editor_completions + self.editor.get_session_completions()


    #@-node:get_main_completion_list
    #@-node:Context Interface
    #@-others

Context.default = CMisc()
#@-node:class CMisc
#@+node:class CResourceOrTask
class CResourceOrTask(Context):
    #@    @+others
    #@+node:Context Interface
    #@+node:get_main_completion_list
    def get_main_completion_list(self):
        import editor
        return editor._editor_completions \
               + self.editor.get_session_completions() \
               + [("class (Resource):", "class |NewResource(Resource):\n"),
                  ("def NewProject():", "def |NewProject():\n" ) ]
    #@-node:get_main_completion_list
    #@-node:Context Interface
    #@+node:Overwrites (Context)
    #@+node:can_activate
    def can_activate(self, editor, line, prev, next, inside):
        if is_resource(inside): return False
        return not is_resource(next) \
            and (is_import(prev) \
                 and line > prev.get_last_line() + 1 \
                 or is_resource(prev))
    #@nonl
    #@-node:can_activate
    #@-node:Overwrites (Context)
    #@-others

Context.context_list.append(CResourceOrTask())
#@nonl
#@-node:class CResourceOrTask
#@+node:class CTaskOrEvaluation
class CTaskOrEvaluation(Context):
    #@    @+others
    #@+node:Overwrites (Context)
    #@+node:can_activate
    def can_activate(self, editor, line, prev, next, inside):
        if is_task(inside): return False
        return (is_task(prev) or is_project(prev)) \
               and not (is_task(next) or is_project(next))
    #@nonl
    #@-node:can_activate
    #@-node:Overwrites (Context)
    #@-others

Context.context_list.append(CTaskOrEvaluation())
#@nonl
#@-node:class CTaskOrEvaluation
#@+node:class CEvaluation
class CEvaluation(Context):
    editors = {}

    #@    @+others
    #@+node:Interface
    #@+node:activate
    def activate(self, editor, line, prev, next, inside):
        """
        try to activate the context
        """
        can_activate = is_evaluation(prev) and line <= prev.get_last_line() + 1
        if can_activate:
            self.code_item = inside or prev
            return True
        else:
            self.code_item = None
            return False
    #@nonl
    #@-node:activate
    #@+node:get_last_code_item
    def get_last_code_item(self):
        editor = self.code_item.editor
        try:
            return [ci for ci in editor.code_items if is_evaluation(ci) ][-1]
        except IndexError:
            return CProjectDelaration(self.code_item).get_last_code_item()
    #@-node:get_last_code_item
    #@+node:make_browser_menu
    def make_browser_menu(self, menu, action_filter=None):
        if is_evaluation(self.code_item) or "create" in action_filter:
            self.amend_browser_menu(menu, action_filter)
        return True
    #@nonl
    #@-node:make_browser_menu
    #@-node:Interface
    #@-others

Context.context_list.append(CEvaluation())
#@-node:class CEvaluation
#@+node:class CBetweenObservers
class CBetweenObservers(Context):
    editor = None
    #@    @+others
    #@+node:Context Interface
    #@+node:get_main_completion_list
    def get_main_completion_list(self):
        #@    << get_observers >>
        #@+node:<< get_observers >>
        def get_observers(module, prefix, observers):
            if len(prefix.split(".")) > 2: return observers

            try:
                attribs = module.__all__
            except AttributeError:
                attribs = dir(module)

            for a in attribs:
                if a.startswith("_"): continue

                obj = getattr(module, a, None)
                if isinstance(obj, types.ModuleType):
                    name = prefix and ".".join((prefix, a)) or a
                    get_observers(obj, name, observers)
                    continue
                try:
                    if issubclass(obj, fobserver.Observer):
                        name = prefix and ".".join((prefix, a)) or a
                        observers.append(("class %s" % name, "class |My%s(%s):\n" % (a, name)))
                except: pass
            return observers
        #@nonl
        #@-node:<< get_observers >>
        #@nl
        observers = []
        return get_observers(self.editor.get_module(), "", observers) \
                + self.editor.get_session_completions()
    #@-node:get_main_completion_list
    #@-node:Context Interface
    #@+node:Overwrites (Context)
    #@+node:can_activate
    def can_activate(self, editor, line, prev, next, inside):
        def check():
            if inside: return False
            if is_observer(prev) or is_observer_func(prev): return True
            if is_evaluation(prev):
                return line > prev.get_last_line() + 1

            return is_observer(next)

        if check():
            self.editor = editor
            return True
        else:
            self.editor = None
            return False
    #@-node:can_activate
    #@-node:Overwrites (Context)
    #@-others

Context.context_list.append(CBetweenObservers())
#@nonl
#@-node:class CBetweenObservers
#@+node:class CBetweenResource
class CBetweenResource(Context):
    #@    @+others
    #@+node:Context Interface
    #@+node:get_main_completion_list
    def get_main_completion_list(self):
        return [("class (Resource):", "class |NewResource(Resource):\n")]
    #@-node:get_main_completion_list
    #@-node:Context Interface
    #@+node:Overwrites (Context)
    #@+node:can_activate
    def can_activate(self, editor, line, prev, next, inside):
        if inside: return False
        return is_resource(next) \
            and (is_resource(prev) \
                 or is_import(prev) \
                    and line > prev.get_last_line() + 1)

    #@-node:can_activate
    #@-node:Overwrites (Context)
    #@-others

Context.context_list.append(CBetweenResource())    
#@nonl
#@-node:class CBetweenResource
#@-node:Subclasses
#@-others
#@nonl
#@-node:class Context
#@-others
#@nonl
#@-node:@file gui/editor/context.py
#@-leo
