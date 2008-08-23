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

import datetime
import metapie
import locale
import tools
import weakref
import peer
import events
import sys
from mtransaction import ConstraintError, Transaction

_ = tools.get_gettext()


_id_counter = 0
def _idendity(val): return val

class Type(object):
    readonly = False

    def __init__(self):
        global _id_counter
        _id_counter += 1
        self.__id__ = _id_counter 

    
    def _create(self, model, name):
        self.name = name
        self.model = model

        if self.readonly:
            setattr(model, name, property(self._get_readonly_value))
        else:
            self.private_name = "_" + model.__name__ + "__" + name
            setattr(model, self.private_name, self.default())
            setattr(model, name, property(self._get_value, self._set_value))


    def _set_value(self, imodel, value):
        proxy = Transaction.make_proxy(imodel)
        value = self.convert(value)
        value = getattr(imodel, "_set_" + self.name, _idendity)(value)
        setattr(proxy, self.private_name, value)

        try:
            proxy.remove_error(self.name)
        except AttributeError:
            pass
        
        imodel.fire(self.name, self.name)
        imodel.fire("default", self.name)

        
    def _get_value(self, imodel):
        proxy = Transaction.get_proxy(imodel)

        try:
            result = getattr(proxy, self.private_name)
        except AttributeError:
            try:
                result = getattr(imodel, self.private_name)
            except AttributeError:
                #this can only happen after a ODB schema change
                result = self.default()

        return getattr(imodel, "_get_" + self.name, _idendity)(result)


    def _get_readonly_value(self, imodel):
        return getattr(imodel, "_get_" + self.name)()


    def __value_tuple__(self, imodel):
        return getattr(imodel, self.name)
    

    def convert(self, value):
        return value
    

    def _commit_value(self, obj, proxy):
        raise RuntimeError("abstract")


    def _rollback_value(self, obj, proxy):
        pass


    def default(self):
        return None


    def width_format(self):
        """
        The result is used to calculate the with of
        editor widgets, row columns etc.
        should return a string, that is filled
        with the maximal count of an average wide character
        """
        return 'X' * len(self.to_string(self.default()))


    def create_widget(self, parent, name):
        return self._widget_(parent, name)


    def to_string(self, value):
        if value is None: return ""
        return unicode(value)


    def clone(self):
        raise RuntimeError("type cannot be cloned")

        

class AtomType(Type):
    def __init__(self, default=None, readonly=False):
        Type.__init__(self)
        self.defval = default
        self.readonly = readonly


    def default(self):
        return self.defval

        
    def _commit_value(self, imodel, proxy):
        setattr(imodel, self.private_name,
                getattr(proxy, self.private_name))


    def index_clone(self):
        return self.__class__(self.defval)



class Text(AtomType):
    def __init__(self, default="", none=False,
                 multi_line=False, is_password=False,
                 readonly=False):
        AtomType.__init__(self, default, readonly)
        self.multi_line = multi_line
        self.none = none
        self.is_password = is_password


    def index_clone(self):
        return self.__class__(self.defval, self.none,
                              self.multi_line)


    def width_format(self):
        return "XXXXXXXX"



class Int(AtomType):
    def __init__(self, default=0, none=False, readonly=False):
        AtomType.__init__(self, default, readonly)
        self.none = none


    def convert(self, value):
        if value is None: return None
        return int(value)


    def index_clone(self):
        return self.__class__(self.defval, self.none)


    def width_format(self):
        return "0000000000"


class Float(AtomType):
    def __init__(self, default=0.0, width=5, precision=2,
                 none=False, readonly=False):
        AtomType.__init__(self, default, readonly)
        self.width = width
        self.precision = precision
        self.none = none

        
    def to_string(self, value):
        if value is None: return ""
        locale.format("%*.*f", (self.width, self.precision, value), False)
        return str(value)


    def convert(self, value):
        if value is None: return None
        return float(value)


    def index_clone(self):
        return self.__class__(self.defval, self.width,
                              self.precision, self.none)

    def width_format(self):
        return "0" * (self.width + 1)




class Money(AtomType):
    def __init__(self, default=0.0, width=10, none=False, readonly=False):
        AtomType.__init__(self, default, readonly)
        self.none = none
        self.width = width
        

    def to_string(self, value):
        if value is None: return ""
        locale.format("%.2f", value, True)
        return str(value)


    def convert(self, value):
        if value is None: return None
        return float(value)


    def index_clone(self):
        return self.__class__(self.defval, self.none)


    def width_format(self):
        return "0" * (self.width + 1 + self.width / 3) 


