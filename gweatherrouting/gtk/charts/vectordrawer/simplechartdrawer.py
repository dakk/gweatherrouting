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
import cairo
import gi

gi.require_version("Gtk", "3.0")
# try:
#     gi.require_version("OsmGpsMap", "1.2")
# except:
#     gi.require_version("OsmGpsMap", "1.0")

from gi.repository import OsmGpsMap

from gweatherrouting.gtk.style import Style

from .vectorchartdrawer import VectorChartDrawer


class SimpleChartDrawer(VectorChartDrawer):
    def draw(self, gpsmap, cr, vector_file, bounding):
        stroke_style = Style.chart_palettes[self.palette].land_stroke
        fill_style = Style.chart_palettes[self.palette].land_fill
        sea_style = Style.chart_palettes[self.palette].sea
        contourn_style = Style.chart_palettes[self.palette].shallow_sea

        self.background_render(gpsmap, cr, sea_style)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        for i in range(vector_file.GetLayerCount()):
            layer = vector_file.GetLayerByIndex(i)
            layer.SetSpatialFilter(bounding)

            # Iterate over features
            feat = layer.GetNextFeature()
            while feat is not None:
                if not feat:
                    continue

                geom = feat.GetGeometryRef()
                geom = bounding.Intersection(geom)
                self.feature_render(
                    gpsmap,
                    cr,
                    geom,
                    feat,
                    layer,
                    stroke_style,
                    fill_style,
                    contourn_style,
                )
                feat = layer.GetNextFeature()

    def background_render(self, gpsmap, cr, sea_style):
        width = float(gpsmap.get_allocated_width())
        height = float(gpsmap.get_allocated_height())
        sea_style.apply(cr)
        cr.rectangle(0, 0, width, height)
        cr.stroke_preserve()
        cr.fill()

    def feature_render(
        self, gpsmap, cr, geom, feat, layer, stroke_style, fill_style, contourn_style
    ):
        for i in range(0, geom.GetGeometryCount()):
            stroke_style.apply(cr)
            g = geom.GetGeometryRef(i)

            if g.GetGeometryName() == "POLYGON":
                self.feature_render(
                    gpsmap, cr, g, feat, layer, stroke_style, fill_style, contourn_style
                )

            for ii in range(0, g.GetPointCount()):
                pt = g.GetPoint(ii)
                xx, yy = gpsmap.convert_geographic_to_screen(
                    OsmGpsMap.MapPoint.new_degrees(pt[1], pt[0])
                )
                cr.line_to(xx, yy)

            cr.close_path()
            cr.stroke_preserve()
            fill_style.apply(cr)
            cr.fill()
