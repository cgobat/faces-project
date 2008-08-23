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

"""
metapie
-------
an application framework based on wxpython

"""

__version__ = "0.3.1"

dbmodule = None
_dbcommit = None
PersistentBase = None
Container = None

def _init_db_module(name, persistent_base, container, dbcommit):
    global PersistentBase, Container, dbmodule, _dbcommit

    if dbmodule and dbmodule != name:
        raise ValueError("database module already set to '%s'", dbmodule)

    dbmodule = name
    PersistentBase = persistent_base
    Container = container
    _dbcommit = dbcommit
    

_view_builders = {}
def build_view(cls, nview, name_view_class):
    try:
        return _view_builders[name_view_class](cls, nview)
    except KeyError:
        return None

