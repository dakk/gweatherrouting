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
import cairo

SUPPORTED_LAYERS = {
                    "polygon" : ("LNDARE", "DEPARE","OBSTRN", "UWTROC"),
                    "line": ("COALNE", "DEPCNT"), 
                    "point": ("SOUNDG", "LIGHTS", "BOYLAT", "WRECKS")
                   }
SAFE_DEPTH = 5

class S57ChartDrawer(VectorChartDrawer):
    def draw(self, gpsmap, cr, vector_file, bounding):
        # NOTE: Actually to ensure proper visualization the file is read three
        # times. This aspect could be improved

        # Draw polygon layers
        for i in range(vector_file.GetLayerCount()):
            layer = vector_file.GetLayerByIndex(i)
            layer_name = layer.GetName()
            layer_defn = layer.GetLayerDefn()
            geom_field_count = layer_defn.GetGeomFieldCount()
            if geom_field_count == 0:
                continue
            if layer_name in SUPPORTED_LAYERS["polygon"]:
                self._render_layer(layer, gpsmap, cr, layer_name, bounding)

        # Draw line layers
        for i in range(vector_file.GetLayerCount()):
            layer = vector_file.GetLayerByIndex(i)
            layer_name = layer.GetName()
            layer_defn = layer.GetLayerDefn()
            geom_field_count = layer_defn.GetGeomFieldCount()
            if geom_field_count == 0:
                continue
            if layer_name in SUPPORTED_LAYERS["line"]:
                self._render_layer(layer, gpsmap, cr, layer_name, bounding)

        # Draw point layers
        for i in range(vector_file.GetLayerCount()):
            layer = vector_file.GetLayerByIndex(i)
            layer_name = layer.GetName()
            layer_defn = layer.GetLayerDefn()
            geom_field_count = layer_defn.GetGeomFieldCount()
            if geom_field_count == 0:
                continue
            if layer_name in SUPPORTED_LAYERS["point"]:
                self._render_layer(layer, gpsmap, cr, layer_name, bounding)

    def _render_layer(self, layer, gpsmap, cr, layer_name, bounding):
        layer.SetSpatialFilter(bounding)
        layer.ResetReading()

        feature = layer.GetNextFeature()
        while feature is not None:
            l_geom = feature.GetGeometryRef()
            if l_geom is None:
                feature = layer.GetNextFeature()
                continue

            if layer_name in SUPPORTED_LAYERS["polygon"]:
                self._render_polygon_geometry(gpsmap, cr, l_geom,
                                              layer_name, feature)
            elif layer_name in SUPPORTED_LAYERS["line"]:
                self._render_line_geometry(gpsmap, cr, l_geom, layer_name)
            elif layer_name in SUPPORTED_LAYERS["point"]:
                self._render_point_geometry(gpsmap, cr, l_geom, layer_name)
            else:
                print(f"ERROR: layer {layer_name} not supported")

            feature = layer.GetNextFeature()


    def _render_polygon_geometry(self, gpsmap, cr, l_geom, layer_name, feature):
        l_geom_name = l_geom.GetGeometryName()

        # Define layer color
        if layer_name == "LNDARE":      # land
            cr.set_source_rgba(0.4, 0.2, 0, 1.0)
        elif layer_name == "DEPARE":    # depth area

            # Access the minimum depth
            field_index = feature.GetFieldIndex("DRVAL1")
            if field_index != -1 and feature.IsFieldSet(field_index):
                drval1 = feature.GetFieldAsDouble(field_index)
            else:
                drval1 = None

            if drval1 is None:
                cr.set_source_rgba(0, 0, 0, 1.0)
            elif drval1<0:
                cr.set_source_rgba(0, 0.28, 0.63, 1.0)
            elif drval1>=0 and drval1<SAFE_DEPTH:
                cr.set_source_rgba(0, 0.45, 1, 1.0)
            elif drval1>=SAFE_DEPTH:
                cr.set_source_rgba(0.5, 0.72, 1, 1.0)
            else:
                cr.set_source_rgba(0, 0, 0, 1.0)

        elif layer_name == "OBSTRN":
            cr.set_source_rgba(0, 1, 0, 0.4)
        elif layer_name == "UWTROC":
            cr.set_source_rgba(0, 0, 1, 0.4)
        else:
            print("ERROR: layer not handled")
            return

        if l_geom_name == "POLYGON":
            self._draw_polygon(gpsmap, cr, l_geom)
        elif l_geom_name == "MULTIPOLYGON":
            for i in range(l_geom.GetGeometryCount()):
                poly = l_geom.GetGeometryRef(i)
                self._draw_polygon(gpsmap, cr, poly)

    def _render_line_geometry(self, gpsmap, cr, l_geom, layer_name):
        l_geom_name = l_geom.GetGeometryName()

        if layer_name == "COALNE":
            cr.set_source_rgba(0.6, 0.6, 0.6, 0.8)
            cr.set_line_width(1.2)
        elif layer_name == "DEPCNT":
            cr.set_source_rgba(0, 0, 0, 0.8)
            cr.set_line_width(0.8)
        else:
            print("ERROR: layer not handled")
            return

        if l_geom_name == "LINESTRING":
            self._draw_line(gpsmap, cr, l_geom)
        elif l_geom_name == "MULTILINESTRING":
            for i in range(l_geom.GetGeometryCount()):
                line = l_geom.GetGeometryRef(i)
                self._draw_line(gpsmap, cr, line)

    def _render_point_geometry(self, gpsmap, cr, l_geom, layer_name):
        l_geom_name = l_geom.GetGeometryName()
        pt_radius = 1.5
        if layer_name == "SOUNDG":
            cr.set_source_rgba(0.1, 0.1, 0.1, 0.9)
        elif layer_name == "LIGHTS":
            cr.set_source_rgba(0.9, 0.9, 0.1, 0.7)
            pt_radius = 9
        elif layer_name == "BOYLAT":
            cr.set_source_rgba(1, 0, 0, 0.7)
            pt_radius = 5
        elif layer_name == "WRECKS":
            pt_radius = 5
            cr.set_source_rgba(1, 0.6, 0.1, 0.7)
        else:
            print("ERROR: layer not handled")
            return

        if l_geom_name == "POINT":
            self._draw_point(gpsmap, cr, l_geom, pt_radius)
        elif l_geom_name == "MULTIPOINT":
            for i in range(l_geom.GetGeometryCount()):
                point = l_geom.GetGeometryRef(i)
                self._draw_point(gpsmap, cr, point, pt_radius)

    def _draw_polygon(self, gpsmap, cr, polygon):
        ring_count = polygon.GetGeometryCount()
        if ring_count == 0:
            return

        cr.new_path()
        cr.set_fill_rule(cairo.FillRule.EVEN_ODD)

        for ring_idx in range(ring_count):
            ring = polygon.GetGeometryRef(ring_idx)
            self._draw_ring(gpsmap, cr, ring)

        cr.fill()
        cr.restore()

    def _draw_line(self, gpsmap, cr, line):
        if line is None or line.GetPointCount() == 0:
            return

        for idx in range(line.GetPointCount()):
            pt = line.GetPoint(idx)
            lon = pt[0]
            lat = pt[1]
            x,y = gpsmap.convert_geographic_to_screen(MapPoint.new_degrees(lat,lon))

            if idx==0:
                cr.move_to(x,y)
            else:
                cr.line_to(x,y)

        cr.stroke()

    def _draw_point(self, gpsmap, cr, point_geom, pt_radius):
        pt = point_geom.GetPoint(0)
        lon = pt[0]
        lat = pt[1]
        depth = pt[2] if (len(pt)>2 and pt[2]!=0.0) else None

        x,y = gpsmap.convert_geographic_to_screen(MapPoint.new_degrees(lat,lon))

        cr.arc(x, y, pt_radius, 0, 2*3.1416)
        cr.fill()

        if depth is not None:
            cr.set_font_size(8)
            cr.move_to(x+3, y-3)
            cr.show_text(f"{depth:.1f}")

    def _draw_ring(self, gpsmap, cr, ring):
        if ring is None or ring.GetPointCount()==0:
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

