#@+leo-ver=4
#@+node:@file gui/editor/task.py
#@@language python
#@<< Copyright >>
#@+node:<< Copyright >>
############################################################################
#   Copyright (C) 2005, 2006, 2007, 2008 by Reithinger GmbH
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
import context
import faces.plocale
import datetime
import faces.pcalendar as pcalendar
import faces.task as ftask
import metapie.dbtransient as db
import metapie.gui.views as views
import classifiers
import editor
from attribedit import *
#@-node:<< Imports >>
#@nl

_is_source_ = True
_ = faces.plocale.get_gettext()

#@+others
#@+node:ExpressionEvaluator
#@+node:class PathWrapper
class PathWrapper(object):
    def __init__(self, code_item, path_str):
        self._path_str = path_str
        self._code_item = code_item


    def _get_up(self):
        new_item = self._code_item.get_parent()
        new_path = "%s.up" % (self._path_str)
        return PathWrapper(new_item, new_path)

    up = property(_get_up)

    def _get_root(self):
        return PathWrapper(get_code_root(self._code_item), "root")

    root = property(_get_root)


    def __getattr__(self, name):
        child = filter(lambda c: c.name == name, self._code_item.get_children())
        if child:
            return PathWrapper(child[0], "%s.%s" % (self._path_str, name))

        return ValueWrapper(AttributeWrapper(self._path_str, name), 
                            ["%s.%s" % (self._path_str, name)])


    def __str__(self):
        return self._path_str
#@-node:class PathWrapper
#@+node:class AttributeWrapper
class AttributeWrapper(object):
    def __init__(self, path, attrib):
        self.path = path
        self.attrib = attrib

    def __str__(self):
        return "%s.%s" % (str(self.path), self.attrib)
#@nonl
#@-node:class AttributeWrapper
#@+node:class ValueWrapper
class ValueWrapper(ftask._ValueWrapper):
    def _vw(self, operand, *args):
        refs = reduce(lambda a, b: a + b, map(ftask._ref, args), [])
        vals = map(ftask._val, args)
        vals.insert(0, operand)
        return ValueWrapper(tuple(vals), refs)


    def _cmp(self, operand, *args):
        refs = reduce(lambda a, b: a + b, map(ftask._ref, args), [])
        vals = map(str, args)
        result = operand(*vals)
        map(lambda a: _sref(a, refs), args)
        return result


#@-node:class ValueWrapper
#@+node:class TaskEvaluator
class TaskEvaluator(object):
    def __init__(self, expression, context):
        #@        << define path variables >>
        #@+node:<< define path variables >>
        me = PathWrapper(context.code_item, "me")
        up = me.up
        root = me.root
        up._path_str = "up"
        root._path_str = "root"
        #@nonl
        #@-node:<< define path variables >>
        #@nl
        #@        << define wmax and wmin >>
        #@+node:<< define wmax and wmin >>
        def to_value_wrapper(a):
            if isinstance(a, ValueWrapper):
                return a

            return ValueWrapper(a, [])

        def wmax(*args):
            args = map(to_value_wrapper, args)
            first = args[0]
            return first._vw(max, *args)

        def wmin(*args):
            args = map(to_value_wrapper, args)
            first = args[0]
            return first._vw(min, *args)
        #@nonl
        #@-node:<< define wmax and wmin >>
        #@nl

        vars = { "up" : up,
                 "root" : root,
                 "me" : me,
                 "max" : wmax,
                 "min" : wmin  }

        try:
            editor = context.code_item.editor
            self.attributes = editor.eval_expression(expression, vars, context)
        except Exception, e:
            self.error = e
