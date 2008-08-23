#@+leo-ver=4
#@+node:@file gui/editor/observer.py
#@@language python
#@<< Copyright >>
#@+node:<< Copyright >>
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

#@-node:<< Copyright >>
#@nl
"""
A collection of functions for editing tasks and their attributes
"""
#@<< Imports >>
#@+node:<< Imports >>
import sys
import inspect
import faces.plocale
import faces.task as ftask
import faces.observer as fobserver
import matplotlib.font_manager as fm
import metapie.gui.pyeditor as pyeditor
import docparser
from metapie.gui.controller import ResourceManager
from attribedit import *
import editorlib
try:
    set
except NameError:
    from sets import Set as set
#@nonl
#@-node:<< Imports >>
#@nl

_is_source_ = True
_ = faces.plocale.get_gettext()

#@+others
#@+node:class ObserverEvaluator
class ObserverEvaluator(object):
    def __init__(self, expression, context):
        vars = { "unify" : lambda *args: ("unify", args),
                 "intersect" : lambda *args: ("intersect", args),
                 "difference" : lambda *args: ("difference", args), }
        try:
            editor = context.code_item.editor
            self.attributes = editor.eval_expression(expression, vars, context)
        except Exception, e:
            self.error = e
                        
        

        
        
#@nonl
#@-node:class ObserverEvaluator
#@+node:Models and Views
#@+node:Property
#@+node:Widgets
#@+node:class BoolEnum
class BoolEnum(BoolEnum):
    __type__ = db.Text
#@nonl
#@-node:class BoolEnum
#@+node:class FamilyCombo
class FamilyCombo(widgets.Combo):
    def __init__(self, *args, **kwargs):
        widgets.Combo.__init__(self, *args, **kwargs)
        names = fm.fontManager.ttfdict.keys()
        names.sort()
        map(self.Append, names)
#@nonl
#@-node:class FamilyCombo
#@+node:class WeightCombo
class WeightCombo(widgets.Combo):
    def __init__(self, *args, **kwargs):
        widgets.Combo.__init__(self, *args, **kwargs)
        choices = map(lambda kv: (kv[1], kv[0]), fm.weight_dict.items())
        choices.sort()
        map(self.Append, map(lambda vk: vk[1], choices))
#@nonl
#@-node:class WeightCombo
#@+node:class SizeCombo
class SizeCombo(widgets.Combo):
    def __init__(self, *args, **kwargs):
        widgets.Combo.__init__(self, *args, **kwargs)
        choices = map(lambda kv: (kv[1], kv[0]), fm.font_scalings.items())
        choices.sort()
        map(self.Append, map(lambda vk: vk[1], choices))
#@nonl
#@-node:class SizeCombo
#@+node:class VariantEnum
class VariantEnum(widgets.Enumerate):
    __type__ = db.Text
    
    def get_choices(self, itype):
        return { "capitals" : "capitals",
                 "small-caps" : "small-caps",
                 "normal" : "normal" }
#@nonl
#@-node:class VariantEnum
#@+node:class LinestyleEnum
class LinestyleEnum(widgets.Enumerate):
    __type__ = db.Text
    
    def get_choices(self, itype):
        return { "solid" : "solid",
                 "dashed" : "dashed",
                 "dashdot": "dashdot",
                 "dotted" : "dotted" }
#@nonl
#@-node:class LinestyleEnum
#@+node:class JoinstyleEnum
class JoinstyleEnum(widgets.Enumerate):
    __type__ = db.Text
    
    def get_choices(self, itype):
        return { "miter" : "miter",
                 "round" : "round",
                 "bevel" : "bevel" }
#@nonl
#@-node:class JoinstyleEnum
#@+node:class StyleEnum
class StyleEnum(widgets.Enumerate):
    __type__ = db.Text
    
    def get_choices(self, itype):
        return { "italics" : "italics",
                 "oblique" : "oblique",
                 "normal" : "normal" }
