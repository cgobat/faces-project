# -*- coding: utf-8 -*-

"""
This file demonstrates the use of multiple different Calendars within a project
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
    
def Example1():
    #Notice that the projects ends at 17:00 while the last task 
    # (SamkeLikeCalendar2.Task4) ends at 17:30. This is because
    #17:30 is no a valid working time at the projects calendar
    
    resource = Bob
    vacation = [("2005-1-18", "2005-1-19")]
    working_days = ("mon,tue,wed,thu,fri", "8:00-12:00", "13:00-17:00")
    
    
    def Calendar1():
        def Task1():
            start = "2005-1-16"
            effort = "1w"
            
        def Task2():
            start = up.Task1.end
            effort = "0.5d"
            

    def Calendar2():
        vacation = [("2005-1-26", "2005-1-27")]
        working_days = ("mon,tue,wed,thu,fri", "7:30-11:30", "13:30-17:30")

        def Task3():
            start = up.up.Calendar1.end
            effort = "1.5d"
    
            
    def SameLikeCalendar2():
        calendar = up.Calendar2.calendar
        
        def Task4():
            start = up.up.Calendar2.Task3.start
            effort = "2d"
        
            

Example1.balanced = BalancedProject(Example1)

##################################################################

#Another example to set a standard calendar

calendar1 = Calendar()
calendar1.set_working_days("mon,tue,wed,thu,fri", "8:00-12:00", "13:00-17:00")
calendar1.set_vacation([("2005-1-18", "2005-1-19")])

calendar2 = Calendar()
calendar2.set_working_days("mon,tue,wed,thu,fri", "7:30-11:30", "13:30-17:30")


def Example2():
    resource = Jim
    
    calendar = calendar1 | calendar2
    #calendar unifies all working times and days of calendar1 and calendar2
    
    def Calendar1():
        calendar = calendar1
        
        def Task1():
            start = "2005-1-16"
            effort = "1w"
            
        def Task2():
            start = up.Task1.end
            effort = "0.5d"
            

    def Calendar2():
        calendar = calendar2

        def Task3():
            start = up.up.Calendar1.end
            effort = "1.5d"
    
            
    def SameLikeCalendar2():
        calendar = up.Calendar2.calendar
        
        def Task4():
            start = up.up.Calendar2.Task3.start
            effort = "2d"
    

Example2.balanced= BalancedProject(Example2)

class Gantt1(gantt.Standard):
    data = Example1.balanced
    

class Gantt2(gantt.Standard):
    data = Example2.balanced
    
    
    

class Report1(report.Standard):
    data = Example1.balanced

    def make_report(self, data):
        for t in data: 
            yield (t.indent_name(), t.start, t.end, t.effort)

            
class Report2(Report1):
    data = Example2.balanced
            

class Load1(resource.Standard):
    data = Example1.balanced
    

class Load2(resource.Standard):
    data = Example2.balanced
    


