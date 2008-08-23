# -*- coding: utf-8 -*-

"""
Changing the zoom to fit
------------------------
This examples changes the zoom to fit button to fixed zoom position
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
    start = "1.1.2005"
    now = "5.1.2005 10:00"
    minimum_time_unit = 1
    
    def Task1():
        effort = "1w"
        
        
    def Task2():
        start = up.start
        effort = "2H"
        
        


project = BalancedProject(My_Project)
project = AdjustedProject(project)


class Gantt(gantt.Standard):
    data = project
    sharex = "share1"
    show_now = True
    
    def setup_axes_interface(self, axes):
        super(Gantt, self).setup_axes_interface(axes)
        
        def autoscale_view():
            now = self.data.calendar.WorkingDate(self.data.calendar.now)
            axes.set_time_lim(now - "4d", now + "4d")
            axes.check_limits()
            
        self._autoscale_view = autoscale_view
    

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

