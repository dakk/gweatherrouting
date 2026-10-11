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

import math
from functools import lru_cache
from typing import List

import cairo
import gi
import numpy as np

gi.require_version("Gtk", "3.0")

from gi.repository import GObject

from gweatherrouting.common import wind_color
from gweatherrouting.core.utils import point_in_country

from .windrenderer import WindOverlayRenderer


@lru_cache(maxsize=16384)
def wind_on_ground(lat, lon):
    """Reuse the static land mask between neighboring wind viewports."""
    return point_in_country(lat, lon)


class WindPainter:
    """Draw a frozen set of wind samples without accessing GTK or live settings."""

    def __init__(self, settings_manager, on_ground=wind_on_ground):
        self.settings_manager = settings_manager
        self._on_ground = on_ground

    def draw_wind_barb(self, cr, x, y, wdir, wspeed):
        """Draw a wind barb in standard meteorological notation.

        The barb points in the direction the wind comes FROM.
        Short barb = 5 kt, long barb = 10 kt, pennant (flag) = 50 kt.
        """
        wspeed_kt = wspeed * 1.94384  # m/s to knots
        opacity = self.settings_manager.gribArrowOpacity

        r, g, b = wind_color(wspeed)
        cr.set_source_rgba(r, g, b, opacity)

        # Wind barb points into the wind (direction wind comes FROM)
        angle = math.radians(wdir)
        shaft_len = 20

        cr.save()
        cr.translate(x, y)
        cr.rotate(angle)

        # Draw shaft (line pointing up = into the wind)
        cr.move_to(0, 0)
        cr.line_to(0, -shaft_len)
        cr.stroke()

        # Draw dot for calm winds
        if wspeed_kt < 2.5:
            cr.arc(0, 0, 2, 0, 2 * math.pi)
            cr.stroke()
            cr.restore()
            return

        # Build barbs from tip downward
        remaining = wspeed_kt
        barb_y = float(-shaft_len)
        barb_spacing = 3.5
        barb_len = 8

        # Pennants (50 kt each)
        while remaining >= 47.5:
            cr.move_to(0, barb_y)
            cr.line_to(barb_len, barb_y)
            cr.line_to(0, barb_y + barb_spacing)
            cr.close_path()
            cr.fill()
            barb_y += barb_spacing
            remaining -= 50

        # Long barbs (10 kt each)
        while remaining >= 7.5:
            cr.move_to(0, barb_y)
            cr.line_to(barb_len, barb_y)
            cr.stroke()
            barb_y += barb_spacing
            remaining -= 10

        # Short barb (5 kt)
        if remaining >= 2.5:
            cr.move_to(0, barb_y)
            cr.line_to(barb_len * 0.5, barb_y)
            cr.stroke()

        cr.restore()

    def draw(self, gpsmap, cr, data):
        if not data or len(data) == 0:
            return

        scale = int(gpsmap.get_scale() / 350.0)
        if scale < 1:
            scale = 1

        # Draw color fill (smooth gradient between grid points)
        self._draw_color_fill(gpsmap, cr, data, scale)

        # Draw wind barbs
        cr.set_line_width(1)
        points = self._barb_points(gpsmap, data, scale)
        if points:
            lats = np.array([p[2][0] for p in points], dtype=np.float64)
            lons = np.array([p[2][1] for p in points], dtype=np.float64)
            xxs, yys = gpsmap.convert_geographic_to_screen_batch(lats, lons)
            for xx, yy, p in zip(xxs, yys, points):
                if gpsmap.render_cancelled():
                    return
                self.draw_wind_barb(cr, xx, yy, p[0], p[1])

    def _barb_points(self, gpsmap, data, scale):
        points = []
        for row in data[::scale]:
            if gpsmap.render_cancelled():
                return []
            for point in row[::scale]:
                if not self.settings_manager.gribArrowOnGround:
                    if self._on_ground(point[2][0], point[2][1]):
                        continue
                points.append(point)
        return points

    def _grid_screen_points(self, gpsmap, data, scale):
        # Batch-convert all grid points used as quad corners
        point_map = {}
        all_lats: List = []
        all_lons: List = []
        for i in range(0, len(data), scale):
            if gpsmap.render_cancelled():
                return
            row = data[i]
            for j in range(0, len(row), scale):
                point_map[(i, j)] = len(all_lats)
                d = row[j]
                all_lats.append(d[2][0])
                all_lons.append(d[2][1])

        if not all_lats:
            return

        lats = np.array(all_lats, dtype=np.float64)
        lons = np.array(all_lons, dtype=np.float64)
        screen_xs, screen_ys = gpsmap.convert_geographic_to_screen_batch(lats, lons)
        return point_map, screen_xs, screen_ys

    def _draw_color_fill(self, gpsmap, cr, data, scale):
        """Draw interpolated color fill between grid points."""
        opacity = self.settings_manager.gribArrowOpacity * 0.3
        projected = self._grid_screen_points(gpsmap, data, scale)
        if projected is None:
            return
        point_map, screen_xs, screen_ys = projected

        for i in range(0, len(data) - scale, scale):
            if gpsmap.render_cancelled():
                return
            for j in range(0, len(data[i]) - scale, scale):
                try:
                    d_tl = data[i][j]
                    d_tr = data[i][j + scale]
                    d_bl = data[i + scale][j]
                    d_br = data[i + scale][j + scale]
                except IndexError:
                    continue

                try:
                    x_tl = screen_xs[point_map[(i, j)]]
                    y_tl = screen_ys[point_map[(i, j)]]
                    x_tr = screen_xs[point_map[(i, j + scale)]]
                    y_tr = screen_ys[point_map[(i, j + scale)]]
                    x_bl = screen_xs[point_map[(i + scale, j)]]
                    y_bl = screen_ys[point_map[(i + scale, j)]]
                    x_br = screen_xs[point_map[(i + scale, j + scale)]]
                    y_br = screen_ys[point_map[(i + scale, j + scale)]]
                except KeyError:
                    continue

                pat = cairo.MeshPattern()
                pat.begin_patch()
                # Path: TL → TR → BR → BL (clockwise)
                pat.move_to(x_tl, y_tl)
                pat.line_to(x_tr, y_tr)
                pat.line_to(x_br, y_br)
                pat.line_to(x_bl, y_bl)

                # Corners match path order: 0=TL, 1=TR, 2=BR, 3=BL
                r, g, b = wind_color(d_tl[1])
                pat.set_corner_color_rgba(0, r, g, b, opacity)
                r, g, b = wind_color(d_tr[1])
                pat.set_corner_color_rgba(1, r, g, b, opacity)
                r, g, b = wind_color(d_br[1])
                pat.set_corner_color_rgba(2, r, g, b, opacity)
                r, g, b = wind_color(d_bl[1])
                pat.set_corner_color_rgba(3, r, g, b, opacity)
                pat.end_patch()

                cr.set_source(pat)
                cr.move_to(x_tl, y_tl)
                cr.line_to(x_tr, y_tr)
                cr.line_to(x_br, y_br)
                cr.line_to(x_bl, y_bl)
                cr.close_path()
                cr.fill()


