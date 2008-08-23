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

import os as _os
import faces

_is_source_ = False

try:
    #install the cache in a permanent module
    _cache = faces._clocking_cache
except AttributeError:
    _cache = faces._clocking_cache = {}


def generate(filename, project):
    cf = open(filename, "w")
    for r in project.all_resources():
        print >> cf, r.name

    print >> cf
    
    for t in project:
        if t.booked_resource:
            print >> cf, t._idendity_()
        
    cf.close()


def read(path, extension="", clear_cache=False):
    if _cache.has_key(path):
        if clear_cache: del _cache[path]
        else: return _cache[path]

    result = ""
    
    try:
        files = _os.listdir(path)
        files = filter(lambda t: t.endswith(extension), files)
        for f in files:
            result += file(_os.path.join(path, f)).read()
    except Exception, e:
        result = file(path).read()

    items = eval("[" + result + "]")
    _cache[path] = items
    return items
        

def clear_cache():
    _cache.clear()
    return True

clear_cache.faces_menu = "clocking/clear cache"


