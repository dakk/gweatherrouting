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

		self.depthChart = False
		self.speedChart = True
		self.apparentWindChart = False
		self.trueWindChart = True
		self.hdgChart = True


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

		# TODO: add poitns to map using track 


	def saveToFile(self, filepath):
		pass 

	def startRecording(self):
		pass 

	def clear(self):
		self.data = []

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
