#@+leo-ver=4
#@+node:@file gui/editor/docparser.py
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
#@<< Imports >>
#@+node:<< Imports >>
import re
import inspect
import textwrap



#@-node:<< Imports >>
#@nl


_is_source = True
_FIELD_BULLET = re.compile('^\s*@(\w+)( [^{}:\n]+)?:( +|$)', re.MULTILINE)
_ESCAPE = re.compile('[A-Z]+{([^}]+)}')

#@+others
#@+node:_get_indentdation
def _get_indentdation(line):
    return len(line) - len(line.lstrip())
#@-node:_get_indentdation
#@+node:unescape
def unescape(txt):
    return _ESCAPE.sub(r"\1", txt)
#@-node:unescape
#@+node:class DocParser
class DocParser(object):
    #@	@+others
    #@+node:__init__
    def __init__(self, text):
        self.clear()
        self.description = self.parse_description(text)
        self.parse_fields(text)
    #@-node:__init__
    #@+node:clear
    def clear(self):
        self.description = ""
        self.order = {}
        self.attribs = {}
        self.types = {}
        self.params = {}
        self.args = None
    #@-node:clear
    #@+node:parse_fields
    def parse_fields(self, txt):
        field = { "var" : self.attribs,
                  "param": self.params,
                  "type" : self.types }

        docs = txt.split("\n")

        for i in range(len(docs)):
            line = docs[i]
            mo = _FIELD_BULLET.search(line)
            if mo:
                type_ = mo.group(1)
                name = mo.group(2)
                indent = _get_indentdation(line)
                for j in range(i + 1, len(docs)):
                    if _get_indentdation(docs[j]) < indent \
                           or _FIELD_BULLET.search(docs[j]):
                        break

                dlines = map(lambda l: l[indent:], docs[i + 1:j])
                dlines.insert(0, line[mo.end():].strip())

                desc = unescape("\n".join(dlines))
                try:
                    if name:
                        name = name.strip()
                        field[type_].setdefault(name.strip(),
                                                textwrap.dedent(desc).strip())
                        self.order.setdefault(name, i)
                    else:
                        field[type_] = textwrap.dedent(desc).strip()
                except KeyError: pass

                i = j

        self.args = field.get("args", None)
    #@-node:parse_fields
    #@+node:parse_methods
    def parse_methods(self, instance):
        ismf = lambda o: inspect.isfunction(o) or inspect.ismethod(0)
        for name, val in inspect.getmembers(instance, ismf):
            self.methods[name] = self.parse_description(val.__doc__ or "")
    #@-node:parse_methods
    #@+node:parse_description
    def parse_description(self, desc):
        mo = _FIELD_BULLET.search(desc)
        desc = bool(mo) and desc[:mo.start()] or desc
        return textwrap.dedent(desc).strip()
    #@-node:parse_description
    #@-others
#@-node:class DocParser
#@+node:class DocBase
class DocBase(object):
    #@	<< declarations >>
    #@+node:<< declarations >>
    min_width = 40

    #@-node:<< declarations >>
    #@nl
    #@	@+others
    #@+node:argspec
    def argspec(self, obj):
        args = inspect.getargspec(obj)
        try:
            if args[0][0] == "self": del args[0][0]
        except IndexError:
            pass

        return inspect.formatargspec(*args)
    #@-node:argspec
    #@+node:get_doc
    def get_doc(self, field):
        return ()
    #@-node:get_doc
    #@-others
#@-node:class DocBase
#@+node:class ClassDoc
class ClassDoc(DocBase):
    #@	@+others
    #@+node:__init__
    def __init__(self, instance):
        try:
            doc = str(instance.__doc__ or "")
        except AttributeError:
            doc = ""

        parser = DocParser(doc)

        self.description = parser.description
        self.order = parser.order
        self.attribs = parser.attribs
        self.params = parser.params
        self.init_args = "()"

        args = parser.args

        parser.params = {}
        if inspect.isclass(instance):
            cls = instance
        else:
            cls = instance.__class__

        for c in inspect.getmro(cls):
            try:
                doc = str(c.__doc__ or "")
            except AttributeError:
                doc = ""

            parser.parse_fields(doc)

        self.parse_methods(instance)
        self.init_args = args is None and self.init_args or args
    #@-node:__init__
    #@+node:get_doc
    def get_doc(self, field):
        desc = self.attribs.get(field)
        if desc:
            desc = textwrap.fill(desc, self.min_width)
            return len(field) + 1, "%s:\n%s" % (field, desc)

        desc = self.methods.get(field)
        if desc:
            header = field + self.args[field]
            desc = textwrap.fill(desc, max(self.min_width, len(header) + 1))
            return len(header) + 1, "%s:\n%s" % (header, desc)

        return ()
    #@-node:get_doc
    #@+node:constructor
    def constructor(self, name):
        header = name + self.init_args
        desc = textwrap.fill(self.description,
                             max(self.min_width, len(header) + 1))
        return len(header) + 1, "%s:\n%s" % (header, desc)
    #@-node:constructor
    #@+node:parse_methods
    def parse_methods(self, instance):
        self.methods = {}
        self.args = {}
        for name, val in inspect.getmembers(instance, inspect.ismethod):
            if val.__doc__:
                parser = DocParser(str(val.__doc__))
                self.methods[name] = parser.description
                if parser.args:
                    self.args[name] = parser.args
                    continue

                self.args[name] = self.argspec(val)

            if name == "__init__":
                self.init_args = self.argspec(val)
    #@-node:parse_methods
    #@-others
#@-node:class ClassDoc
#@+node:class ModuleDoc
class ModuleDoc(DocBase):
    #@	@+others
    #@+node:__init__
    def __init__(self, module):
        self.description = str(module.__doc__ or "")
    #@-node:__init__
    #@+node:constructor
    def constructor(self, name):
        desc = textwrap.fill(self.description,
                             max(self.min_width, len(name) + 1))
        return len(name) + 1, "%s:\n%s" % (name, desc)
    #@-node:constructor
    #@-others
#@-node:class ModuleDoc
#@+node:class FunctionDoc
class FunctionDoc(DocBase):
    #@	@+others
    #@+node:__init__
    def __init__(self, func):
        doc = str(func.__doc__ or "")

        if inspect.ismethod(func) and not doc:
            for c in inspect.getmro(func.im_class):
                attr = getattr(c, func.__name__, func)
                if attr.__doc__:
                    doc = attr.__doc__
                    break

        parser = DocParser(doc)
        self.description = parser.description
        self.args = parser.args is None and self.argspec(func) or parser.args
    #@-node:__init__
    #@+node:constructor
    def constructor(self, name):
        header = name + self.args
        desc = textwrap.fill(self.description,
                             max(self.min_width, len(header) + 1))
        return len(header) + 1, "%s:\n%s" % (header, desc)
    #@-node:constructor
    #@-others
#@-node:class FunctionDoc
#@-others
#@-node:@file gui/editor/docparser.py
#@-leo
