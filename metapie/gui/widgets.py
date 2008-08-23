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
import wx.grid as wxg
import wx.lib.masked as masked
import wx.lib.intctrl as intctrl
import wx.lib.colourselect as colourselect
import controller
import wxcontrols
import wxcontrols.expander as expander
import datetime
import locale
import sys
import metapie.dblayout as dblayout
import metapie.events as events
import metapie.tools as tools
import tools as gtools
import os.path
import bisect
import inspect

_ = tools.get_gettext()


class IView(object):
    def inspect(self, imodel, attrib):
        """
        Specifies which model value will be inspected
        update the view state
        """
        pass
    

    def end_inspect(self):
        """
        End value inspection, saves the state if it was changed
        """
        pass
    

    def update_errors(self):
        """
        Update error controls
        """
        pass


_widget_registry = {}


def _get_widget(itype, parent, name):
    for cls in inspect.getmro(itype.__class__):
        ntype = cls.__name__
        widget = _widget_registry.get((ntype, name))
        if widget: break
        widget = _widget_registry.get((ntype, "default"))
        if widget: break
    else:
        raise ValueError("No widget registered for type '%s'" \
                         % itype.__class__.__name__)
    
    if getattr(itype, "none", False) \
       and not getattr(widget, "__none_state__", False):
        container = NoneWidget(itype, parent, name, widget)
        return container
    else:
        return widget(itype, parent, name)


class _MetaWidget(type):
    def __init__(cls, name, bases, dict_):
        super(_MetaWidget, cls).__init__(name, bases, dict_)
        if cls.__type__:
            cls.__type__._widget_ = _get_widget
            try:
                type_name = dict_["__view_name__"]
            except KeyError:
                type_name = name

            _widget_registry[(cls.__type__.__name__, type_name)] = cls


class Widget(IView):
    __metaclass__ = _MetaWidget
    __type__ = None

    def end_inspect(self):
        try:
            self.imodel
        except AttributeError:
            pass
        else:
            self.imodel.detach(self.update)
            del self.imodel
            del self.attrib


class AtomWidget(Widget):
    def set_width(self, width_string):
        w, h = self.GetTextExtent(width_string + "X")
        w1, h = self.GetClientSize()
        self.SetClientSize((w, h))
        #w, h = self.GetSize()
        self.SetMinSize((w, h))
        self.CacheBestSize((w, h))


    def set_height(self, line_count):
        w, h = self.GetTextExtent('X')
        h *= line_count
        w, h1 = self.GetClientSize()
        self.SetClientSize((w, h))
        w, h = self.GetSize()
        self.SetMinSize((w, h))
        self.CacheBestSize((w, h))
        

    def inspect(self, imodel, attrib):
        self.end_inspect()
        self.imodel = imodel
        self.attrib = attrib
        imodel.attach(self.update, attrib)
        self.update(attrib)


    __ignore_update = False #just to be shure not to cause a recursion
    def update(self, name):
        if self.__ignore_update: return
        new = getattr(self.imodel, self.attrib)
        self.SetValue(new)

       
    def save(self):
        self.__ignore_update = True
        setattr(self.imodel, self.attrib, self.GetValue())
        #to considert value changes while setting
        self.SetValue(getattr(self.imodel, self.attrib))
        self.__ignore_update = False


           
