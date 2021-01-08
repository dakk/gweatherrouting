import gi
import os

from .gdalvectorchart import GDALVectorChart

gi.require_version("Gtk", "3.0")
gi.require_version("OsmGpsMap", "1.0")

from gi.repository import Gtk, Gio, GObject, OsmGpsMap


class ChartLayer:
	def __init__(self, layer, path, ctype = 'vector', enabled = True):
		self.layer = layer
		self.path = path
		self.ctype = ctype
		self.enabled = enabled

class ChartManager(GObject.GObject, OsmGpsMap.MapLayer):
	def __init__(self, m):
		GObject.GObject.__init__(self)

		self.map = m
		self.charts = {}

	def loadBaseChart(self):
		self.charts["countries.geojson"] = ChartLayer(
			GDALVectorChart(os.path.abspath(os.path.dirname(__file__)) + "/../../../data/countries.geojson"),
			os.path.abspath(os.path.dirname(__file__)) + "/../../../data/countries.geojson"
		)

		# self.charts["s57"] = GDALVectorChart(
		#     '/home/dakk/ENC_ROOT/US2EC03M/US2EC03M.000', 'S57'
		# )


	def loadVectorLayer(self, path):
		pass

	def loadRasterLayer(self, path):
		pass

	def removeLayer(self, name):
		del self.charts[name]

	def do_draw(self, gpsmap, cr):
		for x in self.charts:
			if self.charts[x].enabled:
				self.charts[x].layer.do_draw(gpsmap, cr)

	def do_render(self, gpsmap):
		for x in self.charts:
			if self.charts[x].enabled:
				self.charts[x].layer.do_render(gpsmap)

	def do_busy(self):
		for x in self.charts:
			if self.charts[x].enabled:
				self.charts[x].layer.do_busy()

	def do_button_press(self, gpsmap, gdkeventbutton):
		for x in self.charts:
			if self.charts[x].enabled:
				self.charts[x].layer.do_button_press(gpsmap, gdkeventbutton)


GObject.type_register(ChartManager)
