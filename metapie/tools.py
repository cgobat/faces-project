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

import gettext
import os.path
import sys
import wx

if wx.USE_UNICODE:
    def get_gettext():
        try:
            return gettext.translation("metapie").ugettext
        except:
            try:
                if sys.frozen:
                    path = os.path.dirname(sys.argv[0])
                    path = os.path.join(path, "resources", "metapie", "locale")
                else:
                    path = os.path.split(__file__)[0]
                    path = os.path.join(path, "locale")

                return gettext.translation("metapie", path).ugettext
            except Exception, e:
                return lambda msg: msg
else:
    def get_gettext():
        return lambda msg: msg



