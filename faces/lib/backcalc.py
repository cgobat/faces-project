############################################################################
#   Copyright (C) 2005, 2006 by Reithinger GmbH
#   mreithinger@web.de
#
#   This file is part of faces.
#                                                                         
#   faces is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   faces is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the
#   Free Software Foundation, Inc.,
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
############################################################################

"""
Project backward calculation.
"""
import faces
import faces.task as ftask
import faces.utils as utils
import math

def _create_eval_factory(evaluation):
    if isinstance(evaluation, ftask.AdjustedProject):
        raise RuntimeError("you cannot backward calculate an AdjustedProject")

    if isinstance(evaluation, ftask.BalancedProject):
        def create_clone():
            return evaluation.__class__(evaluation._function,
                                        evaluation.scenario,
                                        evaluation.id,
                                        evaluation.balance)
        return create_clone

    if isinstance(evaluation, ftask.Project):
        def create_clone():
            return evaluation.__class__(evaluation._function,
                                        evaluation.scenario,
                                        evaluation.id)
        return create_clone
                                 

    raise TypeError("argument is no Project Type")


def calc_back_project(evaluation, end_date):
    factory = _create_eval_factory(evaluation)

    to_start = evaluation._to_start
    end_date = evaluation._to_end(end_date)
    ev_start = evaluation.start
    ev_end = evaluation.end
    test_data = [ None ]

    if ev_end > end_date:
        raise RuntimeError('argument("%s") is bevore project end ("%s")' \
                           % (test_data.strftime(), evaluation.to_string.end))


    def check_hook(task, name, value):
        tv = value
        if isinstance(value, dict):
            tv = value[task.scenario]
        
        if isinstance(tv, ftask._ValueWrapper):
            #find absolute value
            for t, a in tv._ref:
                if not t:
                    raise RuntimeError("For backward you may not specify "\
                                       "a concrete date at %s" % task.path)
            return value
            
        if test_data[0] and test_data[0] != task or name == "end":
            raise RuntimeError("You have specified at least two concrete start dates "\
                               "for backward calculation you may only specfy one: (%s, %s)" \
                               % (test_data[0].path, task.path))
           
        test_data[0] = task
        return value
    
    faces.Task._set_hook("start", check_hook)
    faces.Task._set_hook("end", check_hook)

    

    utils.progress_start("Backward calculation",
                         math.log(end_date - ev_start, 2) + 1)
        
    def make_calc_hook(start_value):
        start_task = test_data[0]._idendity_()
        def calc_hook(task, name, value):
            if task._idendity_() == start_task:
                return start_value
            return value

        return calc_hook
        
    try:
        factory()

        count = 1
        ev_end = end_date
        pivot = (ev_start + ev_end) / 2
        while ev_start + 1 < ev_end:
            utils.progress_update(count)
            count += 1

            faces.Task._set_hook("start", make_calc_hook(pivot))
            project = factory()
            
            if project.end > end_date:
                ev_end = pivot
            elif project.end < end_date:
                ev_start = pivot
            else:
                break

            pivot = (ev_start + ev_end) / 2

        return test_data[0], project._to_start(pivot), project.end
    finally:
        faces.Task._set_hook("start")
        faces.Task._set_hook("end")
        utils.progress_end()
    
        


