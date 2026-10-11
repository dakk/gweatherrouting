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
import os
from typing import List, Optional
from weakref import WeakKeyDictionary

import cairo
import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gdk, GObject, Gtk

from gweatherrouting.common import resource_path
from gweatherrouting.core.core import LinePointValidityProvider
from gweatherrouting.core.enccharts import chart_scale_rank
from gweatherrouting.core.storage import DATA_DIR
from gweatherrouting.gtk.settings import SettingsManager
from gweatherrouting.gtk.widgets.mapwidget import MapViewport

from .chartlayer import ChartLayer
from .chsrenderer import CHSRenderer
from .gdalrasterchart import GDALRasterChart
from .gdalvectorchart import GDALVectorChart
from .encrenderer import ENCOverlayRenderer
from gweatherrouting.gtk.widgets.overlayrenderer import paint_viewport
from .vectordrawer.s57chartdrawer import S57ChartDrawer
from .gshhs import (
    AskDownloadDialog,
    CombinedDownloadDialog,
    GSHHSVectorChart,
)

logger = logging.getLogger("gweatherrouting")


class ChartManager(GObject.GObject):
    def __init__(self, settings_manager):
        GObject.GObject.__init__(self)
        self.charts: List[ChartLayer] = []
        self.gshhsLayer: Optional[GSHHSVectorChart] = None
        self.osmLayer: Optional[GDALVectorChart] = None
        self.settings_manager: SettingsManager = settings_manager
        self.maps: List = []
        self._chart_surfaces: WeakKeyDictionary[
            object, tuple[tuple, MapViewport, cairo.ImageSurface]
        ] = WeakKeyDictionary()
        self._enc_renderer = ENCOverlayRenderer()
        self._chs_renderer = CHSRenderer(os.path.join(DATA_DIR, "chs-tiles"))

        self.settings_manager.register_on_change(
            "chartPalette", self.on_chart_palette_changed
        )
        self.settings_manager.register_on_change(
            "canadianCharts", self.on_canadian_charts_changed
        )

    def add_map(self, m):
        self.maps.append(m)
        m.connect("destroy", lambda canvas: self._enc_renderer.forget(canvas))
        m.connect("destroy", lambda canvas: self._chs_renderer.forget(canvas))
        m.connect("unmap", lambda canvas: self._chs_renderer.forget(canvas))

    def on_canadian_charts_changed(self, enabled):
        self._chs_renderer.set_enabled(enabled)
        for canvas in self.maps:
            canvas.queue_draw()

    def get_line_point_validity_providers(self):
        lpvp: List[LinePointValidityProvider] = []
        for x in filter(lambda x: x.enabled, self.charts):
            if isinstance(x, LinePointValidityProvider):
                lpvp += [x]
        return lpvp

    def on_chart_palette_changed(self, v):
        self._palette = v
        self._chart_surfaces.clear()
        for m in self.maps:
            m.map_redraw_idle()

    def _load_base_gshhs(self):
        if os.path.exists(DATA_DIR + "/gshhs"):
            self.gshhsLayer = GSHHSVectorChart(
                DATA_DIR + "/gshhs", self.settings_manager
            )
            self.charts = [self.gshhsLayer] + self.charts

    def _load_base_osm(self):
        if os.path.exists(DATA_DIR + "/seamarks.pbf"):
            self.osmLayer = GDALVectorChart(
                DATA_DIR + "/seamarks.pbf", self.settings_manager
            )
            self.charts = self.charts + [self.osmLayer]

    def load_base_chart(self, parent):
        self._load_base_gshhs()
        self._load_base_osm()

        gshhs_missing = self.gshhsLayer is None
        osm_missing = self.osmLayer is None

        if not gshhs_missing and not osm_missing:
            return

        def f():
            Gdk.threads_enter()
            ask_diag = AskDownloadDialog(parent, gshhs_missing, osm_missing)
            r = ask_diag.run()
            download_gshhs = ask_diag.download_gshhs
            download_osm = ask_diag.download_osm
            ask_diag.destroy()

            if r == Gtk.ResponseType.OK and (download_gshhs or download_osm):
                down_diag = CombinedDownloadDialog(parent, download_gshhs, download_osm)
                r = down_diag.run()
                down_diag.destroy()
                if r == Gtk.ResponseType.OK:
                    if download_gshhs:
                        self._load_base_gshhs()
                    if download_osm:
                        self._load_base_osm()

            if not self.gshhsLayer:
                self.charts = [
                    GDALVectorChart(
                        resource_path("gweatherrouting", "data/countries.geojson"),
                        self.settings_manager,
                    )
                ] + self.charts

            Gdk.threads_leave()

        GObject.timeout_add(10, f)

    def load_vector_layer(self, path, metadata=None, enabled=True):
        logger.info("Loading vector chart %s", path)
        chart = GDALVectorChart(
            path, self.settings_manager, metadata=metadata, enabled=enabled
        )
        self.charts += [chart]

        if self.osmLayer and enabled and not path.lower().endswith(".000"):
            self.osmLayer.enabled = False
        if self.gshhsLayer and enabled and not path.lower().endswith(".000"):
            self.gshhsLayer.force_downscale = True

        return chart

    def detailed_chart_at(self, lat, lon, scale, enabled=None):
        """Return the loaded chart best suited to this point and display scale."""
        candidates = sorted(
            (c for c in self.charts if enabled is None or c.enabled == enabled),
            key=lambda c: (
                chart_scale_rank(getattr(c, "_native_scale", 0), scale),
                not c.enabled,
                c.path,
            ),
        )
        for chart in candidates:
            if isinstance(chart, GDALVectorChart) and chart.covers_point(
                lat, lon, scale
            ):
                return chart
            if isinstance(chart, GDALRasterChart):
                for _, bbox, *_ in chart.metadata or []:
                    if (
                        min(bbox[0][0], bbox[1][0])
                        <= lat
                        <= max(bbox[0][0], bbox[1][0])
                    ):
                        if (
                            min(bbox[0][1], bbox[1][1])
                            <= lon
                            <= max(bbox[0][1], bbox[1][1])
                        ):
                            return chart
        return None

    def chart_suggestion_at(self, catalog, lat, lon, scale):
        """Offer a better scale, even when a usable chart already covers the point."""
        active = self.detailed_chart_at(lat, lon, scale, enabled=True)
        disabled = self.detailed_chart_at(lat, lon, scale, enabled=False)
        cell = catalog.chart_at(lat, lon, scale)

        def rank(chart):
            return chart_scale_rank(getattr(chart, "_native_scale", 0), scale)

        if disabled and (active is None or rank(disabled) < rank(active)):
            if cell is None or rank(disabled) <= chart_scale_rank(cell.scale, scale):
                return None, disabled
        if cell and (
            active is None or chart_scale_rank(cell.scale, scale) < rank(active)
        ):
            # A catalog cell may already have been imported from another directory.
            imported = next(
                (
                    c
                    for c in self.charts
                    if os.path.splitext(os.path.basename(c.path))[0].upper()
                    == cell.name
                ),
                None,
            )
            if imported and imported.enabled:
                return None, None
            return cell, imported
        return None, None

    def enable_downloaded_chart(self, path):
        chart = next((c for c in self.charts if c.path == path), None)
        if chart is None:
            chart = self.load_vector_layer(path)
        chart.enabled = True
        entries = list(self.settings_manager[chart.ctype + "Charts"] or [])
        entry = next((e for e in entries if e["path"] == path), None)
        if entry:
            entry["enabled"] = True
        else:
            entries.append({"path": path, "metadata": chart.metadata, "enabled": True})
        self.settings_manager[chart.ctype + "Charts"] = entries
        self.settings_manager.save()
        for m in self.maps:
            m.map_redraw_idle()
        return chart

    def load_raster_layer(self, path, metadata=None, enabled=True):
        logger.info("Loading raster chart %s", path)
        chart = GDALRasterChart(
            path, self.settings_manager, metadata=metadata, enabled=enabled
        )
        self.charts += [chart]

        if self.osmLayer and enabled:
            self.osmLayer.enabled = False
        if self.gshhsLayer and enabled:
            self.gshhsLayer.force_downscale = True
        return chart

    def do_draw(self, gpsmap, cr):
        base, enc = [], []
        for chart in self.charts:
            if isinstance(chart, GDALVectorChart) and isinstance(
                chart.drawer, S57ChartDrawer
            ):
                if chart.enabled:
                    enc.append(
                        (chart.path, chart._native_scale, chart._coverage_envelopes)
                    )
            else:
                base.append(chart)
        self._draw_base(gpsmap, cr, base)
        self._chs_renderer.draw(gpsmap, cr)
        self._enc_renderer.draw(gpsmap, cr, tuple(enc), self._palette)

    def _draw_base(self, gpsmap, cr, charts):
        # Chart pixels are static while instruments, weather and routes repaint.
        # A margin also lets small pans reuse the same image at a shifted origin.
        margin = 128
        width, height = gpsmap.get_allocated_width(), gpsmap.get_allocated_height()
        factor = gpsmap.get_scale_factor()
        signature = (
            width,
            height,
            factor,
            gpsmap._zoom,
            tuple(
                (id(c), c.enabled, getattr(c, "force_downscale", False)) for c in charts
            ),
        )
        cached = self._chart_surfaces.get(gpsmap)
        if cached and getattr(gpsmap, "_zoom_animating", False):
            old_signature = cached[0]
            if (
                old_signature[:3] == signature[:3]
                and old_signature[4:] == signature[4:]
            ):
                paint_viewport(gpsmap, cr, cached[1], cached[2])
                return
        offset_x = offset_y = 0.0
        if cached and cached[0] == signature:
            viewport = cached[1]
            offset_x = viewport._lon_to_x(viewport._center_lon)
            offset_x -= viewport._lon_to_x(gpsmap._center_lon)
            offset_y = viewport._lat_to_y(viewport._center_lat)
            offset_y -= viewport._lat_to_y(gpsmap._center_lat)
        if (
            not cached
            or cached[0] != signature
            or max(abs(offset_x), abs(offset_y)) > margin
        ):

            def invalidate():
                self._chart_surfaces.pop(gpsmap, None)
                gpsmap.queue_draw()

            viewport = MapViewport(gpsmap, margin, invalidate)
            surface = cairo.ImageSurface(
                cairo.FORMAT_ARGB32, viewport.width * factor, viewport.height * factor
            )
            surface.set_device_scale(factor, factor)
            chart_cr = cairo.Context(surface)
            for chart in filter(lambda c: c.enabled, charts):
                chart_cr.save()
                chart.do_draw(viewport, chart_cr)
                chart_cr.restore()
            cached = (signature, viewport, surface)
            self._chart_surfaces[gpsmap] = cached
            offset_x = offset_y = 0.0
        cr.set_source_surface(cached[2], offset_x - margin, offset_y - margin)
        cr.paint()

    def do_render(self, gpsmap):
        for x in filter(lambda x: x.enabled, self.charts):
            x.do_render(gpsmap)

    def do_busy(self):
        for x in filter(lambda x: x.enabled, self.charts):
            x.do_busy()

    def query_point(self, lat, lon, tolerance=0.001):
        """Query all vector chart layers for features near a given lat/lon."""
        results = []
        for chart in filter(lambda x: x.enabled, self.charts):
            if isinstance(chart, GDALVectorChart):
                results.extend(chart.query_point(lat, lon, tolerance))
        return results

    def do_button_press(self, gpsmap, gdkeventbutton):
        for x in filter(lambda x: x.enabled, self.charts):
            x.do_button_press(gpsmap, gdkeventbutton)
