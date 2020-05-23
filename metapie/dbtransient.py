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
Objects that will not be persistent
"""
from __future__ import absolute_import
from builtins import str
from builtins import object
import metapie
from . import peer
import bisect

class _ResultSet(object):
    """Lazily accessed set of objects."""

    def __init__(self, uids, uidutil):
        self.uids = uids
        self.uidutil = uidutil


    def __len__(self):
        return len(self.uids)


    def __delitem__(self, imodel):
        try:
            index = self.uids.index(imodel.id())
        except ValueError:
            raise KeyError("model does not exist in container", imodel)
        else:
            del self.uids[index]
        

    def __getitem__(self, index):
        return self.uidutil[self.uids[index]]


    
class FieldIndex(object):
    def __init__(self):
        self.index = []


    def index_id(self, docid, value):
        bisect.insort_right(self.index, (value, docid))


    def unindex_id(self, docid):
        pos = 0
        while pos < len(self.index):
            if self.index[pos][1] == docid:
                del self.index[pos]
            else:
                pos += 1


    def apply(self, min, max=None, excludemin=False, excludemax=False):
        pos = bisect.bisect_right(self.index, (min, 0))

        if excludemin:
            while pos < len(self.index):
                value, docid = self.index[pos]
                if value != min: break
                pos += 1

        def all_keys():
            while pos < len(self.index):
                value, docid = self.index[pos]
                if max:
                    if excludemax and value == max: break
                    if value > max: break

                yield docid
                pos += 1

        return list(all_keys())


class Container(peer.Peer):
    def __init__(self, imodel, peer_class, name_to_me, name_to_peer, index):
        self._container = {}
        self._imodel = imodel
        self._peer_class = peer_class
        self._name_to_me = name_to_me
        self._name_to_peer = name_to_peer
        

    def check_peer(self, imodel):
        if not isinstance(imodel, self._peer_class):
            raise ValueError("'%s' is not of type '%s'"%
                             (str(imodel), self.contained_class.__name__))


    def fire(self):
        self._imodel.fire(self._name_to_peer, self._name_to_peer)
        self._imodel.fire("default", self._name_to_peer)
        

    def insert(self, imodel, fire=True):
        self.check_peer(imodel)
        if self._insert_item(imodel):
            self._add_to_peer(imodel, self._imodel)
            if fire: self.fire()


    def delete(self, imodel, fire=True):
        if self._del_item(imodel):
            self._remove_from_peer(imodel, self._imodel)
            if fire: self.fire()
        else:
            raise KeyError("model does not exist in container", imodel)


    def recatalog(self, obj):
        return False


    def sequence(self):
        keys = list(self._container.keys())
        keys.sort()
        return _ResultSet(keys, self._container)


    def __bool__(self): return len(self._container) > 0
    def __len__(self): return len(self._container)
    def __iter__(self): return iter(self._container.values())
    def __contains__(self, imodel): return imodel.id() in self._container
    def __getitem__(self, key): return self._container[key]
    def __delitem__(self, imodel): self.delete(imodel)


    def _insert_item(self, imodel):
        if imodel.id() not in self._container:
            self._container[imodel.id()] = imodel
            return True
        
        return False


    def _del_item(self, imodel):
        try:
            del self._container[imodel.id()]
        except KeyError:
            return False

        return True


class IdGenerator(object):
    instance = None

    def get_id(cls, type="default"):
        if not cls.instance: cls.instance = cls()
        counter = getattr(cls.instance, type, 0)
        setattr(cls.instance, type, counter + 1)
        return counter

    get_id = classmethod(get_id)

    

class _PersistentBase(object):
    __id_type__ = None
    
    def __init__(self):
        #generate a unique long lasting id
        self.__id = IdGenerator.get_id(self.__id_type__ \
                                       or self.__class__.__name__)
        #self.__id = int(time.time()) % 100000 + (id(self) % 10000) * 100000

    
    def id(self): return self.__id
    
def _commitdumy(): pass
metapie._init_db_module("transient", _PersistentBase, Container, _commitdumy)

from .dblayout import *