class NoneWidget(wx.PyPanel, Widget):
    """
    A container for widgets that may be none
    """

    class ModelProxy(object):
        #simulats a model

        _imodel_ = None

        def __init__(self):
            self.__dict__["_ModelProxy__subject"] = events.Subject()


        def _set_imodel(self, imodel):
            self.__dict__["_imodel_"] = imodel
        

        def attach(self, *args, **kwargs):
            self.__subject.attach(*args, **kwargs)


        def fire(self, *args, **kwargs):
            self.__subject.fire(*args, **kwargs)
                                  

        def detach(self, *args, **kwargs):
            self.__subject.attach(*args, **kwargs)

            
        def __getattr__(self, name):
            return getattr(self._imodel_, name)


        def __setattr__(self, name, value):
            setattr(self._imodel_, name, value)

    
    def __init__(self, itype, parent, name, widget):
        wx.PyPanel.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL)
        Widget.__init__(self)

        bmp = controller.ResourceManager.load_bitmap("enabled.gif")#clear_right22.gif")
        self.imodel_proxy = self.ModelProxy()
        self.defvalue = itype.default()
        self.is_none = False
        self.check = wx.BitmapButton(self, -1, bmp)
        self.iwidget = widget(itype, self, name)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.check, 0, wx.EXPAND)
        sizer.Add(self.iwidget, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetMinSize(sizer.GetMinSize())
        self.CacheBestSize(sizer.GetMinSize())
        self.check.Bind(wx.EVT_BUTTON, self._on_button)


    def inspect(self, imodel, attrib):
        self.end_inspect()
        self.imodel_proxy._set_imodel(imodel)
        self.imodel = imodel
        self.attrib = attrib
        self.imodel.attach(self.update, attrib)
        self.iwidget.inspect(self.imodel_proxy, attrib)
        self.update(attrib)


    def end_inspect(self):
        try:
            self.imodel.detach(self.update)
        except AttributeError:
            pass
        else:
            self.imodel.detach(self.update)
            self.imodel_proxy._set_imodel(None)
            del self.imodel
            del self.attrib
        

    __ignore_update = False
    def update(self, name):
        value = getattr(self.imodel, self.attrib)
        if value is not None: self.defvalue = value
        if self.__ignore_update: return
        self.set_none(value)
        self.imodel_proxy.fire(self.attrib, self.attrib)
        

    def _on_button(self, event):
        if self.set_none(self.is_none or None):
            self.__ignore_update = True
            if self.is_none:
                setattr(self.imodel, self.attrib, None)
            else:
                setattr(self.imodel, self.attrib, self.defvalue)
                self.imodel_proxy.fire(self.attrib, self.attrib)
                
            self.__ignore_update = False


    def layout(self):
        try:
            self.Layout()
            self.GetParent().layout()
        except AttributeError:
            pass


    def set_none(self, value):
        old_none = self.is_none
        self.is_none = value is None
        if old_none == self.is_none: return False

        load_bitmap = controller.ResourceManager.load_bitmap
        if self.is_none:
            bmp = load_bitmap("disabled.gif")#"edit22.gif")
        else:
            bmp = load_bitmap("enabled.gif")#"clear_right22.gif")

        self.check.SetBitmapLabel(bmp)
        for c in self.GetChildren():
            if c is not self.check:
                c.Enable(not self.is_none)

        return True


    def Enable(self, flag):
        wx.PyPanel.Enable(self, flag)
        enable = flag and not self.is_none
        for c in self.GetChildren():
            c.Enable(enable)

        self.check.Enable(flag)


    def __getattr__(self, name):
        if name in ("imodel", "attrib"): raise AttributeError()
        return getattr(self.iwidget, name)


class BrowseWidget(wx.PyPanel, IView):
    """
    A container for widgets that have a browse button
    """
    __metaclass__ = _MetaWidget
    __type__ = None

    def __init__(self, itype, parent, name, widget):
        wx.PyPanel.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL)
        Widget.__init__(self)

        self.iwidget = widget(itype, self, name)
        self.browse = self.create_browse_button()
        #self.browse.SetMinSize((-1, self.iwidget.GetBestSize().height))

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.iwidget, 1, wx.EXPAND)
        sizer.Add(self.browse)
        
        self.SetSizer(sizer)
        self.browse.Bind(wx.EVT_BUTTON, self._on_button)


    def create_browse_button(self):
        return wx.Button(self, -1, _("Browse"))


    def adjust_size(self):
        sizer = self.GetSizer()
        self.SetMinSize(sizer.GetMinSize())
        self.CacheBestSize(sizer.GetMinSize())


    def _on_button(self, event):
        pass


    def inspect(self, imodel, attrib):
        self.iwidget.inspect(imodel, attrib)


    def end_inspect(self):
        self.iwidget.end_inspect()
       

    def Enable(self, flag):
        wx.PyPanel.Enable(self, flag)
        for c in self.GetChildren(): c.Enable(flag)


    def set_width(self, width_string):
        self.iwidget.set_width(width_string)
        self.adjust_size()


    def set_height(self, line_count):
        self.iwidget.set_height(line_count)
        self.adjust_size()


    def __getattr__(self, name):
        return getattr(self.iwidget, name)


class KillFocusNotifier(AtomWidget):
    def __init__(self, setup_events=True):
        AtomWidget.__init__(self)
        self.changed_state = False
        if setup_events:
            gtools.EVT_CHILD_KILL_FOCUS(self, self._on_kill_focus)
        

    def change_state(self, event):
        self.changed_state = True
        event.Skip()


    def update(self, name):
        AtomWidget.update(self, name)
        self.changed_state = False
                    

    def _on_kill_focus(self, event):
        event.Skip()
        if self.changed_state:
            self.save()
            self.changed_state = False


    def inspect(self, imodel, attribute):
        AtomWidget.inspect(self, imodel, attribute)
        self.changed_state = False
        

    def end_inspect(self):
        if self.changed_state:
            self.changed_state = False
            try:
                self.imodel
            except AttributeError: pass
            else: self.save()
        
        AtomWidget.end_inspect(self)
        

class Changeling(wx.PyPanel, Widget):
    """
    A widget that can edit various text types
    """
    
    __type__ = dblayout.Text

    def __init__(self, itype, parent, name):
        wx.PyPanel.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL)
        Widget.__init__(self)

        self.itype = itype
        self.inside = None
        self.last_name = None
        self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        self.change("Color")
        

    def change(self, name):
        if name == self.last_name: return
        
        old_inside = self.inside
        self.last_name = name
        self.inside = self.itype.create_widget(self, name)
        self.inspect = self.inside.inspect
        self.end_inspect = self.inside.end_inspect
        sizer = self.GetSizer()
        sizer.Add(self.inside, 1, wx.EXPAND)
        
        if old_inside:
            old_inside.end_inspect()
            sizer.Remove(old_inside)

        self.Layout()


    def __getattr__(self, name):
        return getattr(self.inside, name)


    def DoGetBestSize(self):
        return self.inside.GetBestSize()



class Text(wx.TextCtrl, KillFocusNotifier):
    __type__ = dblayout.Text
    __view_name__ = "default"
    
    def __init__(self, itype, parent, name):
        style = 0
        if itype.is_password: style |= wx.TE_PASSWORD
        if itype.multi_line: style |= wx.TE_MULTILINE
        wx.TextCtrl.__init__(self, parent, -1, style=style)
        KillFocusNotifier.__init__(self)
        self.Bind(wx.EVT_TEXT, self.change_state)
        self.set_width(itype.width_format())
       

    def SetValue(self, value):
        if value is None: return
        wx.TextCtrl.SetValue(self, unicode(value))
        

