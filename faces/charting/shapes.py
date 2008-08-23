#@+leo-ver=4
#@+node:@file charting/shapes.py
#@+at
# gantt widgets can have the different shapes in this modules.
# 
# For all shapes:
# the first item of the returned shape list, has to be a patch, that defines, 
# the connection points
# 
# 
#@-at
#@@code
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
from patches import *
from tools import *
import widgets


#@-node:<< Imports >>
#@nl

__all__ = ("bar", "brace", "combibar", "diamond", "circle", "wedge", "house")
_is_source_ = True

#@+others
#@+node:bar
def bar(props, name, complete=0):
    kwargs = make_properties(props, name)
    bar = Polygon(((LEFT, BOTTOM),
                   (LEFT, VCENTER),
                   (LEFT, TOP),
                   (HCENTER, TOP),
                   (RIGHT, TOP),
                   (RIGHT, VCENTER),
                   (RIGHT, BOTTOM),
                   (HCENTER, BOTTOM)), **kwargs)
    if complete:
        kwargs = make_properties(props, "%s.complete" % name)
        complete /= 100.0
        complete = Rectangle((LEFT, BOTTOM + VSEP * FACTOR / 4),
                             (RIGHT - LEFT) * complete,
                             VSEP * FACTOR / 2,
                             **kwargs)
        return (bar, complete)

    return (bar,)
#@-node:bar
#@+node:brace
def brace(props, name):
    kwargs = make_properties(props, name)
    HALF = FACTOR / 2
    return (Polygon([(LEFT, TOP),
                     (RIGHT, TOP),
                     (RIGHT, BOTTOM),
                     (RIGHT - HALF * HSEP, BOTTOM + HALF * VSEP),
                     (LEFT + HALF * HSEP, BOTTOM + HALF * VSEP),
                     (LEFT, BOTTOM)], **kwargs),)
#@-node:brace
#@+node:combibar
def combibar(props, name, left, right, complete):
    left = left(props, name + ".start", VCENTER, LEFT)
    right = right(props, name + ".end", VCENTER, RIGHT)

    half_height = props(name + ".bar.height") * VSEP / 2
    top = VCENTER + half_height
    bottom = VCENTER - half_height

    def left_vert(vert):
        x, y = float(vert[0]), float(vert[1])
        return x < LEFT.get() or y > top.get() or y < bottom.get()

    def right_vert(vert):
        x, y = float(vert[0]), float(vert[1])
        return x > RIGHT.get() or y > top.get() or y < bottom.get()

    outline_verts = filter(left_vert, left[0].get_verts())\
                    + [(HCENTER, top), (HCENTER, bottom)] \
                    + filter(right_vert, right[0].get_verts())

    outline = Polygon(outline_verts)
    outline.set_visible(False)

    kwargs = make_properties(props, name + ".bar")
    bar = Polygon([(LEFT, top), (RIGHT, top),
                   (RIGHT, bottom), (LEFT, bottom)], **kwargs)

    #only take the visible part of the symbols
    sleft = left[int(len(left) > 1)]
    sright = right[int(len(right) > 1)]

    if complete:
        kwargs = make_properties(props, name + ".complete")
        half_height = props(name + ".complete.height") * VSEP / 2
        top = VCENTER + half_height
        bottom = VCENTER - half_height
        right = LEFT + (RIGHT - LEFT) * complete / 100
        complete = Polygon([(LEFT, top), (right, top),
                            (right, bottom), (LEFT, bottom)], **kwargs)

        return (outline, bar, complete, sleft, sright)

    return (outline, bar, sleft, sright)
#@-node:combibar
#@+node:diamond
def diamond(props, name="", vc=None, hc=None):
    """
    A diamond symbol, that can be be used as an argument,
    for a widgets set_shape method or for a combined shape
    like combibar.

    @args:
    """
    if name: name = ".%s" % name
    vc = vc or VCENTER
    hc = hc or HCENTER
    kwargs = make_properties(props, "diamond" + name)
    mag = props("diamond" + name + ".magnification")
    HALF = mag * FACTOR / 2
    return (Polygon([(hc - HALF * HSEP, vc),
                     (hc, vc - HALF * VSEP),
                     (hc + HALF * HSEP, vc),
                     (hc, vc + HALF * VSEP)], **kwargs),)
#@-node:diamond
#@+node:circle
def circle(props, name="", vc=None, hc=None):
    if name: name = ".%s" % name
    vc = vc or VCENTER
    hc = hc or HCENTER
    kwargs = make_properties(props, "circle" + name)
    mag = props("circle" + name + ".magnification")

    HALF = mag * FACTOR / 2

    shape = (Polygon([(hc - HALF * HSEP, vc),
                      (hc, vc - HALF * VSEP),
                      (hc + HALF * HSEP, vc),
                      (hc, vc + HALF * VSEP)]),
             Circle((hc, vc), HALF*VSEP, **kwargs))
    shape[0].set_visible(False)
    return shape
#@-node:circle
#@+node:wedge
def wedge(props, name="", vc=None, hc=None):
    if name: name = ".%s" % name
    vc = vc or VCENTER
    hc = hc or HCENTER
    kwargs = make_properties(props, "wedge" + name)
    mag = props("wedge" + name + ".magnification")

    HALF = mag * FACTOR / 2

    if props("wedge" + name + ".up", True):
        base = VCENTER - HALF * VSEP
        head = VCENTER + HALF * VSEP
    else:
        base = VCENTER + HALF * VSEP
        head = VCENTER - HALF * VSEP

    return (Polygon([(hc - HALF * HSEP, base),
                     (hc, base),
                     (hc + HALF * HSEP, base),
                     (hc + HALF * HSEP / 2, vc),
                     (hc, head),
                     (hc - HALF * HSEP / 2, vc)], **kwargs),)
#@-node:wedge
#@+node:house
def house(props, name="", vc=None, hc=None):
    if name: name = ".%s" % name
    vc = vc or VCENTER
    hc = hc or HCENTER
    kwargs = make_properties(props, "house" + name)
    mag = props("house" + name + ".magnification")

    HALF = mag * FACTOR / 2

    if props("house" + name + ".up", True):
        base = VCENTER - HALF * VSEP
        head = VCENTER + HALF * VSEP
    else:
        base = VCENTER + HALF * VSEP
        head = VCENTER - HALF * VSEP

    return (Polygon([(hc - HALF * HSEP, base),
                     (hc, base),
                     (hc + HALF * HSEP, base),
                     (hc + HALF * HSEP, vc),
                     (hc, head),
                     (hc - HALF * HSEP, vc)], **kwargs),)
#@-node:house
#@-others

symbols = ("diamond", "circle", "wedge", "house")

#@-node:@file charting/shapes.py
#@-leo
