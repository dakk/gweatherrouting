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

from threading import Thread
import gi
import os
import nmeatoolkit as nt 
import cairo
import io
import numpy
import PIL
import gi

from gweatherrouting.core.timecontrol import TimeControl
from gweatherrouting.ui.gtk.widgets.timetravel import TimeTravelWidget 

gi.require_version('OsmGpsMap', '1.2')
gi.require_version('Gtk', '3.0')
gi.require_version('Dazzle', '1.0')

from gi.repository import Gtk, OsmGpsMap, Gdk 
from threading import Lock
import logging

logger = logging.getLogger ('gweatherrouting')

LOG_TEMP_FILE = '/tmp/gwr-recording.log'

class LogsStack(Gtk.Box, nt.Output, nt.Input):		
	def __init__(self, parent, chartManager, core):
		Gtk.Widget.__init__(self)

		self.parent = parent
		self.core = core
		self.recording = False
		self.loading = False 
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

		self.cropA = None 
		self.cropB = None 

		self.core.connectionManager.connect("data", self.dataHandler)

		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.abspath(os.path.dirname(__file__)) + "/logsstack.glade")
		self.builder.connect_signals(self)

		self.pack_start(self.builder.get_object("logscontent"), True, True, 0)
		self.graphArea = self.builder.get_object("grapharea")


		self.statusBar = self.builder.get_object("statusbar")

		self.show_all()

		self.map = self.builder.get_object("map")
		self.map.set_center_and_zoom (39., 9., 6)
		# self.map.layer_add (chartManager)


		self.timeControl = TimeControl()
		self.selectedTime = self.timeControl.getTime()
		self.timetravelWidget = TimeTravelWidget(self.parent, self.timeControl, self.map, True)
		self.timeControl.connect('time-change', self.onTimeChange)
		self.builder.get_object("timetravelcontainer").pack_start(self.timetravelWidget, True, True, 0)

		self.show_all()

		self.builder.get_object('stop-button').hide()

		self.recordinThread = None 
		self.loadingThread = None

		try:
			self.loadingThread = Thread(target=self.loadFromFile, args=(LOG_TEMP_FILE,))
			self.loadingThread.start ()
		except:
			pass 

	def onTimeChange(self, time):
		self.selectedTime = time
		if not self.recording and not self.loading:
			self.graphArea.queue_draw()
			self.map.queue_draw()
	
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
				self.statusBar.push(0, "Loading %s" % filepath)
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
			
	def setCropA(self, widget):
		self.cropA = self.selectedTime
		self.graphArea.queue_draw()
			
	def setCropB(self, widget):
		self.cropB = self.selectedTime
		self.graphArea.queue_draw()
	
	def cropData(self, widget):
		if self.cropA == None and self.cropB == None:
			return

		if self.cropA == None:
			self.cropA = self.data[0].time

		if self.cropB == None:
			self.cropB = self.data[-1].time

		self.data = [d for d in self.data if d.time >= self.cropA and d.time <= self.cropB]


		self.rebuildTrack()
		self.graphArea.queue_draw()
		
		if self.recordedData:
			self.recordedData.flush()
			self.recordedData.close()
		os.system('mv %s %s.2' % (LOG_TEMP_FILE, LOG_TEMP_FILE))
		pip = nt.Pipeline(
			nt.FileInput(LOG_TEMP_FILE + ".2"),
			nt.FileOutput(LOG_TEMP_FILE),
			nt.ToStringTranslator(),
			[ nt.CropPipe(self.cropA, self.cropB) ]
		)
		pip.run()
		os.system('rm %s.2' % LOG_TEMP_FILE)
		self.cropA = None
		self.cropB = None

	def onRecordingClick(self, widget):
		if self.recording:
			return 

		self.builder.get_object('record-button').hide()
		self.builder.get_object('stop-button').show()

		self.statusBar.push(0, "Recording from devices...")
		self.recordinThread = Thread(target=self.startRecording, args=())
		self.recordinThread.start()

	def onStopRecordingClick(self, widget):
		self.recording = False
		self.recordedData.close()
		self.toSend = []
		logger.debug("Stopping recording...")

		self.builder.get_object('record-button').show()
		self.builder.get_object('stop-button').hide()
		self.statusBar.push(0, "Recording stopped")

		self.recordinThread.join()

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
			self.timeControl.setTime(x.time)	

			if len(self.data) % 150 == 0:
				point = OsmGpsMap.MapPoint.new_degrees(x.lat, x.lon)
				self.track.add_point(point)
			
			if self.recording or len(self.data) % 5000 == 0:
				self.map.set_center_and_zoom (x.lat, x.lon, 12)
				logger.debug("Recorded %d points" % len(self.data))
				self.statusBar.push(0, "%s track points" % len(self.data))
			
			Gdk.threads_leave()


	def close(self):
		if len(self.data) < 2:
			return

		self.data = self.data[1::]

		Gdk.threads_enter()
		self.map.set_center_and_zoom (self.data[0].lat, self.data[0].lon, 12)
		self.map.queue_draw()
		self.graphArea.queue_draw()
		self.loading = False
		Gdk.threads_leave()

	def onSaveClick(self, widget):
		dialog = Gtk.FileChooserDialog("Save log", self.parent, Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
		dialog.set_do_overwrite_confirmation(True)
		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			filename = dialog.get_filename()
			dialog.destroy()
			os.system('cp %s %s' % (LOG_TEMP_FILE, filename))

			self.statusBar.push(0, "Saved to %s" % filename)
		else:
			dialog.destroy()

	def loadFromFile(self, filepath):
		self.loading = True
		self.data = []
		ext = filepath.split('.')[-1]

		# TODO: support for gpx files 

		if self.track:
			self.map.track_remove(self.track)

		self.track = OsmGpsMap.MapTrack()
		self.map.track_add(self.track)
		self.track.set_property('line-width', 1)

		try:
			fi = nt.FileInput(filepath)
		except:
			logger.error("Error loading file %s" % filepath)
			self.loading = False
			return


		pip = nt.Pipeline(
			fi,
			self,
			nt.TrackPointTranslator(),
			[
				#nt.SeatalkPipe(),
				nt.FilterPipe(exclude=["ALK", "VDM"]),
				nt.TrueWindPipe()
			]
		)
		pip.run()

		if filepath != LOG_TEMP_FILE:
			os.system('cp %s %s' % (filepath, LOG_TEMP_FILE))
		# self.statusBar.push(0, "Load completed!")


	def saveToFile(self, filepath):
		pass 

	def clearData(self, widget):
		self.data = []
	
		if self.recordedData:
			self.recordedData.close()
		self.recordedData = open(LOG_TEMP_FILE, 'w')
		self.toSend = []
		if self.track:
			self.map.track_remove(self.track)		
		self.track = OsmGpsMap.MapTrack()
		self.track.set_property('line-width', 1)
		self.map.track_add(self.track)
		self.map.queue_draw()
		self.graphArea.queue_draw()
		logger.debug("Data cleared")

	def rebuildTrack(self):
		if self.track:
			self.map.track_remove(self.track)		
		self.track = OsmGpsMap.MapTrack()
		self.track.set_property('line-width', 1)
		self.map.track_add(self.track)
		for x in self.data[0::150]:
			point = OsmGpsMap.MapPoint.new_degrees(x.lat, x.lon)
			self.track.add_point(point)
		self.map.queue_draw()

	def startRecording(self):
		logger.debug("Recording started")
		self.recording = True
		self.recordedData = open(LOG_TEMP_FILE, 'w')

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
		width = a.width

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
		fig.set_size_inches((width / 100), (a.height / 100.))

		i = 0
		ii = -1
		self.highlightedValues = None 
		self.statusBar.push(0, "")

		if not self.recording and not self.loading:
			ii = numpy.where((x > (numpy.datetime64(self.selectedTime))) & (x < (numpy.datetime64(self.selectedTime) + numpy.timedelta64(self.timetravelWidget.getChangeUnit(), 's'))))
			try:
				ii = ii[0][0]
				self.highlightedValue = y[ii]
				self.map.gps_clear()
				self.map.gps_add(self.highlightedValue.lat, self.highlightedValue.lon, self.highlightedValue.hdg)

				self.statusBar.push(0, "Time: %s, Position: (%.2f, %.2f), Speed: %.1fkn, Heading: %d, TWS: %.1fkn, TWA: %d, TWD: %d, Depth: %.2f" % (self.selectedTime, self.highlightedValue.lat, self.highlightedValue.lon, self.highlightedValue.speed, self.highlightedValue.hdg, self.highlightedValue.tws, self.highlightedValue.twa, (self.highlightedValue.twa + self.highlightedValue.hdg) % 360, self.highlightedValue.depth))
			except:
				ii = -1

		def highlight(i, data):
			if(ii != -1):
				ax1[i].plot(x[ii], data[ii], color='#f00', marker='o', markersize=4)
				# ax1[i].axvline(x=ii)

			

		if self.speedChart:
			if i < nplots - 1:
				plt.setp(ax1[i].get_xticklabels(), visible=False)

			data = list(map(lambda x: x.speed if x.speed else 0, y))
			ax1[i].plot(x, data, color='#8dd3c7', linewidth=0.6,label='Speed')	

			highlight(i, data)

			ax1[i].legend()
			i+=1
		if self.apparentWindChart or self.trueWindChart:
			if i < nplots - 1:
				plt.setp(ax1[i].get_xticklabels(), visible=False)

			if self.apparentWindChart:
				data = list(map(lambda x: x.aws if x.aws else 0, y))
				ax1[i].plot(x, data, color='#feffb3', linewidth=0.6,label='AWS')
				ax1[i].legend()

				highlight(i, data)
			if self.trueWindChart:
				data = list(map(lambda x: x.tws if x.tws else 0, y))
				ax1[i].plot(x, data, color='#bfbbd9', linewidth=0.6,label='TWS')
				ax1[i].legend()
				
				highlight(i, data)
			i+=1

		if self.depthChart:
			if i < nplots - 1:
				plt.setp(ax1[i].get_xticklabels(), visible=False)

			data = list(map(lambda x: x.depth if x.depth else 0, y))
			ax1[i].plot(x, data, color='#fa8174', linewidth=0.6,label='Depth')	
			ax1[i].legend()

			highlight(i, data)
			i += 1


		if self.hdgChart or self.apparentWindChart or self.trueWindChart:
			if i < nplots - 1:
				plt.setp(ax1[i].get_xticklabels(), visible=False)

			ax2 = ax1[i]
			
			if self.apparentWindChart:
				if self.rwChart:
					data = list(map(lambda x: x.awa if x.awa else 0, y))
					ax2.plot(x, data, color='#fe11b3', linewidth=0.3,label='AWA')
					highlight(i, data)

				data = list(map(lambda x: (x.awa + x.hdg) % 360 if x.awa else 0, y))
				ax2.plot(x, data, color='#feffb3', linewidth=0.6,label='AWD')
				highlight(i, data)
			if self.trueWindChart:
				if self.rwChart:
					data = list(map(lambda x: x.twa if x.twa else 0, y))
					ax2.plot(x, data, color='#bf11d9', linewidth=0.3,label='TWA')
					highlight(i, data)

				data = list(map(lambda x: (x.twa + x.hdg) % 360 if x.twa else 0, y))
				ax2.plot(x, data, color='#bfbbd9', linewidth=0.6,label='TWD')

				highlight(i, data)
			if self.hdgChart:
				data = list(map(lambda x: x.hdg if x.hdg else 0, y))
				ax2.plot(x, data, color='#81b1d2', linewidth=0.6,label='HDG')

				highlight(i, data)

			ax2.legend()

		if self.cropA != None:
			try:
				ii = numpy.where((x > (numpy.datetime64(self.cropA))) & (x < (numpy.datetime64(self.cropA) + numpy.timedelta64(self.timetravelWidget.getChangeUnit(), 's'))))
				for axx in ax1:
					axx.axvline(x=x[ii[0][0]], color='#ffffff', linewidth=0.5)
			except:
				pass 

		if self.cropB != None:
			try:
				ii = numpy.where((x > (numpy.datetime64(self.cropB))) & (x < (numpy.datetime64(self.cropB) + numpy.timedelta64(self.timetravelWidget.getChangeUnit(), 's'))))
				for axx in ax1:
					axx.axvline(x=x[ii[0][0]], color='#ffffff', linewidth=0.5)
			except:
				pass

	
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
