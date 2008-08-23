############################################################################
#   Copyright (C) 2005, 2006 by Reithinger GmbH
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
import wx.stc
import wx.lib.newevent
import keyword
import bisect
import weakref
import sys
import itertools
from controller import controller



if 'wxMSW' in wx.PlatformInfo:
    faces = { 'times'     : 'Times New Roman',
              'mono'      : 'Courier New',
              'helv'      : 'Arial',
              'lucida'    : 'Lucida Console',
              'other'     : 'Comic Sans MS',
              'size'      : 10,
              'lnsize'    : 8,
              'backcol'   : '#FFFFFF',
              'calltipbg' : '#FFFFB8',
              'calltipfg' : '#404040',
            }

elif 'wxGTK' in wx.PlatformInfo and 'gtk2' in wx.PlatformInfo:
    faces = { 'times'     : 'Serif',
              'mono'      : 'Monospace',
              'helv'      : 'Sans',
              'other'     : 'new century schoolbook',
              'size'      : 10,
              'lnsize'    : 9,
              'backcol'   : '#FFFFFF',
              'calltipbg' : '#FFFFB8',
              'calltipfg' : '#404040',
            }

elif 'wxMac' in wx.PlatformInfo:
    faces = { 'times'     : 'Lucida Grande',
              'mono'      : 'Courier New',
              'helv'      : 'Geneva',
              'other'     : 'Comic Sans MS',
              'size'      : 13,
              'lnsize'    : 10,
              'backcol'   : '#FFFFFF',
              'calltipbg' : '#FFFFB8',
              'calltipfg' : '#404040',
            }

else: # GTK1, etc.
    faces = { 'times'     : 'Times',
              'mono'      : 'Courier',
              'helv'      : 'Helvetica',
              'other'     : 'new century schoolbook',
              'size'      : 12,
              'lnsize'    : 10,
              'backcol'   : '#FFFFFF',
              'calltipbg' : '#FFFFB8',
              'calltipfg' : '#404040',
            }



class SearchControl(wx.TextCtrl):
    def __init__(self, parent, id, editor, forward=True):
        wx.TextCtrl.__init__(self, parent, id, size=(300,-1))
        self.SetFocus()
        self.editor = editor
        self.search_stack = []
        self.search_text = ""
        self.case_sensitive = 0
        self.forward = forward

        wx.EVT_KEY_DOWN(self, self._on_key_down)
        wx.EVT_CHAR(self, self._on_char)
        wx.EVT_KILL_FOCUS(self, self._on_kill_focus)


    def _on_kill_focus(self, event):
        editor = self.editor
        editor.last_search = self.search_text
        controller().remove_menu_items(self)

        def clean_up():
            editor.SetFocus()
            toolbar = controller().get_toolbar()
            toolbar.remove_by_title("search")
            
        wx.CallAfter(clean_up)


    def push_text(self, text):
        start = self.editor.GetSelectionStart()
        self.search_stack.append((start, len(text)))
        self.search_text += text
        search_len = len(self.search_text)
        self.SetValue(self.search_text)
        self.SetInsertionPoint(search_len)

        if text.isupper():
            self.case_sensitive += 1

        self.find(start, self.forward and self.editor.GetLength() or 0)


    def pop_text(self):
        if self.search_stack:
            last = self.search_stack.pop()
            self.search_text = self.search_text[:-last[1]]
            search_len = len(self.search_text)
            self.SetValue(self.search_text)
            self.SetInsertionPoint(search_len)
            self.editor.GotoPos(last[0])
            self.editor.SetSelectionEnd(last[0] + search_len)


    def _on_char(self, event):
        self.push_text(unichr(event.GetKeyCode()))


    def _on_key_down(self, event):
        keycode = event.GetKeyCode()

        if 32 <= keycode < 255 \
               or keycode in [ wx.WXK_SHIFT, wx.WXK_CONTROL ]:

            if event.ControlDown():
                if keycode == ord("W"):
                    s = self.editor.GetCurrentPos()
                    e = self.editor.WordEndPosition(s, 0)
                    text = self.editor.GetTextRange(s, e)
                    self.push_text(text.lower())

                return

            event.Skip()
            return

        if keycode == wx.WXK_BACK:
            self.pop_text()
            return

        self.editor.ProcessEvent(event)
        self._on_kill_focus(None)


    def menu_find_forward(self):
        start = self.editor.GetSelectionStart()
        self.find(start + 1, self.editor.GetLength())


    def menu_find_backward(self):
        start = self.editor.GetSelectionStart()
        if start > 0:
            self.find(start - 1, 1)


    def find(self, start, end):
        if not self.search_text:
            text = getattr(self.editor, "last_search", "")
            if text:
                self.push_text(text)
            else:
                return

        if self.case_sensitive:
            flag = wx.stc.STC_FIND_MATCHCASE
        else:
            flag = 0

        editor = self.editor
        search_text = self.search_text.encode("utf-8", "ignore")
        pos = editor.FindText(start, end, self.search_text, flag)
        if pos > 0:
            editor.GotoPos(pos)
            editor.SetSelectionEnd(pos + len(search_text))
        else:
            if start < end:
                start = 0
            else:
                start = editor.GetLength()

        pos = editor.FindText(start, end, self.search_text, flag)
        if pos > 0:
            editor.GotoPos(pos)
            editor.SetSelectionEnd(pos + len(search_text))