class Static(wx.StaticText, Widget):
    __type__ = dblayout.Text
    __none_state__ = True


    def __init__(self, itype, parent, name):
        wx.StaticText.__init__(self, parent, -1)
        Widget.__init__(self)
        

    def inspect(self, imodel, attrib):
        self.end_inspect()
        self.imodel = imodel
        self.attrib = attrib
        imodel.attach(self.update, attrib)
        self.update(attrib)


    def update(self, name):
        new = getattr(self.imodel, self.attrib)
        self.SetLabel(new)


class Color(BrowseWidget):
    __type__ = dblayout.Text
    
    def __init__(self, itype, parent, name):
        BrowseWidget.__init__(self, itype, parent, name, Text)
        self.iwidget.set_width("#FFFFFF")
        self.adjust_size()


    def create_browse_button(self):
        return colourselect.ColourSelect(self, -1)


    def update(self, name):
        text = getattr(self.imodel, name)

        try:
            if text[0] == '#':
                #windows can not interprete color string :-(
                r = int(text[1:3], 16)
                g = int(text[3:5], 16)
                b = int(text[5:7], 16)
                color = wx.Colour(r, g, b)
            else:
                color = wx.NamedColour(text)
        except IndexError:
            color = wx.NamedColour("white")
            setattr(self.imodel, name, "white")
                    
        if not color.Ok():
            color = wx.NamedColour("white")
            setattr(self.imodel, name, "white")

        self.browse.SetValue(color)


    def inspect(self, imodel, attrib):
        self.imodel = imodel
        self.imodel.attach(self.update, attrib)
        self.update(attrib)
        self.iwidget.inspect(imodel, attrib)


    def end_inspect(self):
        self.iwidget.end_inspect()
        try:
            self.imodel
        except AttributeError:
            pass
        else:
            self.imodel.detach(self.update)
            del self.imodel


    def _on_button(self, event):
        data = wx.ColourData()
        data.SetColour(wx.NamedColour(self.iwidget.GetValue()))
        dlg = wx.ColourDialog(wx.GetApp().GetTopWindow(), data)
        if dlg.ShowModal() == wx.ID_OK:
            colour = "#%02X%02X%02X" % dlg.GetColourData().GetColour().Get()
            self.iwidget.SetValue(colour)
            self.iwidget.save()


class SaveFile(BrowseWidget):
    __type__ = dblayout.Text
    option = wx.SAVE
    label = _("Save")
    
    def __init__(self, itype, parent, name):
        BrowseWidget.__init__(self, itype, parent, name, Text)
        self.browse.SetLabel(self.label)
        self.iwidget.set_width('X' * 15)
        self.filter = "(*)|*"
        self.adjust_size()


    def set_filter(self, filter):
        self.filter = filter


    def _on_button(self, event):
        path = self.iwidget.GetValue()
        dname, fname = os.path.split(path)
        
        dlg = wx.FileDialog(wx.GetApp().GetTopWindow(), _("Choose a filename"),
                            dname, fname, self.filter, self.option)
        if dlg.ShowModal() == wx.ID_OK:
            self.iwidget.SetValue(dlg.GetPath())
            self.iwidget.save()


class OpenFile(SaveFile):
    option = wx.OPEN
    label = _("&Browse")


class ChooseDir(BrowseWidget):
    __type__ = dblayout.Text
    option = wx.SAVE
    label = _("Choose")
    
    def __init__(self, itype, parent, name):
        BrowseWidget.__init__(self, itype, parent, name, Text)
        self.browse.SetLabel(self.label)
        self.iwidget.set_width('X' * 15)
        self.filter = "(*)|*"
        self.adjust_size()


    def set_filter(self, filter):
        self.filter = filter


    def _on_button(self, event):
        path = self.iwidget.GetValue()
        dlg = wx.DirDialog(wx.GetApp().GetTopWindow(), _("Choose Directory"), path)
        if dlg.ShowModal() == wx.ID_OK:
            self.iwidget.SetValue(dlg.GetPath())
            self.iwidget.save()


class Int(intctrl.IntCtrl, KillFocusNotifier):
    __type__ = dblayout.Int
    __view_name__ = "default"
    
    def __init__(self, itype, parent, name):
        intctrl.IntCtrl.__init__(self, parent, -1, allow_none=itype.none)
        KillFocusNotifier.__init__(self)
        intctrl.EVT_INT(self, -1, self.change_state)



class PatchedNumCtrl(masked.NumCtrl):
    def SetValue(self, value):
        try:
            masked.NumCtrl.SetValue(self, value)
        except ValueError:
            # filter out an annoying and wrong error message
            pass


    def _OnChar(self, event):
        try:
            masked.NumCtrl._OnChar(self, event)
        except IndexError:
            # filter out an annoying and wrong error message
            pass
        
        

class Float(PatchedNumCtrl, KillFocusNotifier):
    __type__ = dblayout.Float
    __view_name__ = "default"
    
    def __init__(self, itype, parent, name):
        encoding = locale.getlocale()[1] or "ascii"
        
        decimal = locale.localeconv()["decimal_point"].decode(encoding)
        group = locale.localeconv()["thousands_sep"].decode(encoding)
        width, precision = self.get_width_precision(itype)
        
        PatchedNumCtrl.__init__(self, parent, -1,
                                integerWidth=width - precision,
                                fractionWidth=precision,
                                groupDigits = False,
                                groupChar=group or '#',
                                allowNone=itype.none,
                                signedForegroundColour="Black",
                                useFixedWidthFont=False,
                                decimalChar=decimal)

        KillFocusNotifier.__init__(self)
        #self.Bind(masked.EVT_NUM, self.change_state) does not work under gtk in 2.8.3
        self.Bind(wx.EVT_CHAR, self.change_state)


    def get_width_precision(self, itype):
        return itype.width, itype.precision


    def SetValue(self, value):
        try:
            masked.NumCtrl.SetValue(self, value)
        except ValueError:
            # filter out an annoying and wrong error message
            pass


