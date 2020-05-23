#! /usr/bin/python

## depreceated!! (use dbzope)

from __future__ import print_function
from __future__ import division
from builtins import str
from builtins import range
from past.utils import old_div
from builtins import object
import datetime
import sys
import types
import string

from BTrees import OOBTree
import persistent
from zope.index import field
#from BTrees.IFBTree import IFSet, weightedIntersection


class ValidationError(Exception):
    def __init__(self, errors):
        self.errors = errors


    def __str__(self):
        return "ValidationError:" + str(self.errors)
#\
               #string.join("\n", [repr(e) for e in self.errors.values() ])
    


class ConstraintError(Exception): pass
        


class ContainerAttribute(Attribute):
    def __init__(self, peer_class, name_to_me, keys=None):
        self.peer_class = peer_class
        self.name_to_me = name_to_me
        self.keys = keys
    
    def create(self, parent):
        return Container(parent, self.peer_class, self.name_to_me, self.keys)
    

class _MPeerOperation(object):
    def remove_from_peer(self, peer, parent):
        if not self.name_to_me:
            return
            
        peer_end = getattr(peer, self.name_to_me)
        if isinstance(peer_end, Container):
            peer_end._del_item(parent)
        else:
            peer._values[self.name_to_me] = None


    def add_to_peer(self, peer, parent):
        peer_end = peer._values[self.name_to_me]
        if isinstance(peer_end, Container):
            peer_end._insert_item(parent)
        else:
            peer._values[self.name_to_me] = parent


class ReferenceAttribute(Attribute, _MPeerOperation):
    def __init__(self, peer_class, name_to_peer, name_to_me):
        self.peer_class = peer_class
        self.name_to_peer = name_to_peer
        self.name_to_me = name_to_me


    def create(self, obj):
        return None


    def convert(self, parent, new_peer):
        if not isinstance(new_peer, (type(None), self.peer_class)):
            raise ValueError("'%s' is not of type '%s'"%
                             (str(new_peer), self.peer_class.__name__))

        old_peer = parent._values[self.name_to_peer]
        if old_peer is new_peer:
            return new_peer
        
        if old_peer:
            self.remove_from_peer(old_peer, parent)
                
        if new_peer:
            self.add_to_peer(new_peer, parent)

        return new_peer
        


class _ResultSet(object):
    """Lazily accessed set of objects."""

    def __init__(self, uids, uidutil):
        self.uids = uids
        self.uidutil = uidutil


    def __len__(self):
        return len(self.uids)


    def __iter__(self):
        for uid in self.uids:
            obj = self.uidutil[uid]
            yield obj



class Container(_MPeerOperation, persistent.Persistent):
    def __init__(self, parent, peer_class, name_to_me, keys=None):
        self.container = OOBTree.OOBTree()
        self.parent = parent
        self.peer_class = peer_class
        self.name_to_me = name_to_me

        self.keys = {}
        if keys:
            self._p_changed = 1
            for k, v in keys.items():
                self.keys[k] = v()


    def insert(self, obj):
        if not isinstance(obj, self.peer_class):
            raise ValueError("'%s' is not of type '%s'"%
                             (str(obj), self.contained_class.__name__))

        if self._insert_item(obj):
            self.add_to_peer(obj, self.parent)


    def search(self, query, sort=None):
        results = []
        for k, v in query.items():
            index = self.keys[k]
            r = index.apply(v)
            if r is None:
                continue
            if not r:
                return _ResultSet(r, self)

            results.append((len(r), r))


        results.sort()
        _, result = results.pop(0)
        for _, r in results:
            _, result = weightedIntersection(result, r)

        if sort:
            if type(sort) == str:
                sort = [ sort ]
            
            s_r = OOBTree.OOBTree()
            for r in result:
                obj = self.container[r]
                val = [obj._values[s] for s in sort]
                s_r[tuple(val)] = obj

            return list(s_r.values())

            
        return _ResultSet(result, self.container)


    def __len__(self): return len(self.container)
    def __iter__(self): return iter(self.container)
    def __contains__(self, y): return y in self.container
    def __iter__(self): return iter(self.container.values())


    def __delitem__(self, id):
        obj = self[id]
        if self._del_item(obj):
            self.remove_from_peer(obj, self.parent)


    def _insert_item(self, obj):
        id_ = id(obj)
        if id_ in self.container:
            return False

        self.container.insert(id(obj), obj)
        self._add_to_index(obj)
        return True


    def _del_item(self, obj):
        if id_ not in self:
            return False
        
        del self.container[id(obj)]
        self._remove_from_index(obj)
        return True


    def _recatalog(self, obj):
        if id(obj) in self:
            self._remove_from_index(obj)
            self._add_to_index(obj)


    def _add_to_index(self, obj):
        id_ = id(obj)
        for k, v in self.keys.items():
            v.index_doc(id_, obj._values[k])


    def _remove_from_index(self, obj):
        id_ = id(obj)
        for v in list(self.keys.values()):
            v.unindex_doc(id_)