class StyleMixin:
    standard_indent = 4

    def setup_style(self):
        self.StyleClearAll()

        self.SetTabWidth(8)
        self.SetTabIndents(1)
        self.SetUseTabs(0)
        self.SetIndent(self.standard_indent)
        self.SetIndentationGuides(1)
        self.SetBackSpaceUnIndents(1)

        # Global default styles for all languages
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,
                          "face:%(mono)s,size:%(size)d" % faces)
	
        self.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER,
                          "back:#C0C0C0,face:%(mono)s,size:%(lnsize)d" % faces)

        self.StyleSetSpec(wx.stc.STC_STYLE_CONTROLCHAR,
                          "face:%(other)s" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACELIGHT,
                          "fore:#0000FF,back:#FCFC94")
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACEBAD,
                          "fore:#FF0000,back:#000000")

        # Python styles
        # Default 
        self.StyleSetSpec(wx.stc.STC_P_DEFAULT,
                          "fore:#000000,face:%(mono)s,size:%(size)d" % faces)
        # Comments
        self.StyleSetSpec(wx.stc.STC_P_COMMENTLINE,
                          "fore:#007F00,face:%(other)s,size:%(size)d" % faces)
        # Number
        self.StyleSetSpec(wx.stc.STC_P_NUMBER,
                          "fore:#007F7F,size:%(size)d" % faces)
        # String
        self.StyleSetSpec(wx.stc.STC_P_STRING,
                          "fore:#7F007F,face:%(mono)s,size:%(size)d" % faces)
        # Single quoted string
        self.StyleSetSpec(wx.stc.STC_P_CHARACTER,
                          "fore:#7F007F,face:%(mono)s,size:%(size)d" % faces)
        # Keyword
        self.StyleSetSpec(wx.stc.STC_P_WORD,
                          "face:%(mono)s,fore:#00007F,"\
                          "bold,size:%(size)d" % faces)
        # Triple quotes
        self.StyleSetSpec(wx.stc.STC_P_TRIPLE,
                          "face:%(mono)s,fore:#7F0000,size:%(size)d" % faces)
        # Triple double quotes
        self.StyleSetSpec(wx.stc.STC_P_TRIPLEDOUBLE,
                          "face:%(mono)s,fore:#7F0000,size:%(size)d" % faces)
        # Class name definition
        self.StyleSetSpec(wx.stc.STC_P_CLASSNAME,
                          "face:%(mono)s,fore:#0000FF,"\
                          "bold,underline,size:%(size)d" % faces)
        # Function or method name definition
        self.StyleSetSpec(wx.stc.STC_P_DEFNAME,
                          "face:%(mono)s,fore:#007F7F,bold,size:%(size)d" \
                          % faces)
        # Operators
        self.StyleSetSpec(wx.stc.STC_P_OPERATOR,
                          "face:%(mono)s,bold,size:%(size)d" % faces)
        # Identifiers
        self.StyleSetSpec(wx.stc.STC_P_IDENTIFIER,
                          "fore:#000000,face:%(mono)s,size:%(size)d" % faces)
        # Comment-blocks
        self.StyleSetSpec(wx.stc.STC_P_COMMENTBLOCK,
                          "fore:#7F7F7F,size:%(size)d" % faces)
            
        # End of line where string is not closed
        self.StyleSetSpec(wx.stc.STC_P_STRINGEOL,
                          "fore:#000000,face:%(mono)s,"\
                          "back:#E0C0E0,eol,size:%(size)d" % faces)
    
        
    def setup_eol(self):
        self.eol = "\n"
        self.SetEOLMode(wx.stc.STC_EOL_LF)
    

    __last_line = None
    __line_digits = 0
    def adjust_number_margin(self, margin=0):
        if self.GetLineCount() == self.__last_line: return
        line = self.__last_line = self.GetLineCount()
        line_str = ' ' + "".join(map(lambda x: '8', str(line)))
        
        if self.__line_digits != len(line_str):
            self.__line_digits = len(line_str)
            w = self.TextWidth(wx.stc.STC_STYLE_LINENUMBER, line_str)
            self.SetMarginWidth(margin, w)
            
