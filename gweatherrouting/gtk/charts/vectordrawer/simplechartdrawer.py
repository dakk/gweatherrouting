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

import cairo
import numpy as np

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

    @staticmethod
    def _geom_to_screen_batch(gpsmap, g):
        """Extract OGR geometry points and batch-convert to screen coords."""
        npts = g.GetPointCount()
        if npts == 0:
            return None, None
        lats = np.empty(npts, dtype=np.float64)
        lons = np.empty(npts, dtype=np.float64)
        for ii in range(npts):
            pt = g.GetPoint(ii)
            lats[ii] = pt[1]
            lons[ii] = pt[0]
        xs, ys = gpsmap.convert_geographic_to_screen_batch(lats, lons)
        return xs.tolist(), ys.tolist()

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

            xs, ys = self._geom_to_screen_batch(gpsmap, g)
            if xs is not None:
                cr.move_to(xs[0], ys[0])
                for ii in range(1, len(xs)):
                    cr.line_to(xs[ii], ys[ii])

            cr.close_path()
            cr.stroke_preserve()
            fill_style.apply(cr)
            cr.fill()
