############################################################################
#   Copyright (C) 2005, 2006 by Reithinger GmbH
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

"""
release management functions
"""

import faces
import faces.task as ftask
import warnings

_is_source_ = False
__all__ = ("use_warnings", "ReleaseMixin")

use_warnings=True


class ReleaseMixin(object):
    def modify_widget(self, go, task):
        if task.copy_src:
            go.fobj = task.copy_src


def make_release_hook(task, name, release):
    """
    Makes all tasks of the given release to children of
    the current task
    """
    try:
        if task.children:
            return
    except AttributeError:
        pass

    
    try:
        registry = task.root._release_registry
    except AttributeError:
        return

    try:
        tasks = registry[release]
    except KeyError:
        #defer task
        raise ftask._IncompleteError('release "%s" does not exist' % release)


    def index(t):
        return (map(int, t.index.split(".")), t)

    rchildren = [ index(t) for t in tasks.values() ] # values() has wrong sort
    rchildren.sort()

    # the following is adirty hack, but
    # the usual
    #    def make_clone(child_task):
    #        def clone()
    #            copy_src = child_task
    #
    #        return clone
    #
    # does not work for some reason.
    
    try:
        path_task_map = task.root.path_task_map
    except AttributeError:
        path_task_map = task.root.path_task_map = {}


    def internal_call():
        src_tsk = me.root.path_task_map.get(me.path)
        me.copy_src = src_tsk

    def clone():
        internal_call()

    path = task.path + ".%s"
    for i, t in rchildren:
        task._set_attrib(t.name, clone)
        path_task_map[path % t.name] = t



def release_hook(task, name, value):
    try:
        registry = task.root._release_registry
    except AttributeError:
        registry = task.root._release_registry = {}

    registry.setdefault(value, {})[task.path] = task
    return value


def modules_hook(task, name, value):
    try:
        my_modules = task.__dict__[name]
    except KeyError:
        if not isinstance(value, (tuple, list)):
            if use_warnings:
                warnings.warn('modules must be a list[] or a tuple()',
                              RuntimeWarning, 2)

            return value

        my_modules = []
        for v in value:
            if not isinstance(v, ftask._Path): continue
            v = v._task
            if getattr(v, "release_module", False):
                # amodule can only be inserted once!
                continue  
            v.release_module = task
            my_modules.append(v)

    if my_modules and isinstance(my_modules, list):
        effort = task._to_delta(sum([ t.effort for t in my_modules ]))
    else:
        effort = task._to_delta("1M")

    if not task._is_frozen:
        task.effort = effort
        
    return my_modules


faces.Task._set_hook("release", release_hook)
faces.Task._set_hook("make_release", make_release_hook)
faces.Task._set_hook("modules", modules_hook)

def faces_clean_up():
    faces.Task._set_hook("release")
    faces.Task._set_hook("make_release")
    faces.Task._set_hook("modules")
    
        
if faces.gui_controller:
    import faces.gui.editor.editor as editor
    import faces.gui.editor.context as context

    def get_release_completions(obj=None):
        print "get_release_completions", obj
        return [("0.1.0", "0.1.0")]

    context.PTask.__attrib_completions__["release"] = "release = "
    context.PTask.__attrib_completions__["make_release"] = "make_release = "
    #context.PTask.__attrib_completions__["#make_release"] = "get_release_completions"
    context.PTask.__attrib_completions__["modules"] = "modules = [|]"
    

    _old_faces_clean_up = faces_clean_up
    def faces_clean_up():
        _old_faces_clean_up()
    
        try:
            del context.PTask.__attrib_completions__["release"]
            del context.PTask.__attrib_completions__["make_release"]
            #del context.PTask.__attrib_completions__
            del context.PTask.__attrib_completions__["modules"]
        except KeyError: pass