#@-node:class TaskEvaluator
#@-node:ExpressionEvaluator
#@+node:Models and Views
#@+node:ScenarioContainer
#@+node:class ScenarioContainer
class ScenarioContainer(db.Model):
    child = db.Model.type(readonly=True)
    error = db.Text()
    #@    @+others
    #@+node:__init__
    def __init__(self, child_model, context, attrib_name, evaluator, default):
        self.child_model = child_model
        self.code_item = code_item = context.code_item
        self.attrib_name = attrib_name
        self.scenarios = ["_default"]

        #@    << calculate attribute value >>
        #@+node:<< calculate attribute value >>
        attribs = code_item.editor.get_attribs(self.code_item)
        if self.attrib_name in attribs:
            line = attribs[self.attrib_name]
            expression = code_item.editor.get_expression(line)
        else:
            expression = ""

        evaluation = evaluator(expression, context)
        try:
            self.error = "%s: %s" % (evaluation.error.__class__.__name__, \
                                     str(evaluation.error))
            value = default
        except AttributeError:
            if expression:
                value = evaluation.attributes.get(attrib_name) 
            else:
                value = default

        #@-node:<< calculate attribute value >>
        #@nl

        child_model = lambda v: self.child_model(self.code_item, 
                                                 self.attrib_name, 
                                                 v)
        if not isinstance(value, dict):
            self.child__default = child_model(value)
            self.scenarios = ["_default"]
            self.default = value
        else:
            self.scenarios = []

            if "_default" not in value:
                value["_default"] = value.values()[0]

            self.default = value["_default"]

            for k, v in value.iteritems():
                setattr(self, "child_%s" % k, child_model(v))
                self.scenarios.append(k)

    #@-node:__init__
    #@+node:remove_scenario
    def remove_scenario(self, name):
        if name == "_default": return None

        try:    
            self.scenarios.remove(name)
        except ValueError:
            return False

        child = getattr(self, "child_%s" % name)
        delattr(self, "child_%s" % name)
        return child
    #@nonl
    #@-node:remove_scenario
    #@+node:add_scenario
    def add_scenario(self, name):
        if name in self.scenarios: return None
        child = self.child_model(self.code_item, 
                                 self.attrib_name, 
                                 self.default)
        setattr(self, "child_%s" % name, child)
        self.scenarios.append(name)
        return child
    #@nonl
    #@-node:add_scenario
    #@+node:show
    def show(self):
        #no wizzard while processing
        if controller().is_processing(): return

        dlg = editorlib.PatchedDialog(controller().frame,  -1, 
                _("Edit %s") % self.attrib_name,
                style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        dlg.SetClientSize((10, 10))
        view = self.constitute()(dlg)
        view.layout()
        dlg.simulate_modal(self.code_item.editor)
    #@nonl
    #@-node:show
    #@+node:code
    def code(self):
        default = self.child__default
        scenarios = list(self.scenarios)
        scenarios.remove("_default")

        if scenarios:
            first = "%s = Multi(%s" % (self.attrib_name, unicode(default))
            others = map(lambda s: '%s=%s' % (s, unicode(getattr(self, "child_%s" % s))), scenarios)
            others.insert(0, first)
            max_len = sum(map(len, others)) + len(others) * 2 + self.code_item.indent + 4
            joiner = max_len > 80 and ",\n" or ", "
            return "%s)" % joiner.join(others)
        else:
            return "%s = %s" % (self.attrib_name, unicode(default))
    #@nonl
    #@-node:code
    #@+node:realize
    def realize(self):
        root = get_code_root(self.code_item)
        try:
            root.all_scenarios.update(self.scenarios)
        except AttributeError:
            root.all_scenarios = set(self.scenarios)

        editor = self.code_item.editor
        attribs = editor.get_attribs(self.code_item)
        if self.attrib_name in attribs:
            editor.replace_expression(self.code(), attribs[self.attrib_name])
        else:
            editor.insert_expression(self.code_item, self.code())
    #@-node:realize
    #@-others
#@nonl
#@-node:class ScenarioContainer
#@+node:class ScenarioView
class ScenarioView(editorlib.MainView):
    __model__ = ScenarioContainer
    __view_name__ = "default"
    vgap = 0


    format = _("""
error(Static)
lbl_error
new|(0,3)|remove
(0,3)>
-->
notebook(Page_default[_default])>
(0,3)>
-->
(0,3)
(buttons)>
""")


    #@    @+others
    #@+node:create_controls
    def create_controls(self):
        self.new = self.get_button(_("Add Scenario"))
        self.remove = self.get_button(_("Remove Scenario"))

        def new_scenario():
            simodel = NewScenario(self.imodel)
            simodel.show(self)

        self.new.attach(new_scenario)
        self.remove.attach(self.remove_scenario)


    #@-node:create_controls
    #@+node:remove_scenario
    def remove_scenario(self):
        current = self.notebook.GetSelection()
        scenario = self.notebook.GetPageText(current)
        child = self.imodel.remove_scenario(scenario)
        if child:
            self.notebook.DeletePage(current)
            self.update_remove_button()
            #self.transaction.
    #@nonl
    #@-node:remove_scenario
    #@+node:add_scenario
    def add_scenario(self, scenario):
        child = self.imodel.add_scenario(scenario)
        if child:
            page = self.create_subform(self.notebook, "Page%s" % scenario)
            page.inspect(self.imodel, scenario)
            self.notebook.AddPage(page, scenario, True)
            self.remove.Enable(True)
            self.update_remove_button()

    #@-node:add_scenario
    #@+node:prepare
    def prepare(self):
        self.grow_col(-1)
        self.grow_row(5)
        self.buttons.grow_col(0)
        self.error.Hide()
        self.error.SetForegroundColour(self.error_colour)
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, 
                           lambda e: self.update_remove_button())
        self.update_remove_button()

    def update_remove_button(self):
        if self.remove:
            self.remove.Enable(self.notebook.GetSelection() != 0)
    #@-node:prepare
    #@+node:constitute
    def constitute(self, imodel):
        super(ScenarioView, self).constitute(imodel)
        for s in self.imodel.scenarios:
            if s != "_default":
                page = self.create_subform(self.notebook, "Page%s" % s)
                page.inspect(self.imodel, s)
                self.notebook.AddPage(page, s)

        if imodel.error: self.error.Show()
        self.update_remove_button()
    #@nonl
    #@-node:constitute
    #@+node:modify_subview
    def modify_subview(self, subview_class, name):
        if not name.startswith("Page"): return subview_class
        me = self

        class Page(subview_class):
            format = "child_"  + name[4:] + ">"

            def get_control(self, name):
                if name.startswith("child_"):
                    name = "child"

                return super(Page, self).get_control(name)

            def inspect_state(self):
                ichild = getattr(self.imodel, "child_%s" % name[4:])
                me.transaction.include(ichild)
                self.widgets["child"].inspect(self.imodel, "child_%s" % name[4:])


            def prepare(self):
                self.grow_col(0)
                self.grow_row(0)

        return Page
    #@nonl
    #@-node:modify_subview
    #@-others