#@nonl
#@-node:class StyleEnum
#@-node:Widgets
#@+node:class Property
class Property(db.Model):
    name_groups = []
    name = db.Text()
    value = db.Text()

    #@    @+others
    #@-others
    def check_constraints(self):
        error = db.ConstraintError()
        try:
            faces.charting.widgets.check_property(self.name, self.value)
        except ValueError, e:
            error = db.ConstraintError()
            error.message["value"] = str(e)
            raise error


    def _set_name(self, name):
        if self.value:
            try:
                faces.charting.widgets.check_property(name, self.value)
                return name
            except ValueError:
                pass

        self.__name = name
        if name.endswith("color"):
            self.value = "white"
        elif name.endswith("fill"):
            self.value = "True"
        elif name.endswith("width"):
            self.value = 1.0
        elif name.endswith("alpha"):
            self.value = 1.0
        elif name.endswith("height"):
            self.value = 4.0
        elif name.endswith("magnification"):
            self.value = 1.0
        elif name.endswith("family"):
            self.value = "sans-serif"
        elif name.endswith("weight"):
            self.value = "normal"
        elif name.endswith("size"):
            self.value = "medium"
        elif name.endswith("variant"):
            self.value = "normal"
        elif name.endswith("antialiased"):
            self.value = "True"
        elif name.endswith("up"):
            self.value = "True"
        elif name.endswith("linestyle"):
            self.value = "solid"
        elif name.endswith("joinstyle"):
            self.value = "miter"
        elif name.endswith("style"):
            self.value = "normal"
        elif name == "tickers":
            self.value = "1, 2"

        return name

    def _set_value(self, val):
        def name_is(*options):
            for o in options:
                if self.name.endswith(o): return True
            return False
        
        if name_is("width", "alpha", "magnification", "height"):
            try:
                val = float(val)
            except ValueError:
                val = 0.0
        elif name_is("fill", "antialiased", "up"):
            if str(val).upper() == "FALSE": val = False
            else: val = bool(val)
        elif name_is("size", "weight"):
            val = str(val)
        elif self.name == "tickers":
            val = str(val).replace("(", "").replace(")", "")
            val = tuple(map(int, val.split(",")))

        return val
    

    def __str__(self):
        def to_float(val):
            try:
                return "%.1f" % float(val)
            except ValueError:
                return "0.0"
            
        def to_string(val): return '"%s"' % val
        def to_int(val):
            try:
                return "%i" % int(val)
            except ValueError:
                return "0"

        def name_is(*options):
            for o in options:
                if self.name.endswith(o): return True
            return False
            
        formater = to_string
        if name_is("width", "alpha", "magnification", "height"):
            formater = to_float
        elif name_is("fill", "antialiased", "up"):
            formater = to_int
        elif self.name == "tickers":
            def formater(val):
                return "(%s, )" % ", ".join(map(str, val))
        elif name_is("size", "weight"):
            try:
                int(self.value)
                formater = to_int
            except ValueError:
                pass

        return '"%s" : %s' % (self.name, formater(self.value))


    def init_groups(cls):
        cls.name_groups = []

    init_groups = classmethod(init_groups)
    
    def fill_gc_group(cls, group):
        styles = ("edgecolor", "linewidth", "linestyle",
                  "antialiased", "alpha", "joinstyle" )

        if group: group += "."
        cls.name_groups.extend(map(lambda s: group + s, styles))


    fill_gc_group = classmethod(fill_gc_group)
                          
    def fill_patch_group(cls, group):
        styles = faces.charting.widgets._PropertyAware.patch_attribs
        cls.name_groups.extend(map(lambda s: group + "." + s, styles))

    fill_patch_group = classmethod(fill_patch_group)


    def fill_font_group(cls, group):
        styles = faces.charting.widgets._PropertyAware.font_attribs
        if group: group += "."
        cls.name_groups.extend(map(lambda s: group + s, styles))
        cls.name_groups.append(group + "color") 

    fill_font_group = classmethod(fill_font_group)


    def apply_groups(cls):
        singulized = dict(zip(cls.name_groups, [0]*len(cls.name_groups)))
        cls.name_groups = singulized.keys()
        cls.name_groups.sort()

    apply_groups = classmethod(apply_groups)
        

    def set_default_groups(cls):
        cls.fill_gc_group("")
        cls.fill_font_group("")
        cls.name_groups.append("fill")
        cls.name_groups.append("facecolor")
        cls.name_groups.append("background.facecolor")
        cls.fill_patch_group("marker")
        cls.fill_patch_group("focused.marker")

    set_default_groups = classmethod(set_default_groups)
