# -*- coding: iso8859-15 -*-
#this is the faces project plan

#what want you like to do?
#uncomment one of the following lines
#mode = ["track"]
#mode = ["plan"]
mode = ["manage"]
mode = ["plan", "manage", "track"]


if __name__ == "__main__":
    #generate all observers for html
    mode = ["plan", "manage", "track"]

current_version = "0.12.0"

def in_mode(*modes):
    for m in modes:
        if m in mode: return True
        
    return False


from faces import *
from faces.lib import report
from faces.lib import gantt
from faces.lib import resource
from faces.lib import workbreakdown
from faces.lib import generator
from faces.tools import clocking
#from faces.tools import taskcoach

set_default_chart_font_size(7)
Task.__attrib_completions__["notes"] = 'notes = "|"'   

#currently only one is working

class michael(Resource): 
    vacation = [("28.06.2005 00:00", "04.07.2005 00:00"),
                ("11.07.2005 00:00", "16.08.2005 00:00"),
                ("10.02.2006 00:00", "11.03.2006 00:00"),
                ("25.09.2006 00:00", "25.09.2006 00:00"),
                ("02.10.2006 01:58", "13.10.2006 00:00")]

class other(Resource):
    pass
    

#work break down structure plan
def Faces_Structure():
    start = "20.6.2005"
    note = ""
    version = ""
    
    def Extra_Tools():
        def WorkingTime_Collector():
            note = "gui tool to collect WorkingTimes"
            effort = Multi("3H 45M", planed="8d")
            complete = 100

    def Localization():
        def German():
            effort = "5d"

        
    def Gui():
        def Misc():
            def HelpFunction():
                effort = "5d"
                complete = 100

            def Autorefresh():
                effort = "2H"
                note = "when project changed by an extern editor"
            
        def Menus():
            note = "new menu option"
            
            def Print_Charts():
                effort = "2d"
                complete = 100
        
            def Export_Charts():
                effort = "1d"
                complete = 100

            def Link():
                note = "link and unlink a window"
                effort = "1H"
                complete = 100

            def Copy_Path():
                note = "copy the path of the selected\n window to the cliboard"
                effort = "1H"
                complete = 100
                
        def Editor():
            def Tipwindow():
                note = "tip windows"
                effort = "1d"
                complete = 100
                
            def Multi_Comments():
                note = "comment and uncommment muliple lines"
                effort = "0.5d"
                complete = 100
                
            def Goto_Line():
                effort = "0.5d"
                note = "a goto line function"
                complete = 100
                
            def Bookmarks():
                effort = "1d"
                note = "mark and retrieve bookmarks"
                
            def Editor_Macros():
                effort = "0.5d"
                complete = 100
                
            def Search_and_Replace_Dialog():
                effort = "0.5d"
                complete = 100

            def Context_Info_Menu():
                effort = "0.5d"
                complete = 100
                note = """
                 show all context variables 
                 by right mouse click 
                 """

            def Background_Parsing():
                effort = "2d"
                complete = 100
                note = """
                 editor parses the code while editing,
                 and provides also context info without saving
                 the source
                 """

        def Views():
            def Scheduled_View():
                effort = "1H"
                complete = 100
                            
            def Report_View():
                effort = "3H"
                complete = 100
                
            def Workbreakdown_View():
                effort = "1d"
                complete = 100
                
            def Perth_View():
                effort = "1w"
                
                
        def Main_Gui():
            effort = "2d"
            complete = 100

            
    def Framework():
        def Knowledge_Base():
            note = "Funktionen zum Sammeln und \nWiederverwenden von Erfahrungswerten"
            effort = "2w"
            
        
        def Task():
            def Generate_Snapshots():
                effort = Multi("6H 45M", planed="1d")
                complete = 100
                
            def Search():
                "search tasks with uncomplete path"
                effort = "2H"
            
            def Tracking_Functions():
                effort = Multi("2H 45M", planed="1w")
                note = "collecting efforts and \nadjust the project"
                complete = 100
                            
        def Resource():
            def Load_Save_Resource_Calendar():
                effort = "2d"


        def Charts():
            def Time_Based():
                def Base():
                    effort = "5H"
                    complete = 100
                
                def Gantt():
                    effort = "4H"
                    complete = 100
                    
                def Resource():
                    effort = "2d"
                    complete = 100
                    
                    
            def Workbreakdown():
                effort = "1d"
                complete = 100
                
            def Perth():
                effort = "1w"
                

        def Libraries():
            def Gantt():
                def Standard():
                    effort = "1M"
                    complete = 100
                    
                def Critical():
                    effort = "1H"
                    complete = 100
                    
                def Compare():
                    effort = "1H"
                    complete = 100
                
            def Report():
                def Standard():
                    effort = "1M"
                    complete = 100
                    
                def Critical():
                    effort = "1H"
                    complete = 100
                    
                def Titles():
                    effort = "0.5H"
                    complete = 100
                
                def Resource_Bookings():
                    effort = "1H"

                def Calendar():
                    effort = "2d"
                    note = "overview of start and end dates"
                    complete = 100
                    
            def Resource():
                def Standard():
                    effort = "1M"
                    complete = 100

                
            def WorkBreakDown():
                effort = "4H"
                complete = 100

        def Pcalendar():
            effort = "1d"
            complete = 100
            
        def Renderer():
            effort = "1d"
            complete = 100

        def Colors():
            effort = "30M"
            complete = 100
            
            
        def Operators():
            def Intersect_Function():
                effort = "1H"
                complete = 100
            
            def Unite_Function():
                effort = "4H"
                complete = 100
                
            def Difference_Function():
                effort = "4H"
                complete = 100
            

        def Report():
            effort = "2d"
            complete = 100


        def Html_Generator():
            effort = "5d"
            complete = 100
            
                
    def Documentation():
        def Abstract():
            effort = "1d"
            #todo = "1H"
            complete = 100
        
        def Quick_Tutorial():
            def Section_1_to_5():
                effort = "5d"
                complete = 100
                
            def Rest_Sections():
                effort = "15d"
                complete = 100
            
        def Advanced_Techniques():
            effort = "10d"
            
        def Project_Phases():
            effort = "10d"
                        
        def References():
            effort = "10d"
            complete = 20
            
        def Concepts():
            effort = "1w"
                        

    def Environment():
        def Web_Page():
            effort = "1d"
            complete = 100

        def Setup():
            effort = "2H"
            complete = 100

    
