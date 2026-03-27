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

from gweatherrouting.gtk.style import CairoStyle, Style
from gweatherrouting.gtk.widgets.mapwidget import MapPoint

from .vectorchartdrawer import VectorChartDrawer

logger = logging.getLogger("gweatherrouting")

# Depth color styles
DEPTH_SHALLOW = CairoStyle(color=(0.45, 0.71, 0.94, 1.0))  # Light blue
DEPTH_MEDIUM = CairoStyle(color=(0.65, 0.85, 0.95, 1.0))   # Very light blue
DEPTH_DEEP = CairoStyle(color=(0.83, 0.92, 0.93, 1.0))     # Near white-blue

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
    def __init__(self, settings_manager):
        super().__init__(settings_manager)
        self._cached_surface = None
        self._last_cache_key = None

    def on_chart_palette_changed(self, v):
        super().on_chart_palette_changed(v)
        self._cached_surface = None
        self._last_cache_key = None

    def draw(self, gpsmap, cr, vector_file, bounding):
        width = int(gpsmap.get_allocated_width())
        height = int(gpsmap.get_allocated_height())

        # Build cache key from viewport state
        p1, p2 = gpsmap.get_bbox()
        scale = gpsmap.get_scale()
        cache_key = (p1.get_degrees(), p2.get_degrees(), scale, width, height,
                     self.palette)

        if cache_key == self._last_cache_key and self._cached_surface:
            cr.set_source_surface(self._cached_surface, 0, 0)
            cr.paint()
            return

        # Render to offscreen surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        offscreen_cr = cairo.Context(surface)
        self._do_render(gpsmap, offscreen_cr, vector_file, scale, p1, p2,
                        width, height)

        self._cached_surface = surface
        self._last_cache_key = cache_key
        cr.set_source_surface(surface, 0, 0)
        cr.paint()

    def _do_render(self, gpsmap, cr, vector_file, scale, p1, p2, width, height):
        palette = Style.chart_palettes[self.palette]

        # Fill background with sea color
        palette.sea.apply(cr)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        # Get viewport bounds
        lat1, lon1 = p1.get_degrees()
        lat2, lon2 = p2.get_degrees()
        min_lat = min(lat1, lat2)
        max_lat = max(lat1, lat2)
        min_lon = min(lon1, lon2)
        max_lon = max(lon1, lon2)

        # Determine scale level
        scale_level = vector_file.get_scale_for_zoom(scale)

        # Get visible cells
        cells = vector_file.get_cells_for_bbox(
            min_lat, min_lon, max_lat, max_lon, scale_level
        )

        logger.debug(
            "CM93 draw: scale=%.1f level=%s bbox=(%.2f,%.2f)-(%.2f,%.2f) cells=%d",
            scale, scale_level, min_lat, min_lon, max_lat, max_lon, len(cells),
        )

        if not cells:
            return

        # Single-pass: separate features by geometry type
        areas = []
        lines_points = []
        for cell in cells:
            for feat in cell.features:
                if feat.geom_type == "A":
                    areas.append(feat)
                else:
                    lines_points.append(feat)

        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        # Render areas first (sorted by priority)
        areas.sort(key=lambda f: f.priority)
        for feature in areas:
            try:
                self._render_area(gpsmap, cr, feature, palette)
            except Exception:
                pass

        # Then lines and points on top
        lines_points.sort(key=lambda f: f.priority)
        for feature in lines_points:
            try:
                if feature.geom_type == "L":
                    self._render_line(gpsmap, cr, feature, palette)
                elif feature.geom_type == "P":
                    self._render_point(gpsmap, cr, feature, palette, scale)
            except Exception:
                pass

    def _render_area(self, gpsmap, cr, feature, palette):
        name = feature.obj_name

        if name == "LNDARE":
            stroke = palette.land_stroke
            fill = palette.land_fill
        elif name == "DEPARE":
            drval1 = feature.attributes.get("DRVAL1", 0)
            drval2 = feature.attributes.get("DRVAL2", 100)
            if isinstance(drval1, (int, float)) and drval1 < 5:
                fill = palette.shallow_sea
            elif isinstance(drval2, (int, float)) and drval2 < 20:
                fill = DEPTH_MEDIUM
            else:
                fill = DEPTH_DEEP
            stroke = CONTOUR_STYLE
        elif name == "DRGARE":
            fill = DEPTH_MEDIUM
            stroke = CONTOUR_STYLE
        elif name in ("BUAARE", "BUISGL"):
            stroke = palette.land_stroke
            fill = BUILDUP_FILL
        elif name in ("LAKARE", "RIVERS"):
            stroke = CONTOUR_STYLE
            fill = palette.sea
        elif name in ("ACHARE", "ANCBRT"):
            fill = CairoStyle(color=(0.8, 0.8, 0.95, 0.3))
            stroke = CairoStyle(color=(0.5, 0.5, 0.7, 0.5), line_width=0.5)
        elif name in ("RESARE", "CTNARE"):
            fill = CairoStyle(color=(0.95, 0.85, 0.85, 0.3))
            stroke = CairoStyle(color=(0.7, 0.4, 0.4, 0.5), line_width=0.5, dash=3.0)
        else:
            stroke = DEFAULT_AREA_STROKE
            fill = DEFAULT_AREA_FILL

        for ring in feature.geometry:
            if not ring or len(ring) < 3:
                continue

            first = True
            for lat, lon in ring:
                x, y = gpsmap.convert_geographic_to_screen(
                    MapPoint.new_degrees(lat, lon)
                )
                if first:
                    cr.move_to(x, y)
                    first = False
                else:
                    cr.line_to(x, y)

            cr.close_path()
            fill.apply(cr)
            cr.fill_preserve()
            stroke.apply(cr)
            cr.stroke()

    def _render_line(self, gpsmap, cr, feature, palette):
        name = feature.obj_name

        if name == "COALNE":
            style = CairoStyle(
                color=palette.land_stroke.color, line_width=1.5
            )
        elif name == "DEPCNT":
            style = CONTOUR_STYLE
        elif name in ("NAVLNE", "FERYRT", "TSELNE"):
            style = DASHED_STYLE
        elif name == "SLCONS":
            style = CairoStyle(
                color=palette.land_stroke.color, line_width=1.0
            )
        else:
            style = DEFAULT_LINE

        points = feature.geometry
        if not points or len(points) < 2:
            return

        style.apply(cr)
        first = True
        for lat, lon in points:
            x, y = gpsmap.convert_geographic_to_screen(
                MapPoint.new_degrees(lat, lon)
            )
            if first:
                cr.move_to(x, y)
                first = False
            else:
                cr.line_to(x, y)

        cr.stroke()
        Style.reset_dash(cr)

    def _render_point(self, gpsmap, cr, feature, palette, scale):
        name = feature.obj_name
        if not feature.geometry:
            return

        lat, lon = feature.geometry[0]
        x, y = gpsmap.convert_geographic_to_screen(MapPoint.new_degrees(lat, lon))

        if name == "SOUNDG":
            depth = feature.attributes.get("VALSOU")
            if depth is None:
                # Try to get depth from the z coordinate if stored
                depth = feature.attributes.get("DRVAL1", "")
            if depth is not None and depth != "":
                SOUNDING_STYLE.apply(cr)
                cr.move_to(x + 2, y + 2)
                if isinstance(depth, float):
                    cr.show_text(f"{depth:.1f}")
                else:
                    cr.show_text(str(depth))

        elif name == "LIGHTS":
            # Draw a small yellow star/circle
            LIGHT_STYLE.apply(cr)
            cr.arc(x, y, 4, 0, 2 * math.pi)
            cr.fill()
            # Draw rays
            cr.set_line_width(0.5)
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                cr.move_to(x + 4 * math.cos(rad), y + 4 * math.sin(rad))
                cr.line_to(x + 7 * math.cos(rad), y + 7 * math.sin(rad))
            cr.stroke()

        elif name in ("BCNCAR", "BCNLAT", "BCNISD", "BCNSAW", "BCNSPP"):
            BEACON_STYLE.apply(cr)
            cr.set_line_width(1.5)
            # Triangle symbol
            cr.move_to(x, y - 5)
            cr.line_to(x - 4, y + 3)
            cr.line_to(x + 4, y + 3)
            cr.close_path()
            cr.stroke()

        elif name in ("BOYCAR", "BOYISD", "BOYSAW", "BOYSPP"):
            DEFAULT_POINT.apply(cr)
            cr.arc(x, y, 3, 0, 2 * math.pi)
            cr.fill()

        elif name == "BOYLAT":
            catlam = feature.attributes.get("CATLAM", 0)
            if catlam == 1:  # Port
                BUOY_RED.apply(cr)
            else:
                BUOY_GREEN.apply(cr)
            cr.arc(x, y, 3, 0, 2 * math.pi)
            cr.fill()

        elif name in ("WRECKS", "UWTROC", "OBSTRN"):
            WRECK_STYLE.apply(cr)
            cr.set_line_width(1.0)
            # X mark
            cr.move_to(x - 3, y - 3)
            cr.line_to(x + 3, y + 3)
            cr.move_to(x + 3, y - 3)
            cr.line_to(x - 3, y + 3)
            cr.stroke()

        elif name in ("LNDMRK", "SILTNK", "CHIMNY", "TOWERS"):
            BEACON_STYLE.apply(cr)
            cr.set_line_width(1.0)
            # Small square
            cr.rectangle(x - 2, y - 2, 4, 4)
            cr.stroke()

        else:
            # Skip unknown points at high zoom to reduce clutter
            if scale > 100:
                return
            DEFAULT_POINT.apply(cr)
            cr.arc(x, y, 1.5, 0, 2 * math.pi)
            cr.fill()