#@nonl
#@-node:class Property
#@+node:class PropertySet
class PropertySet(db.Model):
    def __init__(self, code_item, attrib, value):
        super(PropertySet, self).__init__()
        for k, v in (value or {}).iteritems():
            self.properties.insert(Property(name=k, value=v))            
        

    def __str__(self):
        return "{%s}" % ",\n".join(map(str, self.properties))


db.Relation("properies",
            db.End(Property, "properties", multi='*'),
            db.End(PropertySet))
#@nonl
#@-node:class PropertySet
#@+node:class PropertySetView
class PropertySetView(views.FormView):
    __model__ = PropertySet
    __view_name__ = "default"
    vgap = 0
    format = """
properties>
delete
"""
    def create_controls(self):
        self.properties = self.get_control("properties(PropertyGrid)")
        self.delete = self.properties.get_delete_button(self)
    
    def prepare(self):
        self.grow_col(0)
        self.grow_row(0)
#@nonl
#@-node:class PropertySetView
#@+node:class PropertyGrid
class PropertyGrid(grid.EditGrid, views.GridView):
    __model__ = Property
    columns = (("name(Combo)", _("Name")),
               ("value(Changeling)", _("Value")))
    resize_col = 0


    def begin_edit(self, name):
        if name == "name":
            if self.name.GetCount() != len(self.__model__.name_groups):
                self.name.Clear()
                for a in self.__model__.name_groups:
                    self.name.Append(a)
            return
        
        if name == "value":
            if self.imodel.name.endswith("color"):
                self.value.change("Color")
            elif self.imodel.name.endswith("width"):
                self.value.change("Text")
            elif self.imodel.name.endswith("fill"):
                self.value.change("BoolEnum")
            elif self.imodel.name.endswith("family"):
                self.value.change("FamilyCombo")
            elif self.imodel.name.endswith("weight"):
                self.value.change("WeightCombo")
            elif self.imodel.name.endswith("size"):
                self.value.change("SizeCombo")
            elif self.imodel.name.endswith("variant"):
                self.value.change("VariantEnum")
            elif self.imodel.name.endswith("antialiased"):
                self.value.change("BoolEnum")
            elif self.imodel.name.endswith("up"):
                self.value.change("BoolEnum")
            elif self.imodel.name.endswith("linestyle"):
                self.value.change("LinestyleEnum")
            elif self.imodel.name.endswith("joinstyle"):
                self.value.change("JoinstyleEnum")
            elif self.imodel.name.endswith("style"):
                self.value.change("StyleEnum")
            else:
                self.value.change("default")


    def inserted(self, imodel):
        return bool(imodel.name)
#@nonl
#@-node:class PropertyGrid
#@-node:Property
#@+node:Evaluation
#@+node:class Evaluation
class Evaluation(db.Model):
    value = EvaluationNames()
    
    #@    @+others
    #@+node:__init__
    def __init__(self, code_item=None, attrib=None, value=None):
        super(Evaluation, self).__init__()
    
        eval_type = Evaluation.__attributes_map__["value"]
        if attrib:
            eval_type.fill(code_item.editor.model)
            
        if value:
            model = code_item.editor.model
            for name, data in model.evaluations.iteritems():
                if value is data:
                    self.value = name
                    break
        else:
            self.value = eval_type.choices.keys()[0]
    
    #@-node:__init__
    #@+node:__str__
    def __str__(self):
        return self.value
    #@-node:__str__
    #@-others
    
#@nonl
#@-node:class Evaluation
#@+node:class EvaluationView
class EvaluationView(views.FormView):
    __model__ = Evaluation
    __view_name__ = "default"
    vgap = 0
    format = "value"
#@nonl
#@-node:class EvaluationView
#@+node:class EvaluationGrid
class EvaluationGrid(grid.EditGrid, views.GridView):
    __model__ = Evaluation
    columns = (("value", _("Name")),)
    resize_col = 0