NOTYPE = -1
CLASS = 0
FUNCTION = 1
IMPORT = 2

#to be used as mixin
class _CodeItem(object):
    obj_type = CLASS
    indent = 0
    name = ""
    is_header = True
    marker = None
    editor = None

    def __cmp__(self, other):
        if isinstance(other, int):
            return cmp(self.get_line(), other)
        
        return cmp(self.get_line(), other.get_line())


    def __repr__(self):
        return self.name


    def get_line(self):
        return self.editor.MarkerLineFromHandle(self.marker)


    def is_parent(self, item):
        if self.indent >= item.indent: return False
        next_header = self.editor.find_next_header(self.get_line() + 1,
                                                   self.indent)
        return item.get_line() < next_header


    def get_last_line(self, include_white=False):
        editor = self.editor
        get_indent = editor.GetLineIndentation
        get_length = editor.LineLength
        pindent = self.indent
        
        def is_greater_indent(l):
            return not (get_length(l) - 1 > get_indent(l) <= pindent)

        lines = xrange(self.get_line() + 1, editor.GetLineCount())
        lines = itertools.takewhile(is_greater_indent, lines)

        if self.is_header:
            if include_white:
                def has_content(l):
                    indent = get_indent(l)
                    return indent > pindent or indent == get_length(l) - 1
            else:
                def has_content(l): return get_indent(l) > pindent
        else:
            if include_white:
                def has_content(l): return get_indent(l) <= get_length(l) - 1
            else:
                def has_content(l): return get_indent(l) < get_length(l) - 1
    
        lines = [ l for l in lines if has_content(l) ]
        return lines and lines[-1] or self.get_line()


    def get_parent(self):
        indent = self.indent
        if not indent:
            return None

        items = self.editor.code_items
        try:
            pos = items.index(self)
        except ValueError:
            return None

        while pos > 0:
            siblings = tuple(itertools.takewhile(\
                lambda i: items[i].indent >= indent,
                xrange(pos - 1, -1, -1)))

            try:
                pos = siblings[-1] - 1
            except IndexError:
                pos -= 1

            parent = pos >= 0 and items[pos] or None
            if parent:
                if parent.is_parent(self): 
                    return parent
                else:
                    #  this is not the parent try again
                    continue
            else:
                return None


    def get_args(self):
        line = self.get_line()
        text = self.editor.GetLine(line)
        brace_start = self.editor.PositionFromLine(line) + text.find("(")
        brace_end = self.editor.BraceMatch(brace_start)
        args = unicode(self.editor.GetTextRange(brace_start + 1, brace_end))
        return tuple(filter(bool, map(unicode.strip, args.split(","))))


    def has_children(self):
        editor = self.editor
        line = self.get_line() + 1
        ni = editor.next_item_line(line)
        nh = editor.find_next_header(line, self.indent)
        return ni < nh and editor.GetLineIndentation(ni) > self.indent


    def get_children(self, recursive=False):
        editor = self.editor
        code_items = editor.code_items
        line = self.get_line()
        index = bisect.bisect_left(code_items, line)
        pindent = self.indent

        end_line = self.editor.find_next_header(line + 1, pindent)
        is_children = lambda c: c.indent > pindent and c.get_line() < end_line
        children = itertools.takewhile(is_children, code_items[index + 1:])

        if not recursive:
            children = tuple(children)
            try:
                first = children[0]
            except IndexError:
                return ()

            findent = first.indent
            is_sibling = lambda c: c.indent == findent
            return filter(is_sibling, children)

        return children


    def rename(self, new_name):
        editor = self.editor
        line = self.get_line()
        editor.SetTargetStart(editor.PositionFromLine(line))
        editor.SetTargetEnd(editor.GetLineEndPosition(line))
        pos = editor.SearchInTarget(self.name)
        if pos < 0: return
        editor.SetTargetStart(pos)
        editor.SetTargetEnd(pos + len(self.name))
        editor.ReplaceTarget(new_name)
        editor.check_code_updates(line, line)


    def remove(self):
        editor = self.editor
        line = self.get_line()
        last_line = self.get_last_line(True)
        start = editor.PositionFromLine(line)
        end = editor.GetLineEndPosition(last_line) + 1
        text = editor.GetTextRange(start, end)
        editor.SetTargetStart(start)
        editor.SetTargetEnd(end)
        editor.ReplaceTarget("")
        editor.check_code_updates(line, line + 1)
        return text, line, last_line - line

        
    def move_after(self, code_item):
        editor = self.editor

        editor.BeginUndoAction()
        text, start_line, lines = self.remove()
        line = code_item.get_last_line(True) + 1
        editor.InsertText(editor.PositionFromLine(line), text)
        editor.adjust_indent(line, line + lines,  
                             code_item.indent - self.indent)
        editor.check_code_updates(line, line + lines)
        editor.EndUndoAction()
        return line
        

    def move_before(self, code_item):
        editor = self.editor

        editor.BeginUndoAction()

        text, start_line, lines = self.remove()
        line = code_item.get_line()
        editor.InsertText(editor.PositionFromLine(line) - 1, "\n" + text[:-1])
        editor.adjust_indent(line, line + lines, 
                             code_item.indent - self.indent)
        editor.check_code_updates(line, line + lines)
        editor.EndUndoAction()
        return line
        