#@nonl
#@-node:class ScenarioView
#@+node:class NewScenario
class NewScenario(db.Model):
    scenario = db.Text("_default")

    #@    @+others
    #@+node:__init__
    def __init__(self, parent_imodel):
        self.parent_imodel = parent_imodel
    #@nonl
    #@-node:__init__
    #@+node:get_scenarios
    def get_scenarios(self):
        scenarios = set()
        parent_imodel = self.parent_imodel
        try:
            scenarios.update(parent_imodel.code_item.obj.root.all_scenarios)
        except AttributeError:
            pass

        try:
            root = get_code_root(parent_imodel.code_item)
            scenarios.update(root.all_scenarios)
        except AttributeError:
            pass

        scenarios.update(parent_imodel.scenarios)
        return scenarios
    #@nonl
    #@-node:get_scenarios
    #@+node:show
    def show(self, parent):
        dlg = editorlib.PatchedDialog(controller().frame,  -1, 
                    _("Add Scenario"), style=wx.DEFAULT_DIALOG_STYLE)

        dlg.SetClientSize((10, 10))
        view = self.constitute()(dlg)
        view.layout()
        self.parent = parent
        dlg.simulate_modal(parent)
    #@nonl
    #@-node:show
    #@+node:realize
    def realize(self):
        self.parent.add_scenario(self.scenario)
    #@nonl
    #@-node:realize
    #@-others
