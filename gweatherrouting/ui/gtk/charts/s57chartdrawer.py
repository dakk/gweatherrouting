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