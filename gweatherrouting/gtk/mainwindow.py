# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
'''

# TODO:
# https://eeperry.wordpress.com/2013/01/05/pygtk-new-style-python-class-using-builder/

import gi
import os

from .chartstack import ChartStack
from .polarstack import PolarStack
from .regattastack import RegattaStack
from .logsstack import LogsStack

gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.2')

from gi.repository import Gtk, Gdk, GObject 

from .. import log
import logging

from .settings import SettingsWindow
from .projectpropertieswindow import ProjectPropertiesWindow
from .gribmanagerwindow import GribManagerWindow
from .charts import ChartManager
from .settings import SettingsManager

logger = logging.getLogger ('gweatherrouting')


class MainWindow:
	def __init__(self, core):
		self.core = core

		self.settingsManager = SettingsManager()

		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.abspath(os.path.dirname(__file__)) + "/mainwindow.glade")
		self.builder.connect_signals(self)

		self.window = self.builder.get_object("main-window")
		self.window.connect("delete-event", self.quit)
		self.window.set_default_size (1024, 600)
		self.window.show_all()
		# self.window.maximize ()

		self.builder.get_object("project-properties-button").hide()

		# Initialize chart manager
		self.chartManager = ChartManager()
		self.chartManager.loadBaseChart(self.window)
		
		for x in self.settingsManager.vectorCharts:
			l = self.chartManager.loadVectorLayer(x['path'], x['metadata'])

		for x in self.settingsManager.rasterCharts:
			l = self.chartManager.loadRasterLayer(x['path'], x['metadata'])


		Gdk.threads_init()

		self.chartStack = ChartStack(self.window, self.chartManager, self.core)
		self.builder.get_object("chartcontainer").pack_start(self.chartStack, True, True, 0)

		self.logsStack = LogsStack(self.window, self.chartManager, self.core)
		self.builder.get_object("logscontainer").pack_start(self.logsStack, True, True, 0)

		self.builder.get_object("regattacontainertop").hide()
		# self.regattaStack = RegattaStack(self.window, self.chartManager, self.core)
		# self.builder.get_object("regattacontainer").pack_start(self.regattaStack, True, True, 0)

		self.builder.get_object("polarcontainertop").hide()
		# self.polarStack = PolarStack(self.window, self.core)
		# self.builder.get_object("polarcontainer").pack_start(self.polarStack, True, True, 0)



	def quit(self, a, b):
		logger.info("Quitting...")
		Gtk.main_quit()

	def onAbout(self, item):
		dialog = self.builder.get_object('about-dialog')
		dialog.run ()
		dialog.hide ()

	def onSettings(self, event):
		w = SettingsWindow(self, self.settingsManager, self.core)
		w.show ()

	def onProjectProperties(self, event):
		w = ProjectPropertiesWindow()
		w.show ()

	def onGribManager(self, event):
		w = GribManagerWindow(self.core.gribManager)
		w.show ()
