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
import sys

_ = faces.plocale.get_gettext()
_is_source_ = True
_cache = { }

__all__ = ("generate_for_resources", "generate", "clear_cache", "read", "update_project")


class Node(object):
    def __init__(self, name, **attribs):
        self.name = name
        self.attribs = attribs
        self.text = []
        self.children = []

    def add_char_data(self, data):
        self.text.append(data)

    def add_element(self, name, attribs):
        element = Node(name, **convert_attribs(attribs))
        self.children.append(element)
        return element

    def xml(self):
        attribs = map(lambda kv: u'%s="%s"' % kv, self.attribs.items())
        attribs = ' '.join(attribs)
        children = map(lambda x: x.xml(), self.children)
        children = ''.join(children)
        return u'<%s %s>%s%s</%s>' % (self.name, attribs, u''.join(self.text), children, self.name)


class RecursiveNode(Node):
    def add_element(self, name, attribs):
        if name == self.name:
            element = self.__class__(**convert_attribs(attribs))
            self.children.append(element)
            return element
        return super(RecursiveNode, self).add_element(name, attribs)

class Category(RecursiveNode):
    def __init__(self, **attribs):
        super(Category, self).__init__('category', **attribs)

        categorizables = attribs.get('categorizables', '')
        if categorizables:
            self.categorizables = set(categorizables.split())
        else:
            self.categorizables = set()

    def belongs(self, obj):
        return obj.attribs['id'] in self.categorizables

    def add(self, obj):
        self.categorizables.add(obj.attribs['id'])

    def xml(self):
        if self.categorizables:
            self.attribs['categorizables'] = u' '.join(self.categorizables)
        else:
            try:
                del self.attribs['categorizables']
            except KeyError:
                pass

        return super(Category, self).xml()


class Effort(Node):
    def __init__(self, **attribs):
        super(Effort, self).__init__('effort', **attribs)


class Task(RecursiveNode):
    def __init__(self, **attribs):
        super(Task, self).__init__('task', **attribs)

    def add_element(self, name, attribs):
        if name == 'effort':
            effort = Effort(**convert_attribs(attribs))
            self.children.append(effort)
            return effort
        return super(Task, self).add_element(name, attribs)

    def __iter__(self):
        def walkdown(obj):
            if isinstance(obj, Task):
                yield obj
            try:
                for c in obj.children:
                    for r in walkdown(c):
                        if isinstance(r, Task):
                            yield r
            except AttributeError:
                pass

        return walkdown(self)


class TaskList(Task):
    def __init__(self):
        super(TaskList, self).__init__(subject="root")

    def add_element(self, name, attribs):
        try:
            element = { 'task': Task,
                        'category': Category }[name](**convert_attribs(attribs))
        except KeyError:
            return super(TaskList, self).add_element(name, attribs)
        else:
            self.children.append(element)
            return element

    def filter_for_category(self, category):
        return filter(lambda x: isinstance(x, Task) and category.belongs(x), self.children)

    def xml(self):
        return ''.join(map(lambda x: x.xml(), self.children))


def assign_categories(categories, tasks):
    for category in categories:
        for task in tasks:
            category.add(task)


def parse_file(path):
    root = TaskList()
    stack = [ root ]
    parser = xml.parsers.expat.ParserCreate()

    def start_element(name, attrs):
        if name == "tasks":
            return

        element = stack[-1].add_element(name, attrs)
        stack.append(element)

    def end_element(name):
        if name == "tasks":
            return

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


def make_id(task):
    return '%s:%s'% (id(task), time.time())


def make_task(ftask, resource, encoding):
    t = Task(subject=ftask.name.decode(encoding),
             id=make_id(ftask).decode(encoding),
             priority=ftask.priority,
             lastModificationTime=str(datetime.datetime.now()),
             startdate=str(ftask.start.to_datetime().date()),
             duedate=str(ftask.end.to_datetime().date()))

    description = Node('description')

    if ftask.title != ftask.name:
        description.text.append(ftask.title)

    try:
        description.text.append(textwrap.dedent(ftask.notes).strip())
    except AttributeError:
        pass

    t.children.append(description)

    if resource:
        resources = [ resource ]
    else:
        resources = list(ftask._iter_booked_resources())

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

                t.children.append(e)

            budget += b.work_time

    t.attribs["budget"] = "%i:%i:0" % (budget / 60, budget % 60)
    return t


def find_project_categories(root, project_id):
    for facesCategory in root.children:
        if isinstance(facesCategory, Category) and facesCategory.attribs['subject'] == 'Faces projects':
            break
    else:
        facesCategory = Category(subject=u'Faces projects')
        facesCategory.attribs['id'] = make_id(facesCategory)
        root.children.append(facesCategory)

    for projectCategory in facesCategory.children:
        if isinstance(projectCategory, Category) and projectCategory.attribs['subject'] == project_id:
            break
    else:
        projectCategory = Category(subject=projectId)
        projectCategory.attribs['id'] = make_id(projectCategory)
        facesCategory.children.append(projectCategory)

    return projectCategory, facesCategory


def read(path, project_id, clear_cache=False):
    if _cache.has_key(path):
        if clear_cache:
            del _cache[path]
        else:
            return _cache[path]

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

        root = parse_file(p)
        projectCategory, facesCategory = find_project_categories(root, project_id)

        def find_items(task, path=""):
            if path:
                path = '%s.%s' % (path, task.attribs['subject'])
            else:
                if not projectCategory.belongs(task):
                    return []
                path = project_id

            items = map(lambda t: find_items(t, path), [child for child in task.children if isinstance(child, Task)])
            if items:
                return reduce(operator.add, items, [])

            def convert_effort(effort):
                description = None
                for child in effort.children:
                    if child.name == 'description':
                        try:
                            description = child.text[0]
                        except IndexError:
                            pass
                        break

                resname = description or default_resname

                fmt = '%Y-%m-%d %H:%M'
                start = effort.attribs["start"][:16]
                stop = effort.attribs["stop"][:16]

                delta = datetime.datetime.strptime(stop, fmt) - datetime.datetime.strptime(start, fmt)

                return (path, resname, start, stop, delta)

            return map(convert_effort, [child for child in task.children if isinstance(child, Effort)])

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

    projectCategory, facesCategory = find_project_categories(root, project._idendity_().decode(encoding))

    croot = root.filter_for_category(projectCategory)

    cproject = make_task(project, resource, encoding)

    if not croot:
        croot = cproject
        root.children.append(croot)
    else:
        croot = croot[0]
        croot.attribs = cproject.attribs
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

    assign_categories([facesCategory, projectCategory], croot)

    out = codecs.open(path, 'w', 'utf-8')
    print >> out, '<?xml version="1.0" ?>'
    print >> out, '<?taskcoach release="0.70.1" tskversion="19"?>'
    print >> out, '<tasks>%s</tasks>' % root.xml().encode('UTF-8')
    out.close()
    return True

 	  	 