#release plan
def faces_release():
    title = "release plan"
    start = "14.6.2005"
    resource = michael
    version = ""
    now = "23.11.2006 20:00"
    #properties = { "end.wedgeline.False" : True }
    
    def Release_0_1_0():
        note = "First public alpha release"
        version = "0.1.0"
        balance = SLOPPY
        gantt_accumulate = True
        
        def Misc_Features():
            def Link():
                copy_src = structure.Gui.Menus.Link
                
            def Copy_Path():
                copy_src = structure.Gui.Menus.Copy_Path

        def Gui():
            def Scheduled_View():
                copy_src = structure.Gui.Views.Scheduled_View
                
            def Main_Gui():
                copy_src = structure.Gui.Main_Gui

        def FrameWork():
            def BaseScheduled():
                copy_src = structure.Framework.Charts.Time_Based.Base
                
            def Lib():
                def Gantt():
                    def Standard():
                        copy_src = structure.Framework.Libraries.Gantt.Standard
                        
                    def Critical():
                        copy_src = structure.Framework.Libraries.Gantt.Critical
                            
                    def Compare():
                        copy_src = structure.Framework.Libraries.Gantt.Compare
                                                
                def Report():
                    def Standard():
                        copy_src = structure.Framework.Libraries.Report.Standard
                                                
                    def Critical():
                        copy_src = structure.Framework.Libraries.Report.Critical
                                            
                    def Titles():
                        copy_src = structure.Framework.Libraries.Report.Titles
                                            
            def Pcalendar():
                copy_src = structure.Framework.Pcalendar
                            
            def Colors():
                copy_src = structure.Framework.Colors
                                
            def Intersect_Function():
                copy_src = structure.Framework.Operators.Intersect_Function
                
        def Documentation():
            def abstract():
                copy_src = structure.Documentation.Abstract
                            
            def section_1_to_5():
                copy_src = structure.Documentation.Quick_Tutorial.Section_1_to_5
                            
        
        def Environment():
            def Web_Page():
                copy_src = structure.Environment.Web_Page
                            
            def Setup():
                copy_src = structure.Environment.Setup
                
    def Release_0_1_1():
        start = up.Release_0_1_0.end
        note = "extra debugging"
        effort = "1d"
        complete = 100
                
    def Release_0_2_0():
        start = up.Release_0_1_1.end
        version = "0.2.1"
        title = "Release 0.2.0"

        def Iterations():
            def I1_0_1_0():
                effort = up.up.up.Release_0_1_0.effort * 0.3
                length = up.up.Increments.length
                balance = STRICT
                complete = 100

        def Increments():
            def Chart_Resource():
                copy_src = structure.Framework.Charts.Time_Based.Resource
                
            def Lib_Resource_Standard():
                copy_src = structure.Framework.Libraries.Resource.Standard
                
            def rest_sections():
                copy_src = structure.Documentation.Quick_Tutorial.Rest_Sections
                        
            def Gantt():
                _ref = structure.Framework.Charts.Time_Based.Gantt
                copy_src = _ref
                    

    def Release_0_3_0():
        start = up.Release_0_2_0.end
        version = "0.3.0"
        
        def Iterations():
            def Iter2_0_1_0():
                effort = Multi("5H", planed=up.up.up.Release_0_1_0.effort * 0.2)
                length = up.up.Increments.length
                balance = STRICT
                complete = 100
        
            def Iter1_0_2_0():
                effort = Multi("2H", planed=up.up.up.Release_0_2_0.effort * 0.3)
                length = up.up.Increments.length
                balance = STRICT
                complete = 100

        def Increments():
            def gui():
                def Tipwindow():
                    copy_src = structure.Gui.Editor.Tipwindow
                    
                def Multi_Comments():
                    copy_src = structure.Gui.Editor.Multi_Comments
                    
                def Goto_Line():
                    copy_src = structure.Gui.Editor.Goto_Line
            
                def Editor_Macros():
                    copy_src = structure.Gui.Editor.Editor_Macros
                    
                def Search_and_Replace_Dialog():
                    copy_src = structure.Gui.Editor.Search_and_Replace_Dialog
                    
                def Chart_Workbreakdown():
                    copy_src = structure.Framework.Charts.Workbreakdown
                        
                def Lib_WorkBreakDown():
                    copy_src = structure.Framework.Libraries.WorkBreakDown
                            
                def Workbreakdown_View():
                    copy_src = structure.Gui.Views.Workbreakdown_View
                    
    def Release_0_4_0():
        start = up.Release_0_3_0.end
        version = "0.4.0"
        
        def Iterations():
            def Iter2_0_2_0():
                effort = up.up.up.Release_0_2_0.effort * 0.2
                length = up.up.Increments.length
                balance = STRICT
                complete = 100
    
            def Iter1_0_3_0():
                effort = up.up.up.Release_0_3_0.effort * 0.3
                length = up.up.Increments.length
                balance = STRICT
                complete = 100

        def Increments():
            def Html_Generator():
                copy_src = structure.Framework.Html_Generator
                length = "10d"
                

    def Release_0_5_0():
        start = up.Release_0_4_0.end
        version = "0.5.0"
        note = "Beta Version"
        
        def Iterations():
            def Debugging_and_Refacturing():
                effort = "3d"
                length = up.up.Increments.length
                balance = STRICT
                complete = 100
                note = """
                 changes:
                 clean method of StandardHTML 
                 """

            def Documenting_Source_code():
                effort = "1w"
                length = up.up.Increments.length
                balance = STRICT
                complete = 100

        def Increments():
            def References_Part1():
                copy_src = structure.Documentation.References
                effort = structure.Documentation.References.effort / 2
                complete = 100

            def Calendar():
                copy_src = structure.Framework.Libraries.Report.Calendar
                complete = 100
        
    def Release_0_5_1():
        version = "0.5.1"
        start = up.Release_0_5_0.end
        note = "Beta version"
        
        def Debugging_and_Refacturing():
            effort = "4d"
            length = up.Increments.length
            balance = STRICT
            complete = 100
    
        def Increments():
            def Concepts():
                effort = "1w"
                copy_src = structure.Documentation.Concepts
                complete = 100
            
    
    def Release_0_6_1():
        start = up.Release_0_5_1.end
        version = "0.6.1"
        
        def Iterations():
            def Debugging_and_Refacturing():
                effort = Multi("1d 1H 15M", planed="3d")
                end = up.up.Increments.end
                note = "improve tracking"
                balance = STRICT
                complete = 100
                
        def Increments():
            def Tracking_Functions():
                copy_src = structure.Framework.Task.Tracking_Functions

            def WorkingTime_Collector():
                copy_src = structure.Extra_Tools.WorkingTime_Collector
                complete = 100


    def Release_0_7_0():
        start = up.Release_0_6_1.end
        version = "0.7.0"
        
        def Iterations():
            def Calendar_Rewrite():
                effort = Multi("6H 15M", planed="2d")
                #effort = "2d"
                complete = 100
                
            def Chart_Rewrite():
                load = 0.75
                complete = 100
                effort = Multi("22d 2H 45M", planed="1w")
                note = """
                 change to mathplot renderer,
                 new calendar functions, 
                 connect workingtime blocks in resource charts"""
                
            def Debugging():
                effort = Multi("2d 6H", planed="2d")
                start = up.up.Increments.start
                end = up.up.Increments.end
                complete = 100

        def Increments():
            load = 0.6
            
            def Print_Charts():
                copy_src = structure.Gui.Menus.Print_Charts
                complete = 100
                                
            def Mathplot_Chart():
                effort = Multi("1d 30M", planed="2d")
                complete = 100
                
            def Documentation_Update():
                effort = Multi("2d 1H 45M", planed="1w")
                complete = 100
                
    def Release_0_7_1():
        start = up.Release_0_7_0.end
        version = "0.7.1"
        
        def Iterations():
            def Error_Handling():
                note = "Error handling in charting module"
                effort = "3H"
                complete = 100
                
            def TimeTabledChart():
                note = "finish 1"
                effort = "5H 30M"
                complete = 100
                
            def Debugging():
                start = up.up.Increments.start
                end = up.up.Increments.end
                effort = "2d 6H 15M"
                max_load = 2
                complete = 100
                
        def Increments():
            def Webpage():
                def Text_Updates():
                    effort = "6H 30M"
                    complete = 100
                    
                def Forum():
                    effort = "1d"
                    complete = 100

            def Convenience():
                note = "insert date dialog"
                effort = "5d 3H 15M"
                complete = 100
        
            def Dokumentation():
                effort = "0d 4H 45M"
                note = """
                -Workbreakdown reference"""
                complete = 100
        
    def Release_0_7_2():
        version = "0.7.2"
        start = up.Release_0_7_1.end
        
        def Iterations():
            def Debugging_and_Refacturing():
                length = up.up.Increments.length
                balance = STRICT
                effort = "1d 4H 45M"
                complete = 100
                
        def Increments():
            def SaveChart():
                effort = Multi("1d 2H 45M", planed="2d")
                complete = 100
        
    def Release_0_7_3():
        version = "0.7.3"
        start = max(up.Release_0_7_2.end, "7.2.2006 12:00")
        
        def Increments():
            def PrintChart():
                note = """
                Modify or replace chart.save, with an
                better mechanism
                """
                effort = Multi("3d 45M", planed="4H")
                complete = 100
                                
                
        def Iterations():
            def Debugging_and_Refacturing():
                load = 0.3
                length = up.up.Increments.length
                complete = 100
                effort = "15M"
                
    def Release_0_7_4():
        version = "0.7.4"
        start = up.Release_0_7_3.end
                
        def Iterations():
            def Debugging_and_Refacturing():
                effort = Multi("4H 30M", planed="1d")
                complete = 100
                #length = up.up.Increments.length

                
    def Release_0_8_0():
        version = "0.8.0"
        start = up.Release_0_7_4.end

        def Iterations():
            def Debugging_and_Refacturing():
                start = up.up.Increments.start
                effort = Multi("4H 30M", planed="3d")
                length = up.up.Increments.length
                complete = 100
                
            def Make_Release():
                effort = Multi("5H", planend="4H")
                start = up.up.Increments.end + "1d"
                complete = 100
        
        def Increments():
            load = 0.7
            def PrintReports():
                effort = "1d 2H"
                complete = 100
                
            def EditTask_Dialog():
                effort = Multi("2d 45M", planed="2d")
                complete = 100
                
            def EditResource_Dialog():
                effort = Multi("2H", planend="1d")
                complete = 100
                
            def EditCalendar_Dialog():
                effort = Multi("2H 45M", planed="1d")
                complete = 100
                
                
    def Release_0_8_1():
        version = "0.8.1"
        start = up.Release_0_8_0.end
        
        def Iterations():
            def Debugging_and_Refacturing():
                start = up.up.Increments.start
                effort = Multi("2d 2H", planed="2d")
                length = up.up.Increments.length
                complete = 100
                
            def Make_Release():
                effort = Multi("2H", planed="4H")
                start = up.up.Increments.end + "1d"
                complete = 100
        
        def Increments():
            load = 0.7
            
            def EditTimeChart_Dialog():
                effort = Multi("3H", planed="3d")
                complete = 100
            
            def EditReport_Dialog():
                effort = Multi("2H", planed="2d")
                complete = 100
                
            def Calltips():
                effort = Multi("1d 1H 45M", planed="1d")
                complete = 100

                
            def Generate_Snapshots():
                copy_src = structure.Framework.Task.Generate_Snapshots
                complete = 100

                
    def Release_0_9_0():
        version = "0.9.0"
        start = up.Release_0_8_1.end
        notes = "Release Kanadidate"
                
        
        def Iterations():
            def Debugging_and_Refacturing():
                load = 0.3
                length = up.up.Increments.length
                balance = STRICT
                complete = 100
                
            def Make_Release_8_2():
                start = "24.04.2006 13:00"
                effort = Multi("1H 45M", planed="4H")
                notes = """
                 many bugfixes, that should be released.
                 """
                gantt_shape = "diamond"
                complete = 100
                                
                
            def Make_Release():
                effort = Multi("6H", planed="4H")
                start = up.up.Increments.end + "1d"
                gantt_shape = "diamond"
                complete = 100
                
                
        def Increments():
            def EditChart_Dialogs():
                effort = Multi("2d 3H 30M", planed="5d")
                complete = 100
                

            def Facility_Howto():
                effort = Multi("30M", planed="3H")
                complete = 100
                

    def Release_0_9_1():
        start = up.Release_0_9_0.end
        version = "0.9.1"
                
        def Iterations():
            def Debugging_and_Refacturing():
                title = "Debug all"
                effort = Multi("2d 5H 30M", planed="4d")
                length = up.up.Increments.length
                balance = STRICT
                complete = 100

                fixed = [ "editor.show_task wrong search start",
                          "report.instrument_data wrong wrap for iterators",
                          "snapshot saves resource allocations"
                          "chartview refactoring",
                          "tidier popup menus",
                          "editor.show_task: finds the attribute again",
                          "print_chart: zoom to extent works correctly now"
                          "print_chart: better handling of media size"
                          "log window: error locator bug at wrapped error lines"
                          "editor.browser: runs correctly also under windows"
                          "controls improved" ]
                
                # 16.5 - 18.5 20H
                
            
            def Make_Release():
                effort = Multi("0d 1H 30M", planed="4H")
                start = up.up.Increments.end + "1d"
                gantt_shape = "diamond"
                complete = 100
                

        def Increments():
            def CrashBackups():
                effort = Multi("2H", planed="1d")
                complete = 100
                
            def TaskCoach():
                title = "Task coach interface"
                effort =  Multi("1d 2H 45M", planed="1d")
                complete = 100
                

    def Release_0_9_2():
        start = max(up.Release_0_9_1.end, "29.05.2006")
        version = "0.9.2"
                
        def Iterations():
            def Debugging_and_Refacturing():
                title = "Debug all"
                effort = Multi("1d", planed="4d")
                length = up.up.Increments.length
                balance = STRICT
                notes = """
                 -ghostscript und poster auf ctypes umstellen.
                 
                 - Refactoring of wizzard code (in new directory)
                 - plugin support
                 
                 metapie:
                 global incrementierender index für db.Type instances (um die reihenolge
                 der instanzierung herauszu bekommen)
                 read_only attribut für db.Types
                 
                 """
                complete = 100
                fixed = ["me returns better guess values",
                         "howto code for periodicals is improved",
                         "tabs are replaced by spaces",
                         "link_view attribute for observers implemented",
                         "report error handling",
                         "parent adjustments for tasks with acual data",
                         "editor component refactored",
                         "autoindent bugs are fixed",
                         "charting code was refactored" ]
                
                # 16.5 - 18.5 20H
                
            
            def Make_Release():
                effort = Multi("2H 45M", planed="4H")
                start = up.up.Increments.end + "1d"
                gantt_shape = "diamond"
                complete = 100

        def Increments():
            def EditReport_Dialogs():
                effort = "1H"
                complete = 100

            def BrowserImageList():
                effort = Multi("6H 15M", planed="0.5d")
                complete = 100
                notes = """
                 - tooltips
                 - create_project
                 - delete items
                 """
                
            def AdvancedEditing():
                effort = "4H 15M"
                notes = """
                 1. Edit Objects when the editor is hidden (in gantt charts and report)(done)
                 2. Browser edit(50%)
                 3. Direct editing inside the grid
                 4. Name editing
                 """
                complete = 100
                
    def Release_0_9_3():
        start = max(up.Release_0_9_2.end)
        version = "0.10.0"
                
        def Iterations():
            def Debugging_and_Refacturing():
                title = "Debug all"
                effort = Multi("13d 6H", planed="3d")
                load = DailyMax("3H")
                balance = STRICT
                complete = 100
                notes = """
                 
                 
                 
                 - plugin support
                 
                 
                 """

                fixed = ["bug nr. 1495787",
                         "Task: another (hopefully the last) me attrib fix",
                         "browser performance tuned",
                         "editor: update_code bugs fixed",
                         "Task code refactored tracer => bytecompiler",
                         "snapshots: resource allocation bug fixed",
                         "browser: workaround for display inconviniences",
                         "editor: highlights the active object",
                         "Task: It is now possible to reference parents",
                         "Task: bug fixes for recusrion errors",
                         "Task: it is possible to refer to parent ends i.e. up.end",
                         "Editor: fixed syntax error, if last line is indented"
                         "Gui: Better error handling",
                         "Gui: Improved Module reloading"
                         ]
                
                # 16.5 - 18.5 20H
                
            
            def Make_Release():
                effort = Multi("2H 30M", planed="4H")
                start = up.Debugging_and_Refacturing.end + "1d"
                gantt_shape = "diamond"
                complete = 100
                notes = """
                 Antwort schreiben für: improving periodicals
                 
                 """
                
                
                
    def Release_0_10_1():
        start = max(up.Release_0_9_3.end, "17.07.2006 14:00")
        version = "0.10.1"
                
        def Iterations():
            def Debugging_and_Refacturing():
                title = "Debug all"
                effort = Multi("1d 2H", planed="4d")
                length = up.up.Increments.length
                balance = STRICT
                notes = """
                 
                 - plugin support
                 - bei speichern position behalten
                 """
                complete = 100
                
                
                # 16.5 - 18.5 20H
                
            
            def Make_Release():
                effort = Multi("3H 15M", planed="4H")
                start = up.up.Increments.end + "1d"
                gantt_shape = "diamond"
                notes = """
                 Antwort schreiben für: improving periodicals
                 Fehler: Hier complete mit dialog ändern und dann auf aktualisieren drücken!!  
                 2: Applikation schließt nicht richtig.
                 """
                complete = 100

        def Increments():
            def TaskCalendar():
                effort = Multi("4H 45M", planed="3d")
                complete = 100
                
            def AttributeEditor():
                notes = """
                 - Task complete
                 - Observers
                 """
                effort = Multi("2d", planed="4d")
                complete = 100
                
                
        
    def Release_0_10_2():
        start = up.Release_0_10_1.end
        version = "0.10.2"
        
        def Iterations():
            def Debugging_and_Refacturing():
                effort = Multi("1d 6H 15M", planed="3d")
                #print "start", me.start.strftime()
                length = up.up.Increments.length
                #print "iter length", length, _l, up.up.Increments.path, me.path
                balance = STRICT
                complete = 100
                
            def Make_Release():
                effort = Multi("3H 15M", planed="4H")
                start = up.up.Increments.end + "1d"
                complete = 100
                gantt_shape = "diamond"
                

        def Increments():
            def AttributeEditor():
                notes = """
                 - Property Editor
                 - Scenario Container
                 """
                effort = Multi("2d 2H 45M", planed="2d")
                complete = 100

                
    def Release_0_10_3():
        start = up.Release_0_10_2.end
        version = "0.10.3"
        
        def Iterations():
            def Debugging_and_Refacturing():
                effort = Multi("1d 5H 45M", planed="3d")
                complete = 100

                
            def Make_Release():
                effort = Multi("1H", planed="4H")
                start = up.up.Increments.end + "1d"
                complete = 100
                gantt_shape = "diamond"
                

        def Increments():
            def BrowserMenu():
                def InsertTasks():
                    effort = Multi("4H 45M", planed="1d")
                    complete = 100

                def CorrectProjects():
                    notes = """
                     Menüpunkt: Anhand von code_item soll nach text änderungen,
                     das Projekt so korregiert werden damit es wieder in einen 
                     konsistenten Zustand gebracht werden.
                    """
                    effort = Multi("0d 3H 15M", planed="2d")
                    complete = 100
                     
                    
    def Release_0_11_0():
        start = up.Release_0_10_3.end
        version = "0.11.0"     
        
        def Iterations():
            def Debugging_and_Refacturing():
                start = up.up.Increments.start
                end = up.up.Increments.end
                effort = Multi("3d 3H", planed="3d")
                notes = """
                 - Project Context Menu funktioniert nicht (ist der splash)
                 - vacation monat wechsel ist ncht möglich (ok)
                 -  Diesen Task mit balance SMART und SLOPPY überprüfen.(ok)
                 """
                balance = STRICT
                complete = 100
                
            def Make_Release():
                effort = "4H"
                start = up.up.Increments.end + "1d"
                gantt_shape = "diamond"
                complete = 100
        
        def Increments():
            load = 0.6
            
            def ProjectMenu():
                def RenameTask():
                    effort = Multi("1H", planed="2H")
                    complete = 100
                
                def RenameResource():
                    effort = Multi("1H", planed="4H")
                    notes = """
                     Correct code anpassen
                     """
                    complete = 100
                    
                def CreateEvaluation():
                    title = "Create And Change Evaluation"
                    effort = Multi("5H 45M", planed="1d")
                    complete = 100
                    
                def CreateImport():
                    effort = Multi("30M", planed="2H")
                    complete = 100
                    
                def RemoveTask():
                    effort = "2H"
                    notes = """
                     Correct code anpassen
                     """
                    complete = 100
                    
                def RemoveResource():
                    effort = Multi("30M", planed="2H")
                    notes = """
                     Correct code anpassen
                     """
                    complete = 100
                    
                def CreateObserver():
                    effort = Multi("3H 45M", planed="4H")
                    complete = 100
                    
                def RenameObserver():
                    effort = Multi("30M", planed="2H")
                    complete = 100
                
                def MoveTask():
                    notes = """
                     drag and drop and per menu
                     """
                    complete = 100
                    
                def TaskData():
                    complete = 100
                    title = "Show task data of different Evaluations"
                    notes = """
                     Insert menu to choose the actual displayed data
                     todo: curent_eval_var_name (die aktuell verwendeten eval daten)
                           sollen nicht in _function gespeichert werden sondern in einer
                           map innerhalb der session, damit nach einem refresh der
                           curent_eval_var_name beibehalten wird (ca. 2H)
                           
                     """
                    effort = "2H 30M"
                                        
                def RemoveObserver():
                    effort = Multi("15M", planed="30M")
                    complete = 100
                    
                    
                def HTMLGeneratorDailog():
                    effort = Multi("2H", planed="3H")
                    complete = 100

    def Release_0_12_0():
        start = up.Release_0_11_0.end
        version = "0.12.0"
        max_load = DailyMax("4H")

        def Iterations():
            def Debugging_and_Refacturing():
                start = up.up.Increments.start
                end = up.up.Increments.end
                effort = "3d"
                balance = STRICT
                notes = """
                Rename of projects ==> rename in rest of file(ok)
                
                in edit dialogs den default button setzen
                
                In Windows:
                campux Besipiel drag and drop von content ==> 
                TreeControl reagiert nicht mehr
                
                Resource calendar for each scenario?
                """
                
                
            def Make_Release():
                effort = "4H"
                start = up.up.Increments.end + "1d"
                gantt_shape = "diamond"
                

        
        def Increments():
            def Dokumentation():
                effort = "3d"
                notes = """
                 -source dokumentation
                 -howtos (tests/rsource_task_load zum howto machen)
                 -help files
                 """
                
        
            def Perth_Chart():
                copy_src = structure.Framework.Charts.Perth
                
            def Change_Attribute_Declarations():
                def Task_Handling():
                    effort = "4H"
                    
                def AttributeEditors():
                    effort = "1d"
                    
            
    def Release_0_13_0():
        start = up.Release_0_12_0.end
        version = "0.13.0"
        
        def Increments():
            def CriticalChain():
                title = "Critical chain Computing"
            
            def Icons():
                effort = "2d"
                notes = """
                 -rename
                 -remove
                 -insert after
                 -inser before
                 -indent 
                 -unindent
                 """

            def Load_Save_Resource_Calendar():
                copy_src = structure.Framework.Resource.Load_Save_Resource_Calendar
            
            
            def BrowserMenu():
                effort = "2d"
                notes = """
                 - tooltips
                 - create_project
                 - delete items
                 """
            
            def TaskCoach_Howto():
                title = "A howto use the Task coach interface"
                effort = "5H"
                
                
            def Perth_Function_and_Howto():
                notes="Implementing perth estimation method"
                effort = "4H"
                
            def References_Part2():
                copy_src = structure.Documentation.References
                effort = structure.Documentation.References.effort / 2
                    
            def advanced_techniques():
                balance = SMART
                copy_src = structure.Documentation.Advanced_Techniques
        
                
            def MultiProjectBalancing():
                note = """
                A Howto for Enterprise resource balancing
                """
                effort = "4H"

            def ZeitstahlChart():
                effort = "1w"

    def Milestones():
        title = "Publication Milestones"

        def Pub1():
            start = up.up.Release_0_1_1.end
            line = "ms"
            milestone = True

        def Pub2():
            # Date cuts the reference to  up.Pub1.end 
            start = max(up.up.Release_0_2_0.end, Date(up.Pub1.end + "1w"))
            line = "ms"
            gantt_same_row = up.Pub1
            milestone = True
            
        def Pub3():
            start = max(up.up.Release_0_3_0.end, Date(up.Pub2.end + "1w"))
            line = "ms"
            gantt_same_row = up.Pub1
            milestone = True

        def Pub4():
            start = max(up.up.Release_0_4_0.end, Date(up.Pub3.end + "1w"))
            line = "ms"
            gantt_same_row = up.Pub1
            milestone = True

        def Pub5():
            start = max(up.up.Release_0_5_0.end, Date(up.Pub4.end + "1w"))
            line = "ms"
            gantt_same_row = up.Pub1
            milestone = True
            
        def Pub5_1():
            start = up.up.Release_0_5_1.end
            milestone = True
            gantt_same_row = up.Pub1

        def Pub6_1():
            start = up.up.Release_0_6_1.end
            milestone = True
            gantt_same_row = up.Pub1
            
        def Pub7_0():
            start = up.up.Release_0_7_0.end
            milestone = True
            gantt_same_row = up.Pub1
            
        def Pub7_1():
            start = up.up.Release_0_7_1.end
            milestone = True
            gantt_same_row = up.Pub1

            
        def Pub7_2():
            start = max(up.up.Release_0_7_2.end, "31.01.2006")
            milestone = True
            gantt_same_row = up.Pub1

        def Pub7_3():
            start = up.up.Release_0_7_3.end
            milestone = True
            gantt_same_row = up.Pub1

        def Pub7_4():
            start = up.up.Release_0_7_4.end
            milestone = True
            gantt_same_row = up.Pub1
            
        def Pub8_0():
            start = up.up.Release_0_8_0.end
            milestone = True
            gantt_same_row = up.Pub1
            
        def Pub8_1():
            start = up.up.Release_0_8_1.end
            milestone = True
            gantt_same_row = up.Pub1
            
        def Pub9_1():
            start = up.up.Release_0_9_1.end
            milestone = True
            gantt_same_row = up.Pub1
            
        def Pub9_2():
            start = up.up.Release_0_9_2.end
            milestone = True
            gantt_same_row = up.Pub1
            
        def End():
            start = max(root.Release_0_11_0.end, "20.4.2006")
            gantt_same_row = up.Pub1
            milestone = True