#@nonl
#@-node:class NewScenario
#@+node:class NewScenarioView
class NewScenarioView(editorlib.MainView):
    __model__ = NewScenario
    __view_name__ = "default"
    format = (""" 
[Scenario: ]|scenario(Combo)
-->
(buttons)>
""")

    format_buttons = """
btn_ok{r}|btn_cancel{r}
"""

    #@    @+others
    #@+node:constitute
    def constitute(self, imodel):
        super(NewScenarioView, self).constitute(imodel)
        self.update_scenarios()

    #@-node:constitute
    #@+node:update_scenarios
    def update_scenarios(self):
        self.scenario.Clear()
        map(self.scenario.Append, self.imodel.get_scenarios())
    #@-node:update_scenarios
    #@-others
#@nonl
#@-node:class NewScenarioView
#@-node:ScenarioContainer
#@+node:Balance
class Balance(db.Model):
    value = db.Enumerate(ftask._allocator_strings)
    #@    @+others
    #@+node:__init__
    def __init__(self, code_item, attrib, value):
        super(Balance, self).__init__()
        self.value = value or ftask.SMART
    #@nonl
    #@-node:__init__
    #@+node:__str__
    def __str__(self):
        return '%s' % ftask._allocator_strings[self.value]
    #@-node:__str__
    #@-others

class BalanceView(views.FormView):
    __model__ = Balance
    __view_name__ = "default"
    vgap = 0
    format = "value>"

    def prepare(self):
        self.grow_col(0)
#@-node:Balance
#@+node:RefDate
#@+node:class RefDate
class RefDate(db.Model):
    """
    A date that can refer to other tasks
    """
    fixed = db.DateTime(none=True)

    #@    @+others
    #@+node:__init__
    def __init__(self, code_item, attrib, value):
        super(RefDate, self).__init__()
        self.code_item = code_item
        self.item_path = editor.get_code_item_path(code_item)

        #@    << define path_argument >>
        #@+node:<< define path_argument >>
        def path_argument(path):
            if path.startswith("up."):
                return { "path": ftask.create_absolute_path(self.item_path, path),
                         "relative": True }

            return { "path": path,
                     "relative": False }
        #@nonl
        #@-node:<< define path_argument >>
        #@nl

        def is_predecessor(obj):
            return isinstance(obj, AttributeWrapper) and obj.attrib in ("start", "end")

        def parse_value(value):
            if isinstance(value, tuple):
                operand = value[0]
                if operand == max:
                    map(parse_value, value[1:])
                    return
                #@            << add predecessor with lag >>
                #@+node:<< add predecessor with lag >>
                sign = { operator.add : "+", operator.sub : "-" }.get(value[0])
                if not sign: return

                pred = None
                lag = None
                for v in value[1:]:
                    if is_predecessor(v):
                        pred = v
                    elif isinstance(v, basestring):
                        lag = v

                if pred:
                    self.preds.insert(Predecessor(lag=sign+lag, 
                                                  ptype=pred.attrib,
                                                  **path_argument(pred.path)))

                return
                #@nonl
                #@-node:<< add predecessor with lag >>
                #@nl

            if is_predecessor(value):
                #@            << add predecessor without lag >>
                #@+node:<< add predecessor without lag >>
                self.preds.insert(Predecessor(value=value.attrib,
                                              **path_argument(value.path)))
                return
                #@nonl
                #@-node:<< add predecessor without lag >>
                #@nl

            if isinstance(value, (basestring, datetime.datetime)):
                #@            << set fixed date >>
                #@+node:<< set fixed date >>
                try:
                    self.fixed = pcalendar.to_datetime(value)
                except ValueError:
                    pass
                return
                #@nonl
                #@-node:<< set fixed date >>
                #@nl

        self.fixed = None            
        parse_value(ftask._val(value))


    #@-node:__init__
    #@+node:__str__
    def __str__(self):
        preds = [ p.to_string(self.item_path) for p in self.preds ]
        if self.fixed:
            preds.append(self.fixed.strftime('"%x %H:%M"'))

        if len(preds) > 1:
            return "max(%s)" % ", ".join(preds)
        else:
            return "".join(preds)
    #@nonl
    #@-node:__str__
    #@-others
