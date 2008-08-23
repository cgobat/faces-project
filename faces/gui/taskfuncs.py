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

import faces.plocale
import wx
import faces.plocale

_ = faces.plocale.get_gettext()



_copy_path_menu = None
_copy_name_menu = None

def make_menu_task_clipboard(controller, task, menu=None, pos=20000):
    global _copy_path_menu, _copy_name_menu
    
    path = task.path
    name = task.name
    
    def copy_task_path():
        clipboard = wx.TheClipboard
        clipboard.Open()
        clipboard.SetData(wx.TextDataObject(path))
        clipboard.Close()

    def copy_task_name():
        clipboard = wx.TheClipboard
        clipboard.Open()
        clipboard.SetData(wx.TextDataObject(name))
        clipboard.Close()

    if not menu:
        top = controller.get_top_menu()
        menu = top.make_menu(_("&Edit"), pos=100)
        pos1 = 250
        pos2 = 251
    else:
        pos1 = pos
        pos2 = pos + 1
        
    _copy_path_menu = menu.make_item(0, _("Copy &Path\tCTRL-P"),
                                     copy_task_path, pos=pos1)
    _copy_name_menu = menu.make_item(0, _("Copy &Name\tCTRL-N"),
                                     copy_task_name, pos=pos2)

    
    menu.make_separator(_("Copy &Path"), True)
    menu.make_separator(_("Copy &Name"))


def remove_menu_task_clipboard(controller):
    global _copy_path_menu, _copy_name_menu
    if _copy_path_menu: _copy_path_menu.remove()
    if _copy_name_menu: _copy_name_menu.remove()
    _copy_path_menu = None
    _copy_name_menu = None
        
    
