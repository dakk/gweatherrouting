# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
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

from threading import Thread
import gi
import os
import json
import math

from gweatherrouting.ui.gtk.logs.logdata import LogData
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject


class LogsWidget(Gtk.Box):		
	def __init__(self, chartManager, connManager):
		Gtk.Widget.__init__(self)

		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.abspath(os.path.dirname(__file__)) + "/logscontent.glade")
		self.builder.connect_signals(self)

		# self.set_default_size (800, 600)


		self.pack_start(self.builder.get_object("logscontent"), True, True, 0)
		self.graphArea = self.builder.get_object("grapharea")

		self.show_all()


		self.map = self.builder.get_object("map")
		self.map.set_center_and_zoom (39., 9., 6)
		# self.map.layer_add (chartManager)

		self.logData = LogData(connManager, self.graphArea, self.map)
		self.builder.get_object('stop-button').hide()
		self.builder.get_object('loading-progress').hide()

		self.recordinThread = None 
		self.loadingThread = None


	
	def onLoadClick(self, widget):
		dialog = Gtk.FileChooserDialog ("Please choose a file", self,
					Gtk.FileChooserAction.OPEN,
					(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
			
		filter_nmea = Gtk.FileFilter ()		
		filter_nmea.set_name ("NMEA log")
		# filter_nmea.add_mime_type ("application/gpx+xml")
		filter_nmea.add_pattern ('*.nmea')
		dialog.add_filter (filter_nmea)

		# filter_gpx = Gtk.FileFilter ()		
		# filter_gpx.set_name ("GPX track file")
		# filter_gpx.add_mime_type ("application/gpx+xml")
		# filter_gpx.add_pattern ('*.gpx')
		# dialog.add_filter (filter_gpx)

		response = dialog.run()
		
		if response == Gtk.ResponseType.OK:
			filepath = dialog.get_filename ()
			dialog.destroy ()

			try:
				self.builder.get_object('loading-progress').show()
				self.builder.get_object('loading-progress').set_fraction(0.1)
				self.builder.get_object('loading-progress').set_text("Loading %s" % filepath)
				self.loadingThread = Thread(target=self.logData.loadFromFile, args=(filepath, self.onLogLoadPercentage, self.onLogLoadCompleted,))
				self.loadingThread.start ()
			except Exception as e:
				print(e)
				edialog = Gtk.MessageDialog (self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Error")
				edialog.format_secondary_text ("Cannot open file: %s" % filepath)
				edialog.run ()
				edialog.destroy ()
		else:
			dialog.destroy()

	def __del__(self):
		if self.logData.recording:
			self.logData.stopRecording()
			self.recordinThread.join()

		if self.loadingThread:
			self.loadingThread.join()
			

	def clearData(self, widget):
		self.logData.clearData()

	def startRecording(self, widget):
		if self.logData.recording:
			return 

		self.builder.get_object('record-button').hide()
		self.builder.get_object('stop-button').show()
		self.recordinThread = Thread(target=self.logData.startRecording, args=())
		self.recordinThread.start()

	def stopRecording(self, widget):
		self.logData.stopRecording()
		self.builder.get_object('record-button').show()
		self.builder.get_object('stop-button').hide()
		self.recordinThread.join()

	def onLogLoadPercentage (self, s):
		if s % 1000 == 0:
			print ('Loading log file: %d sentences' % s)
			self.builder.get_object('loading-progress').set_fraction(0.5)
			self.builder.get_object('loading-progress').set_text("%d points" % s)

	def onLogLoadCompleted (self):
		self.builder.get_object('loading-progress').set_fraction(1.)
		self.builder.get_object('loading-progress').set_text("Load completed!")
		GObject.timeout_add (3000, self.builder.get_object('loading-progress').hide)

	def onGraphDraw(self, widget, cr):
		self.logData.draw(widget, cr)

	def toggleSpeedChart(self, widget):
		self.logData.speedChart = not self.logData.speedChart
		self.graphArea.queue_draw()		

	def toggleApparentWindChart(self, widget):
		self.logData.apparentWindChart = not self.logData.apparentWindChart
		self.graphArea.queue_draw()

	def toggleTrueWindChart(self, widget):
		self.logData.trueWindChart = not self.logData.trueWindChart
		self.graphArea.queue_draw()

	def toggleDepthChart(self, widget):
		self.logData.depthChart = not self.logData.depthChart
		self.graphArea.queue_draw()

	def toggleHDGChart(self, widget):
		self.logData.hdgChart = not self.logData.hdgChart
		self.graphArea.queue_draw()
