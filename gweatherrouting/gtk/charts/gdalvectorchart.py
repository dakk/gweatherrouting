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

from gweatherrouting.gtk.charts.cm93driver import CM93Driver
from gweatherrouting.gtk.charts.vectordrawer.osmchartdrawer import OSMChartDrawer

from .chartlayer import ChartLayer
from .vectordrawer import (
    CM93ChartDrawer,
    S57ChartDrawer,
    SimpleChartDrawer,
    VectorChartDrawer,
)


class GDALVectorChart(ChartLayer):
    def __init__(self, path, settings_manager, metadata=None, enabled=True):
        super().__init__(path, "vector", settings_manager, metadata, enabled)

        self.drawer: VectorChartDrawer

        if path.find("geojson") != -1:
            drv_name = "GeoJSON"
            self.drawer = SimpleChartDrawer(settings_manager)
        elif path.find("shp") != -1:
            drv_name = "ESRI Shapefile"
            self.drawer = SimpleChartDrawer(settings_manager)
        elif path.find(".000") != -1:
            drv_name = "S57"
            self.drawer = S57ChartDrawer(settings_manager)
        elif path.find("Cm93") != -1:
            drv_name = "CM93"
            self.drawer = CM93ChartDrawer(settings_manager)
        elif path.find("osm") != -1 or path.find("pbf") != -1:
            drv_name = "OSM"
            self.drawer = OSMChartDrawer(self.settings_manager)
        else:
            raise Exception("Invalid format")

        if drv_name == "CM93":
            drv = CM93Driver()
        else:
            drv = ogr.GetDriverByName(drv_name)
        self.vector_file = drv.Open(path)

        if self.vector_file is None:
            raise Exception("Unable to open vector map %s" % path)

    def on_register(self, on_tick_handler=None):
        pass

    def do_draw(self, gpsmap, cr):
        bounding_geometry = self.get_bounding_geometry(gpsmap)
        self.drawer.draw(gpsmap, cr, self.vector_file, bounding_geometry)

    def do_render(self, gpsmap):
        pass

    def do_busy(self):
        return False

    def do_button_press(self, gpsmap, gdkeventbutton):
        return False