class Money(PatchedNumCtrl, KillFocusNotifier):
    __type__ = dblayout.Money
    __view_name__ = "default"
    
    def __init__(self, itype, parent, name):
        encoding = locale.getlocale()[1] or "ascii"
        decimal = locale.localeconv()["mon_decimal_point"].decode(encoding)
        group = locale.localeconv()["mon_thousands_sep"].decode(encoding)
        frac = locale.localeconv()["frac_digits"]
        
        PatchedNumCtrl.__init__(self, parent, -1,
                                fractionWidth=frac,
                                groupDigits=True,
                                allowNone=itype.none,
                                signedForegroundColour="Black",
                                useFixedWidthFont=False,
                                decimalChar=decimal,
                                groupChar=group)
        
        KillFocusNotifier.__init__(self)
        #self.Bind(masked.EVT_NUM, self.change_state) does not work under gtk in 2.8.3
        self.Bind(wx.EVT_CHAR, self.change_state)

    

class Boolean(wx.CheckBox, AtomWidget):
    __type__ = dblayout.Boolean
    __view_name__ = "default"
    __none_state__ = True
    
    def __init__(self, itype, parent, name):
        wx.CheckBox.__init__(self, parent, -1, "",
                             style=(itype.none \
                                    and (wx.CHK_3STATE \
                                         | wx.CHK_ALLOW_3RD_STATE_FOR_USER)\
                                    or wx.CHK_2STATE))
        Widget.__init__(self)
        self.Bind(wx.EVT_CHECKBOX, lambda e: self.save())
        self.name = name


    def GetValue(self):
        if self.Is3State():
            result = self.Get3StateValue()
            return { wx.CHK_UNCHECKED : False,
                     wx.CHK_CHECKED  : True,
                     wx.CHK_UNDETERMINED : None }[result]

        return wx.CheckBox.GetValue(self)


    def SetValue(self, value):
        if self.Is3State():
            value = { False : wx.CHK_UNCHECKED,
                      True : wx.CHK_CHECKED,
                      None : wx.CHK_UNDETERMINED }[value]
            self.Set3StateValue(value)
        else:
            wx.CheckBox.SetValue(self, value)




class Enumerate(wx.Choice, AtomWidget):
    __type__ = dblayout.Enumerate
    __view_name__ = "default"

    def __init__(self, itype, parent, name):
        self.key_values = self.get_choices(itype)
        encoding = locale.getlocale()[1] or "ascii"

        def change_pair(kv):
            key, value = kv
            if not isinstance(value, unicode):
                value = unicode(value, encoding)
            return value, key
        
        self.value_keys = dict(map(change_pair, self.key_values.iteritems()))
        values = self.value_keys.keys()
        values.sort()

        wx.Choice.__init__(self, parent, -1, choices=values)
        AtomWidget.__init__(self)
        self.Bind(wx.EVT_CHOICE, lambda e: self.save())
        if self.key_values:
            self.SetValue(self.key_values.keys()[0])
        else:
            self.Enable(False)


    def get_choices(self, itype):
        return itype.choices


    def SetValue(self, value):
        try:
            self.SetStringSelection(self.key_values[value])
        except KeyError:
            pass


    def GetValue(self):
        try:
            return self.value_keys[self.GetStringSelection()]
        except KeyError:
            return self.value_keys[self.GetString(0)]


class MultiEnumerate(wx.CheckListBox, KillFocusNotifier):
    __type__ = dblayout.MultiEnumerate
    __view_name__ = "default"

    def __init__(self, itype, parent, name):
        self.key_values = self.get_choices(itype)
        encoding = locale.getlocale()[1] or "ascii"

        def change_pair(kv):
            key, value = kv
            if not isinstance(value, unicode):
                value = unicode(value, encoding)
            return value, key
        
        self.value_keys = dict(map(change_pair, self.key_values.iteritems()))
        values = self.value_keys.keys()
        values.sort()

        wx.CheckListBox.__init__(self, parent, -1, choices=values)
        KillFocusNotifier.__init__(self)

        self.Bind(wx.EVT_CHECKLISTBOX, self.change_state)
        if not self.key_values:
            self.Enable(False)


    def get_choices(self, itype):
        return itype.choices


    def SetValue(self, value):
        for i in range(self.GetCount()):
            self.Check(i, self.value_keys[self.GetString(i)] in value)


    def GetValue(self):
        value = [ self.value_keys[self.GetString(i)]
                  for i in range(self.GetCount())
                  if self.IsChecked(i) ]
            
        return tuple(value)



