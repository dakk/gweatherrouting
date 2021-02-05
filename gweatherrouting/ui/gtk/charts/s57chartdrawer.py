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
import math
import json
from osgeo import ogr, osr, gdal

gi.require_version("Gtk", "3.0")
gi.require_version("OsmGpsMap", "1.0")

from gi.repository import Gtk, Gio, GObject, OsmGpsMap
from .vectorchartdrawer import VectorChartDrawer


class S57ChartDrawer(VectorChartDrawer):
    def backgroundRender(self, gpsmap, cr):
        pass

    def featureRender(self, gpsmap, cr, feat, layer):
        geom = feat.GetGeometryRef()