#@-node:class EvaluationGrid
#@-node:Evaluation
#@+node:MultiEvaluation
#@+node:class MultiEvaluation
class MultiEvaluation(db.Model):
    """
    An editor for a combination of a modules project data
    """
    operator = db.Enumerate({"unify" : _("Unify"),
                             "intersect" : _("Intersect"),
                             "difference" : _("Difference") },
                            default="unify")
    
    #@    @+others
    #@+node:__init__
    def __init__(self, code_item, attrib, value):
        super(MultiEvaluation, self).__init__()
        Evaluation.__attributes_map__["value"].fill(code_item.editor.model)
        
        if isinstance(value, tuple):
            try:
                self.operator = value[0]
            except db.ConstraintError:
                pass
            else:
                for ed in value[1]:
                    self.evals.insert(Evaluation(code_item=code_item, value=ed))
        elif isinstance(value, ftask._ProjectBase):
            self.evals.insert(Evaluation(code_item=code_item, value=value))
            
        
    #@-node:__init__
    #@+node:__str__
    def __str__(self):
        evals = map(str, self.evals)
        if len(evals) > 1:
            return "%s(%s)" % (self.operator, ", ".join(evals))
        
        if evals:
            return evals[0]
            
        return "()"
    #@-node:__str__
    #@+node:check_constraints
    def check_constraints(self):
        if len(self.evals) == 0:
            error = db.ConstraintError()
            error.message["evals"] = _("You have to input at least one evaluation data.")
            raise error
    #@nonl
    #@-node:check_constraints
    #@-others
    
db.Relation("evals",
            db.End(Evaluation, "evals", multi='*'),
            db.End(MultiEvaluation))
#@nonl
#@-node:class MultiEvaluation
#@+node:class MultiEvaluationView
class MultiEvaluationView(views.FormView):
    __model__ = MultiEvaluation
    __view_name__ = "default"
    vgap = 0
    format = _("""
[Operator:]
operator
(0,3)
[Evaluations:]
evals>
(0,3)
delete
""")

    #@    @+others
    #@+node:create_controls
    def create_controls(self):
        self.evals = self.get_control("evals(EvaluationGrid)")
        self.delete = self.evals.get_delete_button(self)
    #@nonl
    #@-node:create_controls
    #@+node:prepare
    def prepare(self):
        self.grow_col(0)
        self.grow_row(3)
    #@nonl
    #@-node:prepare
    #@-others
#@-node:class MultiEvaluationView
#@-node:MultiEvaluation
#@+node:Column
#@+node:class Column
class Column(db.Model):
    value = db.Text()
    header = db.Text()
    choice = []