class Boolean(AtomType):
    def __init__(self, default=False, none=False, readonly=False):
        AtomType.__init__(self, default, readonly)
        self.none = none
        


class Date(AtomType):
    def __init__(self, default=datetime.date.today(),
                 none=False, readonly=False):
        AtomType.__init__(self, default, readonly)
        self.none = none

    
    def to_string(self, value):
        if value is None: return ""
        try:
            return value.strftime("%x")
        except AttributeError:
            pass


    def index_clone(self):
        return self.__class__(self.defval, self.none)


    def __value_tuple__(self, imodel):
        return getattr(imodel, self.name) or datetime.date.min


    
class Time(AtomType):
    def __init__(self, default=datetime.time(0), none=False,
                 format="HHMMSS", readonly=False):
        AtomType.__init__(self, default, readonly)
        self.none = none
        self.format = format


    def to_string(self, value):
        if value is None: return ""
        try:
            format = { "HHMMSS" : "%H:%M:%S",
                       "HHMM" : "%H:%M" }[self.format]
            return value.strftime(format)
        except AttributeError:
            pass


    def width_format(self):
        return self.format + ":"


    def index_clone(self):
        return self.__class__(self.defval, self.none, self.format)


    def __value_tuple__(self, imodel):
        return getattr(imodel, self.name) or datetime.time.min


class DateTime(AtomType):
    def __init__(self, default=datetime.datetime.today(),
                 none=False, format="HHMM", readonly=False):
        AtomType.__init__(self, default, readonly)
        self.none = none
        self.format = format


    def to_string(self, value):
        if value is None: return ""
        try:
            format = { "HHMMSS" : "%x %H:%M:%S",
                       "HHMM" : "%x %H:%M" }[self.format]
            return value.strftime(format)
        except AttributeError:
            pass


    def index_clone(self):
        return self.__class__(self.defval, self.none, self.format)


    def __value_tuple__(self, imodel):
        return getattr(imodel, self.name) or datetime.datetime.min



class Enumerate(AtomType):
    def __init__(self, choices, default=None, readonly=False):
        AtomType.__init__(self, default, readonly)
        self.choices = choices


    def _set_value(self, obj, value):
        if not self.choices.has_key(value):
            error = ConstraintError()
            msg = _("%(model)s.%(attrib)s must be in "
                    "(%(range)s) but is %(value)s") \
                    % { "model" : obj.__class__.__name__,
                        "attrib" : self.name,
                        "range" : ", ".join(map(str, self.choices)),
                        "value" : str(value) }
            error.message[self.name] = msg
            raise error

        super(Enumerate, self)._set_value(obj, value)


    def default(self):
        try:
            return self.defval or self.choices.keys()[0]
        except IndexError:
            return ""


    def to_string(self, value):
        if value is None: return ""
        try:
            return self.choices[value]
        except KeyError:
            return ""


    def index_clone(self):
        return self.__class__(self.choices, self.defval)


class MultiEnumerate(AtomType):
    def __init__(self, choices, default=None, readonly=False):
        AtomType.__init__(self, default, readonly)
        self.choices = choices


    def _set_value(self, obj, value):
        try:
            valiter = iter(value)
        except TypeError:
            valiter = iter((v, ))
            
        for v in valiter:
            if not self.choices.has_key(v):
                error = ConstraintError()
                msg = _("%(model)s.%(attrib)s must be in "
                        "(%(range)s) but is %(value)s") \
                        % { "model" : obj.__class__.__name__,
                            "attrib" : self.name,
                            "range" : ", ".join(map(str, self.choices)),
                            "value" : str(v) }
                error.message[self.name] = msg
                raise error

        AtomType._set_value(self, obj, tuple(value))


    def default(self):
        return self.defval or ()


    def to_string(self, value):
        if value is None: return ""
        
        try:
            return str([ self.choices[v] for v in value ])
        except KeyError:
            return ""


    def index_clone(self):
        return self.__class__(self.choices, self.defval)

   

