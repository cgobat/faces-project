from __future__ import print_function
from __future__ import division
from builtins import object
from past.utils import old_div
import time

class TimeIt(object):
    """
    Miniprofiling
    """
    def __init__(self, name):
        self._sumtime = 0
        self._count = 0
        self._name = name

    def start(self):
        self._start = time.clock()

    def end(self):
        end = time.clock()
        self._sumtime += end - self._start
        self._count += 1
        print("time_it", self._name, end - self._start,\
              old_div(self._sumtime, self._count))

