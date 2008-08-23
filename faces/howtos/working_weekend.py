# -*- coding: iso8859-15 -*-
"""
How to specify the weekend as working days?  
--------------------------------------------
I know that's not normal,however,it happens. 
So could somebody tell me how to do that? 
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

    #every saturday is now a working day
    working_days = [("mon,tue,wed,thu,fri", "8:00-12:00", "13:00-17:00"),
		    ("sat", "8:00-12:00")]
    
    #don't forget to adjust the following attributes if you want to use 
    #the corresponding date literals
    working_days_per_week = 5.5
    working_days_per_month = 22
    working_days_per_year = 220
       
    #make only sunday january 23 to a working day
    extra_work = [("2005-01-23 8:00", "2005-01-23 14:00")]
        
    def Task1():
        start = "2005-1-16"
        effort = "1w"
	
    def Task2():
	start = up.Task1.end
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


