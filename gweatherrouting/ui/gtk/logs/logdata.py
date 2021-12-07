import nmeatoolkit as nt 
import cairo
import matplotlib.pyplot as plt
import io
import numpy
import PIL


class LogData:
	def __init__(self, connManager, graphArea, map):
		self.conn = connManager
		self.graphArea = graphArea
		self.map = map
		self.recording = False
		self.data = []

		self.maxSpeed = 0
		self.maxAWS = 0

	def loadFromFile(self, filepath):
		ext = filepath.split('.')[-1]

		# TODO: support for gpx files 

		pip = nt.Pipeline(
			nt.FileInput(filepath),
			None,
			nt.TrackPointTranslator(),
			[
				nt.SeatalkPipe(),
				nt.TrueWindPipe()
			]
		)
		res = pip.runPartial()
		self.data = res[1::]

		for x in self.data:
			if x.speed and x.speed > self.maxSpeed:
				self.maxSpeed = x.speed
			if x.aws and x.aws > self.maxAWS:
				self.maxAWS = x.aws

	def saveToFile(self, filepath):
		pass 

	def startRecording(self):
		pass 

	def clear(self):
		self.data = []

	def draw(self, widget, ctx):
		if self.data == []:
			return 

		fig  = plt.figure(figsize=(8,2),facecolor = 'white', dpi=100)

		x = numpy.array([x.time for x in self.data])
		plt.plot(x, list(map(lambda x: x.speed, self.data)))	
		plt.plot(x, list(map(lambda x: x.aws, self.data)))	
		plt.plot(x, list(map(lambda x: x.depth, self.data)))	
	
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