#times = taskcoach.read("/home/michael/michael.tsk")
#print "times", times
try:
    times = clocking.read("/home/michael/projstat/faces.clk")
except:
    times = []
#print "times", times
   
structure = Project(Faces_Structure)
not_adjusted = release = BalancedProject(faces_release, performed=times)
release = AdjustedProject(release)

#release = Project(faces_release)

#set the release version in the structur plan

current_release = release.Release_0_1_0

def generate_clocking_file(filename):
    clocking.generate(filename, current_release)
    return True

generate_clocking_file.faces_menu = "clocking/generate"
generate_clocking_file.faces_savefile = "/home/michael/projstat/faces.tsk"


def generate_taskcoach_files(filedir="/home/michael/projstat"):
    #taskcoach.generate_for_resources(filedir, current_release)
    taskcoach.generate_for_resources(filedir, release)
    return True

generate_taskcoach_files.faces_menu = "Task Coach/generate"
generate_taskcoach_files.faces_savedir = "/home/michael/projstat"#_default_clocking_file 


def extract_version_release(release, version):
    current_release = release
    for t in release:
        if t.version == version:
            current_release = t
            version = None
            
        if t.copy_src:
            t.copy_src.version = t.version
            t.copy_src.start = t.start
            t.copy_src.end = t.end
            t.copy_src.effort = t.effort
            
    return current_release