class GribMapLayer(GObject.GObject):
    def __init__(self, grib_manager, time_control, settings_manager):
        GObject.GObject.__init__(self)
        self.visible = True
        self.grib_manager = grib_manager
        self.time_control = time_control
        self.settings_manager = settings_manager
        self._renderer = WindOverlayRenderer(WindPainter)
        self._maps = set()
        self.time_control.connect("time_change", self.on_time_change)

    def set_visible(self, visible):
        self.visible = visible
        if not visible:
            for canvas in self._maps:
                self._renderer.forget(canvas)
        for canvas in self._maps:
            canvas.queue_draw()

    def on_time_change(self, *args):
        for canvas in self._maps:
            canvas.queue_draw()

    def _forget(self, canvas):
        self._renderer.forget(canvas)
        self._maps.discard(canvas)

    def do_draw(self, gpsmap, cr):
        if not self.visible:
            return
        if gpsmap not in self._maps:
            self._maps.add(gpsmap)
            gpsmap.connect("destroy", self._forget)
            gpsmap.connect("unmap", lambda canvas: self._renderer.forget(canvas))
        # All values are captured on the UI thread; workers have private GDAL
        # handles and never consult live widgets, settings, or the routing GRIB.
        style = (
            self.time_control.time,
            self.settings_manager.gribArrowOpacity,
            self.settings_manager.gribArrowOnGround,
        )
        sources = tuple((grib,) for grib in self.grib_manager.gribs)
        self._renderer.draw(gpsmap, cr, sources, style)

    def do_render(self, gpsmap):
        pass

    def do_busy(self):
        return False

    def do_button_press(self, gpsmap, gdkeventbutton):
        return False
