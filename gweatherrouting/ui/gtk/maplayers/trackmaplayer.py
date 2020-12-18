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

    def draw_boat(self, pos, course, speed):
        pass

    def do_draw (self, gpsmap, cr):
        for tr in self.trackManager.routings:
            if not tr.visible:
                continue 

            prevx = None
            prevy = None 
            i = 0

            for p in tr.waypoints:
                i += 1
                x, y = gpsmap.convert_geographic_to_screen (OsmGpsMap.MapPoint.new_degrees (p[0], p[1]))

                if prevx == None:
                    cr.set_source_rgba (1, 1, 1, 0.8)
                    cr.set_font_size(13)
                    cr.move_to(x+10, y)
                    cr.show_text(tr.name)
                    cr.stroke()

                
                cr.set_source_rgba (1, 1, 1, 0.8)
                cr.set_font_size(13)
                cr.move_to(x-4, y+18)
                # cr.show_text(str(p[2]))
                # cr.stroke()


                if prevx != None and prevy != None:
                    cr.set_line_width (3)
                    cr.set_source_rgba (1, 0, 0, 0.8)

                    cr.move_to (prevx, prevy)
                    cr.line_to (x, y)
                    cr.stroke()

                cr.set_line_width (2)
                cr.set_source_rgba (1, 1, 1, 0.8)
                cr.arc(x, y, 5, 0, 2 * math.pi)
                cr.stroke()

                prevx = x
                prevy = y

        for tr in self.trackManager.tracks:
            if not tr.visible:
                continue 

            active = False
            if self.trackManager.activeTrack and self.trackManager.activeTrack.name == tr.name:
                active = True

            prevx = None
            prevy = None 
            i = 0

            for p in tr.waypoints:
                i += 1
                x, y = gpsmap.convert_geographic_to_screen (OsmGpsMap.MapPoint.new_degrees (p[0], p[1]))

                if prevx == None:
                    if active:
                        cr.set_source_rgba (1, 1, 1, 0.8)
                    else:
                        cr.set_source_rgba (1, 1, 1, 0.4)
                    cr.set_font_size(13)
                    cr.move_to(x-10, y-10)
                    cr.show_text(tr.name)
                    cr.stroke()

                
                if active:
                    cr.set_source_rgba (1, 1, 1, 0.8)
                else:
                    cr.set_source_rgba (1, 1, 1, 0.4)
                cr.set_font_size(13)
                cr.move_to(x-4, y+18)
                cr.show_text(str(i))
                cr.stroke()



                if prevx != None and prevy != None:
                    if active:
                        cr.set_line_width (2)
                        cr.set_source_rgba (1, 1, 1, 0.8)
                    else:
                        cr.set_line_width (2)
                        cr.set_source_rgba (1, 1, 1, 0.4)

                    cr.move_to (prevx, prevy)
                    cr.line_to (x, y)
                    cr.stroke()

                if active:
                    cr.set_line_width (2)
                    cr.set_source_rgba (1, 1, 1, 0.8)
                else:
                    cr.set_line_width (2)
                    cr.set_source_rgba (1, 1, 1, 0.4)
                cr.arc(x, y, 5, 0, 2 * math.pi)
                cr.stroke()

                prevx = x
                prevy = y

    def do_render (self, gpsmap):
        pass

    def do_busy (self):
        return False

    def do_button_press (self, gpsmap, gdkeventbutton):
        return False

GObject.type_register (TrackMapLayer)