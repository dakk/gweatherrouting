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
# flake8: noqa: E402
import cairo
import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("OsmGpsMap", "1.2")
except:
    gi.require_version("OsmGpsMap", "1.0")

from gi.repository import OsmGpsMap

from gweatherrouting.gtk.style import Style

from .vectorchartdrawer import VectorChartDrawer


class SimpleChartDrawer(VectorChartDrawer):
    def draw(self, gpsmap, cr, vectorFile, bounding):
        strokeStyle = Style.chartPalettes[self.palette].LandStroke
        fillStyle = Style.chartPalettes[self.palette].LandFill
        seaStyle = Style.chartPalettes[self.palette].Sea
        contournStyle = Style.chartPalettes[self.palette].ShallowSea

        self.backgroundRender(gpsmap, cr, seaStyle)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        for i in range(vectorFile.GetLayerCount()):
            layer = vectorFile.GetLayerByIndex(i)
            layer.SetSpatialFilter(bounding)

            # Iterate over features
            feat = layer.GetNextFeature()
            while feat is not None:
                if not feat:
                    continue

                geom = feat.GetGeometryRef()
                geom = bounding.Intersection(geom)
                self.featureRender(
                    gpsmap, cr, geom, feat, layer, strokeStyle, fillStyle, contournStyle
                )
                feat = layer.GetNextFeature()

    def backgroundRender(self, gpsmap, cr, seaStyle):
        width = float(gpsmap.get_allocated_width())
        height = float(gpsmap.get_allocated_height())
        seaStyle.apply(cr)
        cr.rectangle(0, 0, width, height)
        cr.stroke_preserve()
        cr.fill()

    def featureRender(
        self, gpsmap, cr, geom, feat, layer, strokeStyle, fillStyle, contournStyle
    ):
        for i in range(0, geom.GetGeometryCount()):
            strokeStyle.apply(cr)
            g = geom.GetGeometryRef(i)

            if g.GetGeometryName() == "POLYGON":
                self.featureRender(
                    gpsmap, cr, g, feat, layer, strokeStyle, fillStyle, contournStyle
                )

            for ii in range(0, g.GetPointCount()):
                pt = g.GetPoint(ii)
                xx, yy = gpsmap.convert_geographic_to_screen(
                    OsmGpsMap.MapPoint.new_degrees(pt[1], pt[0])
                )
                cr.line_to(xx, yy)

            cr.close_path()
            cr.stroke_preserve()
            fillStyle.apply(cr)
            cr.fill()
