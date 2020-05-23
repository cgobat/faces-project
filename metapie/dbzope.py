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
DBObject for the ZODB
"""
from __future__ import absolute_import

from builtins import str
from builtins import object
from ZODB import FileStorage, DB
from BTrees import OOBTree
from BTrees.IOBTree import IOBTree, multiunion
from BTrees.IFBTree import intersection
from BTrees.OIBTree import OIBTree
import BTrees.Length
import BTrees.IIBTree as iib
import transaction
import persistent
import metapie
from . import peer
import time


class Database(DB):
    def __init__(self, storage, dbname="application"):
        DB.__init__(self, storage)
        self.connection = self.open()
        dbroot = self.connection.root()
                
        self.application = dbroot.setdefault(dbname, OOBTree.OOBTree())
        IdGenerator.instance = dbroot.setdefault("ids", IdGenerator())


    def make_entrance(self, entrance_class):
        entrance = self.application.get("entrance", None)
        if not entrance:
            entrance = self.application["entrance"] = entrance_class()
            transaction.commit()

        entrance.set_instance()
        return entrance



class FileDatabase(Database):
    def __init__(self, filename, dbname="application"):
        Database.__init__(self, FileStorage.FileStorage(filename), dbname)


class _ResultSet(object):
    """Lazily accessed set of objects."""

    def __init__(self, uids, uidutil):
        self.uids = uids
        self.uidutil = uidutil


    def __len__(self):
        return len(self.uids)


    def __delitem__(self, imodel):
        try:
            self.uids.remove(imodel.id())
        except AttributeError:
            #make mutable
            self.uids = multiunion(self.uids)
            self.uids.remove(imodel.id())


    def __getitem__(self, index):
        return self.uidutil[self.uids[index]]


class SetContainer(object):
    """
    SetContainer is like a IITreeSet but
    it support the operators & | -
    """
    
    def __init__(self, set):
        self.set = iib.IISet(set)

    def __and__(self, other):
        return SetContainer(iib.intersection(self.set, other.set))

    def __or__(self, other):
        return SetContainer(iib.union(self.set, other.set))

    def __sub__(self, other):
        return SetContainer(iib.difference(self.set, other.set))

    def __len__(self):
        return len(self.set)

    

    

class Container(persistent.Persistent, peer.Peer):
    def __init__(self, imodel, peer_class, name_to_me, name_to_peer, index):
        self._container = IOBTree()
        self._imodel = imodel
        self._peer_class = peer_class
        self._name_to_me = name_to_me
        self._name_to_peer = name_to_peer
        self._keys = {}
        self._length = BTrees.Length.Length()
        
        if index:
            prop_to_attrib = dict([(kv[1]._get_value, kv[1]) for kv in iter(peer_class.__attributes_map__.items())])
            
            for attrib, index_type in index:
                if isinstance(attrib, property):
                    attrib = prop_to_attrib[attrib.fget].name

                self._keys[attrib] = index_type()
                setattr(self, attrib, self._keys[attrib])


    def check_peer(self, imodel):
        if not isinstance(imodel, self._peer_class):
            raise ValueError("'%s' is not of type '%s'"%
                             (str(obj), self.contained_class.__name__))


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
        if obj.id() in self._container:
            self._remove_from_index(obj)
            self._add_to_index(obj)
            return True

        return False


    def sequence(self):
        return _ResultSet(list(self._container.keys()), self._container)


    def subset(self, idset):
        try:
            idset = idset.set
        except ttributeError: pass
        return _ResultSet(idset, self._container)


    def __bool__(self): return self._length() > 0
    def __len__(self): return self._length()
    def __iter__(self): return iter(self._container.values())
    def __contains__(self, y): return y.id() in self._container
    def __getitem__(self, key): return self._container[key]
    def __delitem__(self, imodel): self.delete(imodel)


    def _insert_item(self, obj):
        id_ = obj.id()
        if id_ in self._container:
            return False

        self._length.change(1)
        self._container.insert(id_, obj)
        self._add_to_index(obj)
        return True


    def _del_item(self, obj):
        id_ = obj.id()
        if id_ not in self._container:
            return False

        self._length.change(-1)
        del self._container[id_]
        self._remove_from_index(obj)
        return True


    def _add_to_index(self, obj):
        id_ = obj.id()
        for k, v in self._keys.items():
            v.index_id(id_, getattr(obj, k))


    def _remove_from_index(self, obj):
        id_ = obj.id()
        for v in list(self._keys.values()):
            v.unindex_id(id_)


class IdGenerator(persistent.Persistent):
    instance = None

    def get_id(cls, type="default"):
        if not cls.instance: cls.instance = cls()

        counter = getattr(cls.instance, type, 0)
        setattr(cls.instance, type, counter + 1)
        transaction.commit()
        return counter

    get_id = classmethod(get_id)
        


class _PersistentBase(persistent.Persistent, object):
    __id_type__ = None
    
    def __init__(self):
        #generate a unique long lasting id
        self.__id = IdGenerator.get_id(self.__id_type__ \
                                       or self.__class__.__name__)
        #self.__id = int(time.time()) % 100000 + (id(self) % 10000) * 100000
      

    def id(self): return self.__id
    
metapie._init_db_module("zodb", _PersistentBase, Container, transaction.commit)

from .dblayout import *