#mixin for pyeditor

CodeItemEvent, EVT_CODE_ITEM_CHANGED = wx.lib.newevent.NewEvent()

class _CodeBrowserBase(object):
    def _parse_class(self, text):
        pos = text.find("class")

        if 0 <= text.find("#") < pos:
            return False
        
        text = text[pos + 6:].lstrip()
        pos = text.find("(")
        if pos < 0: pos = text.find(":")
        self._name = text[:pos].strip()
        self._type = CLASS
        self._header = True
        return True


    def _parse_func(self, text):
        pos = text.find("def")

        if 0 <= text.find("#") < pos:
            return False
        
        name = text[pos + 4:].lstrip()
        pos = name.find("(")
        self._name = name[:pos].strip()
        self._type = FUNCTION
        self._header = True
        return True


    def _parse_import(self, text):
        self._type = IMPORT
        words = text.split(" ")
        self._name = words[1].strip()
        self._header = False
        return True


    def _parse_from(self, text):
        self._type = IMPORT
        words = text.split(" ")
        self._name = words[1].strip()
        self._name += ".%s" % words[-1].strip()
        self._header = False
        return True
    

class _CodeBrowser(_CodeBrowserBase):
    _rough_class = r"^[^#]*\<class[^:]+:"
    _rough_func = r"^[^#]*\<def[^:]+:"
    _rough_from = r"^from +[a-zA-Z0-9_.]+ +import +[a-zA-Z0-9_.*]+"
    _rough_import = r"^import +[a-zA-Z0-9_.]+"
    _patterns = ((_rough_class, _CodeBrowserBase._parse_class),
                 (_rough_func, _CodeBrowserBase._parse_func),
                 (_rough_from, _CodeBrowserBase._parse_from),
                 (_rough_import, _CodeBrowserBase._parse_import))
    _marker_mask = 1
    _name = None
    _type = NOTYPE
    _line = -1
    _indent = -1
    
    def __init__(self):
        self.code_items = []
        self.MarkerDefine(0, wx.stc.STC_MARK_EMPTY, "white", "white")
        #self.MarkerDefine(0, wx.stc.STC_MARK_ARROW, "green", "white")

        self.SetMarginType(1, wx.stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(1, 1)
        #self.SetMarginWidth(1, 12)


    def __find_text(self, text, start):
        end = self.GetLength()
        pos = self.FindText(start, end, text,
                            wx.stc.STC_FIND_REGEXP|wx.stc.STC_FIND_MATCHCASE)
        if pos < 0: pos = end
        return pos
            

    def __inspect(self):
        end = self.GetLength()

        minmode = min(self.__mode)
        if minmode >= end:
            self._name = None
            self._type = NOTYPE
            self._line = self.GetLineCount()
            return False

        line = self._line = self.LineFromPosition(minmode)
        self._indent = self.GetLineIndentation(line)
        text = self.GetLine(line)
        for i, pattern_parse_func in enumerate(self._patterns):
            if self.__mode[i] == minmode:
                if not pattern_parse_func[1](self, text):
                    self._type = NOTYPE
                return True
                
        raise RuntimeError("parse error")


    def __find_first(self, start):
        self.__mode = [ self.__find_text(p[0], start)
                        for p in self._patterns ]
        return self.__inspect()

        
    def __find_next(self):
        mode = self.__mode
        minmode = min(mode)

        def end_of_line(pos):
            return self.GetLineEndPosition(self.LineFromPosition(pos))

        for i, p in enumerate(self._patterns):
            if mode[i] == minmode:
                mode[i] = self.__find_text(p[0], end_of_line(mode[i]))
                break
        
        return self.__inspect()


    def __new_item(self, do_bisect=False):
        if self._type == NOTYPE: return None
        item = _CodeItem()
        item.indent = self._indent
        item.name = self._name
        item.obj_type = self._type
        item.is_header = self._header
        item.marker = self.MarkerAdd(self._line, 0)
        item.editor = weakref.proxy(self)
        if do_bisect:
            bisect.insort_left(self.code_items, item)
        else:
            self.code_items.append(item)
            
        return item
            
    
    def browse_code(self):
        self.code_items = []
        self.MarkerDeleteAll(0)

        if self.__find_first(0): 
            self.__new_item()
            while self.__find_next():
                self.__new_item()


    def prev_item_line(self, line):
        """
        The line of the previous item
        """
        return self.MarkerPrevious(line, self._marker_mask)


    def next_item_line(self, line):
        """
        The line of the next item
        """
        next_marker = self.MarkerNext(line, self._marker_mask)
        if next_marker < 0: return self.GetLineCount()
        return next_marker

    __update_start = sys.maxint
    __update_end = 0
    def update_code(self, event):
        start = event.GetPosition()
        end = start + event.GetLength()

        mod_type = event.GetModificationType()

        if mod_type == (wx.stc.STC_PERFORMED_UNDO | wx.stc.STC_MOD_BEFOREINSERT):
            #Bug hack: stc does not send the following message
            newev = wx.stc.StyledTextEvent(wx.stc.wxEVT_STC_MODIFIED)
            newev.SetModificationType(wx.stc.STC_PERFORMED_UNDO | wx.stc.STC_MOD_INSERTTEXT)
            newev.SetPosition(start)
            newev.SetLength(event.GetLength())
            newev.SetText(event.GetText())
            wx.CallAfter(self.update_code, newev)
            return
        
        if mod_type & wx.stc.STC_MOD_INSERTTEXT:
            if mod_type & wx.stc.STC_PERFORMED_UNDO:
                if self.GetTextRange(start, end) != event.GetText():
                    return

            start_line =  self.LineFromPosition(start)
            end_line = self.LineFromPosition(end)
            next_item_line = self.next_item_line(start_line)
            next_item_start = self.PositionFromLine(next_item_line)

            if next_item_start < end:
               # the marker has maybe moved
               item = self.code_item_at(next_item_line)
               if start <= next_item_start + item.indent:
                   self.MarkerDeleteHandle(item.marker)
                   item.marker = self.MarkerAdd(end_line, 0)

        
        if mod_type & wx.stc.STC_MOD_INSERTTEXT:
            self.__update_start = min(self.__update_start, start)
            self.__update_end = max(self.__update_end, end)
            self.__check_code_updates_call_count += 1
            wx.FutureCall(200, self.defered_check_code_updates)

        if mod_type & wx.stc.STC_MOD_DELETETEXT:
            if mod_type & wx.stc.STC_PERFORMED_UNDO:
                #dirty hack:some times start is not correct
                start = max(start - 200, 0)
                
            self.__update_start = min(self.__update_start, start)
            self.__update_end = max(self.__update_end, end)
            self.__check_code_updates_call_count += 1
            wx.FutureCall(200, self.defered_check_code_updates)


    __check_code_updates_call_count = 0
    __check_code_updates_yielding = False
    def defered_check_code_updates(self):
        if self.__check_code_updates_yielding:
            wx.FutureCall(200, self.defered_check_code_updates)
            return
            
        self.__check_code_updates_call_count -= 1
        if self.__check_code_updates_call_count > 0: return
        self.__check_code_updates_call_count = 0
        
        if self.__update_start > self.__update_end: return
        start_line = self.LineFromPosition(self.__update_start)
        end_line = self.LineFromPosition(self.__update_end)
        self.__update_start = sys.maxint
        self.__update_end = 0
        self.__check_code_updates_yielding = True
        self.check_code_updates(start_line, end_line)
        self.__check_code_updates_yielding = False

        
    def check_code_updates(self, start_line, end_line):
        changed_list = []
        ctrl = controller()

        if self.code_items:
            # remove and change existing items
            # --------------------------------

            # a marker of a deleted code_item can be moved back
            end_line = self.next_item_line(end_line)
            start_index = bisect.bisect_left(self.code_items, start_line)
            end_index = bisect.bisect_right(self.code_items, end_line) - 1

            last_line = sys.maxint
            for index in xrange(end_index, start_index - 1, -1):
                item = self.code_items[index]
                line = item.get_line()
                remove = False

                if line == -1:
                    remove = True

                elif line >= last_line:
                    remove = True
                else:
                    last_line = line
                    self.__find_first(self.PositionFromLine(line))
                    if self._line != line or self._type == NOTYPE:
                        remove = True

                if remove:
                    def make_get_line(l):
                        def get_line(): return l
                        return get_line
                    
                    def make_get_children(item):
                        children = tuple(item.get_children(True))
                        def get_children(recursive=True):
                            return children

                        return get_children

                    item.get_line = make_get_line(last_line)
                    item.get_children = make_get_children(item)
                    del self.code_items[index]
                    self.MarkerDeleteHandle(item.marker)
                    changed_list.append(("removed", item))

                elif (item.indent, item.name, item.obj_type) != \
                         (self._indent, self._name, self._type):
                    #changed
                    item.indent = self._indent
                    item.name = self._name
                    item.obj_type = self._type
                    changed_list.append(("changed", item))
                else:
                    # reinsert Marker, because a delete in the next iterations
                    # can move my old marker.
                    self.MarkerDeleteHandle(item.marker)
                    item.marker = self.MarkerAdd(line, 0)

                if self.__check_code_updates_yielding:
                    ctrl.Yield(True) # don't disturb user input
                    
        #find new items
        if self.__find_first(self.PositionFromLine(start_line)):
            next_item_line = self.next_item_line
            def new_item():
                if next_item_line(self._line) == self._line: return
                
                l = next_item_line(self._line - 1)
                item = self.__new_item(True)
                if item:
                    changed_list.append(("inserted", item))

            new_item()
                
            while self._line <= end_line and self.__find_next():
                new_item()
                if self.__check_code_updates_yielding:
                    ctrl.Yield(True) # don't disturb user input

        if changed_list:
            self.AddPendingEvent(CodeItemEvent(changed=changed_list))


    def code_items_near(self, line):
        """
        Returns the code items before and after that line
        and True if the line is inside the item before.
        """

        next = self.MarkerNext(line + 1, self._marker_mask)
        if next >= 0:
            next = self.code_items[bisect.bisect_left(self.code_items, next)]
        else:
            next = None

        prev = self.MarkerPrevious(line, self._marker_mask)
        if prev >= 0:
            prev = self.code_items[bisect.bisect_left(self.code_items, prev)]
        else:
            prev = None

        return prev, next
            

    def code_item_at(self, line):
        items = self.code_items
        item_line = self.MarkerPrevious(line, self._marker_mask)
        pos = bisect.bisect_left(items, item_line)
        try:
            item = items[pos]
        except IndexError:
            return None

        if pos == 0 and item.get_line() > line: return None
        while item and item.get_last_line() < line:
            item = item.get_parent()

        return item

                
    def current_code_item(self):
        pos = self.GetCurrentPos()
        line = self.LineFromPosition(pos)
        return self.code_item_at(line)


    def find_next_header(self, line, max_indent):
        start = self.PositionFromLine(line)
        end = self.GetLength()
        line_from_position = self.LineFromPosition
        get_indent = self.GetLineIndentation
        find = self.FindText

        start = find(start + 1, end, ":")
        while 0 <= start < end:
            line = line_from_position(start)
            if get_indent(line) <= max_indent:
                return line

            start = find(start + 1, end, ":")

        return self.GetLineCount()



class PythonEditCtrl(wx.stc.StyledTextCtrl, StyleMixin, _CodeBrowser):
    braces = u"[]{}()"
    
    def __init__(self, parent, style=0):
        wx.stc.StyledTextCtrl.__init__(self, parent, -1,
                                       style=wx.NO_FULL_REPAINT_ON_RESIZE|\
                                       style)
        _CodeBrowser.__init__(self)

        self.SetCaretWidth(2)
        self.SetCaretPeriod(0)

        self.SetLexer(wx.stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, " ".join(keyword.kwlist))
        self.SetProperty("fold", "1")
        #self.SetProperty("tab.timmy.whinge.level", "1")

        self.SetLayoutCache(wx.stc.STC_CACHE_PAGE)
        self.SetMargins(0,0)
        self.SetMarginWidth(1,0)
        self.SetMarginType(0, wx.stc.STC_MARGIN_NUMBER)
        self.adjust_number_margin()
        self.setup_symbol_margin()
        self.setup_style()
        self.setup_eol()
        #self.UsePopUp(0)

        self.SetModEventMask(wx.stc.STC_MOD_INSERTTEXT | \
                             wx.stc.STC_MOD_DELETETEXT | \
                             wx.stc.STC_PERFORMED_UNDO | \
                             wx.stc.STC_PERFORMED_USER | \
                             wx.stc.STC_PERFORMED_REDO)
            
        self.listen()


    def unlisten(self):
        self.Unbind(wx.EVT_IDLE)
        self.Unbind(wx.EVT_KEY_DOWN)
        self.Unbind(wx.stc.EVT_STC_MODIFIED)
        self.Unbind(wx.stc.EVT_STC_CHARADDED)
        self.Unbind(wx.stc.EVT_STC_MARGINCLICK)
        self.Unbind(wx.stc.EVT_STC_UPDATEUI)


    def listen(self):
        self.Bind(wx.EVT_IDLE, self._on_idle)
        self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
        self.Bind(wx.stc.EVT_STC_MODIFIED, self._on_change)
        self.Bind(wx.stc.EVT_STC_CHARADDED, self._on_new_char)
        self.Bind(wx.stc.EVT_STC_MARGINCLICK, self._on_margin_click)
        self.Bind(wx.stc.EVT_STC_UPDATEUI, self._on_update_ui)

    def GetTextRange(self, start, end):
        end = min(end, self.GetLength()) # to avoid scincilla assertions
        return wx.stc.StyledTextCtrl.GetTextRange(self, start, end)


    __last_pos = None
    def _on_idle(self, event):
        self.adjust_number_margin()

        pos = self.GetCurrentPos()
        if pos != self.__last_pos:
            self._on_pos_changed(self.__last_pos, pos)
            self.__last_pos = pos


    def _on_pos_changed(self, old, new):
        pass


    def _on_key_down(self, event):
        if event.GetKeyCode() == wx.WXK_TAB:
            if self.inspect_indent_char("\t"):
                return
            
        event.Skip()

                           
    def _on_change(self, event):
        self.update_code(event)
                
        
    def _on_new_char(self, event):
        self.inspect_indent_char(unichr(event.GetKey()))
        

    def inspect_indent_char(self, key):
        (sstart, send) = self.GetSelection()

        if sstart != send or self.AutoCompActive():
            return False

        if key == self.eol:
            return self.autoindent(self.GetCurrentPos())

        if key == "\t":
            (text, pos) = self.GetCurLine()
            for i in range(0, pos):
                if not text[i].isspace():
                    #I am not at the beginning of the line
                    return False

            return self.autoindent(self.GetCurrentPos())

        return False
        

    def _on_update_ui(self, evt):
        # check for matching braces
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.GetCurrentPos()
        if caretPos > 0:
            charBefore = self.GetCharAt(caretPos - 1)
            styleBefore = self.GetStyleAt(caretPos - 1) & 15

        # check before
        if charBefore and unichr(charBefore) in self.braces \
               and styleBefore == wx.stc.STC_P_OPERATOR:
            braceAtCaret = caretPos - 1

        # check after
        if braceAtCaret < 0:
            charAfter = self.GetCharAt(caretPos)
            styleAfter = self.GetStyleAt(caretPos) & 15
            if charAfter and unichr(charAfter) in self.braces and \
                   styleAfter == wx.stc.STC_P_OPERATOR:
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.BraceMatch(braceAtCaret)

        if braceAtCaret != -1 and braceOpposite == -1:
            self.BraceBadLight(braceAtCaret)
        else:
            self.BraceHighlight(braceAtCaret, braceOpposite)


    def _on_margin_click(self, evt):
        # fold and unfold as needed
        if evt.GetMargin() == 2:
            lineClicked = self.LineFromPosition(evt.GetPosition())
            self.ToggleFold(lineClicked)


    def fold_to_level(self, level):
        stack = [ ]
        for i in range(0, self.GetLineCount()):
            while stack and stack[-1][0] < i:
                fold_line = stack[-1][1]

                if len(stack) >= level + 1:
                    self.SetFoldExpanded(fold_line, 1)
                else:
                    self.SetFoldExpanded(fold_line, 0)

                self.ToggleFold(fold_line)
                del stack[-1]

            lc = self.GetLastChild(i, -1)
            if lc == i: continue
            stack.append((lc, i))
            

    def setup_symbol_margin(self):
        self.SetMarginType(2, wx.stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, wx.stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 12)
        
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEREND,
                          wx.stc.STC_MARK_BOXPLUSCONNECTED,
                          "white", "black")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPENMID,
                          wx.stc.STC_MARK_BOXMINUSCONNECTED,
                          "white", "black")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERMIDTAIL,
                          wx.stc.STC_MARK_TCORNER,
                          "white", "black")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERTAIL,
                          wx.stc.STC_MARK_LCORNER,
                          "white", "black")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERSUB,
                          wx.stc.STC_MARK_VLINE,
                          "white", "black")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDER,
                          wx.stc.STC_MARK_BOXPLUS,
                          "white", "black")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPEN,
                          wx.stc.STC_MARK_BOXMINUS,
                          "white", "black")


    def autoindent(self, cur_pos, change_pos=True):
        line = self.LineFromPosition(cur_pos)
        if line <= 0: return False

        style = self.GetStyleAt(cur_pos) & 15
        line_prev = line
        while line_prev > 0:
            line_prev -= 1
            indent = self.GetLineIndentation(line_prev)
            prevline_start = self.PositionFromLine(line_prev)
            text = self.GetLine(line_prev)
            
            stripped = text.rstrip()
            if not stripped:
                continue

            if stripped.endswith('"""') or stripped.endswith("'''"):
                pos = stripped.find("=")
                if pos >= 0:
                    indent += 1
                else:
                    indent = (indent / self.standard_indent) \
                             * self.standard_indent
                try:
                    indent += tindent
                except UnboundLocalError:
                    pass
                break

            if style in (wx.stc.STC_P_TRIPLEDOUBLE, wx.stc.STC_P_TRIPLE):
                if change_pos:
                    #autoindent was call while editing==>take the indent of
                    #the prevline
                    break

                #autoindent was called after an InsertText
                #==> get the indent by the line and add it to the global
                #    indent of the string
                
                try:
                    tindent
                except UnboundLocalError:
                    tindent = self.GetLineIndentation(line)
                    
                continue

            try:
                #cut comments
                cpos = stripped.index("#")
                def match(quote):
                    count = len(filter(lambda c: c == quote, stripped[:cpos]))
                    return count % 2 == 0

                if match('"') and match("'"):
                    stripped = stripped[:cpos]
            except ValueError:
                pass

            if not stripped: continue
                
            if stripped[-1] == "\\":
                pos = stripped.find("=")
                if pos >= 0:
                    indent = self.GetColumn(prevline_start + pos)
                    break

            indent_set = False
            for c in "([{":
                pos = len(stripped)
                try:
                    while True:
                        pos = stripped.rindex(c, 0, pos)
                        MatchPos = self.BraceMatch(prevline_start + pos)
                        if MatchPos < 0 or MatchPos >= cur_pos:
                            pos += 1
                            while pos < len(stripped) and stripped[pos] == ' ':
                                pos += 1

                            indent = max(self.GetColumn(prevline_start + pos), indent)
                            indent_set = True
                            break
                except ValueError:
                    pass

            if not indent_set:
                if stripped[-1] == ":":
                    indent = self.__get_prev_indent(stripped[:-1].rstrip(),
                                                    prevline_start, indent)
                    indent += self.GetIndent()
                    break

                if stripped[-1] == ',':
                    stripped = stripped[:-1].rstrip()

                indent = self.__get_prev_indent(stripped, prevline_start,
                                                indent)
            break

           
        if indent:
            self.SetLineIndentation(line, indent)
            if change_pos: self.GotoPos(self.GetLineIndentPosition(line))
            return True

        return False


    def adjust_indent(self, start_line, end_line, diff_indent):
        get_indent = self.GetLineIndentation
        set_indent = self.SetLineIndentation
        for l in range(start_line, end_line + 1):
            set_indent(l, get_indent(l) + diff_indent)


    def create_search(self, factory=SearchControl, forward=True):
        def create_search(parent, id_):
            return factory(parent, id_, self, forward)

        toolbar = controller().get_toolbar()
        tool = toolbar.make_control(self, "search", create_search)
        toolbar.make_separator("search", True)


    def __get_prev_indent(self, line_string, prevline_start, default_indent):
        if line_string and line_string[-1] in ")]}":
            MatchPos = self.BraceMatch(prevline_start \
                                       + len(line_string) - 1)
            if MatchPos >= 0:
                l = self.LineFromPosition(MatchPos)
                return self.GetLineIndentation(l)

        return default_indent

                                

try:
    import psyco
except ImportError:
    pass
else:
    psyco.cannotcompile(_CodeItem.get_last_line) #because of itertools

