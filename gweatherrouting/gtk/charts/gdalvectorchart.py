# -*- coding: utf-8 -*-
# Copyright (C) 2017-2026 Davide Gessa
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

from gweatherrouting.core.enccharts import chart_scale_visible
from gweatherrouting.gtk.charts.cm93datasource import CM93DataSource
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

        self._coverage: list[ogr.Geometry] = []
        self._native_scale = 0
        if drv_name == "S57":
            self._load_enc_metadata()
        self._coverage_envelopes = tuple(g.GetEnvelope() for g in self._coverage)

    def _load_enc_metadata(self):
        identification = self.vector_file.GetLayerByName("DSID")
        if identification:
            identification.ResetReading()
            feature = identification.GetNextFeature()
            if feature and feature.GetFieldIndex("DSPM_CSCL") >= 0:
                self._native_scale = feature.GetField("DSPM_CSCL") or 0
        self._coverage = self.read_coverage(self.vector_file)

    @staticmethod
    def read_coverage(vector_file):
        """Read actual ENC coverage, preserving holes and no-coverage panels."""
        coverage: list[ogr.Geometry] = []
        exclusions: list[ogr.Geometry] = []
        layer = vector_file.GetLayerByName("M_COVR")
        if layer is None:
            return coverage
        layer.ResetReading()
        for feature in layer:
            geometry = feature.GetGeometryRef()
            if geometry is not None:
                geometry = geometry.Clone()
                if not geometry.IsValid():
                    geometry = geometry.MakeValid()
                if feature.GetField("CATCOV") == 1:
                    coverage.append(geometry)
                elif feature.GetField("CATCOV") == 2:
                    exclusions.append(geometry)
        for exclusion in exclusions:
            coverage = [g.Difference(exclusion) for g in coverage]
        return [g for g in coverage if g is not None and not g.IsEmpty()]

    def covers_point(self, lat, lon, scale):
        if not chart_scale_visible(self._native_scale, scale):
            return False
        if isinstance(self.vector_file, CM93DataSource):
            level = self.vector_file.get_scale_for_zoom(scale)
            return bool(self.vector_file.get_cells_for_bbox(lat, lon, lat, lon, level))
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint_2D(lon, lat)
        return any(geometry.Intersects(point) for geometry in self._coverage)

    def on_register(self, on_tick_handler=None):
        return True

    def do_draw(self, gpsmap, cr):
        bounding_geometry = self.get_bounding_geometry(gpsmap)
        if isinstance(self.drawer, S57ChartDrawer):
            if not chart_scale_visible(self._native_scale, gpsmap.get_scale()):
                return
            # Avoid scanning offscreen charts, including their attribute layers.
            if self._coverage and not any(
                g.Intersects(bounding_geometry) for g in self._coverage
            ):
                return
        self.drawer.draw(gpsmap, cr, self.vector_file, bounding_geometry)

    def do_render(self, gpsmap):
        pass

    def do_busy(self):
        return False

    def query_point(self, lat, lon, tolerance=0.001):
        """Query vector chart features near a given lat/lon.

        Returns a list of dicts with layer name, geometry type, and attributes.
        """
        if isinstance(self.vector_file, CM93DataSource):
            return self.vector_file.query_point(lat, lon, tolerance)

        results = []
        bbox = ogr.CreateGeometryFromWkt(
            self.get_bounding_wkt_of_coords(
                lat - tolerance, lon - tolerance, lat + tolerance, lon + tolerance
            )
        )

        for i in range(self.vector_file.GetLayerCount()):
            layer = self.vector_file.GetLayerByIndex(i)
            layer.SetSpatialFilter(bbox)
            layer.ResetReading()

            feat = layer.GetNextFeature()
            while feat is not None:
                attrs = {}
                for j in range(feat.GetFieldCount()):
                    fd = feat.GetFieldDefnRef(j)
                    val = feat.GetFieldAsString(j)
                    if val:
                        attrs[fd.GetNameRef()] = val

                geom = feat.GetGeometryRef()
                geom_type = geom.GetGeometryName() if geom else "Unknown"

                results.append(
                    {
                        "layer": layer.GetName(),
                        "geometry": geom_type,
                        "attributes": attrs,
                    }
                )
                feat = layer.GetNextFeature()

        return results

    def do_button_press(self, gpsmap, gdkeventbutton):
        return False
