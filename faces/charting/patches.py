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

import math
import tools
import matplotlib.patches as _patches
import matplotlib.transforms as _transforms
import matplotlib.artist as _artist


Arrow = _patches.Arrow
Polygon = _patches.Polygon
Shadow = _patches.Shadow
Wedge = _patches.Wedge

class Rectangle(_patches.Rectangle):
    def __init__(self, xy, width, height, **kwargs):
        _patches.Rectangle.__init__(self, (0,0), width, height, **kwargs)
        self.xy = xy


class RegularPolygon(_patches.RegularPolygon):
    def __init__(self, xy, numVertices, radius, 
                 orientation=0, **kwargs):

        _patches.Patch.__init__(self, **kwargs)

        self.xy = xy
        self.numVertices = numVertices
        self.radius = radius
        self.orientation = orientation
        hstretch = tools.HSEP / tools.VSEP

        theta = 2*math.pi/self.numVertices * _patches.arange(self.numVertices) + \
                self.orientation
        r = self.radius
        xs = map(lambda t: self.xy[0] + r * math.cos(t) * hstretch, theta)
        ys = map(lambda t: self.xy[1] + r * math.sin(t), theta)

        self.verts = zip(xs, ys)


    def get_verts(self):
        return self.verts


class Circle(RegularPolygon):
    """
    A circle patch
    """
    def __init__(self, xy, radius, resolution=20,  # the number of vertices
                 **kwargs):
        self.center = xy
        self.radius = radius
        RegularPolygon.__init__(self, xy,
                                resolution,
                                radius,
                                orientation=0,
                                **kwargs)

try:
    import PIL.Image as _Image
    from matplotlib.image import pil_to_array as _pil_to_array
    import matplotlib._image as _mimage

    def pil_to_image(pilImage):
        if pilImage.mode in ('RGBA', 'RGBX'):
            im = pilImage # no need to convert images in rgba format
        else: # try to convert to an rgba image
            try:
                im = pilImage.convert('RGBA')
            except ValueError:
                raise RuntimeError('Unknown image mode')


        w, h = im.size
        return _mimage.frombuffer(im.tostring('raw',im.mode,0,-1), w, h, 1)


    class Icon(_artist.Artist):
        def __init__(self, xy, image,
                     verticalalignment='bottom',
                     horizontalalignment='left'):
            _artist.Artist.__init__(self)

            if isinstance(image, basestring):
                image =_Image.open(image)

            self.dpi = image.info.get("dpi", (72, 72))
            self.image = image
            self.cache = pil_to_image(self.image)
            self.cache.dpi = 0
            self.xy = xy


        def draw(self, renderer):
            if not self.get_visible(): return
            self.make_cache()
            xy = self._transform.xy_tup(self.xy)
            renderer.draw_image(xy[0], xy[1], self.cache, self.clipbox)


        def get_window_extent(self, renderer=None):
            w, h = self.image.size
            xy = self._transform.xy_tup(self.xy)
            dpi = self.figure.get_dpi()
            return _transforms.lbwh_to_bbox(xy[0], xy[1],
                                            w * dpi / self.dpi[0],
                                            h * dpi / self.dpi[1])


        def make_cache(self):
            dpi = self.figure.get_dpi()
            if self.cache.dpi != dpi:
                w, h = self.image.size
                tmp = self.image.resize((int(w * dpi / self.dpi[0]),
                                         int(h * dpi / self.dpi[1])))
                self.cache = pil_to_image(tmp)
                self.cache.is_grayscale = False
                self.cache.dpi = dpi
                

except ImportError:
    pass