class Date(wxcontrols.DatePickerCtrl, AtomWidget):
    __type__ = dblayout.Date
    __view_name__ = "default"
    
    def __init__(self, itype, parent, name):
        wxcontrols.DatePickerCtrl.__init__(self, parent,
                                           -1, style=wx.DP_DROPDOWN)
        AtomWidget.__init__(self)
        self.Bind(wx.EVT_DATE_CHANGED, lambda e: self.save())


    def SetValue(self, value):
        if value is None: value = datetime.date.today()
        date = wx.DateTimeFromDMY(value.day, value.month - 1, value.year)
        wxcontrols.DatePickerCtrl.SetValue(self, date)


    def GetValue(self):
        date = wxcontrols.DatePickerCtrl.GetValue(self)
        return datetime.date(date.GetYear(), date.GetMonth() + 1, date.GetDay())



class PatchedTimeCtrl(masked.TimeCtrl):
    def SetValue(self, value):
        #patch  for gtk in 2.8.4
        self.GetParent().changed_state = True
        masked.TimeCtrl.SetValue(self, value)



class Time(wx.PyPanel, KillFocusNotifier):
    __type__ = dblayout.Time
    __view_name__ = "default"
    
    def __init__(self, itype, parent, name):
        wx.PyPanel.__init__(self, parent, -1)
        self.spin = wx.SpinButton(self, style=wx.SP_VERTICAL)
        self.time = PatchedTimeCtrl(self, -1, format="24"+ itype.format,
                                    spinButton=self.spin,
                                    useFixedWidthFont=False,
                                    style=0)
        self.spin.SetSize((-1, self.time.GetSize().height))
        self.time.SetMinSize(self.time.GetSize())
        self.SetMinSize(self.GetBestSize())
        KillFocusNotifier.__init__(self, False)
        #self.time.Bind(masked.EVT_TIMEUPDATE, self.change_state) does not work under gtk in 2.8.4
        self.time.Bind(wx.EVT_CHAR, self.change_state)
        self.time.Bind(wx.EVT_KILL_FOCUS, self._on_kill_focus)
        self.Bind(wx.EVT_SIZE, self._on_size)


    def SetValue(self, value):
        if value is None: return
        time = wx.DateTimeFromHMS(value.hour, value.minute, value.second)
        self.time.SetValue(time)


    def GetValue(self):
        time = self.time.GetValue(as_wxDateTime=True)
        return datetime.time(time.GetHour(), time.GetMinute(), time.GetSecond())


    def _on_size(self, event):
        w, h = self.GetClientSize()
        sw = self.spin.GetSize().width
        self.time.SetDimensions(0, 0, w - sw, h)
        self.spin.SetDimensions(w - sw, 0, sw, h)


    def DoGetBestSize(self):
        tw, th = self.time.GetMinSize()
        sw, sh = self.spin.GetSize()
        return tw + sw, max(th, sh)


