############################################################################
#   Copyright (C) 2005 by Reithinger GmbH
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

import wx
import webbrowser
import tempfile
import os
import faces.plocale
import metapie
import urllib
import sys
import ConfigParser
import metapie.dbtransient as db
import metapie.gui.views as views


_ = faces.plocale.get_gettext()


#--------------------------------------------------------------------------------
#sends project per email

class ProjectSender(object):
    def __init__(self):
        fh, self.path = tempfile.mkstemp(".html")
        os.close(fh)
        self.out = file(self.path, "w")
        print >> self.out,\
_("""    
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html><head><title>Sender Emails</title></head>
<body>
<table border=1>
<tr><td><b>Recipient</b></td><td><b>Files</b></td><td><b>Send</b></td></tr>
""")

    def __del__(self):
        if not self.out.closed: self.out.close()
        

    def add_recipient(self, recipients, subject, projects):
        if isinstance(recipients, (str, unicode)):
            recipients = (recipients,)

        if isinstance(projects[0], (str, unicode)):
            projects = (projects,)

        def make_mail_line():
            to = ";".join(recipients)
            subj = urllib.quote(subject)

            content = ""
            small_content = ""
            for pname, ptext in projects:
                content += '<__project__ name="%s">\n' % str(pname)
                content += ptext
                content += '\n</__project__>\n'

            content = urllib.quote(content)
            return "%s?subject=%s&body=%s" % (to, subj, content)


        print >> self.out,\
_("""
<tr><td valign="top">%(email)s</td>
<td valign="top">%(projects)s</td>
<td valign="top"><a href="mailto:%(mail)s">Send</a></td></tr>
""") % { "email" : "</br>".join(recipients),
         "projects" : "</br> ".join(map(lambda pt: pt[0], projects)),
         "mail" : make_mail_line() }


        def make_small_mail_line():
            to = ";".join(recipients)
            subj = urllib.quote(subject)

            content = ""
            small_content = ""
            for pname, ptext in projects:
                content += '<__project__ name="%s">\n' % str(pname)
                content += '</__project__>\n'

            content = urllib.quote(content)
            return "%s?subject=%s&body=%s" % (to, subj, content)


        print >> self.out,\
_("""
</table>
<p/>
If you click on the links above and nothing happens, you
probably use Microsoft Internet Explorer, which is not able
to generate long email content. Please use the links below
and paste in your project text manually
<p/>
<table border=1>
<tr><td><b>Recipient</b></td><td><b>Files</b></td><td><b>Send</b></td></tr>
<tr><td valign="top">%(email)s</td>
<td valign="top">%(projects)s</td>
<td valign="top"><a href="mailto:%(mail)s">Send</a></td></tr>
""") % { "email" : "</br>".join(recipients),
         "projects" : "</br> ".join(map(lambda pt: pt[0], projects)),
         "mail" : make_small_mail_line() }


    def send(self, new=True):
        print >> self.out, _("</table></body></html>")
        self.out.close()
        webbrowser.open("file://%s" % self.path, new, False)
        


#---------------------------------------------------------------------------
# calls external programs and handles errors

class CallError(db.Model):
    path = db.Text()

    def check_constraints(self):
        if not os.path.exists(self.path):
            error = db.ConstraintError()
            error.message["path"] = _("path does not exist")
            raise error
       


