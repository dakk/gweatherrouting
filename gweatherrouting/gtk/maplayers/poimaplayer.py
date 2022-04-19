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

gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.2')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap

class POIMapLayer (GObject.GObject, OsmGpsMap.MapLayer):
    def __init__ (self, poiManager):
        GObject.GObject.__init__ (self)
        self.poiManager = poiManager


    def do_draw (self, gpsmap, cr):
        for tr in self.poiManager.pois:
            if not tr.visible:
                continue 

            x, y = gpsmap.convert_geographic_to_screen (OsmGpsMap.MapPoint.new_degrees (tr.position[0], tr.position[1]))

            Style.Poi.Quad.apply(cr)
            cr.rectangle(x+3, y-5, len(tr.name) * 6.7, 12)
            cr.stroke_preserve()
            Style.Poi.QuadInt.apply(cr)
            cr.fill()

            Style.Poi.Font.apply(cr)
            cr.move_to(x+5, y+5)
            cr.show_text(tr.name)
            cr.stroke()


            Style.Poi.Dot.apply(cr)
            cr.arc(x, y, 2, 0, 2 * math.pi)
            cr.fill()

            # Triangle
            # cr.move_to(x-5, y-5)
            # cr.line_to(x,y+5)
            # cr.move_to(x+5, y-5)
            # cr.line_to(x,y+5)
            # cr.move_to(x-5, y-5)
            # cr.line_to(x+5,y-5)
            # cr.stroke()

    def do_render (self, gpsmap):
        pass

    def do_busy (self):
        return False

    def do_button_press (self, gpsmap, gdkeventbutton):
        return False

GObject.type_register (POIMapLayer)