import gi

gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap, Gdk


class MainWindowTime:
	play = False

	def __init__(self):
		self.time_adjust = self.builder.get_object('time-adjustment')

	def onPlayClick(self, event):
		self.play = True
		GObject.timeout_add (10, self.onPlayStep)

	def onPlayStep(self):
		self.onFowardClick(None)
		if self.play:
			GObject.timeout_add (1000, self.onPlayStep)

	def onStopClick(self, event):
		self.play = False

	def onFowardClick(self, event):
		self.gribMapLayer.time += 1
		self.map.queue_draw ()
		self.updateTimeSlider()

	def onBackwardClick(self, event):
		if self.gribMapLayer.time > 0:
			self.gribMapLayer.time -= 1
			self.map.queue_draw ()
			self.updateTimeSlider()

	def updateTimeSlider(self):
		self.time_adjust.set_value(int(self.gribMapLayer.time))

	def onTimeSlide (self, widget):
		self.gribMapLayer.time = int (self.time_adjust.get_value())
		self.map.queue_draw ()