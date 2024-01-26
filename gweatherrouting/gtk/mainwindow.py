# -*- coding: utf-8 -*-
# Copyright (C) 2017-2024 Davide Gessa
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

# TODO:
# https://eeperry.wordpress.com/2013/01/05/pygtk-new-style-python-class-using-builder/

import logging
import os

import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("OsmGpsMap", "1.2")
except:
    gi.require_version("OsmGpsMap", "1.0")

from gi.repository import Gdk, Gtk

from .. import log
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
        self.settingsManager = SettingsManager()

        # Add custom icon path
        Gtk.IconTheme.get_default().append_search_path(
            os.path.abspath(os.path.dirname(__file__)) + "/../data/icons"
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
        self.window.connect("delete-event", self.quit)
        self.window.set_default_size(1024, 600)
        self.window.show_all()
        # self.window.maximize ()

        self.builder.get_object("project-properties-button").hide()

        # Initialize chart manager
        self.chartManager = ChartManager(self.settingsManager)
        self.chartManager.loadBaseChart(self.window)

        for x in self.settingsManager.vectorCharts:
            self.chartManager.loadVectorLayer(x["path"], x["metadata"], x["enabled"])

        for x in self.settingsManager.rasterCharts:
            self.chartManager.loadRasterLayer(x["path"], x["metadata"], x["enabled"])

        Gdk.threads_init()

        self.chartStack = ChartStack(
            self.window, self.chartManager, self.core, self.settingsManager
        )
        self.builder.get_object("chartcontainer").pack_start(
            self.chartStack, True, True, 0
        )

        self.logsStack = LogsStack(
            self.window, self.chartManager, self.core, self.settingsManager
        )
        self.builder.get_object("logscontainer").pack_start(
            self.logsStack, True, True, 0
        )

        self.builder.get_object("regattacontainertop").hide()
        # self.regattaStack = RegattaStack(self.window, self.chartManager, self.core)
        # self.builder.get_object("regattacontainer").pack_start(self.regattaStack, True, True, 0)

        # self.builder.get_object("polarcontainertop").hide()
        self.polarStack = PolarStack(self.window, self.core, self.settingsManager)
        self.builder.get_object("polarcontainer").pack_start(
            self.polarStack, True, True, 0
        )

    def quit(self, a, b):
        logger.info("Quitting...")
        Gtk.main_quit()
        self.core.connectionManager.stopPolling()

    def onAbout(self, item):
        dialog = self.builder.get_object("about-dialog")
        dialog.run()
        dialog.hide()

    def onSettings(self, event):
        w = SettingsWindow(self, self.settingsManager, self.core)
        w.show()

    def onProjectProperties(self, event):
        w = ProjectPropertiesWindow()
        w.show()

    def onGribManager(self, event):
        w = GribManagerWindow(self.core.gribManager)
        w.show()
