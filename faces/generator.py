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
import faces
import faces.observer
import faces.plocale
import os
import os.path
import shutil
import faces.utils as utils
import faces.report
import faces.charting.tools as tools
import matplotlib.font_manager as font
import matplotlib.transforms as mtrans
import math

try:
    import Cheetah.Template as CHTemplate

    #make shure that thismodules will be
    #als imported for the freezed version
    import Cheetah.Version
    import Cheetah.DummyTransaction
    import Cheetah.NameMapper
    import Cheetah.CacheRegion
    import Cheetah.Filters 
    import Cheetah.ErrorCatchers

    _cheetah_is_installed = True
except ImportError:
    _cheetah_is_installed = False

_is_source = True
_ = faces.plocale.get_gettext()    

_html_path = utils.get_template_path()
_html_path = os.path.join(_html_path, "html")


def all(module=None):
    def _all_observers(*args):
        if module:
            iterator = ( module, )
        else:
            iterator = sys.modules.values()

        observer = []
        for m in iterator:
            if not m or not getattr(m, "__file__", None) \
                   or getattr(m, "_is_source_", False):
                continue

            for k, v in m.__dict__.items():
                try:
                    if issubclass(v, faces.observer.Observer):
                        observer.append(v)
                except:
                    pass

        return observer

    return _all_observers
 
    

class _GeneratorType(type):
    def __init__(cls, name, bases, dict_):
        cls.faces_menu = _("Generate %s...") % name
        cls.faces_menu_icon = "run16"


class LaTexGenerator(object):
    __metaclass__ = _GeneratorType
    template = ""
    output = ""
    encoding = "utf-8"

    def create(self):
        template = CHTemplate.Template(file=self.template)

        #tst = file("/home/michael/temp/cheetah_modules.py", "w")
        #tst.write(template.generatedModuleCode())
        #tst.close()
    
        #temporary disable progress display of others
        self.progress_start = utils.progress_start
        self.progress_end = utils.progress_end
        self.progress_update = utils.progress_update

        def dumy(*args, **kwargs): pass
        utils.progress_start = dumy
        utils.progress_end = dumy
        utils.progress_update = dumy


        self.progress_start(_("generate Latex for %s")\
                            % self.__class__.__name__,
                            1, _("prepare"))
        try:
            template.me = self

            if self.output:
                of = file(self.output, "w")
            else:
                of = sys.stdout

            print >> of, template
            
            if self.output: of.close()
        finally:
            self.progress_end()
            utils.progress_start = self.progress_start
            utils.progress_end = self.progress_end
            utils.progress_update = self.progress_update


    def encode(self, text):
        if type(text) is unicode:
            return str(text.encode(self.encoding))
        return str(text)

    def _execute(cls):
        cls().create()

    _execute = classmethod(_execute)

    #faces_savedir = ""
    faces_execute = _execute



class Generator(object):
    __metaclass__ = _GeneratorType
    observers = None
    template_path = ""

    __attrib_completions__ = {
        "#observers" : { "generator.all()" : 'generator.all()' },
        "observers" : 'observers = ',
        "template_path" : 'template_path = ""',
        }


    def __init__(self):
        if not self.observers:
            raise RuntimeError("no observer attribute specified")

        if callable(self.observers):
            self.observers = self.observers()
        
        self.observers = self.categorize_observers(self.observers)

    
    def categorize_observers(self, observers):
        types = {}
        
        for o in observers:
            types.setdefault((o.__type_name__, o.__type_image__), []).append(o)

        return types


    def check(self):
        if not _cheetah_is_installed:
            print >> sys.stderr, _("You must have installed the "\
                                   + "Cheetah Template engine " \
                                   + "to perform this")
            return False

        return True


    def template(self, name):
        return CHTemplate.Template(file=os.path.join(self.template_path, name))
    

    def _execute(cls, path):
        cls().create(path)

    _execute = classmethod(_execute)

    faces_savedir = ""
    faces_execute = _execute