#@nonl
#@-node:class Column
#@+node:class ColumnSet
class ColumnSet(SimpleContainer):
    error = db.Text()
    
    #@    @+others
    #@+node:__init__
    def __init__(self, context, attrib_name, data_name):
        editor = context.code_item.editor
        self.attrib_name = attrib_name
        self.code_item = context.code_item
        
        #@    << get the data attribute value >>
        #@+node:<< get the data attribute value >>
        try:
            attribs = editor.eval_expression("evals=%s" % data_name, 
                                             context=context)
            data = attribs["evals"]
            for data_list in data:
                break
                
            if not isinstance(data_list, (list, tuple)):
                data_list = (data_list,)
                
        except Exception, e:
            self.error = "%s: %s" % (e.__class__.__name__, str(e))
            data_list = ()
        #@nonl
        #@-node:<< get the data attribute value >>
        #@nl
        #@    << create the choice list for column values >>
        #@+node:<< create the choice list for column values >>
        Column.choice = []
        self.data_list_len = len(data_list)
        
        for i, c in enumerate(data_list):
            attrlist = self.get_object_attribs(c)
            var_name = self.get_data_var_name(i)
            Column.choice.append(var_name)
            for a in attrlist: 
                Column.choice.append("%s.%s" % (var_name, a))
                
        #@-node:<< create the choice list for column values >>
        #@nl
        
        #@    << get the code_item, that creates the columns >>
        #@+node:<< get the code_item, that creates the columns >>
        self.creator_item = None
        for c in self.code_item.get_children():
            if c.name == attrib_name: 
                self.creator_item = c
                break
        #@nonl
        #@-node:<< get the code_item, that creates the columns >>
        #@nl
        if self.creator_item:
            #@        << get column values >>
            #@+node:<< get column values >>
            start = editor.PositionFromLine(self.creator_item.get_line())
            end = editor.GetLineEndPosition(self.creator_item.get_last_line())
            pos = editor.FindText(start, end, "yield", 0)
            values = editor.get_expression(editor.LineFromPosition(pos))
            values = values[values.index("yield") + 5:].strip()
            try:
                while values[0] in "([" and values[-1] in ")]": 
                    values = values[1:-1].strip()
            except IndexError: pass
            values = [ v.strip() for v in values.split(",") ]
            #@nonl
            #@-node:<< get column values >>
            #@nl
            #@        << get column headers >>
            #@+node:<< get column headers >>
            attribs = editor.get_attribs(self.code_item)
            try:
                headers = editor.get_expression(attribs["headers"])
                headers = editor.eval_expression(headers, context=context)["headers"]
            except KeyError:
                headers = ("",) * len(values)
            
            #@-node:<< get column headers >>
            #@nl
            
            for value, header in zip(values, headers):
                self.columns.insert(Column(value=value.strip(), header=header))
    #@-node:__init__
    #@+node:realize
    def realize(self):
        editor = self.code_item.editor
        columns = [ c for c in self.columns if c.header or c.value ]
        headers = [c.header for c in columns]
        has_headers = bool(filter(bool, headers))
    
        try:
            header_line = editor.get_attribs(self.code_item)["headers"]
        except KeyError:
            header_line = None
        
        if has_headers:
            headers = "headers = (%s)" % ", ".join(['"%s"' % h for h in headers])
            if not header_line:
                editor.insert_expression(self.code_item, headers)
            else:
                editor.replace_expression(headers, header_line)
        elif header_line:
            editor.replace_expression("", header_line)
    
        data_list = ", ".join([ self.get_data_var_name(i) 
                               for i in range(self.data_list_len) ])
        values = [c.value for c in columns]
        maxlen = sum(map(len, values)) + len(values) * 2 + self.code_item.indent + 8
        joiner = maxlen > 80 and ",\n" or ", "
        values = joiner.join(values)
    
        creator_text = "def %s(self, data):\nfor %s in data:\nyield (%s)" \
                        % (self.attrib_name, data_list, values)
          
        if self.creator_item:
            line = self.creator_item.get_line()
            editor.replace_expression(creator_text, line)
        else:
            creator_text = "\n" + creator_text    
            editor.insert_expression(self.code_item, creator_text)
    #@nonl
    #@-node:realize
    #@+node:get_object_attribs
    def get_object_attribs(self, obj):
        try:
            attrlist = obj.__all__
        except AttributeError:
            attrlist = dir(obj)
            
        attrlist = filter(lambda n: n[0] != "_", attrlist)
    
        def make_call(a):
            if callable(getattr(obj, a)):
                return "%s()" % a
            return a
            
        if isinstance(obj, ftask.Task):
            #filter out children
            attrlist = [ a for a in attrlist 
                         if not isinstance(getattr(obj, a), ftask.Task)]
            attrlist = [ make_call(a) for a in attrlist ]
            attrlist += [ "to_string.%s" % a for a in attrlist 
                          if a != "_to_string" and a[-1] != ")" ]
            attrlist.sort()
        else:
            attrlist = [ make_call(a) for a in attrlist ]
        
        return attrlist
    #@nonl
    #@-node:get_object_attribs
    #@-others
    
    def get_data_var_name(self, no):
        if self.data_list_len == 1: return "t"
        return "t%i" % no
        

db.Relation("columns",
            db.End(Column, "columns", multi='*'),
            db.End(ColumnSet))
#@nonl
#@-node:class ColumnSet
#@+node:class ColumnSetView
class ColumnSetView(editorlib.MainView):
    __model__ = ColumnSet
    __view_name__ = "default"
    vgap = 0
    format = """
error(Static)
[Columns:]
columns>
delete
---
(buttons)>
"""
    def create_controls(self):
        self.columns = self.get_control("columns(ColumnGrid)")
        self.delete = self.columns.get_delete_button(self)
    
    def prepare(self):
        self.grow_col(0)
        self.grow_row(1)
        self.buttons.grow_col(0)
        self.error.Hide()
        self.error.SetForegroundColour(self.error_colour)

    def constitute(self, imodel):
        super(ColumnSetView, self).constitute(imodel)
        if imodel.error: self.error.Show()
