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
import logging
import os

# flake8: noqa: E402
from typing import List

import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("OsmGpsMap", "1.2")
except:
    gi.require_version("OsmGpsMap", "1.0")

from gi.repository import Gdk, GObject, Gtk, OsmGpsMap

from gweatherrouting.common import resource_path
from gweatherrouting.core.core import LinePointValidityProvider
from gweatherrouting.core.storage import DATA_DIR
from gweatherrouting.gtk.settings import SettingsManager

from .chartlayer import ChartLayer
from .gdalrasterchart import GDALRasterChart
from .gdalvectorchart import GDALVectorChart
from .gshhs import (
    GSHHSAskDownloadDialog,
    GSHHSDownloadDialog,
    GSHHSVectorChart,
    OSMAskDownloadDialog,
    OSMDownloadDialog,
)

logger = logging.getLogger("gweatherrouting")


class ChartManager(GObject.GObject, OsmGpsMap.MapLayer):
    def __init__(self, settingsManager):
        GObject.GObject.__init__(self)
        self.charts: List[ChartLayer] = []
        self.gshhsLayer: GSHHSVectorChart = None
        self.osmLayer: GDALVectorChart = None
        self.settingsManager: SettingsManager = settingsManager
        self.maps: List[OsmGpsMap] = []

        self.settingsManager.register_on_change(
            "chartPalette", self.onChartPaletteChanged
        )

    def addMap(self, m: OsmGpsMap):
        self.maps.append(m)

    def getLinePointValidityProviders(self):
        lpvp = []
        for x in filter(lambda x: x.enabled, self.charts):
            if isinstance(x, LinePointValidityProvider):
                lpvp += [x]
        return lpvp

    def onChartPaletteChanged(self, v):
        for m in self.maps:
            m.map_redraw_idle()

    def _loadBaseGSHHS(self):
        if os.path.exists(DATA_DIR + "/gshhs"):
            self.gshhsLayer = GSHHSVectorChart(
                DATA_DIR + "/gshhs", self.settingsManager
            )
            self.charts = [self.gshhsLayer] + self.charts

    def _loadBaseOSM(self):
        if os.path.exists(DATA_DIR + "/seamarks.pbf"):
            self.osmLayer = GDALVectorChart(
                DATA_DIR + "/seamarks.pbf", self.settingsManager
            )
            self.charts = self.charts + [self.osmLayer]

    def loadBaseChart(self, parent):
        self._loadBaseGSHHS()

        if not self.gshhsLayer:
            logger.info("GSHHS files not found, open a dialog asking for download")

            def f():
                Gdk.threads_enter()
                ask_diag = GSHHSAskDownloadDialog(parent)
                r = ask_diag.run()
                ask_diag.destroy()
                if r == Gtk.ResponseType.OK:
                    down_diag = GSHHSDownloadDialog(parent)
                    r = down_diag.run()
                    down_diag.destroy()
                    if r == Gtk.ResponseType.OK:
                        self._loadBaseGSHHS()
                else:
                    self.charts = [
                        GDALVectorChart(
                            resource_path("gweatherrouting", "data/countries.geojson"),
                            self.settingsManager,
                        )
                    ] + self.charts

                Gdk.threads_leave()

            GObject.timeout_add(10, f)

        self._loadBaseOSM()

        if not self.osmLayer:
            logger.info("OSM file not found, open a dialog asking for download")

            def ff():
                Gdk.threads_enter()
                ask_diag = OSMAskDownloadDialog(parent)
                r = ask_diag.run()
                ask_diag.destroy()
                if r == Gtk.ResponseType.OK:
                    down_diag = OSMDownloadDialog(parent)
                    r = down_diag.run()
                    down_diag.destroy()
                    if r == Gtk.ResponseType.OK:
                        self._loadBaseOSM()

                Gdk.threads_leave()

            GObject.timeout_add(10, ff)

    def loadVectorLayer(self, path, metadata=None, enabled=True):
        logger.info("Loading vector chart %s", path)
        l = GDALVectorChart(
            path, self.settingsManager, metadata=metadata, enabled=enabled
        )
        self.charts += [l]

        if self.osmLayer and enabled:
            self.osmLayer.enabled = False
        if self.gshhsLayer and enabled:
            self.gshhsLayer.forceDownscale = True

        return l

    def loadRasterLayer(self, path, metadata=None, enabled=True):
        logger.info("Loading raster chart %s", path)
        l = GDALRasterChart(
            path, self.settingsManager, metadata=metadata, enabled=enabled
        )
        self.charts += [l]

        if self.osmLayer and enabled:
            self.osmLayer.enabled = False
        if self.gshhsLayer and enabled:
            self.gshhsLayer.forceDownscale = True
        return l

    def do_draw(self, gpsmap, cr):
        for x in filter(lambda x: x.enabled, self.charts):
            x.do_draw(gpsmap, cr)

    def do_render(self, gpsmap):
        for x in filter(lambda x: x.enabled, self.charts):
            x.do_render(gpsmap)

    def do_busy(self):
        for x in filter(lambda x: x.enabled, self.charts):
            x.do_busy()

    def do_button_press(self, gpsmap, gdkeventbutton):
        for x in filter(lambda x: x.enabled, self.charts):
            x.do_button_press(gpsmap, gdkeventbutton)


GObject.type_register(ChartManager)
