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

import sys
import os
import os.path

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from distutils.command.install_data import install_data
from distutils.dir_util import remove_tree, mkpath
from distutils.errors import DistutilsFileError, DistutilsInternalError
from distutils import log



def copy_tree(src, dst, filter_=None):
    from distutils.file_util import copy_file

    if not os.path.isdir(src):
        raise DistutilsFileError, \
              "cannot copy tree '%s': not a directory" % src
    try:
        names = os.listdir(src)
    except os.error, (errno, errstr):
        if dry_run:
            names = []
        else:
            raise DistutilsFileError, \
                  "error listing files in '%s': %s" % (src, errstr)

    mkpath(dst)
    outputs = []

    for n in names:
        src_name = os.path.join(src, n)
        dst_name = os.path.join(dst, n)

        if filter_ and not filter_(src_name): continue

        if os.path.isdir(src_name):
            outputs.extend(copy_tree(src_name, dst_name, filter_))
        else:
            copy_file(src_name, dst_name)
            outputs.append(dst_name)

    return outputs


def copy_filter(src):
    dir, name = os.path.split(src)
    return name != "setup" and not name.startswith(".svn")


class smart_install_data(install_data):
    def run(self):
        #need to change self.install_dir to the actual library dir
        install_cmd = self.get_finalized_command('install')
        self.install_dir = getattr(install_cmd, 'install_lib')
        return install_data.run(self)


used_install_data = smart_install_data


making_dist = False
make_py2exe = False
help = False


for a in sys.argv:
    if a[1:].startswith("dist") or a.startswith("egg"): making_dist = True
    if a == "py2exe":
        make_py2exe = True
        making_dist = True
        used_install_data = install_data

    if a.startswith("--help") or a.startswith("register"):
        making_dist = False
        help = True
        break


options = {"py2exe": { # create a compressed zip archive
    "compressed": 1,
    "packages": ["encodings", "pytz.zoneinfo", "faces.lib", "faces.charting", "faces.gui", "faces.tools", "faces.gui.editor"],
    "includes": ["faces.tools.clocking",
		 "matplotlib.numerix.random_array",
                 "pylab",
                 "site" ],
    "excludes": [  "curses" ]
    }}

faces_dest_dir = "faces" #os.path.join("src", "faces")
metapie_dest_dir = "metapie" #os.path.join("src", "metapie")


if making_dist:
    try: remove_tree(faces_dest_dir)
    except: pass

    try: remove_tree(metapie_dest_dir)
    except: pass

    import metapie
    import faces
    import matplotlib

    faces_dir = os.path.dirname(faces.__file__)
    metapie_dir = os.path.dirname(metapie.__file__)

    copy_tree(faces_dir, faces_dest_dir, copy_filter)
    copy_tree(metapie_dir, metapie_dest_dir, copy_filter)
else:
    import metapie
    import faces
    import matplotlib


try:
    import py2exe

    manifest_template = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="x86"
    name="%(prog)s"
    type="win32"