#@-node:class ColumnSetView
#@+node:class ColumnGrid
class ColumnGrid(grid.EditGrid, views.GridView):
    __model__ = Column
    columns = (("value(auto_tree)", _("Value")),
               ("header", _("Header")))
    resize_col = 0


    def prepare(self, attribute):
        if attribute == "value":
            self.value.fill_tree(Column.choice)
#@nonl
#@-node:class ColumnGrid
#@-node:Column
#@-node:Models and Views
#@+node:Editors
#@+node:class AttributeEditor
class AttributeEditor(AttributeEditor):
    evaluator = ObserverEvaluator
    #@    @+others
    #@+node:apply
    def apply(self, expression, code_item):
        if code_item.obj_type != pyeditor.CLASS: return False
        return super(AttributeEditor, self).apply(expression, code_item)
    #@-node:apply
    #@-others
#@-node:class AttributeEditor
#@+node:class PropertyEditor
class PropertyEditor(AttributeEditor):
    #@    @+others
    #@+node:__init__
    def __init__(self, attrib_name, create_property_groups):
        super(AttributeEditor, self).__init__(attrib_name, PropertySet)
        self.create_property_groups = create_property_groups
    #@-node:__init__
    #@+node:activate
    def activate(self, context):
        """
        activates the editor.
        """
        imodel = super(PropertyEditor, self).activate(context)
        Property.init_groups()
        self.create_property_groups(Property)
        Property.apply_groups()
        return imodel
        
            
    #@-node:activate
    #@-others
#@-node:class PropertyEditor
#@+node:class ColumnEditor
class ColumnEditor(AttributeEditor):
    #@    @+others
    #@+node:__init__
    def __init__(self, attrib_name, data_name):
        self.attrib_name = attrib_name
        self.data_name = data_name
    #@nonl
    #@-node:__init__
    #@+node:apply
    def apply(self, expression, code_item):
        if code_item.obj_type == pyeditor.CLASS:
            if not expression: 
                return self.attrib_name not in map(repr, code_item.get_children())
                                
            return False
            
        if code_item.obj_type == pyeditor.FUNCTION:
            return code_item.name == self.attrib_name
            
        return False    
        
    
    #@-node:apply
    #@+node:activate
    def activate(self, context):
        """
        activates the editor.
        """
        code_item = context.code_item
        if code_item.obj_type == pyeditor.FUNCTION:
            code_item = code_item.get_parent()
    
        imodel = ColumnSet(context, self.attrib_name, self.data_name)
        imodel.show()
        return imodel
        
            
    #@-node:activate
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        if self.attrib_name in map(repr, code_item.get_children()):
            return "edit"
            
        return "add"
    #@nonl
    #@-node:apply_browser_menu
    #@-others
#@nonl
#@-node:class ColumnEditor
#@+node:class ObserverRenamer
class ObserverRenamer(RenameEditor):
    title = _("Rename Observer")
    __icon__ = "rename16"
    
    def correct_code(self, editor):
        pass
    
#@-node:class ObserverRenamer
#@+node:class ObserverRemover
class ObserverRemover(object):
    __icon__ = "delete16"
    
    #@    @+others
    #@+node:apply
    def apply(self, expression, code_item):
        return False
    #@-node:apply
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        return "extra"
    #@-node:apply_browser_menu
    #@+node:activate
    def activate(self, context):
        context.code_item.remove()
    
            
    #@nonl
    #@-node:activate
    #@-others
