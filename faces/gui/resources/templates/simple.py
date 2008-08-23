# -*- coding: utf-8 -*-
from faces import *
from faces.lib import report
from faces.lib import gantt


def My_Project():
    start = "2005-1-16"
    
    def Task1():
        effort = "1w"

project = Project(My_Project)

class Gantt(gantt.Standard):
    data = project


class Report(report.Standard):
    data = project

    def make_report(self, data):
	for t in data: 
	    yield (t.indent_name(), t.start, t.end, t.effort)
