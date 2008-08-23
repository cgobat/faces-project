# -*- coding: iso8859-15 -*-
"""
Planning a task start conditionally
-----------------------------------
 Lets assume there is taskA and taskB.
 How to plan the start of TaskB the next friday after the end of TaskA ? 
"""

from faces import *
from faces.lib import report
from faces.lib import gantt
from faces.lib import resource
from faces.lib import workbreakdown
from faces.lib import generator
from dateutil import relativedelta as rd


class Bob(Resource):
    pass


def My_Project():
    resource = Bob
    
    def TaskA():
        start = "2005-1-16"
        effort = "5d"

	
    def TaskB():
	start = up.TaskA.end.to_starttime()\
	      + rd.relativedelta(weekday=rd.FR(+1), hour=0, minute=0)
	effort = "1w"
	
	"""
	notice the to_starttime() method. It moves
	up.TaskA.end to the next possible start datetime.
	"""
	

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