class ContainerType(Type):
    __name_view_class__ = "RowView"
    
    def __init__(self, peer_class, name_to_peer, name_to_me, index):
        Type.__init__(self)
        self.peer_class = peer_class
        self.name_to_me = name_to_me
        self.name_to_peer = name_to_peer
        self.index = index
        

    def _set_value(self, obj, value):
        raise AttributeError("'%s' object has readonly attribute '%s'" %
                             (obj.__class__.__name__, self.name_to_peer))


    def _get_value(self, imodel):
        proxy = Transaction.make_proxy(imodel)
        
        container = getattr(imodel, self.private_name, None)
        if container is None:
            container = metapie.Container(imodel, self.peer_class,
                                          self.name_to_me,
                                          self.name_to_peer,
                                          self.index)
            setattr(imodel, self.private_name, container)

        if proxy is imodel: return container

        pcontainer = getattr(proxy, self.private_name, None)
        if pcontainer is None:
            pcontainer = Transaction.ContainerProxy(container)
            setattr(proxy, self.private_name, pcontainer)

        return pcontainer


    def __value_tuple__(self, imodel):
        container = getattr(imodel, self.name)
        return tuple(map(lambda c: c.__value_tuple__(), container))
        

    def _commit_value(self, imodel, proxy):
        container = getattr(proxy, self.private_name)
        container.commit()


    def _rollback_value(self, obj, proxy):
        container = getattr(proxy, self.private_name)
        container.rollback()
                                    

    def default(self):
        return None
    

class ReferenceType(Type, peer.Peer):
    def __init__(self, peer_class, name_to_peer, name_to_me, none):
        Type.__init__(self)
        self._peer_class = peer_class
        self._name_to_peer = name_to_peer
        self._name_to_me = name_to_me
        self.none = none


    def _set_value(self, imodel, value):
        peer = self._get_value(imodel)
        Type._set_value(self, imodel, value)
        
        if value is not peer:
            #add peer to transaction
            try:
                tr = Transaction.get_transaction(imodel)
            except RuntimeError:
                def mark(obj): pass
            else:
                def mark(obj): Transaction.mark_imodel(obj, tr)
            
            if peer:
                mark(peer)
                self._remove_from_peer(peer, imodel)

            if value:
                mark(value)
                self._add_to_peer(value, imodel)


    def __value_tuple__(self, imodel):
        return id(getattr(imodel, self.name))


    def _commit_value(self, imodel, proxy):
        try:
            setattr(imodel, self.private_name,
                    getattr(proxy, self.private_name))
        except AttributeError:
            pass


class _ModelType(AtomType):
    __name_view_class__ = "FormView"
    
    def _get_readonly_value(self, imodel):
        result = getattr(imodel, "_get_" + self.name)()

        proxy = Transaction.get_proxy(imodel)
        try:
            tr = proxy._transaction()
        except AttributeError:
            pass
        else:
            Transaction.mark_imodel(result, weakref.proxy(tr))

        return result


    def _get_value(self, imodel):
        proxy = Transaction.get_proxy(imodel)
        try:
            result = getattr(proxy, self.private_name)
        except AttributeError:
            result = getattr(imodel, self.private_name)

        if result is None: return result
        if result is 1:
            result = self.peer_model(**self.default_args)
            setattr(proxy, self.private_name, result)
            setattr(imodel, self.private_name, result)

        result = getattr(imodel, "_get_" + self.name, _idendity)(result)
        try:
            tr = proxy._transaction()
        except AttributeError:
            pass
        else:
            Transaction.mark_imodel(result, weakref.proxy(tr))

        return result


    def _set_value(self, imodel, value):
        old_value = self._get_value(imodel)
        if value is not old_value:
            Transaction.remove_proxy(old_value)
        super(_ModelType, self)._set_value(imodel, value)


    def __value_tuple__(self, imodel):
        return getattr(imodel, self.name).__value_tuple__()



class _Model(metapie.PersistentBase):
    __attributes_map__ = {}
    __attributes_tuple__ = ()

    def __init__(self):
        metapie.PersistentBase.__init__(self)


