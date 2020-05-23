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
from builtins import object
import difflib


def intersect(p1, *args):
    """
    returns an iterator over a tuple of tasks (for
    each given project the corresponding task).
    The iterator includes only tasks, which
    can be found in all projects.

    @args: (project1, project2, ...)
    """

    for task in p1:
        result = [ task ]
        for o in args:
            t = o.get_task(task.path)
            if t:
                result.append(t)
            else:
                break
        else:
            yield tuple(result)
            

intersect.__call_completion__ = "intersect(|project1, project2)"


def unify_paths(pl1, pl2):
    s = difflib.SequenceMatcher()
    s.set_seqs(pl1, pl2)

    result = []
    for op, p1l, p1h, p2l, p2h in s.get_opcodes():
        if op == 'equal':
            result.extend(pl1[p1l:p1h])
        elif op == 'replace':
            result.extend(pl1[p1l:p1h])
            result.extend(pl2[p2l:p2h])
        elif op == 'delete':
            result.extend(pl1[p1l:p1h])
        elif op == 'insert':
            result.extend(pl2[p2l:p2h])

    return result

        
def unify(p1, *args):
    """
    returns an iterator over a tuple of tasks (for
    each given project the corresponding task).
    The iterator includes all tasks, which
    can be found in any projects.
    If a task is not in a project, the corresponding
    tuple position is None.

    @args: (project1, project2, ...)
    """
    
    result = [p.path for p in p1]

    for p in args:
        pl = [p.path for p in p]
        result = unify_paths(result, pl)

    args = list(args)
    args.insert(0, p1)
    for r in result:
        yield tuple([p.get_task(r) or None for p in args])
    
unify.__call_completion__ = "unify(|project1, project2)"

def difference(p1, *args, **kwargs):
    result = [p.path for p in p1]

    for p in args:
        pl = [p.path for p in p]
        result = unify_paths(result, pl)

    cmp_attribs = kwargs.get("cmp_attribs", ("start", "end", "effort"))
    def extract(t): return [getattr(t, n) for n in cmp_attribs]

    args = list(args)
    args.insert(0, p1)
    for r in result:
        result = tuple([p.get_task(r) or None for p in args])

        if result[0]:
            if result[0].children: yield result
            
            cond = extract(result[0])
            for t in result[1:]:
                if not t:
                    yield result
                    break

                if cond != extract(t):
                    yield result
                    break
        else:
            yield result



def _defer(func):
    class DeferExecution(object):
        __doc__ = func.__doc__
        
        def __init__(self, *args):
            self.args = args

        def __iter__(self):
            return func(*self.args)

    try:
        DeferExecution.__call_completion__ = func.__call_completion__
    except AttributeError:
        pass

    return DeferExecution

intersect = _defer(intersect)
unify = _defer(unify)
difference = _defer(difference)