#@nonl
#@-node:class RefDate
#@+node:class RefDateView
class RefDateView(views.FormView):
    __model__ = RefDate
    __view_name__ = "default"
    vgap = 0
    format = _("""
fixed
(0,3)
[Predecessors:]
predecessors>
(0,3)
delete
""")

    #@    @+others
    #@+node:create_controls
    def create_controls(self):
        self.predecessors = self.get_control("preds(PredecessorGrid)")
        self.delete = self.predecessors.get_delete_button(self)
    #@nonl
    #@-node:create_controls
    #@+node:prepare
    def prepare(self):
        self.grow_col(0)
        self.grow_row(3)
    #@nonl
    #@-node:prepare
    #@+node:constitute
    def constitute(self, imodel):
        super(RefDateView, self).constitute(imodel)
        self.predecessors.create_paths(imodel.code_item)
        self.layout()
    #@-node:constitute
    #@-others
#@-node:class RefDateView
#@+node:class Predecessor
class Predecessor(db.Model):
    path = db.Text()
    relative = db.Boolean(default=False)
    lag = db.Text()
    ptype = db.Enumerate({ "end" : "end" , "start" : "start" },
                         default="end")
    all_paths = []

    #@    @+others
    #@+node:to_string
    def to_string(self, item_path):
        path = self.path
        if self.relative:
            path = ftask.create_relative_path(item_path, path)

        result = "%s.%s" % (path, self.ptype)
        if self.lag:
            if self.lag[0] in ("+", "-"):
                result += ' %s "%s"' % (self.lag[0], self.lag[1:])
            else:
                result += ' + "%s"' % self.lag

        return result
    #@nonl
    #@-node:to_string
    #@+node:check_constraints
    def check_constraints(self):
        error = db.ConstraintError()    
        if not self.path:
            error.message["path"] = _("you have to sperciy a path")

        if self.lag: 
            lag = self.lag.replace("+", "").replace("-", "")

            try:
                val = pcalendar.to_timedelta(self.lag)
            except Exception:
                error.message["lag"] = _("not a valid time delta")

        if error.message:
            raise error
    #@nonl
    #@-node:check_constraints
    #@-others

db.Relation("refdate_predecessor",
            db.End(Predecessor, "preds", multi='*'),
            db.End(RefDate))
#@nonl
#@-node:class Predecessor
#@+node:class PredecessorGrid
class PredecessorGrid(grid.EditGrid, views.GridView):
    __model__ = Predecessor
    columns = (("path(auto_tree)", _("Path")),
               (Predecessor.relative, _("Relative")),
               (Predecessor.lag, _("Lag")),
               (Predecessor.ptype, _("Type")))
    resize_col = 0


    def create_paths(self, code_item):
        root = get_code_root(code_item)
        self.all_paths = all_paths = [ "root" ]

        def add_path(item, prefix):
            if item.name[0] == "_": return
            prefix = "%s.%s" % (prefix, item.name)
            all_paths.append(prefix)
            map(lambda c: add_path(c, prefix), item.get_children())

        map(lambda c: add_path(c, "root"), root.get_children())

        length = all_paths and max(map(len, all_paths)) or 1
        self.set_width(0, "N" * length + "XXX")



    def prepare(self, attribute):
        if attribute == "path":
            self.path.fill_tree(self.all_paths)





#@-node:class PredecessorGrid
#@-node:RefDate
#@-node:Models and Views
#@+node:Editors
#@+node:class ScenarioAttributeEditor
class ScenarioAttributeEditor(AttributeEditor):
    #@    @+others
    #@+node:activate
    def activate(self, context):
        """
        activates the editor.
        """
        imodel = ScenarioContainer(self.edit_model, context, self.attrib_name, 
                                   self.evaluator, self.default)
        imodel.show()


    #@-node:activate
    #@-others
