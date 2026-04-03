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

from .vectorchartdrawer import VectorChartDrawer
from gweatherrouting.gtk.widgets.mapwidget import MapPoint

class S57ChartDrawer(VectorChartDrawer):
    def draw(self, gpsmap, cr, vector_file, bounding):
        width = float(gpsmap.get_allocated_width())
        height = float(gpsmap.get_allocated_height())

        #cr.rectangle(0, 0, width, height)
        #cr.fill()

        # Loop over each layer of the map
        for i in range(vector_file.GetLayerCount()):
            layer = vector_file.GetLayerByIndex(i)
            layer_name = layer.GetName()
            layer_defn = layer.GetLayerDefn()
            geom_field_count = layer_defn.GetGeomFieldCount()

            # Skip non geometry layers
            if geom_field_count == 0:
                print(f"Skip non geometry layer {layer_name}")
                continue

            if layer_name not in ("LNDARE", "DEPARE"):
                continue

            layer.SetSpatialFilter(bounding)
            layer.ResetReading()

            feature = layer.GetNextFeature()
            while feature is not None:
                l_geom = feature.GetGeometryRef()
                if l_geom is not None:
                    self._render_polygon_geometry(gpsmap, cr, l_geom, layer_name, feature)
                feature = layer.GetNextFeature()

    def _render_polygon_geometry(self, gpsmap, cr, l_geom, layer_name, feature):
        l_geom_name = l_geom.GetGeometryName()

        # Define layer color
        if layer_name == "LNDARE":
            cr.set_source_rgba(1.0, 0.0, 0.0, 1.0)
        elif layer_name == "DEPARE":
            cr.set_source_rgba(0.0, 1.0, 0.0, 1.0)
        else:
            print("ERROR: layer not handled")
            return

        if l_geom_name == "POLYGON":
            self._draw_polygon(gpsmap, cr, l_geom)
        elif l_geom_name == "MULTYPOLYGON":
            for i in range(l_geom.GetGeometryCount()):
                poly = l_geom.GetGeometryRef(i)
                self._draw_polygon(gpsmap, cr, poly)


    def _draw_polygon(self, gpsmap, cr, polygon):
        ring = polygon.GetGeometryRef(0)
        if ring is None or ring.GetPointCount == 0:
            return

        for idx in range(ring.GetPointCount()):
            pt = ring.GetPoint(idx)
            lon = pt[0]
            lat = pt[1]
            x,y = gpsmap.convert_geographic_to_screen(MapPoint.new_degrees(lat,lon))

            if idx==0:
                cr.move_to(x,y)
            else:
                cr.line_to(x,y)

        cr.close_path()
        cr.fill()
