# -*- coding: utf-8 -*-
# Copyright (C) 2017-2025 Davide Gessa
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
import math
from typing import Tuple

import cairo
import gi

gi.require_version("Gtk", "3.0")
# try:
#     gi.require_version("OsmGpsMap", "1.2")
# except:
#     gi.require_version("OsmGpsMap", "1.0")

from gi.repository import GObject, OsmGpsMap

from gweatherrouting.core import utils
from gweatherrouting.gtk.style import Style


class ToolsMapLayer(GObject.GObject, OsmGpsMap.MapLayer):
    def __init__(self, core):
        GObject.GObject.__init__(self)

        self.measuring = False
        self.measureStart = None
        self.mousePosition: Tuple[float, float, int, int] = (0.0, 0.0, 0, 0)

        self.dashboard = False
        self.compass = False
        self.boat_info = None

        self.gps = None

        self.mob = False
        self.mobPosition = None

        self.poiMoving = False
        self.poiMovingCallback = None

        # TODO: need to create a new class for data
        core.connect("data", self.data_handler)

    def toggle_mob(self, lat, lon):
        if self.mob:
            self.mob = False
            self.mobPosition = None
        else:
            self.mob = True
            self.mobPosition = (float(lat), float(lon))

    def data_handler(self, bi):
        self.boat_info = bi

    def gps_clear(self):
        self.gps = None

    def gps_add(self, lat, lon, hdg=0, speed=None):
        self.gps = (float(lat), float(lon), hdg, speed)

    def enable_poi_moving(self, callback):
        self.poiMoving = True
        self.poiMovingCallback = callback

    def enable_measure(self, lat, lon):
        self.measuring = True
        self.measureStart = (float(lat), float(lon))

    def on_mouse_move(self, lat, lon, x, y):
        self.mousePosition = (float(lat), float(lon), x, y)
        return self.measuring or self.poiMoving

    def set_compass_visible(self, v):
        self.compass = v

    def set_dashboard_visible(self, v):
        self.dashboard = v

    def do_draw(self, gpsmap, cr):  # noqa: C901
        if self.poiMoving:
            # Draw a black dot with a red circle around
            cr.move_to(self.mousePosition[2], self.mousePosition[3])
            cr.set_source_rgb(0, 0, 0)
            cr.arc(self.mousePosition[2], self.mousePosition[3], 1, 0, 2 * math.pi)
            cr.stroke()
            cr.set_source_rgb(1, 0, 0)
            cr.arc(self.mousePosition[2], self.mousePosition[3], 16, 0, 2 * math.pi)
            cr.stroke()

        if self.dashboard and self.boat_info:
            pass

        if self.mob and self.mobPosition:
            lat, lon = self.mobPosition
            x, y = gpsmap.convert_geographic_to_screen(
                OsmGpsMap.MapPoint.new_degrees(lat, lon)
            )

            Style.Track.Mob.apply(cr)
            cr.arc(x, y, 5, 0, 2 * math.pi)
            cr.stroke()

        if self.compass and self.gps:
            x, y = gpsmap.convert_geographic_to_screen(
                OsmGpsMap.MapPoint.new_degrees(self.gps[0], self.gps[1])
            )

            Style.Compass.Font.apply(cr)

            for i in list(range(360))[::45]:
                ii = math.radians(i)
                cr.move_to(x + math.sin(ii) * 80.0, y - math.cos(ii) * 80.0)
                cr.show_text(str(i) + "°")

            for i in list(range(360))[::45]:
                radius = 100
                angle1 = math.radians(i - 5)
                angle2 = math.radians(i + 5)

                cr.set_source_rgba(1, 0.2, 0.2, 0.4)
                cr.move_to(x, y)
                cr.set_line_width(1.0)
                cr.arc(x, y, radius, angle1, angle2)
                cr.fill()

        if self.gps:
            x, y = gpsmap.convert_geographic_to_screen(
                OsmGpsMap.MapPoint.new_degrees(self.gps[0], self.gps[1])
            )
            hdg = math.radians(self.gps[2])
            r = 6
            r2 = 12

            if r2 > 0:
                cr.set_line_width(1.5)
                cr.set_source_rgba(0.75, 0.75, 0.75, 0.4)
                cr.arc(x, y, r2, 0, 2 * math.pi)
                cr.fill()
                cr.set_source_rgba(0.55, 0.55, 0.55, 0.4)
                cr.arc(x, y, r2, 0, 2 * math.pi)
                cr.stroke()

            if r > 0:
                cr.move_to(x - r * math.cos(hdg), y - r * math.sin(hdg))
                cr.line_to(x + 3 * r * math.sin(hdg), y - 3 * r * math.cos(hdg))
                cr.line_to(x + r * math.cos(hdg), y + r * math.sin(hdg))
                cr.close_path()

                cr.set_source_rgba(0.3, 0.3, 1.0, 0.5)
                cr.fill_preserve()

                cr.set_line_width(1.0)
                cr.set_source_rgba(0.0, 0.0, 0.0, 0.5)
                cr.stroke()

                pat = cairo.RadialGradient(x - (r / 5), y - (r / 5), (r / 5), x, y, r)
                pat.add_color_stop_rgba(0, 1, 1, 1, 1.0)
                pat.add_color_stop_rgba(1, 0, 0, 1, 1.0)
                cr.set_source(pat)
                cr.arc(x, y, r, 0, 2 * math.pi)
                cr.fill()

                cr.set_line_width(1.0)
                cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
                cr.arc(x, y, r, 0, 2 * math.pi)
                cr.stroke()

        if self.measuring:
            if self.measureStart is None:
                return

            x, y = gpsmap.convert_geographic_to_screen(
                OsmGpsMap.MapPoint.new_degrees(
                    self.measureStart[0], self.measureStart[1]
                )
            )
            x1, y1 = gpsmap.convert_geographic_to_screen(
                OsmGpsMap.MapPoint.new_degrees(
                    self.mousePosition[0], self.mousePosition[1]
                )
            )
            Style.Measure.Line.apply(cr)
            cr.move_to(x, y)
            cr.line_to(x1, y1)
            cr.stroke()

            d = utils.point_distance(
                self.measureStart[0],
                self.measureStart[1],
                self.mousePosition[0],
                self.mousePosition[1],
                "nm",
            )

            # Calculate bearing
            (_, r) = utils.ortodromic(
                self.measureStart[0],
                self.measureStart[1],
                self.mousePosition[0],
                self.mousePosition[1],
            )

            # Draw info
            Style.Measure.Font.apply(cr)
            cr.move_to(x1 + 15, y1)
            cr.show_text("Dist: %.2f nm" % d)
            cr.move_to(x1 + 15, y1 + 10)
            cr.show_text("HDG: %.2f°" % math.degrees(r))
            cr.stroke()

    def do_render(self, gpsmap):
        pass

    def do_busy(self):
        return False

    def do_button_press(self, gpsmap, gdkeventbutton):
        if self.measuring and gdkeventbutton.button == 1:
            self.measuring = False
            self.measureStart = None
            return True

        if self.poiMoving and gdkeventbutton.button == 1:
            self.poiMoving = False
            if self.poiMovingCallback:
                self.poiMovingCallback(self.mousePosition[0], self.mousePosition[1])
            return True

        return False


GObject.type_register(ToolsMapLayer)
