#@+leo-ver=4
#@+node:@file gui/editor/resource.py
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
A collection of functions for editing tasks and their attributes
"""
#@<< Imports >>
#@+node:<< Imports >>
import sys
import faces.plocale
from attribedit import *
import editorlib
try:
    set
except NameError:
    from sets import Set as set
#@nonl
#@-node:<< Imports >>
#@nl

_is_source_ = True
_ = faces.plocale.get_gettext()

#@+others
#@+node:Editors
#@+node:print_resource_references
def print_resource_references(code_item, outstream=None):
    outstream = outstream or sys.stdout
    rname = code_item.name
    print >> outstream, _('The following lines reference the resource "%s":') % rname
    for m in controller().get_planbuffers():
        for ci, line, start, end in m.editor.find_resource_references(rname):
            print >> outstream, _('   object: "%s", File "%s", line %i') % (ci.name, m.path, line + 1)

    print >> outstream
#@nonl
#@-node:print_resource_references
#@+node:class ResourceRemover
class ResourceRemover(object):
    __icon__ = "delete16"

    #@    @+others
    #@+node:apply
    def apply(self, expression, code_item):
        return False
    #@-node:apply
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        return "extra"
    #@-node:apply_browser_menu
    #@+node:activate
    def activate(self, context):
        references = False
        code_item = context.code_item
        rname = code_item.name
        for m in controller().get_planbuffers():
            if list(m.editor.find_resource_references(rname)):
                references = True
                break

        if references:
            print_resource_references(context.code_item, sys.stderr)
            print >> sys.stderr, _("You have to remove those references before removing the resource!\n")
        else:
            code_item.remove()
    #@-node:activate
    #@-others
#@-node:class ResourceRemover
#@+node:class ReferencePrinter
class ReferencePrinter(object):
    __icon__ = "list16"

    #@    @+others
    #@+node:apply
    def apply(self, expression, code_item):
        return False
    #@-node:apply
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        return "extra"
    #@-node:apply_browser_menu
    #@+node:activate
    def activate(self, context):
        print_resource_references(context.code_item)
    #@-node:activate
    #@-others
#@nonl
#@-node:class ReferencePrinter
#@+node:class ResourceCreator
class ResourceCreator(NameEditor):
    title = _("Create Resource")
    #@    @+others
    #@+node:realize_code
    def realize_code(self):
        now = datetime.datetime.now().strftime("%x %H:%M:%S")
        code = 'class %s(Resource):\n"Inserted at %s"' % (self.name, now)
        context = self.context.__class__(self.context.get_last_code_item())
        context.append_item(code, 0)

    #@-node:realize_code
    #@-others
#@nonl
#@-node:class ResourceCreator
#@+node:class ResourceRenamer
class ResourceRenamer(RenameEditor):
    title = _("Rename Resource")
    __icon__ = "rename16"

    def correct_code(self, editor):
        editor.correct_resource_code(self.context.code_item)
#@-node:class ResourceRenamer
#@-node:Editors
#@+node:Assign Editors
registry = context.CResource.editors
std_attributes = _("Standard/%s")

registry[std_attributes % "title..."] = AttributeEditor("title", String, _("Title"))
registry[std_attributes % "max_load..."] = AttributeEditor("max_load", Float, 1.0)
registry[std_attributes % "vacation..."] = AttributeEditor("vacation", DateTimeRanges)
registry[std_attributes % "efficiency..."] = AttributeEditor("efficiency", Float, 1.0)
registry[std_attributes % "Create Resource...(1000)"] = ResourceCreator()
registry[std_attributes % "Rename...(1010)"] = ResourceRenamer()
registry[std_attributes % "Remove...(1020)"] = ResourceRemover()
registry[std_attributes % "Show References...(1900)"] = ReferencePrinter()
del std_attributes

#@-node:Assign Editors
#@-others
#@nonl
#@-node:@file gui/editor/resource.py
#@-leo