class HTMLGenerator(Generator):
    template_path = os.path.join(_html_path, "standard")
    resource_path = os.path.join(_html_path, "standard", "resources")
    title = ""
    tile_size = (800, 600)
    verbosity = 2
    clean_path = True
    zoom_levels = ( 1, 2 ) #, 4, 6, 8 )
    overlap = 0.2
    font_size = 12
    dpi = 64
    encoding = "utf-8" #"iso8859-15"

    __attrib_completions__ = Generator.__attrib_completions__.copy()
    __attrib_completions__.update({\
        "resource_path" : 'resource_path = ""',
        "title" : 'title = ""',
        "tile_size" : 'tile_size = (800, 600)',
        "verbosity" : 'verbosity = 2',
        "clean_path" : 'clean_path = True',
        "zoom_levels" : 'zoom_levels = ( 1, 2, 4 )',
        "overlap" : 'overlap = 0.2',
        "font_size" : 'font_size = 12',
        "dpi" : 'dpi = 64',
        "encoding" : 'encoding = "iso8859-15"' })
        

    def create(self, path, verbosity=None):
        if not self.check():
            return

        #temporary disable progress display of others
        self.progress_start = utils.progress_start
        self.progress_end = utils.progress_end
        self.progress_update = utils.progress_update

        def dumy(*args, **kwargs): pass
        utils.progress_start = dumy
        utils.progress_end = dumy
        utils.progress_update = dumy
        
        self._filter_observers()
        categories = self.observers.itervalues()
        prog_steps = sum(map(lambda v: len(v), categories)) + 3
        self.progress_start(_("generate HTML for %s")\
                            % self.__class__.__name__,
                            prog_steps, _("prepare"))
        try:
            self._save_create(path, verbosity)
        finally:
            self.progress_end()
            utils.progress_start = self.progress_start
            utils.progress_end = self.progress_end
            utils.progress_update = self.progress_update


    def _filter_observers(self):
        for k in self.observers.keys():
            #in olist are only observers of the same category
            olist = self.observers[k]
            if not hasattr(self, "generate_" + olist[0].__type_name__):
                olist = []
            else:
                olist = filter(lambda o: o.visible, olist)

            if not olist:
                del self.observers[k]
            else:
                self.observers[k] = olist


    def _save_create(self, path, verbosity=None):
        if verbosity is not None:
            self.verbosity = verbosity
            
        if self.verbosity:
            print "start generating..."

        progress = 0
        
        if self.clean_path:
            self.clean(path)

        self.copy_resources(path)
        links = {}
        pages = []


        old_size = font.fontManager.get_default_size()
        tools.set_default_size(self.font_size)
        try:
            for olist in self.observers.itervalues():
                #i olist are only observers of the same category
                generator = getattr(self, "generate_" + olist[0].__type_name__)
                
                for o in olist:
                    progress += 1
                    self.progress_update(progress,
                                         _("generate %s") % o.__name__)
                    link, output = generator(path, o)
                    pages += output
                    links[o.__name__] = link
        finally:
            tools.set_default_size(old_size)

        pages.append((self.frame(), "index.html"))

        if self.verbosity:
            print "write pages"

        progress += 1
        self.progress_update(progress,  _("write out html"))

        for t, n in pages:
            t.links = links
            of = file(os.path.join(path, n), "w")
            print >> of, t
            of.close()
            utils.do_yield()

        if self.verbosity:
            print "finished"


    def clean(self, path):
        if self.verbosity:
            print "clear the directory", path
        
        files = os.listdir(path)
        files = filter(lambda f: f.endswith(".html") \
                       or f.endswith(".png"), files)
        for f in files:
            utils.do_yield()
            fp = os.path.join(path, f)
            try:
                if self.verbosity >= 3: print "remove file", fp
                os.remove(fp)
            except:
                pass

        try:
            subdir = os.path.join(path, "resources")
            if self.verbosity >= 3: print "remove subdir", subdir
            shutil.rmtree(subdir, False)
        except:
            pass
        

    def frame(self):
        frame = self.template("mainframe.tmpl")
        frame.title = self.title
        frame.observers = self.observers
        frame.tile_size = self.tile_size
        frame.encoding = self.encoding
        frame.content = ""
        return frame


    def template(self, name):
        template = Generator.template(self, name)
        template.tile_size = self.tile_size
        return template
    

    def copy_resources(self, path):
        dst = os.path.join(path, "resources")
        try:
            os.mkdir(dst)
        except:
            pass
        
        for f in os.listdir(self.resource_path):
            sfp = os.path.join(self.resource_path, f)
            dfp = os.path.join(dst, f)
            try:
                shutil.copyfile(sfp, dfp)
            except:
                pass


    def encode(self, text):
        try:
            text = text.unicode(self.encoding)
        except AttributeError:
            pass
        
        if isinstance(text, unicode):
            return text.encode(self.encoding)

        return str(text)


    def generate_report(self, path, report):
        if self.verbosity:
            print "generate report '%s'" % report.__name__

        utils.do_yield()
        template = self.template("report.tmpl")
        template.report = report()
        template.Cell = faces.report.Cell
        template.encode = self.encode
                
        #print template
        frame = self.frame()
        frame.content = str(template)
        page_name = report.__name__ + ".html"
        return page_name, [(frame, page_name)]


    def generate_matplot_timechart(self, path, chart_class):
        if self.verbosity:
            print "generate chart '%s'" % chart_class.__name__

        pages = []
        first_page = None

        def_zoom_levels = self.zoom_levels
        zoom_levels = getattr(self, chart_class.__name__ + "_zoom_levels",
                              def_zoom_levels)

        printer = chart_class.printer()
        printer.type = "png"
        printer.dpi = self.dpi
        printer.unit = "pixel"
        
        for l, factor in enumerate(zoom_levels):
            #reset the limits
            printer.set_xlimits()
            printer.set_ylimits()
            printer.width = self.tile_size[0] * factor
            to_add = self.generate_chart_tiles(path, printer, l, zoom_levels)
            if len(to_add) == 1:
                first_page = to_add[0][1]
            pages += to_add
            
        return first_page or pages[0][1], pages



    def generate_matplot_pointchart(self, path, chart_class):
        """
        Zooms from a minimal font size thas displays the whole chart within
        the canvas size, to the default font size
        """

        if self.verbosity:
            print "generate chart '%s'" % chart_class.__name__

        pages = []
        first_page = None

        def_zoom_levels = self.zoom_levels
        zoom_levels = getattr(self, chart_class.__name__ + "_zoom_levels",
                              def_zoom_levels)

        printer = chart_class.printer()
        printer.type = "png"
        printer.dpi = self.dpi
        printer.unit = "pixel"
        printer.refresh()

        tw, th = self.tile_size
        vf = float(printer.height) / th
        hf = float(printer.width) / tw
        f = max(hf, vf)

        if f > 1.0:
            min_font = int(max(self.font_size / f, 3))

            if len(zoom_levels) == 1:
                zoom_levels = (zoom_levels[0], zoom_levels[0] + 1)

            m = float(self.font_size - min_font)\
                / (zoom_levels[-1] - zoom_levels[0])
            t = min_font - m * zoom_levels[0]


            #filter zoom levels that are to narrow
            zoom_levels = list(zoom_levels)
            i = len(zoom_levels) - 1
            last_size = zoom_levels[i] * m + t
            i -= 1
            while i >= 0:
                size = zoom_levels[i] * m + t
                if last_size - size < 2:
                    del zoom_levels[i]
                else:
                    last_size = size

                i -= 1
        else:
            zoom_levels = (1,)
            m = self.font_size
            t = 0

        #print "font factor", f, hf, vf, min_font
        
        for l, factor in enumerate(zoom_levels):
            #reset the limits
            printer.set_xlimits()
            printer.set_ylimits()
            printer.font_size = factor * m + t
            
            to_add = self.generate_chart_tiles(path, printer, l, zoom_levels)
            if len(to_add) == 1:
                first_page = to_add[0][1]
            pages += to_add
            
        return first_page or pages[0][1], pages



    def generate_chart_tiles(self, path, printer, level, zoom_levels):
        #get the original printer values
        printer.refresh()
        width = printer.width
        height = printer.height
        ml, mt, mr, mb = printer.get_margins()
        red_width = width - ml - mr
        red_height = height - mt - mb
        xmin, xmax = printer.get_xlimits()
        ymin, ymax = printer.get_ylimits()

        #calculate steps
        view_box = mtrans.lbwh_to_bbox(0, 0, red_width, red_height)
        data_box = mtrans.lbwh_to_bbox(xmin, ymin, xmax - xmin, ymax - ymin)
        transform = mtrans.get_bbox_transform(view_box, data_box)
        
        tw, th = self.tile_size
        xstep, ystep = self.tile_size
        if xstep < red_width: xstep *= (1 - self.overlap)
        if ystep < red_height: ystep *= (1 - self.overlap)

        cols = int(math.ceil((red_width) / xstep))
        rows = int(math.ceil((red_height) / ystep))

        #some preparing
        result = []
        if self.verbosity:
            print "generate %i x %i tiles for chart '%s' at zoom_level %i" % \
                  (cols, rows, printer._chart.__name__, level + 1)

        utils.do_yield()

        def cname(col, row, ext="html", zlevel=level):
            if col < 0 or col >= cols or row < 0 or row >= rows:
                return ""
            
            return printer._chart.__name__ \
                   + "%i_%i_%i." % (zlevel, col, row) + ext

        zoom_names = map(lambda l: cname(0, 0, zlevel=l[0]),
                         enumerate(zoom_levels))

        #start generating
        try:
            printer.width = tw
            printer.height = th
        except AttributeError:
            pass

        tw -= (ml + mr)
        th -= (mt + mb)

        x = 0
        _d = 0
        for c in range(cols):
            left, _d = transform.xy_tup((x, _d))
            right, _d = transform.xy_tup((x + tw, _d))
            printer.set_xlimits(left, right)
            x += xstep
            
            y = 0
            for r in range(rows):
                if printer.flipy():
                    r = rows - 1 - r
                
                _d, top = transform.xy_tup((_d, y))
                _d, bottom = transform.xy_tup((_d, y + th))
                printer.set_ylimits(top, bottom)
                y += ystep
                
                if self.verbosity > 1:
                    print "    tile (%i, %i)" % (c, r)

                image_name = cname(c, r, "png")
                printer.filename = os.path.join(path, image_name)
                printer.save()
                chart = printer._chart_instance
                template = self.template("chart.tmpl")
                template.image_name = image_name
                template.upper_tile = cname(c, r - 1)
                template.lower_tile = cname(c, r + 1)
                template.left_tile = cname(c - 1, r)
                template.right_tile = cname(c + 1, r)
                template.level = level
                template.zoom_names = zoom_names
                template.tip_infos = self.create_tip_infos(chart)
                frame = self.frame()
                frame.content = str(template)
                result.append((frame, cname(c, r)))
                utils.do_yield()

        return result


    def create_tip_infos(self, chart):
        yoffset = chart._bbox.ymax()
        if chart._top_margin is not None: yoffset += chart._top_margin.get()
            
        def make_info(widget):
            bbox = mtrans.transform_bbox(chart._trans_data, widget.bbox)
            l = int(bbox.xmin())
            r = int(bbox.xmax())
            t = int(bbox.ymax())
            b = int(bbox.ymin())
            t = yoffset - t
            b = yoffset - b

            lines = chart.get_tip(widget)
            if lines:
                template = self.template("tip_window.tmpl")
                lines = map(lambda l: (self.encode(l[0]), self.encode(l[1])), lines)
                template.lines = lines
                text = str(template)
            else:
                text = ""

            return l, t, r, b, text

        def is_visible(widget):
            return widget.overlaps(chart._view_lim)

        visible_widget = filter(is_visible, chart._widgets)
        infos = map(make_info, visible_widget)
        return filter(lambda i: i[4], infos)
            

