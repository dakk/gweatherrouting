# -*- coding: utf-8 -*-
# Copyright (C) 2017-2024 Davide Gessa
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
    def __init__(self, path, ctype, settingsManager, metadata=None, enabled=True):
        self.path = path
        self.ctype = ctype
        self.enabled = enabled
        self.metadata = metadata
        self.settingsManager = settingsManager

    def onRegister(self, onTickHandler=None):
        """Called when the dataset is registered on the software"""
        return

    def getBoundingWKTOfCoords(self, p1lat, p1lon, p2lat, p2lon):
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

    def getBoundingWKT(self, gpsmap):
        p1, p2 = gpsmap.get_bbox()

        p1lat, p1lon = p1.get_degrees()
        p2lat, p2lon = p2.get_degrees()

        return self.getBoundingWKTOfCoords(p1lat, p1lon, p2lat, p2lon)

    def getBoundingGeometry(self, gpsmap):
        wktbb = self.getBoundingWKT(gpsmap)
        return ogr.CreateGeometryFromWkt(wktbb)