class DateTime(wx.PyPanel, IView):
    __metaclass__ = _MetaWidget
    __type__ = dblayout.DateTime
    __view_name__ = "default"
    gap = 5


    class DatePart(Date):
        __type__ = None
        
        def GetValue(self):
            value = getattr(self.imodel, self.attrib)
            if value is None: value = datetime.datetime.now()
            date = wxcontrols.DatePickerCtrl.GetValue(self)
            return value.replace(year=date.GetYear(),
                                 month=date.GetMonth() + 1,
                                 day=date.GetDay())


    class TimePart(Time):
        __type__ = None
        
        def GetValue(self):
            value = getattr(self.imodel, self.attrib)
            if value is None: value = datetime.datetime.now()
            time = self.time.GetValue(as_wxDateTime=True)
            return value.replace(hour=time.GetHour(),
                                 minute=time.GetMinute(),
                                 second=time.GetSecond())

    
    def __init__(self, itype, parent, name):
        wx.PyPanel.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL)
        IView.__init__(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.date = self.DatePart(itype, self, name)
        self.time = self.TimePart(itype, self, name)
        try:
            self.is_open = self.date.is_open
        except AttributeError: pass
        sizer.Add(self.date, self.date.GetMinSize().width, wx.EXPAND)
        sizer.Add((self.gap, 0))
        sizer.Add(self.time, self.time.GetMinSize().width, 0)
        self.SetSizer(sizer)
        self.SetMinSize(sizer.GetMinSize())
        self.CacheBestSize(sizer.GetMinSize())


    def is_open(self):
        #dirty hack for grid bugs. See grid.py PatchEvtHandler::_on_kill_focus
        return False


    def inspect(self, imodel, attrib):
        self.date.inspect(imodel, attrib)
        self.time.inspect(imodel, attrib)


    def end_inspect(self):
        self.date.end_inspect()
        self.time.end_inspect()


class AutoCompleter(expander.Expander, KillFocusNotifier):
    __type__ = dblayout.Text

    def __init__(self, itype, parent, name):
        expander.Expander.__init__(self, parent, -1)
        KillFocusNotifier.__init__(self)
        self.textCtrl.Bind(wx.EVT_CHAR, self._on_complete)
        self.textCtrl.Bind(wx.EVT_TEXT, self.change_state)

    def _prepare_text(self, value):
        self.textCtrl = wx.TextCtrl(self, -1, value, pos=(0,0))
        self.textCtrl.Bind(wx.EVT_KEY_DOWN, self._on_key_down)


    def create_content(self, parent):
        return wx.TextCtrl(parent, -1)


    def make_completion(self, value):
        return ""
       

    def _on_complete(self, event):
        event.Skip()
        char = unichr(event.GetUnicodeKey())
        if char.isspace() or char.isalnum():
            wx.CallAfter(self._start_completion)


    def _start_completion(self):
        pos = self.textCtrl.GetInsertionPoint()
        end = self.textCtrl.GetLastPosition()
        if pos == end: self.make_completion(self.GetValue())


    def complete(self, completion):
        pos = self.textCtrl.GetInsertionPoint()
        end = self.textCtrl.GetLastPosition()
        self.textCtrl.Replace(pos, end, completion[pos:])
        end = self.textCtrl.GetLastPosition()
        self.textCtrl.SetSelection(end, pos)


    def set_width(self, width_string):
        w, h = self.textCtrl.GetTextExtent(width_string + "X")
        w1, h = self.textCtrl.GetBestSize()
        self.textCtrl.SetClientSize((w, h))
        self.textCtrl.SetMinSize((w, h))
        self.textCtrl.CacheBestSize((w, h))
        self.SetSize(self.GetBestSize())



if wx.Platform == '__WXGTK__':
    class Combo(AutoCompleter):
        __type__ = dblayout.Text
        visible_rows = 10
        max_height = 500
        add_new = False

        def create_content(self, parent):
            self.lbox = wx.ListCtrl(parent, -1,
                                    style=wx.LC_REPORT\
                                    |wx.LC_NO_HEADER
                                    |wx.LC_SINGLE_SEL)

            self.lbox.InsertColumn(0, "")

            self.GetCount = self.lbox.GetItemCount
            self.Clear = self.lbox.DeleteAllItems
            self.Delete = self.lbox.DeleteItem

            self.lbox.Bind(wx.EVT_MOUSE_EVENTS, self._on_mouse_events)
            self.lbox.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_activated)
            self.lbox.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_changed)
            self.textCtrl.Bind(wx.EVT_CHAR, self._on_char)
            return self.lbox


        def Append(self, text):
            self.lbox.InsertStringItem(sys.maxint, text)

            if self.lbox.GetItemCount() == self.visible_rows:
                self.max_height = self.lbox_view_rect().height


        def SetValue(self, value):
            AutoCompleter.SetValue(self, unicode(value))
            if self.add_new and not self.contains(value):
                self.Append(value)


        def contains(self, text):
            return self.lbox.FindItem(-1, text) >= 0


        def remove(self, text):
            index = self.lbox.FindItem(-1, text)
            if index >= 0:
                self.DeleteItem(index)


        def _on_char(self, event):
            if self.popup.IsShown():
                main_window = self.lbox.GetMainWindow()
                code = event.GetKeyCode()
                if code in (wx.WXK_UP, wx.WXK_DOWN):
                    event.SetEventObject(main_window)
                    main_window.ProcessEvent(event)
                    return

                if code in (wx.WXK_HOME, wx.WXK_END) and event.ControlDown():
                    event.SetEventObject(main_window)
                    main_window.ProcessEvent(event)
                    return

            event.Skip()


        __send_mouse_event = False
        def _on_mouse_events(self, event):
            if self.__send_mouse_event:
                event.Skip()
                return

            self.__send_mouse_event = True
            main_window = self.lbox.GetMainWindow()
            event.SetEventObject(main_window)
            main_window.ProcessEvent(event)
            self.__send_mouse_event = False
            

        def _on_activated(self, event):
            self.SetValue(event.GetText())
            self.unpop()
            self.save()


        def _on_changed(self, event):
            if not self.__item_selected:
                self.SetValue(event.GetText())


        def lbox_view_rect(self):
            # an implementation of the generic listctrl view rect

            x_max = y_max = 0
            item_rect = self.lbox.GetItemRect
            for i in range(self.GetCount()):
                rect = item_rect(i)
                x_max = max(x_max, rect.GetRight())
                y_max = max(y_max, rect.GetBottom())
            
            x_max += 4
            y_max += 4

            w, h = self.lbox.GetMainWindow().GetClientSize()
            if x_max > w:
                y_max += wx.SystemSettings_GetMetric(wx.SYS_HSCROLL_Y)

            if y_max > h:
                x_max += wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X)

            return wx.Rect(0, 0, x_max, y_max)


        def before_display(self):
            lbox = self.lbox
            lbox.SetColumnWidth(0, self.textCtrl.GetSize().width)
            lbox.Refresh()

            rect = self.lbox_view_rect()
            height = min(rect.height + rect.top, self.max_height)
            self.lbox.CacheBestSize((rect.width + rect.left, height))
            self.popup.adjust_size()

            self.select_item()
            wx.CallAfter(self.textCtrl.SetFocus)


        def change_state(self, event):
            AutoCompleter.change_state(self, event)
            if self.popup.IsShown(): self.select_item()


        __item_selected = False
        def select_item(self):
            self.__item_selected = True

            value = self.GetValue()
            item = self.lbox.FindItem(-1, value)
            if item >= 0:
                self.lbox.Focus(item)
                self.lbox.Select(item)

            self.__item_selected = False


        def make_completion(self, value):
            get_string = self.lbox.GetItemText
            for l in range(self.GetCount()):
                s = get_string(l)
                if s.startswith(value):
                    self.complete(s)
                    break


else:
    class Combo(wx.ComboBox, KillFocusNotifier):
        __type__ = dblayout.Text
        add_new = False

        def __init__(self, itype, parent, name):
            wx.ComboBox.__init__(self, parent, -1, style=wx.CB_DROPDOWN)
            KillFocusNotifier.__init__(self)
            self.Bind(wx.EVT_TEXT, self.change_state)
            self.set_width(itype.width_format())
            

        def SetValue(self, value):
            if value is None: return
            if self.add_new and not self.contains(value):
                self.Append(value)

            wx.CallAfter(wx.ComboBox.SetValue, self, unicode(value))


        def contains(self, text):
            return self.FindString(text) != wx.NOT_FOUND


        def remove(self, text):
            index = self.FindString(text)
            if index != wx.NOT_FOUND:
                self.Delete(index)



