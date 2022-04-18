# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
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
from ..style import *
from weatherrouting import utils

gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.2')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap

class ToolsMapLayer (GObject.GObject, OsmGpsMap.MapLayer):
    def __init__ (self):
        GObject.GObject.__init__ (self)
        
        self.measuring = False 
        self.measureStart = None
        self.mousePosition = None


    def enableMeasure(self, lat, lon):
        self.measuring = True
        self.measureStart = (float(lat), float(lon))

    def onMouseMove(self, lat, lon, x, y):
        self.mousePosition = (float(lat), float(lon), x, y)

        return self.measuring

    def do_draw (self, gpsmap, cr):
        if self.measuring:
            x, y = gpsmap.convert_geographic_to_screen (OsmGpsMap.MapPoint.new_degrees (self.measureStart[0], self.measureStart[1]))
            x1, y1 = gpsmap.convert_geographic_to_screen (OsmGpsMap.MapPoint.new_degrees (self.mousePosition[0], self.mousePosition[1]))
            Style.Measure.Line.apply(cr)
            cr.move_to(x, y)
            cr.line_to(x1, y1)
            cr.stroke()

            # Calculate distance and bearing
            (d, r) = utils.ortodromic(self.measureStart[0], self.measureStart[1], self.mousePosition[0], self.mousePosition[1])

            # Draw info
            Style.Measure.Font.apply(cr)
            cr.move_to(x1+15, y1)
            cr.show_text('Dist: %.2f nm' % d)
            cr.move_to(x1+15, y1+10)
            cr.show_text('HDG: %.2f°' % math.degrees(r))
            cr.stroke()

    def do_render (self, gpsmap):
        pass

    def do_busy (self):
        return False

    def do_button_press (self, gpsmap, gdkeventbutton):
        if self.measuring and gdkeventbutton.button == 1:
            self.measuring = False
            self.measureStart = None
            return True

        return False

GObject.type_register (ToolsMapLayer)