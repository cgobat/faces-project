# -*- coding: utf-8 -*-
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
    minimum_time_unit = 1
    
    def Task1():
        effort = "1w"
        
        
    def Communication():
        start = up.start
        effort = "1H"
        length = "0H"
        


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

