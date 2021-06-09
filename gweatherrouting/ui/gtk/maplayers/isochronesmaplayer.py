# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
"""

import gi
import math
from ..style import Style

gi.require_version("Gtk", "3.0")
gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap


class IsochronesMapLayer(GObject.GObject, OsmGpsMap.MapLayer):
    def __init__(self):
        GObject.GObject.__init__(self)
        self.isochrones = []
        self.path = []

    def setIsochrones(self, isoc, path):
        self.isochrones = isoc
        self.path = path

    def do_draw(self, gpsmap, cr):
        cr.set_source_rgba(0, 0, 0, 0.6)
        cr.set_line_width(1)

        # Render partial routing
        prevx = None
        prevy = None
        i = 0

        for p in self.path:
            i += 1
            x, y = gpsmap.convert_geographic_to_screen(
                OsmGpsMap.MapPoint.new_degrees(p[0], p[1])
            )

            if prevx == None:
                Style.Track.RoutingTrackFont.apply(cr)
                cr.move_to(x + 10, y)
                cr.stroke()

            # Style.Track.RoutingTrackFont.apply(cr)
            cr.move_to(x - 4, y + 18)
            # cr.show_text(str(p[2]))
            # cr.stroke()

            if prevx != None and prevy != None:
                Style.Track.RoutingTrack.apply(cr)

                cr.move_to(prevx, prevy)
                cr.line_to(x, y)
                cr.stroke()

            Style.Track.RoutingTrackCircle.apply(cr)
            cr.arc(x, y, 5, 0, 2 * math.pi)
            cr.stroke()

            prevx = x
            prevy = y

        # Render isochrones
        i = 0
        for ic in self.isochrones:
            # cr.set_source_rgba (0,0,0, 1.0 - i / len (self.isochrones))

            prev = None
            for icpoint in ic:
                cr.set_source_rgba(0, 0, 0, 0.2)
                cr.set_line_width(1)

                x, y = gpsmap.convert_geographic_to_screen(
                    OsmGpsMap.MapPoint.new_degrees(icpoint[0], icpoint[1])
                )

                if prev:
                    cr.move_to(prev[0], prev[1])
                    cr.line_to(x, y)
                    cr.stroke()

                if i > 0:
                    cr.set_source_rgba(1, 0, 0, 0.8)
                    cr.set_line_width(0.6)
                    xa, ya = gpsmap.convert_geographic_to_screen(
                        OsmGpsMap.MapPoint.new_degrees(
                            self.isochrones[i - 1][icpoint[2]][0],
                            self.isochrones[i - 1][icpoint[2]][1],
                        )
                    )
                    cr.move_to(xa, ya)
                    cr.line_to(x, y)
                    cr.stroke()

                prev = (x, y, icpoint)

            # Close the path
            # cr.set_source_rgba (0,0,0,0.3)
            # cr.set_line_width (1)
            # cr.move_to (prev[0], prev[1])
            # x, y = gpsmap.convert_geographic_to_screen (OsmGpsMap.MapPoint.new_degrees (ic[0][0], ic[0][1]))
            # # cr.line_to (x, y)
            # cr.move_to (x, y)
            # cr.stroke ()

            i += 1

    def do_render(self, gpsmap):
        pass

    def do_busy(self):
        return False

    def do_button_press(self, gpsmap, gdkeventbutton):
        return False


GObject.type_register(IsochronesMapLayer)