class TreeAutoCompleter(AutoCompleter):
    __view_name__ = "auto_tree"
    visible_rows = 10
    separator = "."

    
    def create_content(self, parent):
        self.tree = wx.TreeCtrl(parent, -1,
                                style=wx.TR_HIDE_ROOT|\
                                wx.TR_LINES_AT_ROOT|\
                                wx.TR_HAS_BUTTONS)

        self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self._on_activated)
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self._on_changed)
        self.textCtrl.Bind(wx.EVT_CHAR, self._on_char)
        return self.tree

    if wx.Platform == '__WXMSW__':
        def _on_char(self, event):
            if self.popup.IsShown():
                code = event.GetKeyCode()
                if code == wx.WXK_UP:
                    item = self.tree.GetSelection()
                    if not item.IsOk(): return
                    item = self.tree.GetPrevVisible(item)
                    if item.IsOk():
                        self.tree.SelectItem(item)
                        self.tree.ScrollTo(item)
                    return

                if code == wx.WXK_DOWN:
                    item = self.tree.GetSelection()
                    if not item.IsOk(): return
                    item = self.tree.GetNextVisible(item)
                    if item.IsOk():
                        self.tree.SelectItem(item)
                        self.tree.ScrollTo(item)
                    return

                if code == ord('*'):
                    item = self.tree.GetSelection()
                    self.tree.Toggle(item)
                    return
                    
            AutoCompleter._on_key_down(self, event)
    else:
        def _on_char(self, event):
            if self.popup.IsShown():
                code = event.GetKeyCode()
                if code in (wx.WXK_UP, wx.WXK_DOWN):
                    event.SetEventObject(self.tree)
                    self.tree.ProcessEvent(event)
                    return

                if code == ord('*'):
                    event.SetEventObject(self.tree)
                    self.tree.ProcessEvent(event)
                    return

                if code in (wx.WXK_HOME, wx.WXK_END) and event.ControlDown():
                    event.SetEventObject(self.tree)
                    self.tree.ProcessEvent(event)
                    return

            event.Skip()


    def _on_activated(self, event):
        self.SetValue(self.tree.GetItemData(event.GetItem()).GetData())
        self.unpop()        


    def _on_changed(self, event):
        if not self.__item_selected:
            item = event.GetItem()
            if item.IsOk():
                self.SetValue(self.tree.GetItemData(item).GetData())
        

    def change_state(self, event):
        AutoCompleter.change_state(self, event)
        if self.popup.IsShown(): self.select_item()
        

    def before_display(self):
        item = self.tree.GetFirstVisibleItem()
        root = self.tree.GetRootItem()
        collapse = self.tree.Collapse
        next = self.tree.GetNextVisible
        while item.IsOk():
            if item != root:
                collapse(item)
            item = next(item)

        self.select_item()
        w1, h = self.textCtrl.GetSize()
        w2, h = self.popup.GetSize()
        self.popup.SetSize((max(w1, w1), h))
        wx.CallAfter(self.textCtrl.SetFocus)


    __item_selected = False
    def select_item(self):
        self.__item_selected = True
        
        value = self.GetValue()
        pos = bisect.bisect(self.choices, (value, self.tree.GetRootItem()))

        try:
            if self.choices[pos][0] != value:
                pos -= 1

            if self.choices[pos][0] != value:
                raise IndexError
            
        except IndexError:
            pos = len(self.choices) 

        try:
            self.tree.SelectItem(self.choices[pos][1])
        except IndexError: pass
        self.__item_selected = False


    def make_completion(self, value):
        pos = bisect.bisect(self.choices, (value, self.tree.GetRootItem()))
        try:
            val = self.choices[pos][0]
        except IndexError:
            return

        if val.startswith(value): self.complete(val)


    def fill_tree(self, iterator):
        self.tree.DeleteAllItems()
        self.choices = []
        root = self.tree.AddRoot("root")
        stack = []
        width = 0
        
        i = ""
        for i in iterator:
            while stack:
                data = self.tree.GetItemData(stack[-1]).GetData() + self.separator
                if i.startswith(data):
                    text = i[len(data):]
                    item = self.tree.AppendItem(stack[-1], text,
                                                data=wx.TreeItemData(i))
                    stack.append(item)
                    break
                else:
                    stack.pop()
            else:
                item = self.tree.AppendItem(root, str(i),
                                            data=wx.TreeItemData(i))
                stack.append(item)

            bisect.insort(self.choices, (i, item))

        w, h = self.tree.GetTextExtent("XX" + len(stack) * "XXXX" + i)
        width = max(width, w)
          
        w, h = self.tree.GetTextExtent("X")
        rows = min(self.visible_rows, self.tree.GetCount())
        height = int(rows * h * 1.3)
        self.tree.CacheBestSize((width, height))
        self.popup.adjust_size()
                                

