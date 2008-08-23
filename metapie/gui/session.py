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

import wx
from wx import py
from controller import controller
import metapie.navigator as navigator
import pyeditor
import sys
import re
import metapie.tools as tools

_ = tools.get_gettext()


class ShellView(py.shell.Shell, navigator.View, pyeditor.StyleMixin):
    def __init__(self, parent, locals=None):
        if not locals:
            locals = {}
            
        locals["controller"] = controller

        py.shell.Shell.__init__(self, parent, -1,
                                style=wx.SUNKEN_BORDER,
                                locals=locals)
        self.setup_style()
        wx.EVT_IDLE(self, self._on_idle)


    def _on_idle(self, event):
        self.adjust_number_margin(1)
        event.Skip()


    def accept_sibling(self, sibling):
        if not isinstance(sibling, MessageLogger):
            return navigator.SIBLING_ABOVE

        return False


class MessageLogger(wx.TextCtrl, navigator.View):
    instance = None
    source_pos_pattern1 = re.compile(r'File\s+"([^"]+)", line\s+(\d+)')
    source_pos_pattern2 = re.compile(r'([^:]+):(\d+):')
    
    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, -1,
                             style=wx.TE_MULTILINE\
                             |wx.TE_READONLY|wx.TE_RICH|wx.TE_WORDWRAP)

        self.is_err_mode = False
        wx.EVT_KEY_DOWN(self, self.OnKeyDown)
        wx.EVT_LEFT_DCLICK(self, self.OnEnter)
        

    def __height__(self):
        height = controller().stacker.GetClientSizeTuple()[1]
        return height / 4


    def OnKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.OnEnter(event)
        else:
            event.Skip()
            

    def OnEnter(self, event):
        text = self.GetValue()
        pos = self.GetInsertionPoint()
        col, row = self.PositionToXY(pos)
        start = self.XYToPosition(0, row)
        text = self.GetRange(start, self.GetLastPosition())
        try:
            text = text[:text.index("\n")]
        except ValueError:
            pass
        
        self.__jump_to(text)

        
    def Destroy(self):
        wx.TextCtrl.Destroy(self)
        self.__class__.instance = None


    def accept_sibling(self, sibling):
        return navigator.SIBLING_ABOVE


    def append_text(self, text):
        lines = text.split("\n")

        sep = ""
        for l in lines:
            self.AppendText(sep)
            if sep: self.is_err_mode = False
            else:
                sep = "\n"

            start_pos = self.GetLastPosition()
            
            if l.startswith("<e>"):
                self.is_err_mode = False
                self.AppendText(l[3:])
                self.is_err_mode = True
            else:
                self.AppendText(l)

            if self.is_err_mode:
                last_pos = self.GetLastPosition()
                self.SetStyle(start_pos, last_pos, wx.TextAttr(wx.RED))


    def __jump_to(self, text):
        mo = self.source_pos_pattern1.search(text)
        if not mo: mo = self.source_pos_pattern2.search(text)
        if mo: Session.instance.jump_to_file(mo.group(1), int(mo.group(2)))


class _LogStream:
    last_output_was_err = False
    
    def __init__(self, session, is_err):
        self.session = session
        self.is_err = is_err


    def write(self, string):
        if self.is_err:
            sys.__stderr__.write(string)
            if not _LogStream.last_output_was_err:
                string = "<e>%s" % string
                _LogStream.last_output_was_err = True
            
            lines = string.split("\n")
            string = "\n<e>".join(lines)
        else:
            _LogStream.last_output_was_err = False
            sys.__stdout__.write(string)

        session = self.session
       
        def to_view(text):
            try:
                focus = wx.Window_FindFocus()

                view = controller().get_active_view_by_id(session.logger_id)
                view.append_text(text)
                if self.is_err:
                    view.SetFocus()
                elif focus:
                    focus.SetFocus()
            except:
                pass
        
        view = controller().get_active_view_by_id(session.logger_id)
        if not view:
            view = controller().create_view(session.logger_id)
            wx.CallAfter(to_view, session.log_content)

        session.log_content += string
        wx.CallAfter(to_view, string)
    

class Session(navigator.Model):
    SHELL_FACTORY = ShellView
    LOGGER = MessageLogger
    instance = None
    
    def __init__(self):
        self.files = {}
        Session.instance = self

    def __str__(self):
        return "Session"


    def register(self):
        controller().register_view(\
            self, _("Shell"), self.SHELL_FACTORY, "terminal")


    def install_logger(self):
        self.log_content = ""
        self.logger_id = controller().register_view(\
            self, _("Log"), self.LOGGER, "log")
        sys.stdout = _LogStream(self, False)
        sys.stderr = _LogStream(self, True)
        

    def clear_logs(self):
        self.log_content = ""
        _LogStream.last_output_was_err = False
        view = controller().get_active_view_by_id(self.logger_id)
        if view: view.Clear()


    def remove_empty_logview(self):
        if not self.log_content:
            ctrl = controller()
            view = ctrl.get_active_view_by_id(self.logger_id)
            if view: ctrl.destroy_view(view)


    def jump_to_file(self, path, line):
        pass
                

    def accept_sibling(self, sibling):
        return navigator.SIBLING_ABOVE

        
