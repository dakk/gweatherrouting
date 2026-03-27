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

import logging
import math

import cairo
import numpy as np

from gweatherrouting.gtk.style import CairoStyle, Style
from gweatherrouting.gtk.widgets.mapwidget import MapPoint

from .vectorchartdrawer import VectorChartDrawer

logger = logging.getLogger("gweatherrouting")

# Depth color styles
DEPTH_SHALLOW = CairoStyle(color=(0.45, 0.71, 0.94, 1.0))  # Light blue
DEPTH_MEDIUM = CairoStyle(color=(0.65, 0.85, 0.95, 1.0))  # Very light blue
DEPTH_DEEP = CairoStyle(color=(0.83, 0.92, 0.93, 1.0))  # Near white-blue

CONTOUR_STYLE = CairoStyle(color=(0.5, 0.6, 0.7, 0.6), line_width=0.5)
DASHED_STYLE = CairoStyle(color=(0.4, 0.4, 0.5, 0.6), line_width=0.8, dash=4.0)
BUILDUP_FILL = CairoStyle(color=(0.7, 0.65, 0.55, 1.0))
SOUNDING_STYLE = CairoStyle(color=(0.2, 0.2, 0.3, 0.8), font_size=8)
LIGHT_STYLE = CairoStyle(color=(1.0, 1.0, 0.0, 0.9))
BEACON_STYLE = CairoStyle(color=(0.0, 0.0, 0.0, 0.9))
BUOY_RED = CairoStyle(color=(0.8, 0.1, 0.1, 0.9))
BUOY_GREEN = CairoStyle(color=(0.1, 0.6, 0.1, 0.9))
WRECK_STYLE = CairoStyle(color=(0.3, 0.3, 0.3, 0.8), line_width=1.0)
DEFAULT_POINT = CairoStyle(color=(0.3, 0.3, 0.3, 0.6))
DEFAULT_LINE = CairoStyle(color=(0.5, 0.5, 0.5, 0.5), line_width=0.5)
DEFAULT_AREA_FILL = CairoStyle(color=(0.85, 0.85, 0.85, 0.5))
DEFAULT_AREA_STROKE = CairoStyle(color=(0.6, 0.6, 0.6, 0.5), line_width=0.5)