#@-node:class ScenarioAttributeEditor
#@+node:print_task_references
def print_task_references(code_item, outstream=None):
    outstream = outstream or sys.stdout
    tname = code_item.name
    print >> outstream, _('The following lines reference the task "%s":') % tname
    find_references = code_item.editor.find_task_references
    for ci, attrib, line in find_references(code_item):
        print >> outstream, '   task attribute: "%s.%s", File "%s", line %i' \
            % (ci.name, attrib, ci.editor.model.path, line + 1)

    print >> outstream
#@nonl
#@-node:print_task_references
#@+node:class TaskRemover
class TaskRemover(object):
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
        code_item = context.code_item
        editor = code_item.editor

        if list(editor.find_task_references(code_item)):
            print_task_references(context.code_item, sys.stderr)
            print >> sys.stderr, _("You have to remove those references before removing the task!\n")
        else:
            code_item.remove()
    #@-node:activate
    #@-others
#@-node:class TaskRemover
#@+node:class TaskReferencePrinter
class TaskReferencePrinter(object):
    __icon__ = "list16"

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
        print_task_references(context.code_item)
    #@-node:activate
    #@-others
#@-node:class TaskReferencePrinter
#@+node:class TaskIndenter
class TaskIndenter(object):
    __icon__ = "indent16"
    #@    @+others
    #@+node:apply
    def apply(self, expression, code_item):
        return False
    #@-node:apply
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        line = code_item.get_line()
        editor = code_item.editor
        prev_line = editor.prev_item_line(line - 1)
        prev_item = editor.code_item_at(prev_line)

        if classifiers.is_task(prev_item) and prev_item.indent >= code_item.indent:
            return "extra"

        return ""
    #@-node:apply_browser_menu
    #@+node:activate
    def activate(self, context):
        code_item = context.code_item
        editor = code_item.editor
        indent = editor.GetIndent()
        start_line = code_item.get_line()
        end_line = code_item.get_last_line()
        lines = xrange(start_line, end_line  + 1)
        editor.BeginUndoAction()
        for l in lines:
            old_indent = editor.GetLineIndentation(l)
            editor.SetLineIndentation(l, old_indent + indent)

        editor.check_code_updates(start_line, end_line)
        editor.correct_task_code(code_item)
        editor.EndUndoAction()
    #@-node:activate
    #@-others
#@nonl
#@-node:class TaskIndenter
#@+node:class TaskUnindenter
class TaskUnindenter(object):
    __icon__ = "unindent16"
    #@    @+others
    #@+node:apply
    def apply(self, expression, code_item):
        return False
    #@-node:apply
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        parent = code_item.get_parent()
        if classifiers.is_task(parent):
            return "extra"

        return ""
    #@-node:apply_browser_menu
    #@+node:activate
    def activate(self, context):
        code_item = context.code_item
        editor = code_item.editor
        indent = editor.GetIndent()
        start_line = code_item.get_line()
        end_line = code_item.get_last_line()
        lines = xrange(start_line, end_line + 1)
        editor.BeginUndoAction()
        for l in lines:
            old_indent = editor.GetLineIndentation(l)
            editor.SetLineIndentation(l, old_indent - indent)

        editor.check_code_updates(start_line, end_line)
        editor.correct_task_code(code_item)
        editor.EndUndoAction()
    #@-node:activate
    #@-others
#@nonl
#@-node:class TaskUnindenter
#@+node:class TaskRenamer
class TaskRenamer(RenameEditor):
    title = _("Rename Task")
    __icon__ = "rename16"

    def correct_code(self, editor):
        editor.correct_task_code(self.context.code_item)
#@nonl
#@-node:class TaskRenamer
#@+node:class TaskCreator
class TaskCreator(NameEditor):
    title = _("Add Task")

    #@    @+others
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        return "extra"
    #@-node:apply_browser_menu
    #@+node:realize_code
    def realize_code(self):
        now = datetime.datetime.now().strftime("%x %H:%M:%S")
        code = 'def %s():\n"Inserted at %s"' % (self.name, now)
        self.insert_code(code)
    #@-node:realize_code
    #@-others
#@nonl
#@-node:class TaskCreator
#@+node:class SubTaskCreator
class SubTaskCreator(TaskCreator):
    #@    @+others
    #@+node:insert_code
    def insert_code(self, code):
        indent = self.context.code_item.editor.GetIndent()
        self.context.append_item(code, self.context.code_item.indent + indent)
    #@-node:insert_code
    #@-others