class ErrorView(views.FormView):
    __model__ = CallError
    __view_name__ = "default"

    text = """
faces cannot execute the command '%(command)s' of the %(name)s program.
Probably it cannot find the excecutable. Please enter the path to
the executable '%(command)s':
"""
    
    format = _("""
descripton
path(OpenFile)>
%s
(0,0)
--
(buttons){m}
""")

    format_down = _("""
[If you have no idea about %(name)s you probably have not installed it.]
btn_install{m}
""")

    format_buttons = "btn_ok|(0,5)|btn_cancel"
    

    def __init__(self, parent, command, name, download):
        self.command = command
        self.download = download
        self.name = name or command

        if download:
            self.format_down = self.format_down % self.__dict__
            fdown = "(down)"
        else:
            fdown = ""
               
        self.format = self.format % fdown
        super(ErrorView, self).__init__(parent)


    def prepare(self):
        self.grow_row(-3)


    def create_controls(self):
        text = self.text % self.__dict__
        self.descripton = self.get_label(text.strip())


    def create_buttons_controls(self, view):
        view.btn_ok = view.get_button(wx.ID_OK)
        def ok():
            if self.save():
                self.GetParent().EndModal(wx.ID_OK)
                
        view.btn_ok.attach(ok)


    def button_cancel(self):
        self.rollback()
        self.GetParent().EndModal(wx.ID_CANCEL)


    def create_down_controls(self, view):
        view.btn_install = view.get_button(_("Install From Here..."))
        def install():
            webbrowser.open(self.download, True, False)

        view.btn_install.attach(install)


class CallErrorDlg(wx.Dialog):
    def __init__(self, command, path, name, download):
        wx.Dialog.__init__(self,
                           wx.GetApp().GetTopWindow(), -1,
                           _("Error in calling %s") % name,
                           style=wx.DEFAULT_DIALOG_STYLE)

        self.data = CallError(path=path)
        self.command = command
        self.name = name
        self.download = download
       

    def ShowModal(self):
        view = self.data.constitute("default")(self,
                                               self.command,
                                               self.name,
                                               self.download)
        w, h = view.GetSizer().CalcMin()
        self.SetClientSize((w, h + 30))
        return wx.Dialog.ShowModal(self)


def call_command(command, arguments, name=None, download=None):
    config = metapie.controller().config

    if config.has_option("bins", command):
        path = (config.get("bins", command),)
    else:
        cmd = command
        if wx.Platform == '__WXMSW__':
            cmd += '.exe'
        
        path = os.environ.get("PATH", "")
        path = path.split(os.pathsep)
        path.insert(0, os.path.abspath(os.path.split(sys.argv[0])[0]))
        path = map(lambda p: os.path.join(p, cmd), path)

    for p in path:
        try:
            args = [ os.path.split(p)[1] ] + list(arguments)
            if os.spawnv(os.P_WAIT, p, args) == 0: return
        except OSError:
            pass
        
    
    dlg = CallErrorDlg(command, path[-1], name, download)
    try:
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.data.path

            try:
                args = [ os.path.split(str(path))[1] ] + list(arguments)
                result = os.spawnv(os.P_WAIT, path, args)
            except OSError:
                res = -2

            if result == 0:
                try:
                    config.add_section("bins")
                except ConfigParser.DuplicateSectionError:
                    pass

                config.set("bins", command, path)
                return

        raise RuntimeError("cannot execute %s" % command)
    finally:
        dlg.Destroy()
        

##def call_ghostscript(arguments):
##    import ctypes
##    ct

##    gs_main_instance *minst;

##int main(int argc, char *argv[])
##{
##    int code;
##    int exit_code;
##    const char * gsargv[10];
##    int gsargc;
##    gsargv[0] = "ps2pdf";	/* actual value doesn't matter */
##    gsargv[1] = "-dNOPAUSE";
##    gsargv[2] = "-dBATCH";
##    gsargv[3] = "-dSAFER";
##    gsargv[4] = "-sDEVICE=pdfwrite";
##    gsargv[5] = "-sOutputFile=out.pdf";
##    gsargv[6] = "-c";
##    gsargv[7] = ".setpdfwrite";
##    gsargv[8] = "-f";
##    gsargv[9] = "input.ps";
##    gsargc=10;

##    code = gsapi_new_instance(&minst, NULL);
##    if (code < 0)
##	return 1;
##    code = gsapi_init_with_args(minst, gsargc, gsargv);
##    gsapi_exit(minst);

##    gsapi_delete_instance(minst);

##    if ((code == 0) || (code == e_Quit))
##	return 0;
##    return 1;
##}
