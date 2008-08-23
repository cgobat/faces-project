############################################################################
#   Copyright (C) 2006 by Reithinger GmbH
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

import gv
import faces.task
import sys
import faces.charting.charts as charts
import faces.charting.faxes as faxes
import faces.charting.widgets as widgets
import faces.charting.patches as patches
import faces.charting.connector as connector
from faces.charting.tools import *
import faces.charting.printer as printer

remove = gv.rm


class Graphviz(object):
    def __init__(self, go):
        self._go = go

    def __getattr__(self, name):
        return gv.getv(self._go, name)


    def __setattr__(self, name, value):
        if name[0] == "_":
            super(Graphviz, self).__setattr__(name, value)
        else:
            gv.setv(self._go, name, str(value))

        
class Node(Graphviz):
    def name(self):
        return gv.nameof(self._go)

    name = property(name)



class Edge(Graphviz):
    def head(self):
        return Node(gv.headof(self._go))

    head = property(head)

    def tail(self):
        return Node(gv.tailof(self._go))

    tail = property(tail)

    

class Digraph(Graphviz):
    def __init__(self, graph=None, name=None):
        if graph:
            self._go = gv.readstring(str(input))
        elif name:
            self._go = gv.digraph(name)

        self._counter = 0

    def __del__(self):
        if remove:
            remove(self._go)
        

    def add_node(self, name=None, **kwargs):
        if not name:
            self._counter += 1
            name = str(self._counter)
            
        node = Node(gv.node(self._go, name))
        for k, v in kwargs.items():
            setattr(node, k, v)
        return node

                           
    def add_edge(self, tail, head, **kwargs):
        edge = Edge(gv.edge(tail._go, head._go))
        for k, v in kwargs.items():
            setattr(edge, k, v)
            
        return edge


    def layout(self, engine):
        gv.layout(self._go, engine)
        
    def render(self, format, filename=None):
        if filename:
            gv.render(self._go, format, filename)
        else:
            gv.render(self._go, format)

    def __getattr__(self, name):
        return gv.getv(self._go, name)


    def name(self):
        return gv.nameof(self._go)

    name = property(name)


    def nodes(self):
        node = gv.firstnode(self._go)
        while node:
            yield Node(node)
            node = gv.nextnode(self._go, node)

    nodes = property(nodes)

    def edges(self):
        edge = gv.firstedge(self._go)
        while edge:
            yield Edge(edge)
            return
            print "hier"
            edge = gv.nextedge(self._go, edge)
            print "da"

    edges = property(edges)



