#@+leo-ver=4
#@+node:@file gui/editor/classifiers.py
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
Codeitem classifiers.
"""
#@<< Imports >>
#@+node:<< Imports >>
import faces.task as ftask
import faces.resource as fresource
import faces.observer as fobserver
import metapie.gui.pyeditor as pyeditor
#@-node:<< Imports >>
#@nl

__all__ = ("is_task", "is_resource", "is_observer", \
           "is_project", "is_evaluation", "is_import",\
           "get_resource_base", "get_observer_base",\
           "is_observer_func", "EVALUATION")

_is_source_ = True

#@+others
#@+node:is_task
def is_task(item):
    if not item: return False
    try:
        return isinstance(item.obj, ftask.Task) \
            and not isinstance(item.obj, ftask._ProjectBase)
    except AttributeError:
        if item.obj_type == pyeditor.FUNCTION and not item.get_args():
            parent = item.get_parent()
            return is_task(parent) or is_project(parent)

        return False
#@-node:is_task
#@+node:is_resource
def is_resource(item):
    try:
        return isinstance(item.obj, fresource._MetaResource)
    except AttributeError:
        return bool(get_resource_base(item))
    return False


def get_resource_base(item):
    if not item or item.obj_type != pyeditor.CLASS: return None
    module = item.editor.get_module()
    for base in item.get_args():
        try:
            cls = eval("module.%s" % base)
            if isinstance(cls, fresource._MetaResource):
                return cls
        except: pass
    return None
#@-node:is_resource
#@+node:is_observer
def is_observer_func(item):
    try:
        if item.obj_type != pyeditor.FUNCTION: return False
        while item.obj_type == pyeditor.FUNCTION:
            item = item.get_parent()
    except AttributeError:
        return False

    return is_observer(item)


def is_observer(item):
    try:
        return issubclass(item.obj, fobserver.Observer)
    except AttributeError:
        return bool(get_observer_base(item))

    except TypeError:
        return False


def get_observer_base(item):
    if not item or item.obj_type != pyeditor.CLASS: return None
    module = item.editor.get_module()
    for base in item.get_args():
        try:
            cls = eval("module.%s" % base)
            if issubclass(cls, fobserver.Observer):
                return cls
        except: pass
    return None
#@-node:is_observer
#@+node:lightweight classifiers

def _sandwich(func):
    def save(*args):
        try:
            return func(*args)
        except AttributeError:
            return False

    return save   


EVALUATION = pyeditor.IMPORT + 1
is_project = _sandwich(lambda i: i.obj_type != EVALUATION \
                       and isinstance(i.obj, ftask._ProjectBase))
is_evaluation = _sandwich(lambda i: i.obj_type == EVALUATION)
is_import = _sandwich(lambda i: i.obj_type == pyeditor.IMPORT)

del _sandwich
#@-node:lightweight classifiers
#@-others
#@nonl
#@-node:@file gui/editor/classifiers.py
#@-leo