#@-node:class ObserverRemover
#@+node:ObserverCreator
#@+node:class ObserverCreator
class ObserverCreator(SingletonEditor):
    name = db.Text()
    description = db.Text(multi_line=True)
    data = db.Model.type()
    observer = None
    observer_name = None
    title = _("Create Observer")

    #@    @+others
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        return "create"
    #@nonl
    #@-node:apply_browser_menu
    #@+node:init_attributes
    def init_attributes(self):
        self.name = ""
        self.observer = None
        self.data = None
    #@nonl
    #@-node:init_attributes
    #@+node:realize_code
    def realize_code(self):
        now = datetime.datetime.now().strftime("%x %H:%M:%S")
        code = 'class %s(%s):\n"Inserted at %s"' \
                 % (self.name, self.observer_name, now)
                 
        if self.data:
            code += "\ndata = %s" % str(self.data)
        
        context = self.context.__class__(self.context.get_last_code_item())
        context.append_item(code, 0)
    #@nonl
    #@-node:realize_code
    #@+node:check_constraints
    def check_constraints(self):
        if not reg_identifier.match(self.name):
            error = db.ConstraintError()
            error.message["name"] = _("Name is not a valid Identifier")
            raise error
    #@nonl
    #@-node:check_constraints
    #@+node:set_observer
    def set_observer(self, observer, name):
        code_item = self.context.code_item
        description = docparser.ClassDoc(observer).description
    
        registry = EditorRegistry()
        observer.register_editors(registry)
    
        for e in registry.editors.itervalues():
            if e.attrib_name == "data" \
                and e.edit_model in (Evaluation, MultiEvaluation):
                self.data = e.edit_model(code_item, "data", None)
                break
        else:
            self.data = None
    
        self.observer_name = name
        self.observer = observer
        self.description = description or _("No Description")
    #@nonl
    #@-node:set_observer
    #@-others
#@nonl
#@-node:class ObserverCreator
#@+node:class ObserverCreatorView
class ObserverCreatorView(editorlib.MainView):
    __model__ = ObserverCreator
    __view_name__ = "default"
    
    format = _("""
lbl_error               
observer_list>|[Description:]
   ""         |description>
   ""         |[Name: ]
   ""         |name>
   ""         |data_label
   ""         |data>
-->
(buttons)>
""")

    #@    @+others
    #@+node:create_controls
    def create_controls(self):
        self.observer_list = wx.ListCtrl(self, wx.NewId(), 
                                         style=wx.LC_ICON \
                                               |wx.LC_SINGLE_SEL \
                                               |wx.LC_ALIGN_TOP \
                                               |wx.SUNKEN_BORDER)
        self.observer_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_select_item)
        self.data_label = self.get_label(_("Data:"))
    #@nonl
    #@-node:create_controls
    #@+node:prepare
    def prepare(self):
        self.grow_col(-1)
        self.grow_row(2)
        self.buttons.grow_col(0)
        self.description.set_width("X" * 40)
    #@nonl
    #@-node:prepare
    #@+node:constitute
    def constitute(self, imodel):
        super(ObserverCreatorView, self).constitute(imodel)
        
        self.observer_map = {}
        
        #@    << fill observer list >>
        #@+node:<< fill observer list >>
        img_list = wx.ImageList(32, 32)
        img_name_index_map = {}
        
        observers = []
        #@<< find observers >>
        #@+node:<< find observers >>
        module = imodel.context.code_item.editor.get_module()
        ismodule = inspect.ismodule
        for k, v in module.__dict__.iteritems():
            #@    << filter out non valid modules >>
            #@+node:<< filter out non valid modules >>
            if not ismodule(v): continue
            
            try:
                if not v._is_source_: continue
            except AttributeError: continue
            #@nonl
            #@-node:<< filter out non valid modules >>
            #@nl
            #@    << get public attribs of module >>
            #@+node:<< get public attribs of module >>
            try:
                attribs = v.__all__
            except AttributeError:
                attribs = dir(v)
            #@nonl
            #@-node:<< get public attribs of module >>
            #@nl
            for attrib in attribs:
                obj = getattr(v, attrib, None)
                try:
                    if not issubclass(obj, fobserver.Observer):
                        continue
                except TypeError: continue
                
                #@        << add observer image in img_list >>
                #@+node:<< add observer image in img_list >>
                img_name = obj.__type_image__
                if img_name:
                    try:
                        img_index = img_name_index_map[img_name]
                    except KeyError:
                        bmp = ResourceManager.load_bitmap(img_name, (32, 32))
                        img_index = img_name_index_map[img_name]\
                             = img_list.Add(bmp)
                else:
                    img_index = -1
                #@nonl
                #@-node:<< add observer image in img_list >>
                #@nl
                self.observer_map["%s.%s" % (k, attrib)] = obj
                observers.append(("%s.%s" % (k, attrib), img_index))
        #@-node:<< find observers >>
        #@nl
        #@<< fill list control >>
        #@+node:<< fill list control >>
        observers.sort()
        self.observer_list.AssignImageList(img_list, wx.IMAGE_LIST_NORMAL)
        insert_image = self.observer_list.InsertImageStringItem
        insert = self.observer_list.InsertStringItem
        extent = self.observer_list.GetTextExtent
        
        height = 0
        for name, img_index in observers:
            w, h = extent(name + "XXX")
            height = max(h, height)
            if img_index >= 0:
                insert_image(sys.maxint, name, img_index)
            else:
                insert(sys.maxint, name)
        #@nonl
        #@-node:<< fill list control >>
        #@nl
        self.observer_list.Arrange()
        w, h = self.observer_list.GetViewRect().GetSize()
        border = self.observer_list.GetSize() \
                 - self.observer_list.GetClientSize()
        self.observer_list.CacheBestSize((w + border.width, 
                                          (height + 40) * 7))
        self.observer_list.SetItemState(0, wx.LIST_STATE_SELECTED, 
                                        wx.LIST_STATE_SELECTED)
        #@-node:<< fill observer list >>
        #@nl
    #@-node:constitute
    #@+node:state_changed
    def state_changed(self, attrib):
        if attrib == "data":
            if self.imodel.data: 
                self.data.Show()
            else:
                self.data.Hide()
                
            if isinstance(self.imodel.data, Evaluation):
                self.data_label.Show()
            else:
                self.data_label.Hide()
                
            self.layout()
    #@nonl
    #@-node:state_changed
    #@+node:_on_select_item
    def _on_select_item(self, event):
        name = event.GetItem().GetText()
        observer = self.observer_map[name]
        self.imodel.set_observer(observer, name)
    #@nonl
    #@-node:_on_select_item
    #@-others