#@nonl
#@-node:class SubTaskCreator
#@+node:class TaskSiblingCreator
class TaskSiblingCreator(TaskCreator):
    #@    @+others
    #@+node:insert_code
    def insert_code(self, code):
        self.context.append_item(code, self.context.code_item.indent)
    #@-node:insert_code
    #@-others
#@nonl
#@-node:class TaskSiblingCreator
#@+node:class TaskSiblingBeforeCreator
class TaskSiblingBeforeCreator(TaskCreator):
    #@    @+others
    #@+node:insert_code
    def insert_code(self, code):
        self.context.insert_item(code, self.context.code_item.indent)
    #@-node:insert_code
    #@-others
#@nonl
#@-node:class TaskSiblingBeforeCreator
#@+node:class ProjectTaskCreator
class ProjectTaskCreator(NameEditor):
    title = _("Add Project")

    #@    @+others
    #@+node:realize_code
    def realize_code(self):
        now = datetime.datetime.now().strftime("%x")
        code = 'def %s():\nstart = "%s"' % (self.name, now)
        ci = self.context.get_last_code_item()
        context = self.context.__class__(ci)
        start_line, end_line = context.append_item(code, 0)
        ci.editor.check_code_updates(start_line, end_line)
        ci = ci.editor.code_item_at(start_line)
        def dumy(): start = "1.1.2006"
        ci.obj = ftask.Project(dumy)
    #@-node:realize_code
    #@+node:apply_browser_menu
    def apply_browser_menu(self, existing_attribs, code_item):
        return "create"
    #@-node:apply_browser_menu
    #@-others
#@nonl
#@-node:class ProjectTaskCreator
#@+node:class ProjectTaskRenamer
class ProjectTaskRenamer(RenameEditor):
    title = _("Rename Project")
    __icon__ = "rename16"

    #@    @+others
    #@+node:realize_code
    def realize_code(self):
        code = str(self)
        code_item = self.context.code_item
        editor = code_item.editor
        editor.BeginUndoAction()
        if code_item.name != self.name:
            #name has changed ==> change the name in all references
            old_name = code_item.name

            iterator = editor.find_evaluation_references(code_item)
            refs = dict([ (line, ci) for ci, line in iterator ])
            for line in refs.keys():
                start = editor.PositionFromLine(line)
                end = editor.GetLineEndPosition(line)
                editor.SetTargetStart(start)
                editor.SetTargetEnd(end)
                text = editor.GetTextRange(start, end)
                editor.ReplaceTarget(text.replace(old_name, self.name))

        code_item.editor.replace_expression(code, code_item.get_line())

        editor.EndUndoAction()
    #@-node:realize_code
    #@+node:__str__
    def __str__(self):
        return "def %s():" % self.name
    #@nonl
    #@-node:__str__
    #@-others
#@-node:class ProjectTaskRenamer
#@+node:class ScenarioAttributeEditor
class ScenarioAttributeEditor(ScenarioAttributeEditor):
    evaluator = TaskEvaluator

#@-node:class ScenarioAttributeEditor
#@+node:class AttributeEditor
class AttributeEditor(AttributeEditor):
    evaluator = TaskEvaluator
#@-node:class AttributeEditor
#@-node:Editors
#@+node:Assign Editors
tregistry = context.CTask.editors
pregistry = context.CProjectDeclaration.editors

std_attributes = _("Standard/%s")
cal_attributes = _("Calendar/%s")

tregistry[std_attributes % "title..."] = AttributeEditor("title", String, _("Title"))
tregistry[std_attributes % "start..."] = ScenarioAttributeEditor("start", RefDate, datetime.datetime.now())
tregistry[std_attributes % "end..."] = ScenarioAttributeEditor("end", RefDate, datetime.datetime.now())
tregistry[std_attributes % "duration..."] = ScenarioAttributeEditor("duration", Duration, "1d")
tregistry[std_attributes % "effort..."] = ScenarioAttributeEditor("effort", Delta, "1d")
tregistry[std_attributes % "todo..."] = AttributeEditor("todo", Delta, "1d")
tregistry[std_attributes % "done..."] = AttributeEditor("done", Delta, "1d")