current_release = extract_version_release(release, current_version)

class CriticalR(report.Critical):
    data = current_release
    visible = in_mode("manage")

    
class Release_Of(report.Standard):
    data = current_release
    visible = in_mode("manage")
    
    def make_report(self, data):
        for t in data: 
            o = t
            if t.copy_src:
                t = t.copy_src

            yield (t.indent_name(), 
                   t.effort, t.version,
                   t.load,
                   t.complete,
                   t.to_string['%x %H:%M'].start,
                   t.to_string['%x %H:%M'].end,
                   t.length, 
                   t.todo)
            
    def modify_row(self, row):
        task = row[0].get_ref()[0]
        if not isinstance(task, Task):
            return row        
            
        for c in row:
            c.right_border = True
            if task.children:
                c.font_bold = True
                
            if task.complete == 100:
                c.back_color = "green"

        row[0].left_border = True            
        row[-1].right_border = True
            
        return row


class Calendar(report.Calendar):
    visible = in_mode("plan")
    data = release
            
    def prepare_data(self, data):
        return filter(lambda t: not t.children and not t.milestone, tuple(data))
    

class CalendarOf(report.Calendar):
    visible = in_mode("manage")
    data = current_release

class ReleaseMixin(object):
    def create_objects(self, data):
        for t in data:
            if t.depth == 1 or t.milestone:
                yield t

    def get_shape_name(self, task):
        if not task.milestone and not task.name == "Milestones": 
            return "bar"
        return gantt.Standard.get_shape_name(self, task)
        
    def get_property_group(self, task):
        if not task.milestone and not task.name == "Milestones": 
            return "leaf"
            
        return super(ReleaseMixin, self).get_property_group(task)
    
    