class GraphVizChart(charts.MatplotChart):
    data = None
    properties = {#"size" : "sularge", 
                  "facecolor" : "white",
                  "edgecolor" : "black",
                  "linewidth" : 1,
                  "antialiased" : True }
    
    def create_axes(self, rect=None, **kwargs):
        pprop = self.get_patch
        rect = rect or [0, 0, 1, 1]
        fig = self.figure
        ax = fig.add_axes(faxes.PointAxes(fig, rect, **kwargs))
        ax.cla()
        ax.set_marker(pprop("focused.marker"), pprop("marker"))
        return ax

    def get_nodes(self, data):                                                          
        "overwrite"
        for t in data:
            yield t
    
    def printer(cls, **kwargs):
        return printer.PointPrinter(cls, **kwargs)
           
    printer = classmethod(printer)
            
    def create_node_widget(self, node):
        "overwrite"
        pprop = self.get_patch
        
        debug = node.name == "Task3" 
        big = widgets.TableWidget(2, 1)
        small = widgets.TableWidget(2, 2)
        title = widgets.BoxedTextWidget(node.title, node, fattrib="title") 
        start = widgets.BoxedTextWidget(node.to_string.start, node, fattrib="start", left=2) 
        end = widgets.BoxedTextWidget(node.to_string.end, node, fattrib="end", left=2) 
        effort = widgets.BoxedTextWidget(node.to_string.effort, node, fattrib="effort", left=2) 
        length = widgets.BoxedTextWidget(node.to_string.length, node, fattrib="length", left=2) 
        
        big.debug = debug and "big %s" % node.name
        end.debug = debug and "end"
        
        big.set_cell(0, 0, title)
        big.set_cell(1, 0, small)
        small.set_cell(0, 0, start, halign="left")
        small.set_cell(0, 1, end, halign="left")
        small.set_cell(1, 0, length, halign="left")
        small.set_cell(1, 1, effort, halign="left")
        big.add_artist(patches.Rectangle((LEFT, BOTTOM), 
                                       RIGHT-LEFT,
                                       TOP-BOTTOM, 
                                       **pprop("box")))
        
        return big
                                      

    def get_edges(self, nodes):
        "overwrite"
        for t in nodes:
            for sources in t._sources.values():
                for s in sources:
                    path, sattrib = faces.task._split_path(s)
                    yield t.get_task(path), t
                    
    def create_graph(self):
        "overwrite"
        graph = graphviz.Digraph(name="G")
        graph.nodesep = "0,5"
        graph.rankdir = "LR"
        graph.ordering = "in"
        graph.outputorder = "nodesfirst"
        graph.ranksep = "1.4 equally"
        graph.splines = False
        graph.start = "regular"
        return graph
        
        
    def create(self):
        push_active(self)

        w = widgets.TableWidget(3, 2)
        
        helper = faxes.PointAxes(self.figure, [0, 0, 1, 1])
        helper.check_limits()

                
        graph = self.create_graph()
        
        node_to_widget = { }
        nodes = {}        
        for n in self.get_nodes(self.data):
            widget = self.create_node_widget(n)
            helper.add_widget(widget)
            l, b, w, h = widget.bbox.get_bounds()
            w = "%.2f" % (w/72.0)
            h = "%.2f" % (h/72.0)
            w = w.replace(".", ",")
            h = h.replace(".", ",")
            node = nodes[n] = graph.add_node(shape="box", width=w, height=h)
            node_to_widget[node.name] = widget
            
        print "nodes added"
            
        edges = []
        for n1, n2 in self.get_edges(nodes.keys()):
            edges.append((n1, n2))
            graph.add_edge(nodes[n1], nodes[n2])
                           
        
        graph.layout("dot")

        graph.render("dot", "/home/michael/temp/test.dot")
        l, b, r, gheight = map(int, graph.bb.split(","))
                
        for n in graph.nodes:
            w = node_to_widget[n.name]
            x, y = map(int, n.pos.split(","))
            w.set_pos(x, - gheight + y)
            self.axes.add_widget(w)
            
        for n1, n2 in edges:
            w1 = node_to_widget[nodes[n1].name]
            w2 = node_to_widget[nodes[n2].name]
            c = connector.ShortConnector(w1, w2)
            self.axes.add_widget(c)
        
        pop_active()



if __name__ == "__main__":
    graph = Digraph(name="G")
    graph.nodesep = "0,05"
    graph.rankdir = "LR"
    graph.ordering = "in"
    graph.outputorder = "nodesfirst"
    graph.ranksep = "1.4 equally"
    graph.splines = False
    graph.start = "regular"
    n1 = graph.add_node(label="1", width="3,23", shape="box")
    n2 = graph.add_node(label="2")
    print "n1", n1.label, n1.name, n1.width
    e = graph.add_edge(n1, n2)
    graph.render("dot")

    graph.layout("dot")

    graph.render("dot")
    #out.render("png", "/home/michael/temp/test.png")
    #out.render("dot", "/home/michael/temp/test1.dot")
    print "nodes:"
    for n in graph.nodes:
        print "  ", n.name, n.label, n.width, n.pos

    print "edges:"
    print "  ", e.head.label, e.tail.label, e.pos
    #for e in graph.edges:
    #    print "  ", e.head.label, e.tail.label, e.pos
    
    print "ende"
