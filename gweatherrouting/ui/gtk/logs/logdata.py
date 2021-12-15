import nmeatoolkit as nt 
import cairo
import matplotlib.pyplot as plt
import io
import numpy
import PIL
import gi

gi.require_version('OsmGpsMap', '1.2')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap, Gdk
from threading import Lock
import logging

logger = logging.getLogger ('gweatherrouting')

class LogData(nt.Output, nt.Input):
	def __init__(self, connManager, graphArea, map):
		self.conn = connManager
		self.graphArea = graphArea
		self.map = map
		self.recording = False
		self.data = []
		self.track = None
		self.recordedData = []
		self.toSend = []

		self.depthChart = False
		self.speedChart = True
		self.apparentWindChart = False
		self.trueWindChart = True
		self.hdgChart = True

		self.conn.connect("data", self.dataHandler)
		self.llperc = None


	def dataHandler(self, d):
		if self.recording:
			for x in d:
				self.recordedData.append(x.data)
				self.toSend.append(x.data)

	def readSentence(self):
		if len(self.toSend) > 0:
			return self.toSend.pop(0)
		return None 		

	def end(self):
		return not self.recording

	def write(self, x):
		if not x or not isinstance(x, nt.TrackPoint) or not self.recording:
			return None

		self.data.append(x)
		
		Gdk.threads_enter()
		point = OsmGpsMap.MapPoint.new_degrees(x.lat, x.lon)
		self.track.add_point(point)

		self.map.set_center_and_zoom (x.lat, x.lon, 12)
		self.map.queue_draw()

		if len(self.data) % 20 == 1:
			self.graphArea.queue_draw()
			logger.debug("Recorded %d points" % len(self.data))

		if self.llperc:
			self.llperc(len(self.data))
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
		self.llperc = None


	def loadFromFile(self, filepath, llperc, llcomplete):
		self.llperc = llperc
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
				nt.SeatalkPipe(),
				nt.TrueWindPipe()
			]
		)
		pip.run()
		llcomplete()


	def saveToFile(self, filepath):
		pass 

	def stopRecording(self):
		self.recording = False
		self.toSend = []
		logger.debug("Stopping recording...")


	def clearData(self):
		self.data = []
		self.recordedData = []
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

		if not self.track:
			self.track = OsmGpsMap.MapTrack()
			self.track.set_property('line-width', 1)
			self.map.track_add(self.track)

		pip = nt.Pipeline(
			self,
			self,
			nt.TrackPointTranslator(),
			[
				nt.SeatalkPipe(),
				nt.TrueWindPipe()
			]
		)

		r = True
		while self.recording and r:
			r = pip.runOnce()
		logger.debug("Recording stopped")



	def draw(self, widget, ctx):
		s = 20
		a = widget.get_allocation()

		if self.data == []:
			return 

		import matplotlib.pyplot as plt
		plt.style.use('dark_background')
		plt.rcParams.update({'font.size': 8})
		x = numpy.array([x.time for x in self.data[::s]])

		fig, ax1 = plt.subplots(2 if self.hdgChart or self.apparentWindChart or self.trueWindChart else 1)
		fig.set_size_inches((a.width / 100), (a.height / 100.))

		if not (self.hdgChart or self.apparentWindChart or self.trueWindChart):
			ax1 = [ax1]

		if self.speedChart:
			ax1[0].plot(x, list(map(lambda x: x.speed if x.speed else 0, self.data[::s])), color='#8dd3c7', linewidth=0.6,label='Speed')	
		if self.apparentWindChart:
			ax1[0].plot(x, list(map(lambda x: x.aws if x.aws else 0, self.data[::s])), color='#feffb3', linewidth=0.6,label='AWS')
		if self.trueWindChart:
			ax1[0].plot(x, list(map(lambda x: x.tws if x.tws else 0, self.data[::s])), color='#bfbbd9', linewidth=0.6,label='TWS')
		if self.depthChart:
			ax1[0].plot(x, list(map(lambda x: x.depth if x.depth else 0, self.data[::s])), color='#fa8174', linewidth=0.6,label='Depth')	
		
		ax1[0].legend()


		if self.hdgChart or self.apparentWindChart or self.trueWindChart:
			ax2 = ax1[1]
			
			plt.setp(ax1[0].get_xticklabels(), visible=False)
			
			if self.apparentWindChart:
				ax2.plot(x, list(map(lambda x: x.awa if x.awa else 0, self.data[::s])), color='#feffb3', linewidth=0.6,label='AWA')
			if self.trueWindChart:
				ax2.plot(x, list(map(lambda x: x.twa if x.twa else 0, self.data[::s])), color='#bfbbd9', linewidth=0.6,label='TWA')
			if self.hdgChart:
				ax2.plot(x, list(map(lambda x: x.hdg if x.hdg else 0, self.data[::s])), color='#81b1d2', linewidth=0.6,label='HDG')

			ax2.legend()

	
		plt.tight_layout()
		buf = io.BytesIO()
		plt.savefig(buf, dpi=100)
		buf.seek(0)
		buf2= PIL.Image.open(buf)
	
		arr = numpy.array(buf2)
		height, width, channels = arr.shape
		surface = cairo.ImageSurface.create_for_data(arr, cairo.FORMAT_RGB24, width, height)

		ctx.save()
		ctx.set_source_surface (surface, 0, 0)
		ctx.paint()
		ctx.restore()

		fig.clf()
		plt.close(fig)
