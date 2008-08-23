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

import metapie
import navigator
import dblayout
import sys


##class _MetaBrowser(dblayout._MetaModel):
##    def __init__(cls, name, bases, dict_):
##        if cls._contained_:
##            dblayout.Relation("",
##                     dblayout.End(cls._contained_, "objects", multi='*'),
##                     dblayout.End(cls))
##            metapie._browsers_.append(cls)

##        super(_MetaBrowser, cls).__init__(name, bases, dict_)
##        cls.set_instance(cls())

           
##class Browser(dblayout.Model):
##    __metaclass__ = _MetaBrowser
##    __bitmap__ = "browse.gif"
##    _contained_ = None # the contained class (to be set by subclass)
##    _keys_ = None # keys of _contained_ (to be set by subclass)


##    def __str__(self):
##        #return self._contained_.__name__
##        return self.__class__.__name__
        

##    def insert(self, obj):
##        self.objects.insert(obj)


##    def search(self, query, sort=None):
##        return self.objects.search(query, sort)


##    def __len__(self): return len(self.objects)
##    def __iter__(self): return iter(self.objects)
##    def __contains__(self, y): return y in self.objects
##    def __iter__(self): return iter(self.objects)
##    def __getitem__(self, idx): return self.objects[idx]
##    def __delitem__(self, obj): del self.objects[obj]

##    def set_instance(cls, instance): 
##        cls.instance = instance

##    set_instance = classmethod(set_instance)
    

class Browsers(navigator.Model):
    def __init__(self):
        for b in metapie._browsers_:
            setattr(self, b.__name__, b.instance)


    def __str__(self):
        return "Browsers"


    def register(self):
        ctrl = metapie.controller()

        for b in metapie._browsers_:
            browser = b.instance
           
            ctrl.register_view(self,
                               navigator.get_title(browser),
                               browser.constitute("BrowserView"),
                               navigator.get_bitmap(browser))


    def accept_sibling(self, sibling):
        return navigator.SIBLING_BELOW


class _MetaBrowser(type):
    def __init__(cls, name, bases, dict_):
        super(_MetaBrowser, cls).__init__(name, bases, dict_)

        if cls._contained_:
            class _Browser(dblayout.Model): 
                def insert(self, obj): self.objects.insert(obj)
                def search(self, query, sort=None): 
                    return self.objects.search(query, sort)

                def __len__(self): return len(self.objects)
                def __iter__(self): return iter(self.objects)
                def __contains__(self, y): return y in self.objects
                def __iter__(self): return iter(self.objects)
                def __getitem__(self, key): return self.objects[key]
                def __delitem__(self, obj): del self.objects[obj]


            #convert to a top level class that can be pickled
            _Browser.__name__ = name + "_browser_"
            setattr(sys.modules[cls.__module__], _Browser.__name__, _Browser)

            dblayout.Relation("",
                     dblayout.End(cls._contained_, "objects", multi='*'),
                     dblayout.End(_Browser))
            metapie._browsers_.append(cls)
            cls.set_instance(_Browser())


    def set_instance(cls, instance): 
        cls.instance = instance


    def __getattr__(cls, name):
        return getattr(cls.instance, name)


    def __str__(cls):
        return cls.__name__


    def __len__(cls): return len(cls.instance)
    def __iter__(cls): return iter(cls.instance)
    def __contains__(cls, y): return y in cls.instance
    def __iter__(cls): return iter(cls.instance)
    def __getitem__(cls, key): return cls.instance[key]
    def __delitem__(cls, obj): del cls.instance[obj]

           
class Browser:
    __metaclass__ = _MetaBrowser
    __bitmap__ = "browse.gif"
    _contained_ = None # the contained class (to be set by subclass)
    _keys_ = None # keys of _contained_ (to be set by subclass)


        



    




