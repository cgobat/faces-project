# -*- coding: utf-8 -*-
"""
if I have a task with 3 subtasks, and I want all
3 subtasks done by the same resource but I don't care which one, how should
that be coded?
"""

from faces import *
from faces.lib import report
from faces.lib import gantt
from faces.lib import resource
from faces.lib import workbreakdown
from faces.lib import generator

class Bob(Resource):
    pass

class Jim(Resource):
    pass
    

def My_Project():
    resource = Jim|Bob
    start = "2005-1-16"
    
    def Task1():
        effort = "1w"

    def Task2():
        effort = "2d"
        resource = up.Task1.booked_resource
        
    def Task3():
        effort = "4d"
        resource = up.Task2.booked_resource

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

