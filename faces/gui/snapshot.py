############################################################################
#   Copyright (C) 2005 by Reithinger GmbH
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
import wx
import metapie
import metapie.dbtransient as db
import metapie.gui.views as views
import faces.task
import faces.plocale
import datetime
import inspect
import os.path


_is_source_ = True
_ = faces.plocale.get_gettext()

def create(module, encoding):
    pb = faces.task._ProjectBase

    all_projects = filter(lambda kv: isinstance(kv[1], pb), 
                          module.__dict__.iteritems())
    
    projects.clear()
    projects.update(dict(map(lambda kv: (kv[0], kv[0]), all_projects)))

    splitext = os.path.splitext

    my_filename, ext = splitext(inspect.getsourcefile(module))
    filename = my_filename + "_snpt.py"

    result = True, os.path.basename(my_filename + "_snpt")
    for m in filter(inspect.ismodule, module.__dict__.itervalues()):
        if getattr(m, "_is_snapshot_file", False):
            filename = inspect.getsourcefile(m)
            result = True, None
            break

    dlg = SnapshotDialog(metapie.controller().frame,
                         filename=filename,
                         project=projects.values()[0])
    
    if dlg.ShowModal() == wx.ID_OK:
        try:
            inf = file(dlg.snapshot.filename, "r")
            inf.close()
            new_file = False
        except IOError:
            new_file = True


        out = file(dlg.snapshot.filename, "ab+")
        if new_file:
            print >> out, ("""
# -*- coding: %s -*-            
#################################################
# This is a snapshot file for %s
# Dont't load this file directly, instead
# load the snapshot source and import this file.

_is_snapshot_file = True


""" % (encoding, os.path.basename(my_filename))).lstrip()

        project = dict(all_projects)[dlg.snapshot.project]
        print >> out, project.snapshot(name=dlg.snapshot.name)
        out.close()
    else:
        result = False, None
    
    dlg.Destroy()
    return result
    

projects = { "" : "" }


class SnapshotGenerator(db.Model):
    filename = db.Text()
    project = db.Enumerate(projects)
    name = db.Text()

    def _set_project(self, value):
        self.name = value + datetime.datetime.now().strftime("_%y%m%d_%H%M")
        return value


class SnapshotView(views.FormView):
    __model__ = SnapshotGenerator
    __view_name__ = "default"

    format = _("""
[File: ]   |filename(OpenFile)>
[Project: ]|project
[Name: ]   |name
(0,0)
--
(buttons)>
""")


    format_buttons = _("""
btn_ok{r}|btn_cancel{r}
""")

    
    def prepare(self):
        self.buttons.grow_col(0)
        self.grow_col(1)
        self.grow_row(-3)
        self.filename.set_filter(_("py (*.py)|*.py"))
        self.filename.set_width("X" * 30)
        self.name.set_width("X" * 20)
        

    def button_cancel(self):
        self.rollback()
        self.GetParent().EndModal(wx.ID_CANCEL)


    def button_ok(self):
        if self.save():
            self.GetParent().EndModal(wx.ID_OK)


    def layout(self):
        views.FormView.layout(self)
        parent = self.GetParent()
        w, h = parent.GetClientSize()
        wm, hm = self.GetSizer().CalcMin()
        parent.SetClientSize((max(w, wm), max(h, hm)))



class SnapshotDialog(wx.Dialog):
    def __init__(self, parent, **kwargs):
        wx.Dialog.__init__(self, parent, -1, _("Create Snapshot"),
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        self.snapshot = SnapshotGenerator(**kwargs)
        

    def ShowModal(self):
        view = self.snapshot.constitute()(self)
        size = view.GetBestSize()
        self.SetClientSize(size)
        return wx.Dialog.ShowModal(self)



    