tregistry[std_attributes % "length..."] = ScenarioAttributeEditor("length", Delta, "1d")
tregistry[std_attributes % "balance..."] = AttributeEditor("balance", Balance)
tregistry[std_attributes % "notes..."] = AttributeEditor("notes", MultiText)
tregistry[std_attributes % "load..."] = ScenarioAttributeEditor("load", Float, 1.0)
tregistry[std_attributes % "efficiency..."] = ScenarioAttributeEditor("efficiency", Float, 1.0)
tregistry[std_attributes % "max_load..."] = ScenarioAttributeEditor("max_load", Float, 1.0)
tregistry[std_attributes % "priority..."] = AttributeEditor("priority", Int, 500)
tregistry[std_attributes % "complete..."] = AttributeEditor("complete", Int, 100)
tregistry[std_attributes % "milestone..."] = AttributeEditor("milestone", Boolean, True)
tregistry[std_attributes % "resource..."] = AttributeEditor("resource", ResourceSet)

tregistry[cal_attributes % "vacation..."] = AttributeEditor("vacation", DateTimeRanges)
tregistry[cal_attributes % "extra_work..."] = AttributeEditor("extra_work", DateTimeRanges)
tregistry[cal_attributes % "now..."] = AttributeEditor("now", Date, datetime.datetime.now())
tregistry[cal_attributes % "working_days..."] = AttributeEditor("working_days", WorkingTimes,
                                                            [("mon,tue,wed,thu,fri", "08:00-12:00", "13:00-17:00")])
tregistry[cal_attributes % "minimum_time_unit..."] = AttributeEditor("minimum_time_unit", Int, 
                                                                 pcalendar.DEFAULT_MINIMUM_TIME_UNIT)
tregistry[cal_attributes % "working_days_per_week..."] = AttributeEditor("working_days_per_week", Int,
                                                                     pcalendar.DEFAULT_WORKING_DAYS_PER_WEEK)
tregistry[cal_attributes % "working_days_per_month..."] = AttributeEditor("working_days_per_month", Int,
                                                                      pcalendar.DEFAULT_WORKING_DAYS_PER_MONTH)
tregistry[cal_attributes % "working_days_per_year..."] = AttributeEditor("working_days_per_year", Int,
                                                                     pcalendar.DEFAULT_WORKING_DAYS_PER_YEAR)
tregistry[cal_attributes % "working_hours_per_day..."] = AttributeEditor("working_hours_per_day", Int,
                                                                     pcalendar.DEFAULT_WORKING_HOURS_PER_DAY)

pregistry.update(tregistry)

tregistry[_("Task/Create Subtask...(1000)")] = SubTaskCreator()
tregistry[_("Task/Rename...(1010)")] = TaskRenamer()
tregistry[_("Task/Remove...(1012)")] = TaskRemover()
tregistry[_("Task/Insert Sibling After...(1020)")] = TaskSiblingCreator()
tregistry[_("Task/Insert Sibling Before...(1030)")] = TaskSiblingBeforeCreator()
tregistry[_("Task/Indent(1040)")] = TaskIndenter()
tregistry[_("Task/Unindent(1050)")] = TaskUnindenter()
tregistry[_("Task/Show References...(1100)")] = TaskReferencePrinter()


pregistry[_("Project/Create Project...(1000)")] = ProjectTaskCreator()
pregistry[_("Project/Create Task...(1001)")] = SubTaskCreator()
pregistry[_("Project/Rename...(1010)")] = ProjectTaskRenamer()
pregistry[_("Project/Remove...(1012)")] = EvaluationRemover()
pregistry[_("Project/Show References...(1100)")] = EvaluationReferencePrinter()

del pregistry
del tregistry
del std_attributes
del cal_attributes

#@-node:Assign Editors
#@-others
#@nonl
#@-node:@file gui/editor/task.py
#@-leo