class CM93ChartDrawer(VectorChartDrawer):
    def _get_visible_cells(self, gpsmap, vector_file):
        """Get visible cells and viewport bbox for the current viewport."""
        p1, p2 = gpsmap.get_bbox()
        lat1, lon1 = p1.get_degrees()
        lat2, lon2 = p2.get_degrees()
        min_lat, max_lat = min(lat1, lat2), max(lat1, lat2)
        min_lon, max_lon = min(lon1, lon2), max(lon1, lon2)

        scale = gpsmap.get_scale()
        scale_level = vector_file.get_scale_for_zoom(scale)
        cells = vector_file.get_cells_for_bbox(
            min_lat, min_lon, max_lat, max_lon, scale_level
        )

        logger.debug(
            "CM93 draw: scale=%.1f level=%s bbox=(%.2f,%.2f)-(%.2f,%.2f) cells=%d",
            scale,
            scale_level,
            min_lat,
            min_lon,
            max_lat,
            max_lon,
            len(cells),
        )
        viewport = (min_lat, min_lon, max_lat, max_lon)
        return cells, scale, viewport

    @staticmethod
    def _bbox_intersects(feat_bbox, vp):
        """Check if a feature bbox intersects the viewport bbox."""
        if not feat_bbox:
            return True  # no bbox computed, render anyway
        return not (
            feat_bbox[2] < vp[0]
            or feat_bbox[0] > vp[2]
            or feat_bbox[3] < vp[1]
            or feat_bbox[1] > vp[3]
        )

    def _separate_features(self, cells, viewport):
        """Separate cell features into areas and lines/points, culling by viewport."""
        areas = []
        lines_points = []
        for cell in cells:
            for feat in cell.features:
                if not self._bbox_intersects(feat.bbox, viewport):
                    continue
                if feat.geom_type == "A":
                    areas.append(feat)
                else:
                    lines_points.append(feat)
        return areas, lines_points

    @staticmethod
    def _geo_to_screen_batch(gpsmap, points):
        """Convert a list of (lat, lon, ...) points to screen coords via batch numpy."""
        lats = np.array([p[0] for p in points], dtype=np.float64)
        lons = np.array([p[1] for p in points], dtype=np.float64)
        xs, ys = gpsmap.convert_geographic_to_screen_batch(lats, lons)
        return xs.tolist(), ys.tolist()

    def draw(self, gpsmap, cr, vector_file, bounding):
        palette = Style.chart_palettes[self.palette]

        width = float(gpsmap.get_allocated_width())
        height = float(gpsmap.get_allocated_height())
        palette.sea.apply(cr)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        cells, scale, viewport = self._get_visible_cells(gpsmap, vector_file)
        if not cells:
            return

        areas, lines_points = self._separate_features(cells, viewport)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        areas.sort(key=lambda f: f.priority)
        for feature in areas:
            try:
                self._render_area(gpsmap, cr, feature, palette)
            except Exception as e:
                logger.debug("Area render error %s: %s", feature.obj_name, e)

        lines_points.sort(key=lambda f: f.priority)
        for feature in lines_points:
            try:
                if feature.geom_type == "L":
                    self._render_line(gpsmap, cr, feature, palette)
                elif feature.geom_type == "P":
                    self._render_point(gpsmap, cr, feature, palette, scale)
            except Exception as e:
                logger.debug("Feature render error %s: %s", feature.obj_name, e)

    def _get_area_styles(self, name, attributes, palette):
        """Return (fill, stroke) styles for an area feature."""
        if name == "LNDARE":
            return palette.land_fill, palette.land_stroke
        if name == "DEPARE":
            return self._get_depare_styles(attributes, palette)
        if name == "DRGARE":
            return DEPTH_MEDIUM, CONTOUR_STYLE
        if name in ("BUAARE", "BUISGL"):
            return BUILDUP_FILL, palette.land_stroke
        if name in ("LAKARE", "RIVERS"):
            return palette.sea, CONTOUR_STYLE
        if name in ("ACHARE", "ANCBRT"):
            return (
                CairoStyle(color=(0.8, 0.8, 0.95, 0.3)),
                CairoStyle(color=(0.5, 0.5, 0.7, 0.5), line_width=0.5),
            )
        if name in ("RESARE", "CTNARE"):
            return (
                CairoStyle(color=(0.95, 0.85, 0.85, 0.3)),
                CairoStyle(color=(0.7, 0.4, 0.4, 0.5), line_width=0.5, dash=3.0),
            )
        return DEFAULT_AREA_FILL, DEFAULT_AREA_STROKE

    @staticmethod
    def _get_depare_styles(attributes, palette):
        """Return (fill, stroke) for DEPARE features based on depth values."""
        drval1 = attributes.get("DRVAL1", 0)
        drval2 = attributes.get("DRVAL2", 100)
        if isinstance(drval1, (int, float)) and drval1 < 5:
            fill = palette.shallow_sea
        elif isinstance(drval2, (int, float)) and drval2 < 20:
            fill = DEPTH_MEDIUM
        else:
            fill = DEPTH_DEEP
        return fill, CONTOUR_STYLE

    def _render_area(self, gpsmap, cr, feature, palette):
        fill, stroke = self._get_area_styles(
            feature.obj_name, feature.attributes, palette
        )

        for ring in feature.geometry:
            if not ring or len(ring) < 3:
                continue

            xs, ys = self._geo_to_screen_batch(gpsmap, ring)
            cr.move_to(xs[0], ys[0])
            for i in range(1, len(xs)):
                cr.line_to(xs[i], ys[i])

            cr.close_path()
            fill.apply(cr)
            cr.fill_preserve()
            stroke.apply(cr)
            cr.stroke()

    def _render_line(self, gpsmap, cr, feature, palette):
        name = feature.obj_name

        if name == "COALNE":
            style = CairoStyle(color=palette.land_stroke.color, line_width=1.5)
        elif name == "DEPCNT":
            style = CONTOUR_STYLE
        elif name in ("NAVLNE", "FERYRT", "TSELNE"):
            style = DASHED_STYLE
        elif name == "SLCONS":
            style = CairoStyle(color=palette.land_stroke.color, line_width=1.0)
        else:
            style = DEFAULT_LINE

        points = feature.geometry
        if not points or len(points) < 2:
            return

        style.apply(cr)
        xs, ys = self._geo_to_screen_batch(gpsmap, points)
        cr.move_to(xs[0], ys[0])
        for i in range(1, len(xs)):
            cr.line_to(xs[i], ys[i])

        cr.stroke()
        Style.reset_dash(cr)

    def _render_soundings(self, gpsmap, cr, feature):
        """Render sounding (depth) labels for 3D point features."""
        # Filter to renderable soundings first
        valid = [p for p in feature.geometry if len(p) > 2 and p[2] <= 100]
        if not valid:
            return

        SOUNDING_STYLE.apply(cr)
        xs, ys = self._geo_to_screen_batch(gpsmap, valid)
        for i, point in enumerate(valid):
            cr.move_to(xs[i] + 2, ys[i] + 2)
            cr.show_text(f"{point[2]:.1f}")

    @staticmethod
    def _draw_light(cr, x, y):
        """Draw a light symbol (yellow circle with rays)."""
        LIGHT_STYLE.apply(cr)
        cr.arc(x, y, 4, 0, 2 * math.pi)
        cr.fill()
        cr.set_line_width(0.5)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            cr.move_to(x + 4 * math.cos(rad), y + 4 * math.sin(rad))
            cr.line_to(x + 7 * math.cos(rad), y + 7 * math.sin(rad))
        cr.stroke()

    @staticmethod
    def _draw_beacon(cr, x, y):
        """Draw a beacon triangle symbol."""
        BEACON_STYLE.apply(cr)
        cr.set_line_width(1.5)
        cr.move_to(x, y - 5)
        cr.line_to(x - 4, y + 3)
        cr.line_to(x + 4, y + 3)
        cr.close_path()
        cr.stroke()

    @staticmethod
    def _draw_buoy_lateral(cr, x, y, catlam):
        """Draw a lateral buoy (red for port, green otherwise)."""
        if catlam == 1:
            BUOY_RED.apply(cr)
        else:
            BUOY_GREEN.apply(cr)
        cr.arc(x, y, 3, 0, 2 * math.pi)
        cr.fill()

    @staticmethod
    def _draw_wreck(cr, x, y):
        """Draw an X mark for wrecks/obstructions."""
        WRECK_STYLE.apply(cr)
        cr.set_line_width(1.0)
        cr.move_to(x - 3, y - 3)
        cr.line_to(x + 3, y + 3)
        cr.move_to(x + 3, y - 3)
        cr.line_to(x - 3, y + 3)
        cr.stroke()

    _BEACON_NAMES = {"BCNCAR", "BCNLAT", "BCNISD", "BCNSAW", "BCNSPP"}
    _BUOY_NAMES = {"BOYCAR", "BOYISD", "BOYSAW", "BOYSPP"}
    _WRECK_NAMES = {"WRECKS", "UWTROC", "OBSTRN"}
    _LANDMARK_NAMES = {"LNDMRK", "SILTNK", "CHIMNY", "TOWERS"}

    def _render_point(self, gpsmap, cr, feature, palette, scale):
        name = feature.obj_name
        if not feature.geometry:
            return

        if name == "SOUNDG":
            self._render_soundings(gpsmap, cr, feature)
            return

        lat, lon = feature.geometry[0][0], feature.geometry[0][1]
        x, y = gpsmap.convert_geographic_to_screen(MapPoint.new_degrees(lat, lon))

        if name == "LIGHTS":
            self._draw_light(cr, x, y)
        elif name in self._BEACON_NAMES:
            self._draw_beacon(cr, x, y)
        elif name in self._BUOY_NAMES:
            DEFAULT_POINT.apply(cr)
            cr.arc(x, y, 3, 0, 2 * math.pi)
            cr.fill()
        elif name == "BOYLAT":
            catlam = feature.attributes.get("CATLAM", 0)
            self._draw_buoy_lateral(cr, x, y, catlam)
        elif name in self._WRECK_NAMES:
            self._draw_wreck(cr, x, y)
        elif name in self._LANDMARK_NAMES:
            BEACON_STYLE.apply(cr)
            cr.set_line_width(1.0)
            cr.rectangle(x - 2, y - 2, 4, 4)
            cr.stroke()
        else:
            if scale > 100:
                return
            DEFAULT_POINT.apply(cr)
            cr.arc(x, y, 1.5, 0, 2 * math.pi)
            cr.fill()