class Release_Plan(ReleaseMixin, gantt.Standard):
    visible = in_mode("manage", "plan")
    data = release
    sharex = "all"
    title_attrib = "title"
    show_complete = True
    #draw_rowlines = True
    #auto_scale_y = True
    
    def create_diamond(self, widget, title, task):
        widget.set_shape(gantt.diamond)
        widget.text(title, HCENTER, BOTTOM - VSEP,
                    horizontalalignment ="center",
                    verticalalignment="top",
                    fontproperties="bottom")



class Critical(gantt.Critical):
    visible = in_mode("manage", "plan")
    data = release
    data = current_release
    colors = {0 : "red", "4d" : "orange", "1000d" : "green" }
        

class Gantt_of(gantt.Standard):
    visible = in_mode("manage")
    data = current_release
    sharex = "current"
    properties = {"parent.bar.height" : 5.0,
                  "parent.weight" : 900,
                  "parent.bar.facecolor" : "#FFFF00",
                  "parent.bar.edgecolor" : "#FFA500",
                  "leaf.alpha" : 0.7,
                  "leaf.complete.facecolor" : "gold",
                  "leaf.complete.alpha" : 0.6,
                  "parent.end.up" : 0,
                  "parent.complete.height" : 2.0,
                  "parent.bar.alpha" : 0.7,
                  "parent.size" : 15,
                  "leaf.complete.linewidth" : 0.0,
                  "parent.start.facecolor" : "#FFC0CB"}
    parent_shape = "circle_bar_wedge"
     
    def modify_widget(self, go, task):
        if task.copy_src:
            go.fobj = task.copy_src
            
        
            
