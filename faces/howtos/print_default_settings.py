# -*- coding: utf-8 -*-

# -*- coding: iso8859-15 -*-

"""
How to Set print dialog defaults
----------------------------
I'd like to calculate facility costs. 
E.g. a facility costs 1.000 per month. 
I could approximate it by adding such a resource with a daily rate. 
But then I would need to assign it with a certain effort which would
rollup to the the total effort. Of cause I want to see the total 
effort of human resources. 
 
"""


from faces import *
from faces.lib import report
from faces.lib import gantt
from faces.lib import resource
from faces.lib import workbreakdown
from faces.lib import generator

class Bob(Resource):
    pass


def My_Project():
    resource = Bob
    start = "2005-1-16"
    
    def Task1():
        effort = "1w"


project = BalancedProject(My_Project)


class Gantt(gantt.Standard):
    data = project
    sharex = "share1"
    

class Report(report.Standard):
    data = project

    def make_report(self, data):
        for t in data: 
            yield (t.indent_name(), t.start, t.end, t.effort)
    

class Load(resource.Standard):
    data = project
    sharex = "share1"


class Structure(workbreakdown.Standard):
    data = project


class HTML(generator.StandardHTML):
    observers = generator.all()

def print_my_chart():
    printer = Gantt.printer()
    printer.filename = "/tmp/gantt.pdf"
    printer.linewidth = 1.00
    printer.edgecolor = "black"
    printer.unit = "inch"
    printer.set_xlimits(6849430.00, 6852931.00)
    printer.set_ylimits(-0.00, 8)
    printer.fontsize = 6
    printer.width = 10.50
    printer.save()
    printer.end()

    import webbrowser
    webbrowser.open("file:///tmp/gantt.pdf", True, False)

print_my_chart.faces_menu = "Print Gantt"