#@nonl
#@-node:class ObserverCreatorView
#@-node:ObserverCreator
#@-node:Editors
#@+node:Editor Assignment
#@+node:Assign Editors
registry = context.CObserver.editors
registry["Observer/Create...(100)"] = ObserverCreator()
registry["Observer/Rename...(110)"] = ObserverRenamer()
registry["Observer/Remove(120)"] = ObserverRemover()


#@-node:Assign Editors
#@+node:class EditorRegistry
class EditorRegistry(object):
    def __init__(self):
        self.editors = {}

    
    def register(self, name, type, default):
        path = name.split("/")
        self.editors[name] = AttributeEditor(path[-1].rstrip("."), 
                                             type, default)


    def unregister(self):
        cls_name = self.cls.__name__
        for path in self.editors.keys():
            if path.split("/")[0] == cls_name:
                del self.editors[path]
        

    def Boolean(self, name, default=True):
        self.register(name, Boolean, default)

    def Float(self, name, default=1.0):
        self.register(name, Float, default)


    def Date(self, name, default=None):
        self.register(name, Date, default or datetime.datetime.now())

        
    def String(self, name, default=""):
        self.register(name, String, default)
        

    def Symbol(self, name, default):
        self.register(name, Symbol, default)


    def Shape(self, name, default):
        self.register(name, Shape, default)
        

    def MultiEvaluation(self, name):
        self.register(name, MultiEvaluation, None)

        
    def Evaluation(self, name):
        self.register(name, Evaluation, None)
        

    def TwoColorSet(self, name, default):
        self.register(name, TwoColorSet, default)


    def ColorSet(self, name, default):
        self.register(name, ColorSet, default)


    def ColorMap(self, name, default):
        self.register(name, ColorMap, default)
        

    def Property(self, name, create_property_groups):
        path = name.split("/")
        self.editors[name] = \
                     PropertyEditor(path[-1].rstrip("."), 
                                    create_property_groups)


    def Column(self, name, data_name):
        path = name.split("/")
        self.editors[name] = ColumnEditor(path[-1].rstrip("."), data_name)

#@-node:class EditorRegistry
#@-node:Editor Assignment
#@-others
#@nonl
#@-node:@file gui/editor/observer.py
#@-leo
