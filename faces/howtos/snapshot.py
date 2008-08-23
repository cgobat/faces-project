# -*- coding: iso8859-15 -*-

"""
Snapshot
---------------------------------
  This file demonstrates the use of snapshots.
  Snpshots can be created by the menu command at
  Files/Create Snapshot.
"""

from faces import *
from faces.lib import report
from faces.lib import gantt

import snapshot_snpt #This module contains snapshots

Resource.rate = 310.0

class Developers(Resource):
    title = "Developers"


class dev1(Developers):
    title = "Paul Smith"
    rate = 330.0


class dev2(Developers):
    title = "Sébastien Bono"


class dev3(Developers):
    title = "Klaus Müller"
    vacation = [("2002-02-01", "2002-02-05")]


# This is one way to form teams
developers = dev1 & dev2(load=0.5) & dev3
developers.title = "Developers"

class tester(Resource):
    title = "Peter Murphy"
    load = 0.8
    rate = 240.0


class doc(Resource):
    title = "Dim Sung"
    rate = 280.0
    vacation = [("2002-03-11", "2002-03-16")]



def Acso():
    title = "Accounting Software"
    note = ""
    now = "2002-03-05 13:00"
    load = WeeklyMax("35H")
    
    working_days = ("mon,tue,wed,thu,fri", "9:00-13:00", "14:00-18:00")
    
    minimum_time_unit = 60
    account = "dev"

    def PlanAndControl():
        title = "Planing and Controlling"
        #for meeting etc
        resource = dev1 & dev2 & dev3 & tester & doc
        start = up.Deliveries.Begin.start
        end = up.Deliveries.Done.end
        load = WeeklyMax("4H")

        
    def Deliveries():
        title = "Milestones"
        
        account = "rev"

        def Begin():
            title = "Projectstart"
            milestone = True
            start = Multi("2002-01-16", delayed="2002-01-24")
            credit = 33000.0 
            
        def Prev():
            title = "Technology Preview"
            milestone = True
            start = up.up.Software.Backend.end
            credit = 13000.0 
            gantt_same_row = up.Begin

        def Beta():
            title = "Betaversion"
            milestone = True
            start = up.up.Test.Alpha.end
            credit = 13000.0 
            gantt_same_row = up.Begin

        def Done():
            title = "Ship Product to customer" 
            milestone = True
            gantt_same_row = up.Begin
            start = max(up.up.Test.Beta.end, up.up.Manual.end)
            credit = 14000.0 

    def Spec():
        title = "Specification"
        effort = Multi("23d", before="20d")
        resource = developers
        start = up.Deliveries.Begin.end

    def Software():
        title = "Software Development"
        priority = 1000
        
        def Database():
            title = "Database coupling"
            effort = Multi("30d", before="20d")
            resource = Multi(dev1, before=dev1 & dev2)
            start = up.up.Spec.end

        def Gui():
            title = "Graphical User Interface"
            effort = Multi("35d", delayed="40d")
            start = max(up.Database.end, up.Backend.end)
            resource = dev2 & dev3

        if root.scenario != "before":
            def WebInterface():
                title = "Web Interface"
                effort = "30d"
                start = max(up.Database.end, up.Backend.end)
                resource = dev1 | dev2 | dev3
            
        def Backend():
            title = "Back-End Functions"
            effort = Multi("35d", before="30d")
            complete = 95 
            start = max(up.Database.end, up.up.Spec.end)
            resource = dev1 & dev2 


    def Test():
        title = "Software testing"
        
        def Alpha():
            title = "Alpha Test"
            effort = "1w"
            start = up.up.Software.end 
            resource = tester & dev2
            note = "Hopefully most bugs will be found and fixed here."

        def Beta():
            title = "Beta Test"
            effort = "4w"
            start = up.Alpha.end
            resource = tester & dev1

    def Manual():
        max_load = 1.0
        title = "Manual"
        effort = "11w"
        start = up.Deliveries.Begin.end
        account = "doc"
        resource = dev3 & doc

acso_standard = BalancedProject(Acso, balance=SLOPPY)
acso_before = BalancedProject(Acso, balance=SLOPPY, scenario="before")
snapshot = BalancedProject(snapshot_snpt.acso_standard_060414_0030)

class Union(gantt.Compare):
    data = unify(acso_standard, acso_before, snapshot)
    sharex = "time_share"

class Intersection(gantt.Compare):
    #notice: the task web interface will not be displayed
    data = intersect(acso_standard, snapshot)
    
    
class Difference(gantt.Compare):
    #only the tasks that differs will be displayed
    data = difference(acso_standard, snapshot)

class Compare(report.Standard):
    data = unify(acso_standard, snapshot)
    headers = ("Name", 
               "Start(current)",  
               "Start(before)",
               "Effort(current)",
               "Effort(before)",
               "Costs(current)",
               "Costs(before)")
    
    def make_report(self, data):
        for t1, t2 in data: 
            t = t1 or t2
            if t.path.find("Deliveries") > 0: continue
            yield (t.indent_name(),
                   t1 and t1.to_string.start or "",
                   t2 and t2.to_string.start or "",
                   t1 and t1.to_string.effort or "",
                   t2 and t2.to_string.effort or "",
                   t1 and t1.costs("rate") or "",
                   t2 and t2.costs("rate") or "")
            
    def modify_row(self, row):
        for c in row:
            if not c: c.back_color = "gray"
            
        if row[3] != row[4]:
            row[3].back_color = "red"
        
        return row

#------------
from faces.lib import resource

class BeforeRes(resource.Standard):
    data = acso_before
    sharex = "time_share"

class SnapRes(resource.Standard):
    data = snapshot
    sharex = "time_share"
