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


class Peer(object):
    def _remove_from_peer(self, peer, parent_imodel):
        if not self._name_to_me:
            return
            
        peer_end = getattr(peer, self._name_to_me)
        try:
            del peer_end[parent_imodel]
        except KeyError:
            pass
        except TypeError:
            setattr(peer, self._name_to_me, None)


    def _add_to_peer(self, peer, parent_imodel):
        if not peer or not self._name_to_me:
            return

        peer_end = getattr(peer, self._name_to_me)
        try:
            peer_end.insert(parent_imodel)
        except AttributeError:
            setattr(peer, self._name_to_me, parent_imodel)
        
