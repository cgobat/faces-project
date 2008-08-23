# -*- coding: iso8859-15 -*-            
#################################################
# This is a snapshot file for snapshot
# Dont't load this file directly, instead
# load the file snapshot.py  

_is_snapshot_file = True

def acso_standard_060414_0030():
    from faces import Resource
    class dev1(Resource): title = "Paul Smith"
    class dev2(Resource): title = "Sébastien Bono"
    class dev3(Resource): title = "Klaus Müller"
    class doc(Resource): title = "Dim Sung"
    class tester(Resource): title = "Peter Murphy"

    now = "2002-03-05 13:00"
    is_snapshot = True
    priority = 500
    balance = 2
    complete = 61
    milestone = False
    end = "2002-04-26 10:00"
    start = "2002-01-16 09:00"
    effort = 106620
    load = 0.875
    note = ""
    working_days = (("mon,tue,wed,thu,fri", "9:00-13:00", "14:00-18:00"))
    account = "dev"
    minimum_time_unit = 60
    title = "Accounting Software"

    def PlanAndControl():
        priority = 500
        balance = 2
        complete = 48
        milestone = False
        end = "2002-04-26 10:00"
        start = "2002-01-16 09:00"
        effort = 17820
        load = 0.1
        title = "Planing and Controlling"
        resource = \
            dev1(efficiency=1.0, rate=330.0)&\
            dev2(efficiency=1.0, rate=310.0)&\
            tester(efficiency=1.0, load=0.8, rate=240.0)&\
            doc(efficiency=1.0, rate=280.0)&\
            dev3(efficiency=1.0, rate=310.0)
        performed = [
            (dev1, "20020116 09:00", "20020128 18:00", "480M"),
            (dev1, "20020129 09:00", "20020213 13:00", "600M"),
            (dev1, "20020213 14:00", "20020308 16:00", "840M"),
            (dev1, "20020308 16:00", "20020410 15:00", "1140M"),
            (dev1, "20020410 15:00", "20020426 10:00", "600M"),
            (dev2, "20020116 09:00", "20020128 18:00", "480M"),
            (dev2, "20020129 09:00", "20020213 13:00", "600M"),
            (dev2, "20020213 14:00", "20020410 15:00", "1980M"),
            (dev2, "20020410 15:00", "20020426 10:00", "600M"),
            (tester, "20020116 09:00", "20020405 16:00", "2820M"),
            (tester, "20020405 16:00", "20020426 10:00", "720M"),
            (doc, "20020116 09:00", "20020128 18:00", "480M"),
            (doc, "20020129 09:00", "20020131 18:00", "180M"),
            (doc, "20020201 09:00", "20020204 18:00", "120M"),
            (doc, "20020205 09:00", "20020307 18:00", "1140M"),
            (doc, "20020308 09:00", "20020308 18:00", "60M"),
            (doc, "20020318 09:00", "20020426 10:00", "1440M"),
            (dev3, "20020116 09:00", "20020128 18:00", "480M"),
            (dev3, "20020129 09:00", "20020131 18:00", "180M"),
            (dev3, "20020205 09:00", "20020307 18:00", "1140M"),
            (dev3, "20020308 09:00", "20020308 16:00", "60M"),
            (dev3, "20020308 16:00", "20020405 16:00", "960M"),
            (dev3, "20020405 16:00", "20020426 10:00", "720M"),]

    def Deliveries():
        priority = 500
        balance = 2
        complete = 0
        milestone = False
        end = "2002-04-26 10:00"
        start = "2002-01-15 18:00"
        effort = 0
        load = 0.875
        account = "rev"
        title = "Milestones"


        def Begin():
            priority = 500
            balance = 2
            complete = 0
            milestone = True
            end = "2002-01-15 18:00"
            start = "2002-01-15 18:00"
            effort = 0
            load = 0.875
            credit = 33000.0
            title = "Projectstart"


        def Prev():
            priority = 500
            balance = 2
            complete = 0
            milestone = True
            end = "2002-03-08 16:00"
            start = "2002-03-08 16:00"
            effort = 0
            load = 0.875
            gantt_same_row = root.Deliveries.Begin
            credit = 13000.0
            title = "Technology Preview"


        def Beta():
            priority = 500
            balance = 2
            complete = 0
            milestone = True
            end = "2002-04-10 15:00"
            start = "2002-04-10 15:00"
            effort = 0
            load = 0.875
            gantt_same_row = root.Deliveries.Begin
            credit = 13000.0
            title = "Betaversion"


        def Done():
            priority = 500
            balance = 2
            complete = 0
            milestone = True
            end = "2002-04-26 10:00"
            start = "2002-04-26 10:00"
            effort = 0
            load = 0.875
            gantt_same_row = root.Deliveries.Begin
            credit = 14000.0
            title = "Ship Product to customer"


    def Spec():
        priority = 500
        balance = 2
        complete = 100
        milestone = False
        end = "2002-01-28 18:00"
        start = "2002-01-16 09:00"
        effort = 9600
        load = 2.22222222222
        title = "Specification"
        resource = \
            dev1(efficiency=1.0, rate=330.0)&\
            dev2(efficiency=1.0, load=0.5, rate=310.0)&\
            dev3(efficiency=1.0, rate=310.0)
        performed = [
            (dev1, "20020116 09:00", "20020128 18:00", "3780M"),
            (dev2, "20020116 09:00", "20020128 18:00", "2160M"),
            (dev3, "20020116 09:00", "20020128 18:00", "3780M"),]

    def Software():
        priority = 1000
        balance = 2
        complete = 55
        milestone = False
        end = "2002-04-05 16:00"
        start = "2002-01-29 09:00"
        effort = 40800
        load = 0.875
        priority = 1000
        title = "Software Development"


        def Database():
            priority = 1000
            balance = 2
            complete = 100
            milestone = False
            end = "2002-02-13 13:00"
            start = "2002-01-29 09:00"
            effort = 9600
            load = 1.73913043478
            title = "Database coupling"
            resource = \
                dev1(efficiency=1.0, rate=330.0)&\
                dev2(efficiency=1.0, rate=310.0)
            performed = [
                (dev1, "20020129 09:00", "20020213 13:00", "4830M"),
                (dev2, "20020129 09:00", "20020213 13:00", "4830M"),]

        def Gui():
            priority = 1000
            balance = 2
            complete = 0
            milestone = False
            end = "2002-04-05 16:00"
            start = "2002-03-08 16:00"
            effort = 16800
            load = 1.75
            title = "Graphical User Interface"
            resource = \
                dev2(efficiency=1.0, rate=310.0)&\
                dev3(efficiency=1.0, rate=310.0)
            performed = [
                (dev2, "20020308 16:00", "20020405 16:00", "8400M"),
                (dev3, "20020308 16:00", "20020405 16:00", "8400M"),]

        def Backend():
            priority = 1000
            balance = 2
            complete = 95
            milestone = False
            end = "2002-03-08 16:00"
            start = "2002-02-13 14:00"
            effort = 14400
            load = 1.73913043478
            title = "Back-End Functions"
            resource = \
                dev1(efficiency=1.0, rate=330.0)&\
                dev2(efficiency=1.0, rate=310.0)
            performed = [
                (dev1, "20020213 14:00", "20020308 16:00", "7245M"),
                (dev2, "20020213 14:00", "20020308 16:00", "7245M"),]

    def Test():
        priority = 500
        balance = 2
        complete = 0
        milestone = False
        end = "2002-04-26 10:00"
        start = "2002-04-05 16:00"
        effort = 12000
        load = 0.875
        title = "Software testing"


        def Alpha():
            priority = 500
            balance = 2
            complete = 0
            milestone = False
            end = "2002-04-10 15:00"
            start = "2002-04-05 16:00"
            effort = 2400
            load = 1.73913043478
            note = "Hopefully most bugs will be found and fixed here."
            title = "Alpha Test"
            resource = \
                tester(efficiency=1.0, load=0.8, rate=240.0)&\
                dev2(efficiency=1.0, rate=310.0)
            performed = [
                (tester, "20020405 16:00", "20020410 15:00", "1207M"),
                (dev2, "20020405 16:00", "20020410 15:00", "1207M"),]

        def Beta():
            priority = 500
            balance = 2
            complete = 0
            milestone = False
            end = "2002-04-26 10:00"
            start = "2002-04-10 15:00"
            effort = 9600
            load = 1.73913043478
            title = "Beta Test"
            resource = \
                tester(efficiency=1.0, load=0.8, rate=240.0)&\
                dev1(efficiency=1.0, rate=330.0)
            performed = [
                (tester, "20020410 15:00", "20020426 10:00", "4830M"),
                (dev1, "20020410 15:00", "20020426 10:00", "4830M"),]

    def Manual():
        priority = 500
        balance = 2
        complete = 92
        milestone = False
        end = "2002-03-07 18:00"
        start = "2002-01-16 09:00"
        effort = 26400
        load = 1.48648648649
        account = "doc"
        title = "Manual"
        resource = \
            dev3(efficiency=1.0, rate=310.0)&\
            doc(efficiency=1.0, rate=280.0)
        performed = [
            (dev3, "20020129 09:00", "20020131 18:00", "1260M"),
            (dev3, "20020205 09:00", "20020307 18:00", "9660M"),
            (doc, "20020116 09:00", "20020128 18:00", "3780M"),
            (doc, "20020129 09:00", "20020131 18:00", "1260M"),
            (doc, "20020201 09:00", "20020204 18:00", "840M"),
            (doc, "20020205 09:00", "20020307 18:00", "9660M"),]


