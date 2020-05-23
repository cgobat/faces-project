from __future__ import absolute_import
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

from builtins import filter
from builtins import str
from builtins import map
from builtins import object
from . import events
import weakref
import metapie

class ConstraintError(ValueError):
    def __init__(self, **kwargs):
        ValueError.__init__(self, "Model constraints are not satisfied")
        self.message = kwargs


class _SequenceProxy(object):
    def __init__(self, proxy, sequence):
        self.proxy = proxy
        self.sequence = sequence
        for im in proxy._removed_imodels.values():
            try:
                del sequence[im]
            except KeyError:
                pass
            

    def __len__(self):
        return len(self.sequence) + len(self.proxy._new_imodels)


    def __delitem__(self, index):
        imodel = self[index]
        del self.proxy[imodel]

        try:
            del self.sequence[imodel]
        except KeyError:
            pass


    def is_dead(self):
        return self.proxy._dead


    def insert(self, imodel):
        self.proxy.insert(imodel)


    def __getitem__(self, index):
        if index >= len(self.sequence):
            return self.proxy._new_imodels[index - len(self.sequence)]

        imodel = self.sequence[index]
        self.proxy.mark(imodel)
        return imodel


class Transaction(events.Subject):
    active_transactions = { }

    class ContainerProxy(object):
        def __init__(self, src):
            self._src = src
            self._dead = False
            self._removed_imodels = {}
            self._new_imodels = []
            self._transaction = Transaction.get_transaction(src._imodel)
            try:
                keys = src._keys
            except AttributeError:
                return

            for k in list(keys.keys()):
                setattr(self, k, getattr(src, k))


        def mark(self, imodel):
            Transaction.mark_imodel(imodel, self._transaction)


        def commit(self):
            self._dead = True
            if not self._removed_imodels and not self._new_imodels: return

            for v in self._removed_imodels.values():
                self._src.delete(v, False)

            for v in self._new_imodels:
                self._src.insert(v, False)


        def rollback(self):
            self._dead = True


        def insert(self, imodel):
            self._src.check_peer(imodel)
            
            if imodel.id() in self._removed_imodels:
                del self._removed_imodels[imodel.id()]
                self._src._add_to_peer(imodel, self._src._imodel)
                self._src.fire()
            elif (imodel not in self._src \
                  and id(imodel) not in list(map(id, self._new_imodels))):
                
                self.mark(imodel)
                self._new_imodels.append(imodel)
                self._src._add_to_peer(imodel, self._src._imodel)
                self._src.fire()


        def delete(self, imodel):
            def exclude_model():
                try:
                    proxy = self._transaction.active_imodels[imodel]
                except KeyError:
                    pass
                else:
                    proxy.rollback(imodel)
                    del self._transaction.active_imodels[imodel]

            if imodel.id() in self._removed_imodels:
                raise KeyError("model does not exist in container", imodel)

            if imodel in self._src:
                exclude_model()
                self._removed_imodels[imodel.id()] = imodel
                self._src._remove_from_peer(imodel, self._src._imodel)
                self._src.fire()
            else:
                try:
                    index = list(map(id, self._new_imodels)).index(id(imodel))
                except ValueError:
                    raise KeyError("model does not exist in container", imodel)
                else:
                    exclude_model()
                    del self._new_imodels[index]
                    self._src.fire()


        def recatalog(self, obj):
            return self._src.recatalog(obj)


        def __delitem__(self, imodel):
            self.delete(imodel)

            
        def __len__(self):
            return len(self._src) \
                   - len(self._removed_imodels) \
                   + len(self._new_imodels)

        
        def __iter__(self):
            return iter(_SequenceProxy(self, self._src.sequence()))


        def subset(self, idset):
            return _SequenceProxy(self, self._src.subset(idset))


        def sequence(self):
            return _SequenceProxy(self, self._src.sequence())

        
        def __contains__(self, imodel):
            id_ = imodel.id()
            if id_ in self._removed_imodels: return False
            return imodel in self._src or imodel in self._new_imodels


        def __getitem__(self, key):
            if key in self._removed_imodels:
                raise KeyError("key does not exist", key)

            try:
                return self._src[key]
            except KeyError:
                for m in self._new_imodels:
                    if m.id() == key: return m

            raise KeyError


    class ModelProxy(object):
        def __init__(self, transaction):
            self._transaction = weakref.ref(transaction)
            self.error = None


        def remove_error(self, attrib):
            try:
                del self.error.message[attrib]
                if not self.error.message: self.error = None
            except AttributeError:
                pass
            except KeyError:
                pass
                

        def rollback(self, imodel):
            for t in imodel.__attributes_map__.values():
                if hasattr(self, t.private_name):
                    t._rollback_value(imodel, self)
                    delattr(self, t.private_name)
                    imodel.fire(t.name, t.name)

            self.error = None


        def commit(self, imodel):
            self.error = None
            
            for t in imodel.__attributes_map__.values():
                try:
                    pname = t.private_name
                except AttributeError:
                    #readonly attributes don't have a private_name
                    return
                
                if hasattr(self, pname):
                    t._commit_value(imodel, self)
                    delattr(self, pname)

            imodel.reindex()
                

    def remove_proxy(cls, imodel):
        try:
            transaction = cls.get_transaction(imodel)
        except RuntimeError:
            return

        del transaction.active_transactions[imodel]
        try:
            del transaction.active_imodels[imodel]
        except KeyError: pass

    remove_proxy = classmethod(remove_proxy)


    def make_proxy(cls, imodel):
        #proxy or transaction
        
        p_or_t = cls.active_transactions.get(imodel)
        try:
            if not p_or_t: return imodel
        except ReferenceError:
            del cls.active_transactions[imodel]
            return imodel
        
        if isinstance(p_or_t, cls.ModelProxy):
            #it is a proxy
            return p_or_t

        #it is a transaction (weakproxy)
        return p_or_t.include(imodel)
        
        
    make_proxy = classmethod(make_proxy)

    def get_proxy(cls, imodel):
        try:
            p_or_t = cls.active_transactions.get(imodel)
            p_or_t.__class__
            
            if isinstance(p_or_t, cls.ModelProxy):
                return p_or_t
        except ReferenceError:
            del cls.active_transactions[imodel]

        return imodel

        
    get_proxy = classmethod(get_proxy)


    def get_transaction(cls, imodel):
        try:
            p_or_t = cls.active_transactions.get(imodel)
            return weakref.proxy(p_or_t._transaction())
        except ReferenceError:
            raise RuntimeError("no active transaction")
        except AttributeError:
            raise RuntimeError("no active transaction")
    
    
    get_transaction = classmethod(get_transaction)


    def mark_imodel(cls, imodel, transaction):
        assert(type(transaction) is weakref.ProxyType)
        try:
            proxy = cls.active_transactions.setdefault(imodel, transaction)
            proxy.__class__ #causes a ReferenceError if it is a broken reference
        except ReferenceError:
            cls.active_transactions[imodel] = transaction

    mark_imodel = classmethod(mark_imodel)


    
    def __init__(self):
        self.active_imodels = { }


    def __del__(self):
        self.destroy()
        

    def include(self, imodel):
        proxy = self.active_transactions.get(imodel, self)
        if proxy._transaction() is not self:
            raise RuntimeError("the object '%s' belongs "\
                               "already to a transaction" % str(imodel))

        if isinstance(proxy, self.ModelProxy):
            #allready included
            return
            
        proxy = self.ModelProxy(self)
        self.active_transactions[imodel] = proxy
        self.active_imodels[imodel] = proxy
        return proxy
        

    def _transaction(self):
        return self

    
    def commit(self):
        #phase one try commit
        commit_ok = True
        for imodel, proxy in self.active_imodels.items():
            try:
                imodel.check_constraints()
            except ConstraintError as e:
                proxy.error = e
                commit_ok = False
            else:
                proxy.error = None
                
        if commit_ok:
            for imodel, proxy in self.active_imodels.items():
                proxy.commit(imodel)

            self.fire("commit", True)
            metapie._dbcommit()
        else:
            self.fire("commit", False)

        return commit_ok


    def get_errors(self):
        result = {}
        for imodel, proxy in self.active_imodels.items():
            try:
                result[imodel] = proxy.error
            except AttributeError:
                pass

        return result
        

    def rollback(self):
        for imodel, proxy in self.active_imodels.items():
            proxy.rollback(imodel)

        self.fire("rollback")


    def destroy(self):
        def is_my_item(item):
            imodel, p_or_t = item
            try:
                t = p_or_t._transaction()
                return t is self or not t
            except ReferenceError:
                return True

        my_models = list(filter(is_my_item, iter(self.active_transactions.items())))

        for k, v in my_models:
            del self.active_transactions[k]
        
        self.active_imodels.clear()
