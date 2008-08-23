# -*- coding: iso8859-15 -*-
"""
Planning 1 resource in X projects
---------------------------------
 I want to plan for a single resource (me) in multiple projects. 
 Some projects have deadlines, which requires most work to be 
 done before then, but this way of work doesn't scale. I always 
 end up working for the first deadline, and after that there's 
 not enough time for the other projects, or too many new 
 (smallish) projects come up which take up time. 
  
 Is it possible with faces to 'plan' this? I'd like to say that 
 project A requires N hours, deadline march 1st, 
 project B requires M hours, deadline march 5th. 
 When 'N' increases, I'd like warnings that 'M' needs to 
 decrease, or maybe M can stay constant, but another project 
 will have to be adjusted. 
"""


from faces import *
from faces.lib import report
from faces.lib import gantt
from faces.lib import resource
from faces.lib import workbreakdown
from faces.lib import generator

class Chris(Resource):
    pass
    
def A():
    title = "A"
    start = "2005-2-22"
    effort = "4d" #change this to 5d to get a warning 
    resource = Chris

    def __constraint__():
	assert_(me.end <= "2005-3-1")

	
def B():
    title = "B"
    start = "2005-2-22"
    effort = "5d"
    resource = Chris

    def __constraint__():
	if me.end > "2005-3-5":
	    # a nicer message then the standard assert_ 
	    raise RuntimeError("You have to adjust Project 'B'")
	
    
    
def All_Projects():
    Sub_A = A
    Sub_B = B

    
project = BalancedProject(All_Projects)


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