class Resource_of(resource.Standard):
    visible = in_mode("manage")
    data = current_release
    sharex = "current"
    
    
    
    def modify_row(self, row_widget, res):
        self.add_load_line(row_widget, 1.0, edgecolor="red")
        


class Workload(resource.Standard):
    data = release
    visible = in_mode("plan")
    sharex = "all"
    
    
    def create_row(self, res):
        row = resource.Standard.create_row(self, res)
        
        load_1 = self.load_offset(1.0)
        row.add_artist(Polygon(((LEFT, BOTTOM + load_1),
                                (RIGHT, BOTTOM + load_1)),\
                               edgecolor="green"))
        row.text("load 1.0", LEFT + 2*HSEP, BOTTOM + load_1)
        return row
    

class BreakDown(workbreakdown.Standard):
    visible = in_mode("plan")
    data = structure #.Gui
    properties = {"complete.facecolor" : "gold"}
    
    def get_property_group(self, task):
        if task.complete >= 100: return "complete"
        return super(BreakDown, self).get_property_group(task)

        
class Structure_Report(report.Standard):
    data = structure
    visible = in_mode("plan")
    
    def make_report(self, data):
        for t in data: 
            yield (t.indent_name(), t.effort, t.version,
                   t.start, t.end, t.note)

# a report of all tasks which are not assigned to the release plan
class Not_Released(report.Standard):
    data = structure
    visible = in_mode("plan")
    
    def make_report(self, data):
        for t in data: 
            if t.version or t.complete == 100: continue
            cols = (t.indent_name(), t.effort, t.version, t.note)
            if t.children:
                cols = map(lambda c: \
                     report.Cell(c, 
                                 font_bold=True,
                                 back_color="green"), cols)
                
            yield cols

            
