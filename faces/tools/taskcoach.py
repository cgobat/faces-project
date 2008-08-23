############################################################################
#   Copyright (C) 2005,2006 by Reithinger GmbH
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

import os
import xml.parsers.expat
import datetime
import time
import operator
import faces.plocale
import textwrap
import codecs

_ = faces.plocale.get_gettext()
_is_source_ = True
_cache = { }

__all__ = ("generate_for_resources", "generate", "clear_cache", "read")
    

class Forwarder(object):
    def __init__(self, dest):
        self.dest = dest


class Category(Forwarder):
    def add_char_data(self, data):
        self.dest.categories.append(data)


class Attachment(Forwarder):
    def add_char_data(self, data):
        self.dest.attachments.append(data)


class Description(Forwarder):
    def add_char_data(self, data):
        self.dest.description.append(data)
        

class Effort(object):
    def __init__(self, **attribs):
        self.attribs = attribs
        self.description = []

    def add_element(self, name, attribs):
        if name == "description": return Description(self)
        raise ValueError("wrong file format")
        
    def xml(self):
        attribs = map(lambda kv: '%s="%s"' % kv, self.attribs.items())
        attribs = " ".join(attribs)

        def make_tags(tag, seq):
            templ = "<%s>%%s</%s>" % (tag, tag)
            return map(lambda v: templ % v, seq)

        children = make_tags("description", self.description)
        children = "".join(children)
        return "<effort %s>%s</effort>" % (attribs, children)
        

class Task(object):
    def __init__(self, encoding=None, **attribs):
        self.encoding = encoding
        self.attribs = attribs
        self.categories = []
        self.attachments = []
        self.children = []
        self.efforts = []
        self.description = []
        
        
    def __iter__(self):
        def walkdown(obj):
            yield obj
            try:
                for c in obj.children:
                    for r in walkdown(c):
                        yield r
            except AttributeError:
                pass

        return walkdown(self)


    def add_element(self, name, attribs):
        if name == "task":
            task = Task(**convert_attribs(attribs))
            self.children.append(task)
            return task

        if name == "category": return Category(self)
        if name == "attachment": return Attachment(self)
        if name == "description": return Description(self)
        if name == "effort":
            effort = Effort(**convert_attribs(attribs))
            self.efforts.append(effort)
            return effort

        raise ValueError("wrong file format")


    def append(self, child):
        self.children.append(child)


    def filter_for_category(self, cat):
        return filter(lambda t: cat in t.categories, self)


    def project_category(self):
        for c in self.categories:
            if c.startswith("faces_project:"):
                return c[14:]

        return False
    

    def xml(self):
        attribs = map(lambda kv: '%s="%s"' % kv, self.attribs.items())
        attribs = " ".join(attribs)

        def make_tags(tag, seq):
            templ = "<%s>%%s</%s>" % (tag, tag)
            return map(lambda v: templ % v, seq)

        children = []
        children += make_tags("category", self.categories)
        children += make_tags("attachment", self.attachments)
        children += map(Effort.xml, self.efforts)
        children += make_tags("description", ["\n".join(self.description)])
        children = "".join(children)

        if self.encoding:
            children = children.decode(self.encoding)

        children += "".join(map(Task.xml, self.children))
        return "<task %s>%s</task>" % (attribs, children)
        

class TaskList(Task):
    def __init__(self):
        super(TaskList, self).__init__(subject="root")
        

    def add_element(self, name, attribs):
        if name != "task":
            raise ValueError("wrong file format")

        return super(TaskList, self).add_element(name, attribs)


    def xml(self):
        children = map(Task.xml, self.children)
        children = "".join(children)
        return "<tasks>%s</tasks>" % children


def parse_file(path):
    root = TaskList()
    stack = [ root ]
    parser = xml.parsers.expat.ParserCreate()

    def start_element(name, attrs):
        if name == "tasks": return
        element = stack[-1].add_element(name, attrs)
        stack.append(element)

    def end_element(name):
        if name == "tasks": return
        stack.pop()
        
    def char_data(data):
        stack[-1].add_char_data(data)
        
    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    parser.CharacterDataHandler = char_data
    try:
        parser.ParseFile(file(path, "r"))
    except IOError:
        pass
    
    return root