if faces.gui_controller and _cheetah_is_installed:
    import wx
    import metapie.dbtransient as db
    import faces.gui.editor.editorlib as editorlib

    class HTMLGeneratorModel(db.Model):
        template_path = db.Text(os.path.join(_html_path, "standard"))
        resource_path = db.Text(os.path.join(_html_path, "standard",
                                             "resources"))
        output_dir = db.Text()
        title = db.Text()
        tile_width = db.Int(800)
        tile_height = db.Int(600)
        verbosity = db.Int(2)
        clean_path = db.Boolean(True)
        zoom_levels = db.Text("1, 2")
        overlap = db.Float(0.2)
        font_size = db.Int(12)
        dpi = db.Int(64)
        encoding = db.Text("iso8859-15")
        observers = db.MultiEnumerate({})

        def __init__(self, editor):
            super(HTMLGeneratorModel, self).__init__()
            self.encoding = editor.model.get_encoding()
            module = editor.get_module()
            self.title = os.path.splitext(os.path.basename(module.__file__))[0]
            observers = dict([ (o, o.__name__) for o in all(module)()])
            self.__class__.__attributes_map__["observers"].choices = observers
            self.observers = observers.keys()


        def check_constraints(self):
            error = db.ConstraintError()
            if not self.output_dir:
                error.message["output_dir"] = _("Output Directory must be a valid directory")

            try:
                map(int, self.zoom_levels.split(","))
            except ValueError:
                error.message["zoom_levels"] = _("Zoom levels must be a sequence "\
                                                 "of comma seperated integers")


            if error.message:
                raise error

        
        def realize(self):
            class TmpGen(HTMLGenerator):
                title = self.title
                template_path = self.template_path
                resource_path = self.resource_path
                tile_size = (self.tile_width, self.tile_height)
                verbosity = self.verbosity
                clean_path = self.clean_path
                zoom_levels = map(int, self.zoom_levels.split(","))
                overlap = self.overlap
                font_size = self.font_size
                dpi = self.dpi
                encoding = self.encoding
                observers = self.observers

            TmpGen()._execute(self.output_dir)


    class HTMLGeneratorView(editorlib.MainView):
        __model__ = HTMLGeneratorModel
        __view_name__ = "default"
        format = _("""
[Title: ]          |title>
[Encoding:]        |encoding
[Output Directory:]|output_dir(ChooseDir)>
                   |clean_path[clean before generate]
-->                 
[Template Path: ]  |template_path(OpenFile)>
[Resource Path: ]  |resource_path(OpenFile)>
[Verbosity: ]      |verbosity
-->
[Tile Size: ]      |tile_width|[x]|tile_height
[Zoom Levels: ]    |zoom_levels
[Overlap: ]        |overlap
[Font Size:]       |font_size
-->
[Observers:]       |observers
(buttons)>
""")

        format_buttons = """
btn_ok{r}|btn_cancel{r}
"""

        def prepare(self):
            self.grow_col(-1)
            self.grow_row(-2)
            self.buttons.grow_col(0)
            self.template_path.set_width("X" * 40)
            self.observers.set_height(10)


    def create_generate_html(editor):
        def generate_html():
            if faces.gui_controller().is_processing(): return

            dlg = editorlib.PatchedDialog(faces.gui_controller().frame,
                                          -1, _("Generate HTML"),
                    style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

            dlg.SetClientSize((10, 10))
            model = HTMLGeneratorModel(editor)
            view = model.constitute()(dlg)
            view.layout()
            dlg.simulate_modal(editor)

        return generate_html
        

