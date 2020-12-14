# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
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
import colorsys
import math

gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap

class TrackMapLayer (GObject.GObject, OsmGpsMap.MapLayer):
    def __init__ (self, trackManager):
        GObject.GObject.__init__ (self)
        self.trackManager = trackManager


    def do_draw (self, gpsmap, cr):


        for tr in self.trackManager.tracks:
            if not tr.visible:
                continue 

            active = False
            if self.trackManager.activeTrack().name == tr.name:
                active = True

            prevx = None
            prevy = None 

            for p in tr.waypoints:
                x, y = gpsmap.convert_geographic_to_screen (OsmGpsMap.MapPoint.new_degrees (p[0], p[1]))

                if prevx == None:
                    cr.set_source_rgba (1, 1, 1, 0.4)
                    cr.set_font_size(13)
                    cr.move_to(x-10, y-10)
                    cr.show_text(tr.name)
                    cr.stroke()


                if prevx != None and prevy != None:
                    if active:
                        cr.set_line_width (3)
                    else:
                        cr.set_line_width (2)

                    cr.set_source_rgba (1, 1, 1, 0.4)
                    cr.move_to (prevx, prevy)
                    cr.line_to (x, y)
                    cr.stroke()

                cr.set_line_width (2)
                cr.set_source_rgba (1, 1, 1, 0.4)
                cr.arc(x, y, 5, 0, 2 * math.pi)
                cr.stroke()

                prevx = x
                prevy = y


            
        # p1, p2 = gpsmap.get_bbox ()

        # p1lat, p1lon = p1.get_degrees ()
        # p2lat, p2lon = p2.get_degrees ()

        # width = float (gpsmap.get_allocated_width ())
        # height = float (gpsmap.get_allocated_height ())

        # cr.set_line_width (1)
        # cr.set_source_rgb (1,0,0)
        # #print (p1lat, p1lon, p2lat, p2lon)

        # bounds = ((min (p1lat,p2lat), min (p1lon, p2lon)), (max (p1lat,p2lat), max (p1lon, p2lon)))
        # data = self.gribManager.getWind (self.time, bounds)


        # if not data or len(data) == 0 or len(data[0]) == 0:
        #     return

        # x = 0
        # y = 0
        # sep = 1

        # sep = 1 #math.ceil (len (data[0]) / 60)
        # cr.set_line_width (1.5 / (math.ceil (len (data[0]) / 60)))

        # cr.set_line_width (1)

        # for x in data[::sep]:
        #     for y in x[::sep]:
        #         xx, yy = gpsmap.convert_geographic_to_screen (OsmGpsMap.MapPoint.new_degrees (y[2][0], y[2][1]))
        #         self.drawWindArrow (cr, xx, yy, y[0], y[1])


    def do_render (self, gpsmap):
        pass

    def do_busy (self):
        return False

    def do_button_press (self, gpsmap, gdkeventbutton):
        return False

GObject.type_register (TrackMapLayer)