class End(object):
    def __init__(self, class_, name=None, **kwargs):
        self.class_ = class_
        self.name = name
        self.multiplicity = 1
        
        for i in ["multiplicity", "multi"]:
            if i in kwargs:
                self.multiplicity = kwargs[i]
        
        self.keys = kwargs.get("keys", None)
        
        if not name and self.multiplicity is None:
            raise ValueError("A multiplicity of None needs a role name")

        if self.keys:
            if self.multiplicity == 1:
                raise ValueError("keys need a multiplicity of None")

            for k in list(self.keys.keys()):
                if not hasattr(class_, k):
                    raise ValueError("class '%s' has no attribute '%s'" %
                                     (class_.__name__, k))
                    

class Relation(object):
    def __init__(self, name, end1, end2):
        self.name = name
        self.__check_name(end1, end2)
        self.__check_name(end2, end1)
        self.__set_attribs(end1, end2)
        self.__set_attribs(end2, end1)


    def __set_attribs(self, from_, to_):
        if not from_.attrib_name:
            return

        ref_obj = None
        if to_.multiplicity == 1:
            ref_obj = ReferenceAttribute(to_.class_,
                                         from_.attrib_name,
                                         to_.attrib_name)
        else:
            ref_obj = ContainerAttribute(to_.class_, to_.attrib_name,
                                         to_.keys)

        setattr(from_.class_, from_.attrib_name, ref_obj)
           

    def __check_name(self, from_, to_):
        name = to_.name
        if not name and from_.keys:
            #if I am indexable I have to keep a reference to my catalog
            name = "_" + self.name + "_" + lower(to_.class_.__name__)

        from_.attrib_name = name





   

#----------------------------------
class LabelMixin(object):
    def add_with_label(self, parent, sizer, widget):
        h, v = self.expand_info()
        
        label = wx.StaticText(parent, -1, self.id)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        hsizer.Add(vsizer, h and 1 or 0, wx.EXPAND)
        vsizer.Add(label, 0, wx.EXPAND)
        vsizer.Add(widget,  v and 1 or 0, wx.EXPAND)
        sizer.Add(hsizer, 1, wx.EXPAND)

        #vsizer.Add(hsizer, v and 1 or 0, wx.EXPAND, 0)
        #hsizer.Add(label, 0, wx.EXPAND)
        #hsizer.Add(widget, h and 1 or 0, wx.EXPAND)
        #sizer.Add(vsizer, 1, wx.EXPAND)

        


class WidgetProxy(object):
    def add_widget(self, parent, sizer):
        return None


    def expand_info(self):
        return (False, False)
    

class ExecButton(WidgetProxy):
    def __init__(self, view, id_, *args):
        self.id = id_
        self.label = id_

        for a in args:
            if isinstance(a, types.FunctionType):
                self.function = a


    def add_widget(self, parent, sizer):
        button = wx.Button(parent, -1, self.label)
        sizer.Add(button, 0, 0)


class CancelButton(ExecButton):
    def __init__(self, view, id_):
        ExecButton.__init__(self, view, id_)



class MultiPanel(WidgetProxy):
    def __init__(self, label, function):
        pass


class AttribProxy(WidgetProxy):
    def __init__(self, view, model, attrib):
        self.id = attrib.id
        self.view = view
        self.model = model
        self.attrib = attrib


class TextProxy(AttribProxy, LabelMixin):
    def add_widget(self, parent, sizer):
        style = 0
        if self.attrib.multi:
            style = wx.TE_MULTILINE

        text = wx.TextCtrl(parent, -1,
                           getattr(self.model, self.id),
                           style=style)

        self.add_with_label(parent, sizer, text)
        
                    
    def expand_info(self):
        return (True, self.attrib.multi)



class MoneyProxy(AttribProxy):
    pass


class DateProxy(AttribProxy):
    pass