class ModelWidget(wx.PyPanel, AtomWidget):
    __metaclass__ = _MetaWidget
    __type__ = dblayout._ModelType
    __view_name__ = "default"
    
    def __init__(self, itype, parent, name):
        wx.PyPanel.__init__(self, parent, style=wx.TAB_TRAVERSAL)        
        AtomWidget.__init__(self)

        self.view_name = name
        self.iview = None
        self.attrib_model = None
        self.view_class = itype.__name_view_class__
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(sizer)


    def GetValue(self):
        return self.attrib_model


    def SetValue(self, attrib_model):
        last_cmodel = self.attrib_model.__class__
        self.attrib_model = attrib_model
        
        if last_cmodel != attrib_model.__class__:
            sizer = self.GetSizer()
            sizer.DeleteWindows()
            self.last_cmodel = attrib_model.__class__
            try:
                view = attrib_model.get_view(self.view_name, self.view_class)
            except AttributeError:
                pass
            else:
                self.iview = view(self)
                sizer.Add(self.iview, 1, wx.EXPAND)

        if self.iview:
            self.iview.inspect(self.imodel, self.attrib)


    def update_errors(self):
        if self.iview: self.iview.update_errors()


    def show_main_error(self):
        return self.GetParent().show_main_error()


    def layout(self):
        try:
            self.Layout()
            self.GetParent().layout()
        except AttributeError:
            pass


    def end_inspect(self):
        if self.iview: self.iview.end_inspect()
        AtomWidget.end_inspect(self)


    def Enable(self, flag):
        wx.PyPanel.Enable(self, flag)
        for c in self.GetChildren(): c.Enable(flag)


    def GetMinSize(self):
        try:
            return self.iview.GetMinSize()
        except AttributeError:
            return wx.Size(-1, -1)


    def GetBestSize(self):
        try:
            return self.iview.GetBestSize()
        except AttributeError:
            return wx.Size(-1, -1)


    def __getattr__(self, name):
        if name == "imodel": raise AttributeError()
        return getattr(self.iview, name)



class Container(wx.PyPanel, IView):
    __metaclass__ = _MetaWidget
    __type__ = dblayout.ContainerType
    __view_name__ = "default"
    
    def __init__(self, itype, parent, name):
        wx.PyPanel.__init__(self, parent, style=wx.TAB_TRAVERSAL)
        IView.__init__(self)

        self.iview = itype.peer_class.get_view(name, "RowView")(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.iview, 1, wx.EXPAND)
        self.SetSizer(sizer)


    def inspect(self, imodel, attrib):
        self.iview.inspect(imodel, attrib)


    def end_inspect(self):
        self.iview.end_inspect()


    def Enable(self, flag):
        wx.PyPanel.Enable(self, flag)
        for c in self.GetChildren(): c.Enable(flag)


    def GetMinSize(self):
        return self.iview.GetMinSize()


    def GetBestSize(self):
        return self.iview.GetBestSize()


    def __getattr__(self, name):
        return getattr(self.iview, name)



class Reference(expander.Expander, IView):
    __metaclass__ = _MetaWidget
    __type__ = dblayout.ReferenceType
    __view_name__ = "default"
    

    def __init__(self, itype, parent, name):
        self.itype = itype
        expander.Expander.__init__(self, parent, -1)
        IView.__init__(self, iview)
        del self.itype
        

    def _on_key_down(self, event):
        if not event.ShiftDown() and not event.HasModifiers():
            if event.GetKeyCode() == wx.WXK_UP:
                self.choices_widget.move_up()
                return

            if event.GetKeyCode() == wx.WXK_DOWN:
                self.choices_widget.move_down()
                return

        expander.Expander._on_key_down(self, event)


    def _prepare_text(self, value):
        self.textCtrl = wx.TextCtrl(self, -1, value, pos=(0,0),
                                    style=wx.TE_READONLY)


    def selected(self, imodel):
        self.select_item()
        self.unpop()


    def show_value(self):
        if not self.value:
            self.SetValue("")
            return
        
        self.SetValue(str(self.value))
        

    def select_item(self):
        try:
            self.value = self.choices_widget.get_current_imodel()
        except IndexError:
            return
        
        self.show_value()
        self.change_state()


    def create_content(self, parent):
        self.iview = self.itype.peer_class.get_view(name)(parent)

        panel = Panel(parent, -1)
        choices_view = self.view.choices_view()
        self.choices_widget = choices_view.create_widget(panel)
        self.choices_widget.attach(self.selected)

        def _on_key_down(event):
            if event.GetKeyCode() == wx.WXK_ESCAPE:
                self.unpop()
            elif event.GetKeyCode() == wx.WXK_RETURN:
                self.selected(self.choices_widget.get_current_imodel)
                self.unpop()
            else:
                event.Skip()

        self.choices_widget.Bind(wx.EVT_KEY_DOWN, _on_key_down)
        return panel
        
        
    def update(self, imodel, attrib):
        try:
            old_value = self.value
        except AttributeError:
            old_value = self
            
        self.value = getattr(imodel, attrib)
        if old_value is self.value: return
        choices = self.view.choices
        if callable(choices):
            choices = choices(imodel)

        self.choices_widget.set_container(choices)
        self.choices_widget.moveto_imodel(self.value)
        panel = self.choices_widget.GetParent()
        min_size = self.choices_widget.GetMinSize()
        
        panel.SetClientSize(min_size)
        
        size = panel.GetSize()
        size = (size.width + 8, size.height + 8)
        panel.CacheBestSize(size)
        self.popup.adjust_size()
        self.choices_widget.SetSize(panel.GetClientSize())
        self.show_value()
        self.choices_widget.moveto_imodel(self.value)


    def save(self, transaction, imodel, attrib):
        try:
            value = self.choices_widget.get_current_imodel()
        except IndexError:
            value = None
        
        transaction.set_value(imodel, attrib, value, self.iview)



