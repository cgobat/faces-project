############################################################################
#   Copyright (C) 2005 by Reithinger GmbH
#   mreithinger@web.de
#
#   This file is part of metapie.
#                                                                         
#   metapie is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   pyplan is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the
#   Free Software Foundation, Inc.,
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
############################################################################

import weakref
try:
    set
except NameError:
    from sets import Set as set


class Subject(object):
    #no __init__ because auf ZODB
    #Subjects attributes are transient
    #and must be created on the flow

    def detach_all(self):
        try:
            del self._v_observers
        except AttributeError: pass
        
        
    def attach(self, callback, event="default"):
        try:
            observers = self._v_observers
        except AttributeError:
            observers = self._v_observers = { }

        ol = observers.get(event)
        if not ol: ol = observers[event] = set()
        ol.add(callback)


    def attach_weak(self, callback, event="default"):
        self.attach(weakref.ref(callback, self.__detach_weak), event)


    def __detach_weak(self, callback):
        self.detach(callback)


    def detach(self, callback=None, event=None):
        try:
            observers = self._v_observers
        except AttributeError:
            observers = self._v_observers = { }
        
        if callback is None: observers.clear()
        
        def detach_event(ol, callback):
            try:
                if ol: ol.remove(callback)
            except KeyError:
                pass

        if event:
            detach_event(observers.get(event), callback)
        else:
            for ol in observers.itervalues():
                detach_event(ol, callback)
                


    def fire(self, event="default", *args, **kwargs):
        try:
            observers = self._v_observers
        except AttributeError:
            return

        try:
            if self._v_events_disabled: return
        except AttributeError:
            pass

        for cb in self._v_observers.get(event, ()):
            if type(cb) == weakref.ReferenceType:
                cb = cb()
                if cb: cb(*args, **kwargs)
            else:
                cb(*args, **kwargs)
        

    def disable_events():
        try:
            self._v_events_disabled += 1
        except AttributeError:
            self._v_events_disabled = 1


    def enable_events():
        self._v_events_disabled -= 1
        

if __name__ == "__main__":
    def test():
        sender = Subject()

        def call_me():
            print "call me"

        print "before attach"
        sender.attach_weak(call_me)

        print "after attach"

        sender.fire()

        print "end"

    
    test()