class IntProxy(AttribProxy):
    pass


class TableWidget(wx.ListCtrl, wxListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        wxListCtrlAutoWidthMixin.__init__(self)


class ContainerProxy(AttribProxy, LabelMixin):
    def add_widget(self, parent, sizer):
        list_ = TableWidget(parent, -1, style=wx.LC_REPORT \
                            | wx.SUNKEN_BORDER)

        self.add_with_label(parent, sizer, list_)

        
        container = getattr(self.model, self.id)
        assert(isinstance(container, Container))

        elements = container.peer_class._get_view_elements("table_item")

        columns = []
        i = 0
        for e in elements:
            if isinstance(e, Attribute):
                list_.InsertColumn(i, e.id)
                columns.append(e.id)

        i = 0
        for obj in container:
            j = 1
            list_.SetItemData(i, id(obj))
            list_.InsertStringItem(i, str(getattr(obj, columns[0])))
            for c in columns[1:]:
                list_.SetStringItem(i, j, str(getattr(obj, c)))
                j += 1

            i += 1

        
        

    def expand_info(self):
        return (True, True)



class ReferenceProxy(AttribProxy):
    pass


__proxy_registry = { 
    "Text" : TextProxy,
    "Money" : MoneyProxy,
    "Date" : DateProxy,
    "Int" : IntProxy,
    "ContainerAttribute" : ContainerProxy,
    "ReferenceAttribute" : ReferenceProxy
    }


def create_widget_proxi(view, attrib):
    a_n = attrib.__class__.__name__
    v_n = view.name
    m_n = view.model.__class__.__name__
    
    names = [ "%s.%s.%s" % (a_n, v_n, m_n),
              "%s.%s" % (a_n, v_n),
              a_n ]

    for n in names:
        proxy = __proxy_registry.get(n, None)
        if proxy:
            return proxy(view, view.model, attrib)

    raise RuntimeError("proxy not found")
    
    

class _View(object):
    def __init__(self, name, model, elements):
        self.name = name
        self.model = model
        self.elements = elements


    def compile(self, parent, cols=2):
        controls = []
        buttons = []

        # build proxys and separate buttons from other controls
        for e in self.elements:
            if isinstance(e, Attribute):
                proxy = create_widget_proxi(self, e)
            else:
                assert(isinstance(e, (tuple, list)))
                proxy = e[0](self, *e[1:])

            if isinstance(proxy, ExecButton):
                buttons.append(proxy)
            else:
                controls.append(proxy)

            setattr(self, proxy.id, proxy)

        rows = old_div(len(controls), cols)
        if len(controls) % cols:
            rows += 1
            
        sizer = wx.FlexGridSizer(rows, cols, 10, 10)
                
        if buttons:
            ctrl_parent = wxScrolledPanel(parent,
                                          style=wx.TAB_TRAVERSAL \
                                          | wx.SUNKEN_BORDER)
            ctrl_parent.SetSizer(sizer)
            
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            button_sizer.Add((10, 1), 1, 0)
            buttons[0].add_widget(parent, button_sizer)
            for b in buttons[1:]:
                button_sizer.Add((10, 1), 0, 0)
                b.add_widget(parent, button_sizer)

            outer_sizer = wx.BoxSizer(wx.VERTICAL)
            outer_sizer.Add(ctrl_parent, 1, wx.EXPAND)
            outer_sizer.Add((1, 10), 0, 0)
            outer_sizer.Add(button_sizer, 0, wx.EXPAND)
            parent.SetSizer(outer_sizer)
        else:
            ctrl_parent = parent
            parent.SetSizer(sizer)


        col = 0
        row = 0
        growable_rows = { }
        growable_cols = { }
        for c in controls:
            c.add_widget(ctrl_parent, sizer)
            h, v = c.expand_info()

            print("expand", c.id, v, col, row)
            if h:
                growable_cols[col] = True

            if v:
                growable_rows[row] = True

            col += 1
            if col >= cols:
                col = 0
                row += 1

        print("growable_rows", growable_rows)
        for r in list(growable_rows.keys()):
            sizer.AddGrowableRow(r)

        for c in list(growable_cols.keys()):
            sizer.AddGrowableCol(c)

        if buttons:
            ctrl_parent.SetupScrolling()

        parent.Layout()
            
        
    


#-----------------------------------------------------------
    
class Supplier(Model):
    name = Text()
    address = Text(multi=True)
    street = Text()
    zip_code = Text(min_=5, max_=5)
    city = Text()


    def method1(self, a=""):
        "meth"
        
        return "testmethod"

    method1.result = Text()
    method1.a = Text()

    def constraints():
        Constraint("name_test", name or address == "empty")
        Constraint("zip_test",
                   zip_code == "12345" and city == "munich" 
                   or zip_code != "12345")
                 

    def views():
        View("_default",
             name,
             address,
             street,
             zip_code,
             #(Table, batches, "table_item"),
             (ExecButton, "save", Supplier.set),
             (CancelButton, "cancel")
             )

        View("all",
             name,
             address,
             street,
             zip_code,
             (MultiPanel, batches, "edit_item"),
             (ExecButton, "save", Supplier.set),
             (CancelButton, "cancel")
             )

        ##View("method",
##             Supplier.method1.a,
##             (ExecButton, "start", Supplier.method1),
##             (CancelButton),
##             )
        
        View("table_item",
             name,
             address,
             zip_code)
             

    

class Article(Model):
    category = Text(min_=1, max_=60)
    attributes = Text()
    description = Text()
    

class Batch(Model):
    size = Text()
    brutto = Money()
    netto = Money()
    receipt_date = Date()
    receipt_count = Int(min_=1)
    count = Int(min_=0)
    labels = Int(min_=0)


class SubSupplier(Supplier):
    name2 = Text()



Relation("supplier_batches",
         End(Supplier, "supplier", multiplicity=1),
         End(Batch, "batches",
             multiplicity=None,
             keys={"brutto" : field.index.FieldIndex,
                   "netto" : field.index.FieldIndex }))


Relation("article_batches",
         End(Article, "article", multiplicity=1),
         End(Batch, "batches", multiplicity=None))#, keys={"size" : FieldIndex}))








MetaModel.transform()

storage = FileStorage.FileStorage("test.fs")
db=DB(storage)
conn=db.open()
dbroot = conn.root()


app = dbroot.setdefault("application", OOBTree.OOTreeSet())



if not len(app):
    print("app is empty")
    supp = SubSupplier(name2="n2", name="name1", zip_code="12345", city="munich")

    for i in range(0, 200):
        batch = Batch(size=str(i), brutto=float(i), netto=float(1000 - i))
        supp.batches.insert(batch)
        
    app.insert(supp)
    get_transaction().commit()
    print("name2:",supp.name2)
else:
    print("app is not!! empty")


#app.clear()
#get_transaction().commit()

sup2 = Supplier(name="sup2", zip_code="12345", city="munich")

for k in list(app.keys()):
    print("name:",k.name, len(k.batches), k.batches.name_to_me)

    
    id_ = None
    ba = None

    #result = k.batches.search({"netto": (920, 980),
    #                           "brutto": (50, 100)}, sort=["netto"] )
    for r in k.batches:
        print("search batch", r.brutto, r.size, r.netto, getattr(r, "size"))
    
    
    ##for p, v in k.batches.iteritems():
##        id_ = p
##        ba = v
##        print "batches",p,v.size, id(v.supplier)

##    print "len1",len(k.batches), ba.supplier
##    ba.supplier = sup2
##    #del k.batches[id_]
##    print "len2",len(k.batches), ba.supplier



#supp = SubSupplier(name2="n2", name="test_supp", zip_code="12345", city="munich")
#print supp.name, supp.zip_code


#print supp.method1()

s = list(app.keys())[0]
view = s.get_view()

print(view)

#print super(SubSupplier, supp).__class__.__dict__

frame = wx.Frame(None, -1, "pytest1")

frame.Show()
scw = wxScrolledPanel(frame)

class MyApp(wx.App):
    def OnInit(self):
        return True
        
app = MyApp()
app.SetTopWindow(frame)

view.compile(scw)

#sizer = scw.GetSizer()
#print sizer, sizer.CalcMin()
#scw.EnableScrolling(True, True)
#w, h = sizer.CalcMin()
#scw.SetScrollbars(10, 10, w, h)
#scw.SetVirtualSize((200, 500))
#
#scw.FitInside()
#scw.SetupScrolling()
#scw.SetScrollRate(20, 20)
#scw.SetVirtualSize( (200, 500) )
#scw.SetVirtualSizeHints( 500, 500 )

#wx.StaticText(scw, -1, "lll")

print(scw.GetVirtualSize())
print(scw.GetScrollPixelsPerUnit())


frame.FitInside()

app.MainLoop()




