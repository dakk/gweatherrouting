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
from osgeo import ogr


class ChartLayer:
    def __init__(self, path, ctype, settings_manager, metadata=None, enabled=True):
        self.path = path
        self.ctype = ctype
        self.enabled = enabled
        self.metadata = metadata
        self.settings_manager = settings_manager

    def on_register(self, on_tick_handler=None):
        """Called when the dataset is registered on the software"""
        return

    def get_bounding_wkt_of_coords(self, p1lat, p1lon, p2lat, p2lon):
        return "POLYGON((%f %f,%f %f,%f %f,%f %f,%f %f))" % (
            p1lon,
            p1lat,
            p1lon,
            p2lat,
            p2lon,
            p2lat,
            p2lon,
            p1lat,
            p1lon,
            p1lat,
        )

    def get_bounding_wkt(self, gpsmap):
        p1, p2 = gpsmap.get_bbox()

        p1lat, p1lon = p1.get_degrees()
        p2lat, p2lon = p2.get_degrees()

        return self.get_bounding_wkt_of_coords(p1lat, p1lon, p2lat, p2lon)

    def get_bounding_geometry(self, gpsmap):
        wktbb = self.get_bounding_wkt(gpsmap)
        return ogr.CreateGeometryFromWkt(wktbb)

    def do_draw(self, gpsmap, cr):
        pass

    def do_render(self, gpsmap):
        pass

    def do_busy(self):
        return False

    def do_button_press(self, gpsmap, gdkeventbutton):
        return False
