# -*- coding: iso8859-15 -*-

"""
How to calculate basic costs
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



class dev1(Resource):
    rate = 330.0


class dev2(Resource):
    rate = 300

month_per_minute = 1.0 / (30*24*60) # duration is calculated in minutes

def Acso():
    facility_cost = 0.0 #always set a default
        
    def Spec():
        title = "Specification"
        effort = "23d"
        resource = dev1
        start = "1.1.2006"
        facility_cost = 100.0 # a fixed cost
        
    def Software():
        title = "Software Development"
        priority = 1000
        
        def Database():
            title = "Database coupling"
            effort = "31d"
            resource = dev1
            start = up.up.Spec.end
            facility_cost = me.duration * 150 * month_per_minute
            

        def Gui():
            title = "Graphical User Interface"
            effort = Multi("35d", delayed="40d")
            start = up.Database.end
            resource = dev2
            facility_cost = me.duration * 100 * month_per_minute
    

acso_standard = BalancedProject(Acso, balance=SLOPPY)

class Costs(report.Standard):
    data = acso_standard
    headers = ("Name", "Start", "End", "Resource Costs", "Facility Costs", "Sum")
    
    def make_report(self, data):
        for t in data: 
            yield (t.indent_name(), t.start, t.end, 
                   t.costs("rate"), t.sum("facility_cost"),
                   t.costs("rate") + t.sum("facility_cost"))

