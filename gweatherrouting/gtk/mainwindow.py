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

# TODO:
# https://eeperry.wordpress.com/2013/01/05/pygtk-new-style-python-class-using-builder/

import logging
import os

typelib_path = "/usr/lib/girepository-1.0"
if os.path.isdir(typelib_path):
    os.environ["GI_TYPELIB_PATH"] = typelib_path

import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("OsmGpsMap", "1.2")
except:
    gi.require_version("OsmGpsMap", "1.0")

from gi.repository import Gdk, Gtk

from gweatherrouting import log  # noqa: F401
from gweatherrouting.common import resource_path

from .charts import ChartManager
from .chartstack import ChartStack
from .gribmanagerwindow import GribManagerWindow
from .logsstack import LogsStack
from .polarstack import PolarStack
from .projectpropertieswindow import ProjectPropertiesWindow
from .settings import SettingsManager, SettingsWindow

logger = logging.getLogger("gweatherrouting")


class MainWindow:
    def __init__(self, core):
        self.core = core
        self.settings_manager = SettingsManager()

        # Add custom icon path
        Gtk.IconTheme.get_default().append_search_path(
            resource_path("gweatherrouting", "data/icons/")
        )

        # Force dark theme
        settings = Gtk.Settings.get_default()
        # settings.set_property("gtk-theme-name", "")
        settings.set_property("gtk-application-prefer-dark-theme", True)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            os.path.abspath(os.path.dirname(__file__)) + "/mainwindow.glade"
        )
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("main-window")
        self.window.set_title("GWeatherRouting")
        self.window.connect("delete-event", self.quit)
        self.window.set_default_size(1280, 768)
        self.window.show_all()
        self.window.maximize()

        self.builder.get_object("project-properties-button").hide()

        # Initialize chart manager
        self.chart_manager = ChartManager(self.settings_manager)
        self.chart_manager.load_base_chart(self.window)

        for x in self.settings_manager.vectorCharts:
            self.chart_manager.load_vector_layer(x["path"], x["metadata"], x["enabled"])

        for x in self.settings_manager.rasterCharts:
            self.chart_manager.load_raster_layer(x["path"], x["metadata"], x["enabled"])

        Gdk.threads_init()

        self.chartStack = ChartStack(
            self.window, self.chart_manager, self.core, self.settings_manager
        )
        self.builder.get_object("chartcontainer").pack_start(
            self.chartStack, True, True, 0
        )

        self.logsStack = LogsStack(
            self.window, self.chart_manager, self.core, self.settings_manager
        )
        self.builder.get_object("logscontainer").pack_start(
            self.logsStack, True, True, 0
        )

        self.builder.get_object("regattacontainertop").hide()
        # self.regattaStack = RegattaStack(self.window, self.chart_manager, self.core)
        # self.builder.get_object("regattacontainer").pack_start(self.regattaStack, True, True, 0)

        # self.builder.get_object("polarcontainertop").hide()
        self.polarStack = PolarStack(self.window, self.core, self.settings_manager)
        self.builder.get_object("polarcontainer").pack_start(
            self.polarStack, True, True, 0
        )

    def quit(self, a, b):
        logger.info("Quitting...")
        Gtk.main_quit()
        self.core.connectionManager.stop_polling()

    def on_about(self, item):
        dialog = self.builder.get_object("about-dialog")
        dialog.run()
        dialog.hide()

    def on_settings(self, event):
        w = SettingsWindow(self, self.settings_manager, self.core)
        w.show()

    def on_project_properties(self, event):
        w = ProjectPropertiesWindow()
        w.show()

    def on_grib_manager(self, event):
        w = GribManagerWindow(self.core.grib_manager, self.refresh_map)
        w.show()

    def refresh_map(self):
        if self.chartStack.map:
            self.chartStack.map.queue_draw()
            logger.debug("Map refresh requested")
        else:
            logger.warning("Could not refresh map: chartStack or map not available.")
