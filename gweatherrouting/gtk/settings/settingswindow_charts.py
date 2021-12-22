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

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject, Gdk
from threading import Thread


class SettingsWindowCharts:
	def __init__(self, parent, settingsManager, core):
		self.builder.get_object('chart-progress').hide()
		self.reloadChart()

	def reloadChart(self):
		self.chartStore = self.builder.get_object("chart-store")
		self.chartStore.clear()

		for p in self.parent.chartManager.charts:
			self.chartStore.append ([p.path, p.enabled, p.ctype])

	def registeringChart(self, l, t):
		def ticker(x):
			Gdk.threads_enter()
			self.builder.get_object('chart-progress').set_fraction(x)
			Gdk.threads_leave()


		Gdk.threads_enter()
		self.builder.get_object('chart-progress').show()
		Gdk.threads_leave()

		if l.onRegister(ticker):
			vc = self.settingsManager[t + 'Charts']
			if not vc:
				vc = []

			vc.append({
				'path': l.path,
				'metadata': l.metadata
			})
			self.settingsManager[t+'Charts'] = vc

			self.reloadChart()
		else:
			# Show error
			pass

		Gdk.threads_enter()
		self.builder.get_object('chart-progress').hide()
		Gdk.threads_leave()

	def onAddRasterChart(self, widget):
		dialog = Gtk.FileChooserDialog ("Please select a directory", self.window,
			Gtk.FileChooserAction.SELECT_FOLDER,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

		response = dialog.run ()

		if response == Gtk.ResponseType.OK:
			path = dialog.get_filename () + '/'
			l = self.parent.chartManager.loadRasterLayer(path)
			dialog.destroy ()

			Thread(target=self.registeringChart, args=(l, 'raster', )).start()
		else:
			dialog.destroy ()
			

	def onAddVectorChart(self, widget):
		pass