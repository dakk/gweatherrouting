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
    def __init__ (self, resolution, bbox, polygons):
        self.resolution = resolution
        self.bbox = bbox
        self.polygons = polygons

    def lonToX (self, lon, width):
        s = float (abs (self.bbox[1][0]) + abs (self.bbox[1][1]))
        return width - ((lon + 180.0) * width / s)

    def latToY (self, lat, height):
        s = float (abs (self.bbox[0][0]) + abs (self.bbox[0][1]))
        return height - ((lat + 90.0) * height / s)

    def draw (self, widget, cr):
        width = float (widget.get_allocated_width ())
        height = float (widget.get_allocated_height ())

        cr.set_line_width (0.5)

        cr.set_source_rgb(1,0,0)
        cr.move_to (self.lonToX (39., width), self.latToY (-9., height))
        cr.line_to (self.lonToX (-9., width), self.latToY (39., height))
        cr.stroke ()

        cr.set_source_rgb(0,0,0)
        for polygon in self.polygons:
            #print (len (polygon))
            for i in range (0, len (polygon)):
                x = self.lonToX (polygon[i][1], width)
                y = self.latToY (polygon[i][0], height)

                if x < 0.0 or x > width or y < 0.0 or y > height:
                    continue
                
                if i == len (polygon) - 1:
                    nextpol = polygon[0]
                else:
                    nextpol = polygon[i+1]

                if (polygon[i][1] > 170. and nextpol[1] < -170.) or (polygon[i][1] < -170. and nextpol[1] > 170.):
                    continue
                    
                if i == len (polygon) - 1:
                    cr.move_to (x, y)
                    cr.line_to (self.lonToX (nextpol[1], width), self.latToY (nextpol[0], height))
                    cr.stroke ()
                else:
                    cr.move_to (x, y)
                    cr.line_to (self.lonToX (nextpol[1], width), self.latToY (nextpol[0], height))
                    cr.stroke ()


class GSHHGLoader:
    def str32bit (flag):
        flag = bin (flag)[2:]
        if len (flag) < 32:
            flag = (32 - len (flag)) * "0" + flag
        return flag

    def load (self, resolution = 'low', bbox = [(90, -90), (180, -180)]):
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
            filename = this_dir + '/../data/gshhg/low.bin'

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
                        lon = pto[0] * 10 ** -6
                        lat = pto[1] * 10 ** -6

                        lon = 360 - lon
                        if lon > 180.0: 
                           lon = lon - 360
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
        return PolygonalMap (resolution, bbox, polygons)


class MapWidget (Gtk.DrawingArea):
    def __init__ (self):
        Gtk.DrawingArea.__init__(self)
        self.connect ('draw', self.draw)
        self.bbox = [(90, -90), (180, -180)]
        self.zoom = 1
        self.center = (39.221630, 9.217588)
        
        self.map = GSHHGLoader ().load ()
        self._updateBoundingBox ()

    def _updateBoundingBox (self):
        scart = (90. / self.zoom, 180. / self.zoom)

        self.bbox = [
            (self.center[0] + scart[0], self.center[0] - scart[0]), 
            (self.center[1] + scart[1], self.center[1] - scart[1])
        ]

        if self.zoom <= 3. and (self.map.resolution != 'crude' or self.map.bbox != self.bbox):
            self.map = GSHHGLoader ().load (resolution='crude', bbox=self.bbox)
        elif self.zoom <= 7. and (self.map.resolution != 'low' or self.map.bbox != self.bbox):
            self.map = GSHHGLoader ().load (resolution='low', bbox=self.bbox)
        elif self.zoom <= 10. and (self.map.resolution != 'intermediate' or self.map.bbox != self.bbox):
            self.map = GSHHGLoader ().load (resolution='intermediate', bbox=self.bbox)
        else:
            self.map = GSHHGLoader ().load (resolution='intermediate', bbox=self.bbox)

        self.queue_draw()
        print (self.bbox)

    def setCenter (self, lat, lon):
        self.center = (lat, lon)
        self._updateBoundingBox ()

    def setZoom (self, zoom):
        self.zoom = zoom
        print (zoom)
        self._updateBoundingBox ()

    def draw (self, widget, cr):
        cr.set_source_rgb (1, 1, 1)
        cr.paint()
        
        self.map.draw (widget, cr)