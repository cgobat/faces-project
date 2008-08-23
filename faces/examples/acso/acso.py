# -*- coding: iso8859-15 -*-
from faces import *
from faces.lib import report
from faces.lib import gantt
from faces.lib import workbreakdown
from faces.lib import generator
from faces.lib import resource
import faces.charting.charts as ch

faces_show_flow_tool = True

# This file contains an example project. It is borrowed from the
# TaskJuggler project management tool. It uses a made up software
# development project to demontrate some of the basic features of
# pyplan. Please see the pyplan manual for a more detailed
# description of the various syntax elements.


# The daily default rate of all resources. This can be overriden for each
# resource. We specify this, so that we can do a good calculation of
# the costs of the project.
Resource.rate = 310.0
    

class Developers(Resource):
    pass


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


class tester(Resource):
    title = "Peter Murphy"
    load = 0.8
    rate = 240.0


class doc(Resource):
    title = "Dim Sung"
    rate = 280.0
    vacation = [("2002-03-11", "2002-03-16")]


# In order to do a simple profit and loss analysis of the project we
# specify accounts. One for the development costs, one for the
# documentation costs and one account to credit the customer payments
# to.
# In contrast to taskjuggler, pyplan has no build in account support
# Therfore there is no pyplan analogy to the next 3 lines
#account dev "Development" cost
#account doc "Dokumentation" cost
#account rev "Payments" revenue




def Acso():
    title = "Accounting Software"
    note = ""
    
    # Pick a day during the project that will be reported as 'today' in
    # the project reports. If not specified the default calendar epoch will be
    # used, but this will likely be outside of the project range, so it
    # can't be seen in the reports.
    now = "2002-03-05 13:00"
    load = WeeklyMax("35H")
    
    
    #for a better comparision to the taskjuggler original
    #we change the pyplan default values to the taskjuggler values
    working_days = ("mon,tue,wed,thu,fri", "9:00-13:00", "14:00-18:00")
    
    minimum_time_unit = 60

    # Now we specify the work packages. The whole project is described as
    # a task that contains sub tasks. These sub tasks are then broken down
    # into smaller tasks and so on. The innermost tasks describe the real
    # work and have resources allocated to them. Many attributes of tasks
    # are inherited from the enclosing task. This saves you a lot of
    # writing.
    
    # All work related costs will be booked to this account unless the
    # sub tasks specifies it differently.
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
	
	# Some milestones have customer payments associated with them. We
	# credit these payments to the 'rev' account.
	account = "rev"

	def Begin():
	    title = "Projectstart"
	    
	    # A task that has no duration is a milestone. It only needs a
	    # start or end criteria. All other tasks depend on this task.
	    milestone = True
	    # For some reason the actual start of the project got delayed.
	    # We record this, so that we can compare the plan run to the
	    # delayed run of the project.
	    start = Multi("2002-01-16", delayed="2002-01-24")
	    
	    # At the begining of this task we receive a payment from the
	    # customer. This is credited to the account assiciated with this
	    # task when the task starts.
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
	    
	    # The next lines can be uncommented to trigger a warning about
	    # the project being late. For all tasks limits for the start and
	    # end value can be specified. Those limits are checked after the
	    # project has been scheduled. For all violated limits a warning
	    # is issued.

	    #def __constraint__():
	    #    assert_(me.end <= "2002-04-17")

	    start = max(up.up.Test.Beta.end, up.up.Manual.end)
	    credit = 14000.0 


    def Spec():
        title = "Specification"
        # The effort to finish this task is 20 man days. 
        effort = "20d"
        # Now we use the above declared team to allocate the resources
        # for this task. Since they can work in parallel, this task may be
        # finshed earlier than 20 working days.
        resource = developers
        # For this task we use a reference to a further down defined milestone
        # as a start criteria. So this task cannot start, before the specified
        # milestone has been reached.
        # References to other tasks may be relative. Each up. means 'in the
        # scope of the enclosing task'. To descent into a task the .
        # together with the id of the tasks have to be specified.
        start = up.Deliveries.Begin.end


    def Software():
	title = "Software Development"
	
	# The software is the most critical task of the project. So we set
	# the priority of this tasks (and all sub tasks) to 1000, the top
	# priority. The higher the priority the more likely will the task
	# get the requested resources.
	priority = 1000

	
	def Database():
	    title = "Database coupling"
	    effort = "20d"
	    resource = dev1 & dev2
	    # This task depends on a task in the scope of the enclosing
	    # tasks enclosing task. So we need up.up to get there.
	    start = up.up.Spec.end

	def Gui():
	    title = "Graphical User Interface"
	    
	    # This task has taken 5 man days more than originally planned.
	    # We record this as well, so that we can generate reports that
	    # compare the delayed schedule of the project to the original plan.
	    effort = Multi("35d", delayed="40d")
            # the task starts when both database and backend are finished
	    start = max(up.Database.end, up.Backend.end)
	    resource = dev2 & dev3

	def Backend():
	    title = "Back-End Functions"
	    effort = "30d"
	    
	    # This task is behind schedule since it should have been
	    # finished already. To document this we specify that the tasks
	    # is 95% completed. If nothing is specified, TaskJuggler assumes
	    # that the task is on schedule and computes the completion rate
	    # according to the current day and the plan data.
	    complete = 95 
	    start = max(up.Database.end, up.up.Spec.end)
	    resource = dev1 & dev2 


    def Test():
	title = "Software testing"
	
	def Alpha():
	    title = "Alpha Test"
	    # Efforts can not only be specified as man days, but also man
	    # weeks, man hours, etc. Per default taskjuggler assumes a man
	    # week is 40 man hours or 5 man days. These values can be
	    # changed though.
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


