# -*- coding: iso8859-15 -*-
"""
Planning a periodical task
--------------------------
How do you plan a task occuring every day or month  ? 
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


"""
A task can only have one start and one end date and can therefore
never be periodic but you can plan multiple tasks ouccuring periodically
"""
    
def make_periodical(inc, effort="1H"):
    """
    creates a bunch of periodical tasks
    inc: a relativedelta instance from dateutil specifying the periodical increment
    effort: the effort of each task
    
    the task in which this function is called
    must have a start and an end date specified
    
    """
    import faces.pcalendar as pcal
    
    start = me.start.to_datetime() + inc
    end = me.end.to_datetime()

    def mk_Periodical(start_, effort_):
        #create one of the periodical tasks
        def Periodical():
            start = start_
            effort = effort_
            gantt_same_row = up.p_1 #makes a gantt chart to display all tasks in the same row

        return Periodical
    
    j = 1
    while start < end:
        task_name = "p_%i" % j
        task_func = mk_Periodical(start, effort)
        setattr(me, task_name, task_func)
        start += rd.relativedelta(days=+1) + inc
        j += 1
    
    

def My_Project():
    resource = Bob

    def Periodic():
        start = "2005-1-14"
        end = "2005-2-16"
        
        inc = rd.relativedelta(weekday=rd.MO(+1), hour=8, minute=0) # every task should start Monday 8:00 am
        make_periodical(inc, "1d")
            
        

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

