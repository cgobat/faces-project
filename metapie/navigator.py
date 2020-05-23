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


from builtins import str
from builtins import object
SIBLING_ABOVE = 1
SIBLING_BELOW = 2


class Model(object):
    #__title__ = None
    #__bitmap__ = None
    
    
    def register(self):
        abstract


    def accept_sibling(self, sibling):
        return False



class View(object):
    #__title__ = None
    #__bitmap__ = None
    #__height__ = None


    def accept_sibling(self, sibling):
        """
        Called by the controller, to ask if a view
        accepts a sibling beside itself.
        Return Values:
        False: I do not accept the sibling (the sibling will be also asked)
        SIBLING_BELOW: the sibling should appear below me with a sash between us
        SIBLING_ABOVE: dito but above
        """
        return False


    def is_visible(self):
        return self.IsShown() and self.GetParent().IsShown()


    def become_visible(self):
        """
        This function is called, when the view is about to become visible
        """


def get_title(obj):
    title = getattr(obj, "__title__", None)
    if not title:
        title = str(obj)
    elif callable(title):
        title = title()
        
    return title


def get_height(obj):
    height = getattr(obj, "__height__", None)
    if callable(height):
        height = height()

    return height



def get_bitmap(obj):
    bitmap = getattr(obj, "__bitmap__", None)
    if not bitmap: 
        return None
    elif callable(bitmap):
        bitmap = bitmap()

    return bitmap