#compiling the delayed scenario
acso_delayed = Project(Acso, "delayed")


#this line compiles the default scenario of acso
#and allocates the resources to the tasks. SLOPPY is a
#specific algorithm for
#allocating resources. Other values would be STRICT and SMART
acso_standard = BalancedProject(Acso, balance=SLOPPY)

#print "acso", acso_standard._calendar.working_times



# Hide the clock time. Only show the date.
Task.formats["start"] = Task.formats["end"] = "%Y-%m-%d"



# Now the project has been completely specified. Stopping here would
# result in a valid pyplan file that could be processed and
# scheduled. But no reports would be generated to visualize the
# results. 

# simple reports for the default and delayed scenario
class Overview(report.Standard):
    data = acso_standard

    def make_report(self, data):
        for t in self.data:
            yield (t.index,
		   t.indent_name(), 
		   t.start,
		   t.end,
		   t.effort,
		   t.duration,
		   t.complete,
		   t.costs("rate"),
		   t.note)
 
    
class Overview_Delayed(Overview):
    data = acso_delayed


# simple gantt charts for the default and delayed scenario
class Gantt(gantt.Standard):
    data = acso_standard
    sharex = "share"
    parent_shape = "wedge_bar_wedge"
    properties = { "wedge_bar_wedge.bar.facecolor" : "gray",
		   "wedge_bar_wedge.start.facecolor" : "red",
		   "wedge_bar_wedge.end.facecolor" : "green",
		   "wedge_bar_wedge.end.up" : False,
		   "diamond.facecolor" : "gold" }
    #auto_scale_y = True
    #show_rowlines = True

    
    
class Delayed_Gantt(gantt.Standard):
    data = acso_delayed
    time_axis_properties = { "grid.edgecolor" : "green",
			     "grid.linestyle" : "dashed",
			     "free.facecolor" : "indianred",
			     "now.edgecolor" : "black",
			     "now.linestyle" : "dashdot" }
    

#a comparing gantt chart of default and delayed scenario
class Comparing(gantt.Compare):
    draw_connectors = False
    data = intersect(acso_standard, acso_delayed)
    sharex = "share"

	

