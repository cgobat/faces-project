############################################################################
#   Copyright (C) 2005 by Reithinger GmbH
#   mreithinger@web.de
#
#   This file is part of metapie.
#                                                                         
#   metapie is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version  of the License, or
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

import metapie.browser as browser
import metapie.navigator as navigator
import views


Browsers = browser.Browsers


class _MetaBrowser(browser._MetaBrowser):
    def __init__(cls, name, bases, dict_):
        super(_MetaBrowser, cls).__init__(name, bases, dict_)
        if not cls._contained_: return

        class BrowserView(views.FormView, navigator.View):
            __model__ = cls
            format = "objects(%sGrid)>" % cls._contained_.__name__

            def prepare(self):
                self.grow_col(0)
                self.grow_row(0)


class Browser(browser.Browser):
    __metaclass__ = _MetaBrowser
