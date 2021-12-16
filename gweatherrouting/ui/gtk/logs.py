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
import nmeatoolkit as nt 
import cairo
import matplotlib.pyplot as plt
import io
import numpy
import PIL
import gi
from datetime import datetime 

gi.require_version('OsmGpsMap', '1.2')
gi.require_version('Gtk', '3.0')
gi.require_version('Dazzle', '1.0')

from gi.repository import Gtk, Gio, GLib, GObject, OsmGpsMap, Gdk 
from threading import Lock
import logging

logger = logging.getLogger ('gweatherrouting')


class LogsWidget(Gtk.Box, nt.Output, nt.Input):		
	def __init__(self, parent, chartManager, connManager):
		Gtk.Widget.__init__(self)

		self.parent = parent
		self.conn = connManager
		self.recording = False
		self.data = []
		self.track = None
		self.recordedData = None
		self.toSend = []

		self.depthChart = False
		self.speedChart = True
		self.apparentWindChart = False
		self.trueWindChart = True
		self.hdgChart = True
		self.rwChart = False

		self.conn.connect("data", self.dataHandler)

		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.abspath(os.path.dirname(__file__)) + "/logs.glade")
		self.builder.connect_signals(self)

		self.pack_start(self.builder.get_object("logscontent"), True, True, 0)
		self.graphArea = self.builder.get_object("grapharea")

		self.show_all()

		self.map = self.builder.get_object("map")
		self.map.set_center_and_zoom (39., 9., 6)
		# self.map.layer_add (chartManager)

		self.builder.get_object('stop-button').hide()
		self.builder.get_object('loading-progress').hide()

		self.recordinThread = None 
		self.loadingThread = None

		try:
			self.loadingThread = Thread(target=self.loadFromFile, args=('/tmp/gwr-recording.log',))
			self.loadingThread.start ()
		except:
			pass 

	
	def onLoadClick(self, widget):
		dialog = Gtk.FileChooserDialog ("Please choose a file", self.parent,
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
				self.loadingThread = Thread(target=self.loadFromFile, args=(filepath,))
				self.loadingThread.start ()
			except Exception as e:
				print(e)
				edialog = Gtk.MessageDialog (self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Error")
				edialog.format_secondary_text ("Cannot open file: %s" % filepath)
				edialog.run ()
				edialog.destroy ()
		else:
			dialog.destroy()

	def __del__(self):
		if self.recording:
			self.stopRecording()
			self.recordinThread.join()

		if self.loadingThread:
			self.loadingThread.join()
			

	def clearData(self, widget):
		self.clearData()

	def onRecordingClick(self, widget):
		if self.recording:
			return 

		self.builder.get_object('record-button').hide()
		self.builder.get_object('stop-button').show()

		self.builder.get_object('loading-progress').show()
		self.builder.get_object('loading-progress').set_fraction(0.1)
		self.builder.get_object('loading-progress').set_text("Recording from devices...")
		self.recordinThread = Thread(target=self.startRecording, args=())
		self.recordinThread.start()

	def onStopRecordingClick(self, widget):
		self.recording = False
		self.recordedData.close()
		self.toSend = []
		logger.debug("Stopping recording...")

		self.builder.get_object('record-button').show()
		self.builder.get_object('stop-button').hide()
		self.builder.get_object('loading-progress').hide()
		self.recordinThread.join()

	def onLogLoadPercentage (self, s):
		self.builder.get_object('loading-progress').set_fraction(0.5)
		self.builder.get_object('loading-progress').set_text("%d points" % s)

	def onLogLoadCompleted (self):
		self.builder.get_object('loading-progress').set_fraction(1.)
		self.builder.get_object('loading-progress').set_text("Load completed!")
		GObject.timeout_add (3000, self.builder.get_object('loading-progress').hide)


	def toggleSpeedChart(self, widget):
		self.speedChart = not self.speedChart
		self.graphArea.queue_draw()		

	def toggleApparentWindChart(self, widget):
		self.apparentWindChart = not self.apparentWindChart
		self.graphArea.queue_draw()

	def toggleTrueWindChart(self, widget):
		self.trueWindChart = not self.trueWindChart
		self.graphArea.queue_draw()

	def toggleDepthChart(self, widget):
		self.depthChart = not self.depthChart
		self.graphArea.queue_draw()

	def toggleHDGChart(self, widget):
		self.hdgChart = not self.hdgChart
		self.graphArea.queue_draw()

	def toggleRWChart(self, widget):
		self.rwChart = not self.rwChart
		self.graphArea.queue_draw()


	def dataHandler(self, d):
		if self.recording:
			for x in d:
				self.recordedData.write(str(x.data) + '\n')
				self.toSend.append(x.data)

	def readSentence(self):
		if len(self.toSend) > 0:
			return self.toSend.pop(0)
		return None 		

	def end(self):
		return not self.recording

	def write(self, x):
		if not x or not isinstance(x, nt.TrackPoint):
			return None

		self.data.append(x)		

		if len(self.data) % 150 == 0 or (self.recording or len(self.data) % 5000 == 0):
			Gdk.threads_enter()

			if len(self.data) % 150 == 0:
				point = OsmGpsMap.MapPoint.new_degrees(x.lat, x.lon)
				self.track.add_point(point)
			
			if self.recording or len(self.data) % 5000 == 0:
				self.map.set_center_and_zoom (x.lat, x.lon, 12)
				logger.debug("Recorded %d points" % len(self.data))
				self.onLogLoadPercentage(len(self.data))
			
			Gdk.threads_leave()


	def close(self):
		if len(self.data) < 2:
			return

		self.data = self.data[1::]

		Gdk.threads_enter()
		self.map.set_center_and_zoom (self.data[0].lat, self.data[0].lon, 12)
		self.map.queue_draw()
		self.graphArea.queue_draw()
		Gdk.threads_leave()


	def loadFromFile(self, filepath):
		self.data = []
		ext = filepath.split('.')[-1]

		# TODO: support for gpx files 

		if self.track:
			self.map.track_remove(self.track)

		self.track = OsmGpsMap.MapTrack()
		self.map.track_add(self.track)
		self.track.set_property('line-width', 1)

		pip = nt.Pipeline(
			nt.FileInput(filepath),
			self,
			nt.TrackPointTranslator(),
			[
				#nt.SeatalkPipe(),
				nt.FilterPipe(exclude=["ALK", "VDM"]),
				nt.TrueWindPipe()
			]
		)
		pip.run()
		self.onLogLoadCompleted()


	def saveToFile(self, filepath):
		pass 

	def clearData(self, widget):
		self.data = []
	
		if self.recordedData:
			self.recordedData.close()
		self.recordedData = open('/tmp/gwr-recording.log', 'w')
		self.toSend = []
		if self.track:
			self.map.track_remove(self.track)		
		self.track = OsmGpsMap.MapTrack()
		self.track.set_property('line-width', 1)
		self.map.track_add(self.track)
		self.map.queue_draw()
		self.graphArea.queue_draw()
		logger.debug("Data cleared")

	def startRecording(self):
		logger.debug("Recording started")
		self.recording = True
		self.recordedData = open('/tmp/gwr-recording.log', 'w')

		if not self.track:
			self.track = OsmGpsMap.MapTrack()
			self.track.set_property('line-width', 1)
			self.map.track_add(self.track)

		pip = nt.Pipeline(
			self,
			self,
			nt.TrackPointTranslator(),
			[
				#nt.SeatalkPipe(),
				nt.FilterPipe(exclude=["ALK", "VDM"]),
				nt.TrueWindPipe()
			]
		)

		r = True
		while self.recording and r:
			r = pip.runOnce()
		logger.debug("Recording stopped")



	def onGraphDraw(self, widget, ctx):
		s = 20
		a = widget.get_allocation()

		if self.data == []:
			return 

		import matplotlib.pyplot as plt
		plt.style.use('dark_background')
		plt.rcParams.update({'font.size': 8})
		y = self.data[::s]
		x = numpy.array([x.time for x in y])

		nplots = 1

		if self.hdgChart or self.apparentWindChart or self.trueWindChart:
			nplots += 1
		
		if self.speedChart:
			nplots += 1

		if self.depthChart:
			nplots += 1

		fig, ax1 = plt.subplots(nplots)
		try:
			ax1[0] 
		except:
			ax1 = [ax1]
		fig.set_size_inches((a.width / 100), (a.height / 100.))

		i = 0

		if self.speedChart:
			if i < nplots - 1:
				plt.setp(ax1[i].get_xticklabels(), visible=False)

			ax1[i].plot(x, list(map(lambda x: x.speed if x.speed else 0, y)), color='#8dd3c7', linewidth=0.6,label='Speed')	
			ax1[i].legend()
			i+=1
		if self.apparentWindChart or self.trueWindChart:
			if i < nplots - 1:
				plt.setp(ax1[i].get_xticklabels(), visible=False)

			if self.apparentWindChart:
				ax1[i].plot(x, list(map(lambda x: x.aws if x.aws else 0, y)), color='#feffb3', linewidth=0.6,label='AWS')
				ax1[i].legend()
			if self.trueWindChart:
				ax1[i].plot(x, list(map(lambda x: x.tws if x.tws else 0, y)), color='#bfbbd9', linewidth=0.6,label='TWS')
				ax1[i].legend()
			i+=1

		if self.depthChart:
			if i < nplots - 1:
				plt.setp(ax1[i].get_xticklabels(), visible=False)

			ax1[i].plot(x, list(map(lambda x: x.depth if x.depth else 0, y)), color='#fa8174', linewidth=0.6,label='Depth')	
			ax1[i].legend()
			i += 1


		if self.hdgChart or self.apparentWindChart or self.trueWindChart:
			if i < nplots - 1:
				plt.setp(ax1[i].get_xticklabels(), visible=False)

			ax2 = ax1[i]
			
			if self.apparentWindChart:
				if self.rwChart:
					ax2.plot(x, list(map(lambda x: x.awa if x.awa else 0, y)), color='#fe11b3', linewidth=0.3,label='AWA')
				ax2.plot(x, list(map(lambda x: (x.awa + x.hdg) % 360 if x.awa else 0, y)), color='#feffb3', linewidth=0.6,label='AWD')
			if self.trueWindChart:
				if self.rwChart:
					ax2.plot(x, list(map(lambda x: x.twa if x.twa else 0, y)), color='#bf11d9', linewidth=0.3,label='TWA')
				ax2.plot(x, list(map(lambda x: (x.twa + x.hdg) % 360 if x.twa else 0, y)), color='#bfbbd9', linewidth=0.6,label='TWD')
			if self.hdgChart:
				ax2.plot(x, list(map(lambda x: x.hdg if x.hdg else 0, y)), color='#81b1d2', linewidth=0.6,label='HDG')

			ax2.legend()

	
		plt.tight_layout()
		buf = io.BytesIO()
		plt.savefig(buf, dpi=100)
		buf.seek(0)
		buf2 = PIL.Image.open(buf)
	
		arr = numpy.array(buf2)
		height, width, channels = arr.shape
		surface = cairo.ImageSurface.create_for_data(arr, cairo.FORMAT_RGB24, width, height)

		ctx.save()
		ctx.set_source_surface (surface, 0, 0)
		ctx.paint()
		ctx.restore()

		fig.clf()
		plt.close(fig)
