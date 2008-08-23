# -*- coding: utf-8 -*-
from faces import *
from faces.lib import report
from faces.lib import gantt
from faces.lib import resource
from faces.lib import workbreakdown
from faces.lib import generator
from dateutil import relativedelta as rd
import datetime
import faces.pcalendar as pc



        
class ShiftResource(Resource):
    """
    A resource that uses a shift plan for allocation.
    To use the shift allocation algorithm you have to
    use the balancing method SLOPPY.
        
    The shift plan is a sequence of shift_types.
    Shift types can be:
    M: Morning Shift
    L: Late Shift
    N: Night Shift
    F: Non Working Shift
    
    For example the following line:
       shift_plan = "NFMMLLF"
    means the resource has a shift plan of one week begining with 
    a night shift and ending with non working shift, after 7 days 
    it starts again with the night shift.
    
    epoch is the begining of the shift plan
    """
    
    shift_plan = "" 
    epoch = pc.Calendar.EPOCH
    
    def end_of_booking_interval(cls, date, task):
        """
        This method is called by the sloppy resource allocator.
        It calculates the resources load at date and the next date,
        when the load changes, and returns next_date, load.
        
        The allocator will book the task, if the 
           tasks load + resources load <= max_load
        otherwise it will try to book it at next_date.
        """
        
        next, load = super(ShiftResource, cls).end_of_booking_interval(date, task)
        
        dt = date.to_datetime()

        # find out which shift day date is
        epoch_days = (dt - cls.epoch).days
        shift_index = epoch_days % len(cls.shift_plan)
        shift_type = cls.shift_plan[shift_index]
        try:
            shift_tr = task.shift_times[task.shift_type]
        except KeyError:
            # there is no shift time for that type ==> fall back to normal booking
            return next, load
        
        #calculate the next day that has the same shift type
        rot_shift = cls.shift_plan[shift_index:] + cls.shift_plan[:shift_index]
        next_shift_day = rot_shift.index(task.shift_type, 1)
        
        if task.shift_type == shift_type:
            # the task has the same shift type as date ==> try to book
            tr = pc.to_time_range(shift_tr)
            shift_start = dt.replace(hour=tr[0] / 60, minute=tr[0] % 60)
            shift_end = dt.replace(hour=tr[1] / 60, minute=tr[1] % 60)
            if tr[0] > tr[1]: shift_end += datetime.timedelta(days=1)
            
            if dt < shift_start:
                next = min(next, shift_start)
                load = 1000 # the alloctor will definitly not book the task that till next
            elif dt >= shift_end:
                next = min(next, dt + rd.relativedelta(days=next_shift_day,
                                                       hour=tr[0] / 60, minute=tr[0] % 60))
                load = 1000
            else:
                next = min(next, shift_end)

        else:
            # do not book unti the day shift type is equal the task shift type
            tr = pc.to_time_range(shift_tr)
            next = min(next, dt + rd.relativedelta(days=next_shift_day,
                                                   hour=tr[0] / 60, minute=tr[0] % 60))
            load = 1000            
            
        return next, load
        
        
class Team1(ShiftResource):
    shift_plan = "LLLLNNN FFFMMMM MMMFLLL NNNNFFF".replace(" ", "")
    
    
    
class Team2(ShiftResource):
    shift_plan = "FFFMMMM MMMFLLL NNNNFFF LLLLNNN".replace(" ", "")
   
    
    

class Team3(ShiftResource):
    shift_plan = "MMMFLLL NNNNFFF LLLLNNN FFFMMMM".replace(" ", "")



class Team4(ShiftResource):
    shift_plan = "NNNNFFF LLLLNNN FFFMMMM MMMFLLL".replace(" ", "")



def Sysadmin():
    balance = SLOPPY
    duration = "2m"
    start = "01.01.2007 00:00"
    shift_type = ""
    working_days = [("mon, tue, wed, thu, fri, sat, sun", "00:00-23:59")]
        
    def UserSup():
        title = "User Support"
        resource = Team1 & Team2 & Team3 & Team4
        
        # shift_times will be used while allocation
        shift_times = { "M" : "6:00-14:00",
                        "L" : "14:00-22:00",
                        "N" : "22:00-6:00" }
                       
        
        def mshift():
            title = "Morning Shift"
            shift_type = "M"
            duration = root.duration
            
        def lshift():
            title = "Late Shift"
            shift_type = "L"
            duration = root.duration
            
        def nshift():
            title = "Night Shift"
            shift_type = "N"
            duration = root.duration
        
        def fshift():
            #comment the next line to have booking on non-working shifts
            resource = None 
            title = "Non-Working Shift"
            shift_type = "F"
            duration = root.duration
            priority = 100

Sysadmin.balanced = BalancedProject(Sysadmin, "_default", "Sysadmin_balanced", SLOPPY)


class Gantt(gantt.Standard):
    data = Sysadmin.balanced
    sharex = "share1"
    

class Load(resource.Standard):
    data = Sysadmin.balanced
    sharex = "share1"


class Structure(workbreakdown.Standard):
    data = Sysadmin.balanced


class HTML(generator.StandardHTML):
    observers = generator.all()

class AllocationReport(report.Standard):
    data = Sysadmin.balanced
    get_color = Load.get_color
    headers = ("Name", "Start", "End")
        
    def make_report(self, data):
        resources = data.all_resources()
        start = data.start
        end = data.end
        for r in resources:
            yield (report.Cell(r.title, font_bold=True, font_size="large"),"","")
            bookings = [ (b.book_start, b) for b in r.get_bookings_at(start, end) ]
            bookings.sort()
            
            for s, b in bookings:
                task = data.get_task(b.path)
                if self.get_color:
                    back, fore = self.get_color(task)
                else:
                    back, fore = None, None
                
                line = (task.title, b.book_start.strftime("%x %H:%M"), b.book_end.strftime("%x %H:%M")) 
                line = [ report.Cell(c, text_color=fore, back_color=back) for c in line ]
                yield line

