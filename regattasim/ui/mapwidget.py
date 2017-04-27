# -*- coding: utf-8 -*-
# Copyright (C) 2017 Davide Gessa
# Copyright (C) 2012 Riccardo Apolloni
'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
'''

import gi
import math
import os
import struct
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

from .. import config


class PolygonalMap:
    def __init__ (self, polygons):
        self.polygons = polygons

    def lonToX (self, lon, width, bbox):
        s = abs (bbox[1][0]) + abs (bbox[1][1])
        return width - ((lon + 180) * width / s)

    def latToY (self, lat, height, bbox):
        s = abs (bbox[0][0]) + abs (bbox[0][1])
        return height - ((lat + 90) * height / s)


    def draw (self, widget, cr, bbox):
        print ('draw')

        #print (self.lonToX (9, 600, bbox), self.latToY (39, 600, bbox))
        cr.set_line_width (0.5)
        cr.set_source_rgb(0,0,0)
        for polygon in self.polygons:
            #print (len (polygon))
            for i in range (0, len (polygon)):
                x = self.lonToX (polygon[i][1], 600, bbox)
                y = self.latToY (polygon[i][0], 600, bbox)

                if x < 0 or x > 600 or y < 0 or y > 600:
                    continue

                if i == len (polygon) - 1:
                    cr.move_to (x, y)
                    cr.line_to (self.lonToX (polygon[0][1], 600, bbox), self.latToY (polygon[0][0], 600, bbox))
                    cr.stroke ()
                else:
                    cr.move_to (x, y)
                    cr.line_to (self.lonToX (polygon[i+1][1], 600, bbox), self.latToY (polygon[i+1][0], 600, bbox))
                    cr.stroke ()

class GSHHGLoader:
    def str32bit (flag):
        flag = bin (flag)[2:]
        if len (flag) < 32:
            flag = (32 - len (flag)) * "0" + flag
        return flag

    def load (self, resolution = 'crude', bbox = [(90, -90), (180, -180)]):
        this_dir, this_fn = os.path.split (__file__)
        
        if resolution == 'low':
            filename = this_dir + '/../data/gshhg/low.bin'
        elif resolution == 'intermediate':
            filename = this_dir + '/../data/gshhg/intermediate.bin'
        elif resolution == 'high':
            filename = this_dir + '/../data/gshhg/high.bin'
        elif resolution == 'crude':
            filename = this_dir + '/../data/gshhg/crude.bin'
        else:
            filename = this_dir + '/../data/gshhg/crude.bin'

        polygons = []
        file = open (filename, "rb")
        
        if True:
            header = file.read (44)

            while len (header) == 44:
                header = struct.unpack (">11i", header)
                idnum = header[0]
                npti = header[1]
                flag = header[2]
                flag_str = GSHHGLoader.str32bit (flag)
                poligono = []
                if int (flag_str[24:32], 2) == 1:
                    for n in range (0, npti):
                        pto = file.read (8)
                        pto = struct.unpack (">2i", pto)
                        lon = pto[0]*10**-6
                        lat = pto[1]*10**-6
                        if lon > 180.0: 
                            lon = 360.0 - lon
                        #if lat < bbox[0][0] and lat > bbox[0][1] and lon < bbox[1][0] and lon > bbox[1][1]:
                        poligono.append ((lat,lon))
                        #else:
                        #    if len (poligono) > 0:
                        #        polygons.append (poligono)
                        #    poligono = []

                    if len (poligono) > 0:
                        polygons.append (poligono)
                else:
                    file.read (8 * npti)
                header = file.read (44)
        
        
        file.close ()
        return PolygonalMap (polygons)


class MapWidget (Gtk.DrawingArea):
    def __init__ (self):
        Gtk.DrawingArea.__init__(self)
        self.connect ('draw', self.draw)
        self.bbox = [(90, -90), (180, -180)]
        self.zoom = 0
        self.center = (0.0, 0.0)
        
        self.map = GSHHGLoader ().load ()

    def setCenter (self, lat, lon):
        pass

    def setZoom (self, zoom):
        pass

    def draw (self, widget, cr):
        cr.set_source_rgb (1, 1, 1)
        cr.paint()
        
        self.map.draw (widget, cr, self.bbox)