/>
<description>%(prog)s Program</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
'''
    RT_MANIFEST = 24
    
    pp_opt=dict(script="faces/gui/plangui.py",
                other_resources=[(RT_MANIFEST, 1,
                                  manifest_template\
                                  % dict(prog="plangui"))],
                icon_resources=[(1, "faces/gui/resources/images/gantt.ico")],)
                
    class InnoScript:
        def __init__(self, name, lib_dir, dist_dir, windows_exe_files=[],
                     lib_files=[], version="0.1"):
            self.lib_dir = lib_dir
            self.dist_dir = dist_dir
            if not self.dist_dir[-1] in "\\/":
                self.dist_dir += "\\"
            self.name = name
            self.version = version
            self.windows_exe_files = [self.chop(p) for p in windows_exe_files]
            self.lib_files = [self.chop(p) for p in lib_files]


        def chop(self, pathname):
            print "chop", pathname
            assert pathname.startswith(self.dist_dir)
            return pathname[len(self.dist_dir):]


        def create(self, pathname="dist\\faces.iss"):
            self.pathname = pathname
            ofi = self.file = open(pathname, "w")
            print >> ofi, "; WARNING: This script has been created by py2exe." + \
                  " Changes to this script"
            print >> ofi, "; will be overwritten the next time py2exe is run!"
            print >> ofi, r"[Languages]"
            print >> ofi, r'Name: English; MessagesFile: "compiler:Default.isl"'
            print >> ofi, r'Name: Deutsch; MessagesFile: "compiler:Languages\German.isl"'
            print >> ofi
            
            print >> ofi, r"[Setup]"
            print >> ofi, r"AppName=%s" % self.name
            print >> ofi, r"AppVerName=%s %s" % (self.name, self.version)
            print >> ofi, r"DefaultDirName={pf}\%s" % self.name
            print >> ofi, r"DefaultGroupName=%s" % self.name
            print >> ofi, "Compression=bzip"
            print >> ofi

            print >> ofi, r"[Files]"
            for path in self.windows_exe_files + self.lib_files:
                print >> ofi, r'Source: "%s"; DestDir: "{app}\%s"; Flags: ignoreversion'\
                      % (path, os.path.dirname(path))
            print >> ofi

            print >> ofi, r"[Icons]"
            for path in self.windows_exe_files:
                print >> ofi, r'Name: "{group}\%s"; Filename: "{app}\%s"' % \
                      (self.name, path)
            print >> ofi, 'Name: "{group}\Uninstall %s"; Filename: "{uninstallexe}"' % self.name

        def compile(self):
            try:
                import ctypes
            except ImportError:
                try:
                    import win32api
                except ImportError:
                    import os
                    os.startfile(self.pathname)
                else:
                    print "Ok, using win32api."
                    win32api.ShellExecute(0, "compile",
                                          self.pathname,
                                          None,
                                          None,
                                          0)
            else:
                print "Cool, you have ctypes installed."
                res = ctypes.windll.shell32.ShellExecuteA(0, "compile",
                                                          self.pathname,
                                                          None,
                                                          None,
                                                          0)
                if res < 32:
                    raise RuntimeError, "ShellExecute failed, error %d" % res



    class build_installer(py2exe.build_exe.py2exe):
        # This class first builds the exe file(s), then creates a Windows installer.
        # You need InnoSetup for it.
        def run(self):
            # First, let py2exe do it's work.
            py2exe.build_exe.py2exe.run(self)

            lib_dir = self.lib_dir
            dist_dir = self.dist_dir
        
            # create the Installer, using the files py2exe has created.
            script = InnoScript("faces",
                                lib_dir,
                                dist_dir,
                                self.windows_exe_files,
                                self.lib_files,
                                version=faces.__version__)
            print "*** creating the inno setup script***"
            script.create()
            print "*** compiling the inno setup script***"
            script.compile()


        def find_dlls(self, extensions):
            exedir = os.path.dirname(sys.executable)
            dlls = py2exe.build_exe.py2exe.find_dlls(self, extensions)
            #dlls.add(os.path.join(exedir, "msvcp71.dll"))
            #dlls.add(os.path.join(exedir, "msvcr71.dll"))
            #dlls.add(os.path.join(exedir, "gdiplus.dll"))
            #print "extensions", extensions
            #print "dlls", dlls
            #raise RuntimeError()
            return dlls
            
except:
    class build_installer: pass
    pp_opt={}


if not help:
    def get_data_files(unix_src, os_src):
        names = os.listdir(os_src)
        dir_list = []
        file_list = []
        for n in names:
            name = os.path.join(os_src, n)
            if os.path.isdir(name):
                dir_list.extend(get_data_files(unix_src + "/" + n, name))
            else:
                file_list.append(name)

        if file_list:
            dir_list.insert(0, (unix_src, file_list))
        return dir_list

    if make_py2exe:
        import glob
        mat_data_path = matplotlib.get_data_path()

        data_files = get_data_files("resources/faces/templates",
                                    os.path.join(faces_dest_dir, "templates"))
        data_files += get_data_files("resources/faces/gui",
                                     os.path.join(faces_dest_dir,
                                                  "gui", "resources"))
        data_files += get_data_files("resources/metapie",
                                     os.path.join(metapie_dest_dir, "resources"))
        data_files += get_data_files("howtos",
                                     os.path.join(faces_dest_dir, "howtos"))
        
        #data_files += get_data_files("resources/faces/locale",
        #                            os.path.join("faces", "locale"))
        #data_files += get_data_files("resources/metapie/locale",
        #                             os.path.join("metapie", "locale"))

        isdir = os.path.isdir
        split = os.path.split

        def matplot_recursive_add(path, prefix=""):
            paths = glob.glob(os.path.join(path, "*"))
            dirs = [ p for p in paths if isdir(p) ]
            files = [ p for p in paths if not isdir(p) ]
            dir, name = split(path)
            if prefix:
                prefix += "/%s" % name
            else:
                prefix = "matplotlibdata"
            
            if files:
                data_files.append((prefix, files))
            
            for d in dirs:
                matplot_recursive_add(d, prefix)
                
        matplot_recursive_add(mat_data_path)
        data_files.append((".", (os.path.join("..", "extbin", "poster.exe"),)))

    else:
        data_files = get_data_files("faces/templates",
                                    os.path.join(faces_dest_dir, "templates"))
        
        data_files += get_data_files("faces/gui/resources",
                                     os.path.join(faces_dest_dir,
                                                  "gui", "resources"))
        data_files += get_data_files("faces/howtos",
                                     os.path.join(faces_dest_dir, "howtos"))
        data_files += get_data_files("metapie/resources",
                                     os.path.join(metapie_dest_dir, "resources"))
        #data_files += get_data_files("faces/locale",
        #                            os.path.join(faces_dest_dir, "locale"))
        #data_files += get_data_files("metapie/locale",
        #                             os.path.join(metapie_dest_dir, "locale"))



else:
    data_files = []
    

long_desc="""faces is a powerful and flexible
project management tool. It not only offers
many extraordinary features like, multiple
resource balancing algorithms, multi scenario planing.
but can also be easily extended and customized.
Faces consists of a python class framework and a graphical
front-end."""



setup(name="faces-pm", version = faces.__version__,
      url="http://faces.homeip.net/",
      author="Michael Reithinger",
      author_email="mreithinger@web.de",
      description="Extendible project management software",
      long_description=long_desc,
      download_url="http://faces.homeip.net/download.html",
      cmdclass = {"py2exe": build_installer ,
                  'install_data': used_install_data },
      options=options,
      windows=[pp_opt],
      packages=["faces", "faces.gui", "faces.charting",
                "faces.lib", "faces.tools", "metapie",
                "faces.gui.editor",
                "metapie.gui", "metapie.gui.wxcontrols"],
      data_files=data_files,
      classifiers=["Development Status :: 4 - Beta",
                   "Environment :: Console",
                   "Environment :: Win32 (MS Windows)",
                   "Environment :: X11 Applications",
                   "Intended Audience :: Other Audience",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: GNU General Public License (GPL)",
                   "Operating System :: OS Independent",
                   "Topic :: Office/Business",
                   "Topic :: Office/Business :: Scheduling",
                   "Topic :: Software Development" ],
      scripts=['bin/faces'],
#      install_requires=[ 'matplotlib>=0.87.2' ]
#                         'wxPython>=2.6.0',
#                         'Cheetah>=2.0' ],
      )

if making_dist:
    remove_tree(faces_dest_dir)
    remove_tree(metapie_dest_dir)
