# -*- coding: utf-8 -*-
"""
Allocate Tasks to a Resource with as much load as possible.
This is done with the function "VariableLoad"

Have a look at the Gantt and Load Chart to see what happend
"""


from faces import *
from faces.lib import gantt
from faces.lib import resource


class Bob(Resource):
    pass


def My_Project():
    resource = Bob
    start = "2005-1-16"
    balance = SLOPPY
    
    def Database():
        effort = "1d"
        load = 0.5
        
        
    def Gui():
        effort = "3d"
        load = VariableLoad()
        #VariableLoad will allocate GUI with as much load as possible


project = BalancedProject(My_Project)


class Gantt(gantt.Standard):
    data = project
    sharex = "share1"


class Load(resource.Standard):
    data = project
    sharex = "share1"
