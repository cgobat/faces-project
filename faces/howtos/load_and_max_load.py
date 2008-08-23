# -*- coding: iso8859-15 -*-

"""
load & max_load
---------------------------------
  This file demonstrates the difference between load and max_load

"""

from faces import *
from faces.lib import report
from faces.lib import gantt
from faces.lib import resource

class Bob(Resource):
    max_load = 1.5 # Bob may have a 50% overtime
    
    
class Jim(Resource):
    pass


def Different_Loads():
    start = "2005-1-16"
    load = WeeklyMax("30H") # is equivalent to 30H / 40H (the default working week)
                            # == 0.75
    
    def Mutliple_Resources():
        effort = "1w"
	#Jim gets a smaller load than Bob
	resource = Jim(load=WeeklyMax("20H")) & Bob 
	
    def Overtime_Task():
	effort = "1w"
	#Bob has a max_load of 1.5, therefore this task is allocated at the same time as 
	#Task "Mutliple_Resources"
	resource = Bob
	
    def Defered_Task():
	load = 2.0 
	#if load is set explicitly and max_load < load, max_load will become load
        
        effort = "2d"
	resource = Jim
	#the task can only be booked after  Task "Mutliple_Resources"
	
    def Temporary_Overtime():
	effort = "1d"
	#For this task the max_load for all resources is increased to 2.0
	max_load = DailyMax("16H") # a 100% overtime
	load = 1.0
	resource = Jim
	
	#Watch what happens if you uncomment the next line
	#priority = 800 
	#If priority = 800, this task will be allocated before the task 'Multiple_Resources'.
	#When faces want's to allocate the task 'Multiple_Resources' the max_load is 1.0 
	#and  'Multiple_Resources' will be deferred after this task.
		
	#This task will not be deferred because of its max_load.
    
	
	
project = BalancedProject(Different_Loads)

class Gantt(gantt.Standard):
    data = project
    sharex = "all"
    
    
class Loads(resource.Standard):
    data = project
    sharex = "all"

    def modify_row(self, row_widget, res):
        self.add_load_line(row_widget, 1.0, edgecolor="orange")
        self.add_load_line(row_widget, 2.0, edgecolor="red")
        