class _MetaModel(type):
    def __init__(cls, name, bases, dict_):
        super(_MetaModel, cls).__init__(name, bases, dict_)
        cls._collect_attributes()


    def _collect_attributes(cls):
        cls.__attributes_map__ = {}
        
        for b in cls.__bases__:
            if issubclass(b, _Model):
                cls.__attributes_map__.update(b.__attributes_map__)

        attribs = []
        for k, v in cls.__dict__.iteritems():
            if isinstance(v, Type):
                cls.__attributes_map__[k] = v
                attribs.append((k, v))

        for (k, v) in attribs:
            v._create(cls, k)

        ao = map(lambda a: (a.__id__, a), cls.__attributes_map__.values())
        ao.sort()
        cls.__attributes_tuple__ = tuple(map(lambda a: a[1], ao))


    def index(cls):
        return cls._Index_()
        

    def type(cls, none=False, readonly=False, default_args={}):
        class ModelType(_ModelType):
            peer_model = cls
            
            def __init__(self):
                _ModelType.__init__(self, readonly=readonly)
                self.none = none
                self.default_args = default_args

            def default(self):
                return default_args is not None and 1 or None

        return ModelType()



class Model(_Model, events.Subject):
    __metaclass__ = _MetaModel

    def __init__(self, **kwargs):
        super(Model, self).__init__()
        self.set(**kwargs)


    def __cmp__(self, other):
        try:
            other_value = other.__value_tuple__()
        except AttributeError:
            other_value = other
        
        return cmp(self.__value_tuple__(), other_value)


    def __value_tuple__(self):
        return tuple(map(lambda a: a.__value_tuple__(self),
                         self.__attributes_tuple__))
            

    def set(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)


    def reindex(self):
        """
        reindex the model in all containers
        """
        for k, v in self.__attributes_map__.iteritems():
            value = getattr(self, k)
            try:
                getattr(value, v._name_to_me).recatalog(self)
            except AttributeError:
                pass

        try:
            collector = self.__collector__
        except AttributeError:
            return

        if not collector.data.recatalog(self):
            collecotr.data.insert(self)
        

    def check_constraints(self):
        pass
    

    def constitute(self, nview="default", name_view_class="FormView"):
        view = self.get_view(nview, name_view_class)
        def factory(*args, **kwargs):
            iview = view(*args, **kwargs)
            iview.constitute(self)
            return iview

        return factory


    def get_view(cls, nview, name_view_class=""):
        try:
            return cls._views_[nview]
        except KeyError, e:
            view = metapie.build_view(cls, nview, name_view_class)
            if view: return view
            #find first view with same class
            for v in cls._views_.itervalues():
                if v.__name_view_class__ == name_view_class:
                    return v
            
            raise e
        except AttributeError, e:
            view = metapie.build_view(cls, nview, name_view_class)
            if view: return view
            raise e
            

    get_view = classmethod(get_view)



class _MetaModelCollector(_MetaModel):
    def __init__(cls, name, bases, dict_):
        super(_MetaModelCollector, cls).__init__(name, bases, dict_)

        if not cls.__model__: return

        container = ContainerType(cls.__model__, "data", None, cls.__index__)
        container._create(cls, "data")
        cls.__attributes_map__["data"] = container
        cls.__attributes_tuple__ += ( container, )
        cls.__model__.__collector__ = cls


class ModelCollector(Model):
    __metaclass__ = _MetaModelCollector
    __index__ = None
    __model__ = None

    def set_instance(self):
        self.__model__.__collector__ = self


    def __getattr__(self, name):
        return getattr(self.data, name)


class Entrance(Model):
    def set_instance(self):
        self.__class__.instance = self
        for t in self.__attributes_tuple__:
            collector = getattr(self, t.name)
            try:
                collector.set_instance()
            except AttributeError: pass


class Relation(object):
    def __init__(self, name, end1, end2):
        self.name = name
        self.__set_attribs(end1, end2)
        self.__set_attribs(end2, end1)


    def __set_attribs(self, from_, to_):
        if not to_.name or not to_.multiplicity:
            return

        ref_obj = None
        if to_.multiplicity == 1:
            ref_obj = ReferenceType(to_.class_, to_.name,
                                    from_.name, to_.none)
        else:
            ref_obj = ContainerType(to_.class_, to_.name, from_.name, to_.index)

        ref_obj._create(from_.class_, to_.name)
        from_.class_.__attributes_map__[to_.name] = ref_obj
        from_.class_.__attributes_tuple__ += ( ref_obj, )
        


class End(object):
    def __init__(self, class_, name=None, none=False, **kwargs):
        self.class_ = class_
        self.name = name
        self.none = none
        self.multiplicity = 1
        
        for i in ["multiplicity", "multi"]:
            self.multiplicity = kwargs.get(i, self.multiplicity)

        self.index = kwargs.get("index", None)

        if not name and (self.multiplicity == '*' or self.index):
            raise ValueError("A multiplicity of '*' needs a role name")