def convert_attribs(attribs):
    keys = attribs.keys()
    return dict(zip(map(str, keys), map(attribs.get, keys)))


def project_category(project):
    return "faces_project:%s" % project._idendity_()


def make_id(task):
    return '%s:%s'% (id(task), time.time())


def make_task(ftask, resource, encoding):
    t = Task(subject=ftask.name,
             id=make_id(ftask),
             priority=ftask.priority,
             lastModificationTime=str(datetime.datetime.now()),
             startdate=str(ftask.start.to_datetime().date()),
             duedate=str(ftask.end.to_datetime().date()),
             encoding=encoding)

    if ftask.title != ftask.name:
        t.description.append(ftask.title)

    try:
        t.description.append(textwrap.dedent(ftask.notes).strip())
    except AttributeError:
        pass

    t.categories.append("faces")

    if resource: resources = [ resource ]
    else: resources = list(ftask._iter_booked_resources())

    if ftask.complete >= 100:
        t.attribs["completiondate"] = t.attribs["duedate"]

    budget = 0
    for r in resources:
        bookings = r.get_bookings(ftask)
        for b in bookings:
            if b.actual:
                delta = datetime.timedelta(minutes=b.work_time)
                e = Effort(start=str(b.book_start),
                           stop=str(b.book_start + delta))
                if not resource:
                    e.description.append(r.name)
                    
                t.efforts.append(e)

            budget += b.work_time

    t.attribs["budget"] = "%i:%i:0" % (budget / 60, budget % 60)
    return t
    

def read(path, project_id=None, clear_cache=False):
    if _cache.has_key(path):
        if clear_cache: del _cache[path]
        else: return _cache[path]

    if isinstance(path, (list, tuple)):
        files = path
    elif os.path.isdir(path):
        files = filter(lambda f: f.endswith(".tsk"), os.listdir(path))
        files = map(lambda f: os.path.join(path, f), files)
    else:
        files = [path]

    items = []
    for p in files:
        default_resname, ext = os.path.splitext(os.path.basename(p))
        
        def find_items(task, path=""):
            pc = task.project_category()
            if not path:
                if not pc: return []
                if project_id and pc != project_id: return []
                path = pc
            else:
                path = "%s.%s" % (path, task.attribs["subject"])

            items = map(lambda t: find_items(t, path), task.children)
            if items: return reduce(operator.add, items, [])

            def convert_effort(effort):
                resname = effort.description \
                           and effort.description[0] \
                           or default_resname 
                start = effort.attribs["start"][:16]
                stop = effort.attribs["stop"][:16]
                return (path, resname, start, stop)

            return map(convert_effort, task.efforts)
        
        root = parse_file(p)
        items += reduce(operator.add, map(find_items, root.children), [])

    _cache[path] = items
    return items
        

def clear_cache():
    _cache.clear()
    return True

clear_cache.faces_menu = _("Task Coach/Clear Cache")


def generate_for_resources(path, project):
    for r in project.all_resources():
        generate(os.path.join(path, "%s.tsk" % r.name), project, r)

    return True


def generate(path, project, resource=None, encoding="iso8859-15"):
    root = parse_file(path)
    pcat = project_category(project)
    croot = root.filter_for_category(pcat)
    cproject = make_task(project, resource, encoding)
    
    if not croot:
        croot = cproject
        croot.categories.append(pcat)
        root.children.append(croot)
    else:
        croot = croot[0]
        croot.attribs = cproject.attribs
        croot.attachments = cproject.attachments
        croot.efforts = cproject.efforts
        croot.description = cproject.description
        croot.children = []

    def add_tasks(ftask, ctask):
        if ftask.children and ftask.effort == 0:
            #a parent task with milestone children only
            return False
        
        for t in ftask.children:
            if t.milestone: continue
            c = make_task(t, resource, encoding)
            if add_tasks(t, c):
                ctask.children.append(c)

        return True

    add_tasks(project, croot)

    
    out = codecs.open(path, 'w', 'utf-8')
    print >> out, '<?xml version="1.0" ?>'
    print >> out, '<?taskcoach release="0.58" tskversion="13"?>'
    print >> out, root.xml()
    out.close()
    return True