#pyplan does not have any accounting functionality by itself, we program some
def account_report(project):
    accounts = {}

    # filter out parent tasks
    time_sorted_tasks = filter(lambda t: not t.children, project)

    # sort the task on their end value
    time_sorted_tasks = map(lambda t: (t.end, t.path, t), time_sorted_tasks)
    time_sorted_tasks.sort()
    time_sorted_tasks = map(lambda t: t[2], time_sorted_tasks)
    
    #get all acounts and initialize them
    for t in time_sorted_tasks:
	accounts[t.account] = 0.0

    #calculate accout values
    for t in time_sorted_tasks:
        account = t.account
        val = accounts[account]
	costs = t.costs("rate")

        val += (getattr(t, "credit",  0.0) - costs)
        accounts[account] = val

	#set the current account value
	for k, v in accounts.iteritems():
	    setattr(t, "%s_value" % k, v)
        
    return time_sorted_tasks


# create the accounting report
accounts = account_report(acso_standard)

class Account_Rep(report.Standard):
    data = accounts
    headers = ("date", "payment", "development", "documentation",
	       "costs", "revenue")
    
    def make_report(self, data):
	for t in data:
	    yield (t.end, t.rev_value, t.dev_value, \
		   t.doc_value, t.dev_value + t.doc_value,
		   t.rev_value + t.dev_value + t.doc_value)
            
    

#if you compare this example with the taskjuggler original, you will find some slight
#differences in the calculation. These differences are result of different rounding
#of some values. After some days of investigation, I am quite confident that the pyplan
#rounding is the correct one


class Resources(resource.Standard):
    data = acso_standard
    sharex = "share"
    #data = dev1
    #start = acso_standard.start
    #end = acso_standard.end
    #show_scale = False
    #load_factor = 100
    
    

class WBK(workbreakdown.Standard):
    data = acso_standard
    #max_depth = 1

    
class Calendar(report.Calendar):
    data = acso_standard



from matplotlib.pylab import *
import faces.charting.faxes as fx
    
	
#print dev3._calendar.bookings


class PlotAccounts(ch.TimeAxisPlotChart):
    calendar = acso_standard.calendar
    sharex = "share"
    #show_grid = False
    
    def create_plot(self, to_x):
	dates = map(lambda t: to_x(t.end), accounts)
	revenues = map(lambda t: t.rev_value + t.dev_value + t.doc_value, accounts)
	costs = map(lambda t: t.dev_value + t.doc_value, accounts)
	gca().yaxis.set_major_locator(ticker.NullLocator())
        gca().yaxis.set_minor_locator(ticker.NullLocator())
	
	gca().yaxis.set_ticks_position("left")
	
	plot(dates, revenues)
	plot(dates, costs)
	axhline(0, zorder=-10)
	
	for x, y in zip(dates, revenues):
	    t = text(x, y, "%.02f" % y, clip_box=True)
	    	
	for x, y in zip(dates, costs):
	    text(x, y, "%.02f" % y, clip_box=True)
		    
	#print max(revenues), min(revenues)
	gca().dataLim.intervaly().set_bounds(-100000, 50000)
	#print "xlim", gca().get_xlim()
	#gca().set_ylim(-10000, 50000)



class Names(report.Standard):
    visible = False
    data = acso_standard
    
    def make_report(self, data):
	for t in data: 
	    yield (t.indent_name(), t.effort)
    
class GanttVsAccounts(ch.TimeAxisTabledChart):
    content_charts = (Gantt, )
    sharex = "share"
    #visible = False
    show_grid = True
    show_tips = False
    left_report = Names
    #right_report = Names
    properties = { "left.background.facecolor" : "yellow",
		   "right.background.facecolor" : "yellow",
		   "title.weight" : "heavy"}


	
	
class AcsoHTML(generator.StandardHTML):
    title = "Accounting Software"
    observers = generator.all()
    #observers = [ Gantt ]
    font_size = 12

AcsoHTML.faces_savedir = "/home/michaelr/tmp"

	
if __name__ == "__main__":
    #Generate an HTML Report when call at the command line
    import sys
    try:
        dest = sys.argv[1]
    except:
        dest = "/home/michaelr/tmp"

    AcsoHTML().create(dest, 2)
    #save_resource()