class Bookings(report.Standard):
    visible = in_mode("manage")
    data = current_release
        
    def make_report(self, data):
        start = data.start.to_datetime()
        end = data.end.to_datetime()
        resources = data.all_resources()
        scenario = self.data.scenario
        for r in resources: 
            cell = report.Cell(r.name)
            cell.font_bold = True
            cell.font_size = "large"
            yield cell, start, end, data.version
            
            bookings = r.get_bookings_at(start, end, scenario)
            for b in bookings:
                yield b.name, b.book_start.strftime("%x %H:%M"), \
                b.book_end.strftime("%x %H:%M"), b.actual
            
            
        #    yield (t.indent_name(), t.start)
        
    


try:
    import facesproj_snpt #This module contains snapshots
    #to_compare = faces_release
    to_compare = facesproj_snpt.release_060606_2306
    compare_project = Project(facesproj_snpt.release_061020_1250, "_default", "release_060606_2306")
    compare_release = extract_version_release(compare_project, 
                                               current_version) 
                              
    class Compare(gantt.Compare):
        data = unify(current_release, compare_release)

    class Gantt(gantt.Standard):
        data = release
    
    
        
except ImportError:
    pass
    
            
            
            
#
class FacesHTML(generator.StandardHTML):
    title = "Accounting Software"
    observers = generator.all()
    #observers = [Calendar]
    tile_size = (800, 600)
    BreakDown_zoom_levels = ( 1, 1.5, 3 )
   
FacesHTML.faces_savedir = "/home/michael/temp/faces_html"

new_test = False
if new_test:
    from pylab import *
    
    class Free(ch.PylabChart):
        def create(self):
            
            sg = SmallGantt(self.figure, [0, 0.2, 1, 0.8])
            #sr = SmallResource(gca())
            
            cal_date = sg.time_scale.to_num
                    
            axes([0, 0, 1, 0.2], sharex=gca())#.set_frame_on(False)
            #axes([0.1, 0.1, 0.8, 0.3])
            
            starts = map(lambda t: (cal_date(t.start), t), release)
            starts.sort()
            depths = map(lambda s: s[1].depth, starts)
            starts = map(lambda s: s[0], starts)
            
            plot(starts, depths)
    
    
if __name__ == "__main__":
    import sys
    import locale

    dest = sys.argv[1]
    locale.setlocale(locale.LC_ALL, "")
    FacesHTML().create(dest, 2)
