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
import os
import requests
from threading import Thread
from osgeo import ogr, osr, gdal
from gweatherrouting.core.storage import DATA_DIR, TEMP_DIR
from gweatherrouting.gtk.charts.chartlayer import ChartLayer


gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.2')

from gi.repository import Gtk, Gdk, GObject 

from ... import log
from .gdalvectorchart import GDALVectorChart
import logging


logger = logging.getLogger ('gweatherrouting')

class GSHHSAskDownloadDialog(Gtk.Dialog):
	def __init__(self, parent):
		super().__init__(title="Base Map Download", transient_for=parent, flags=0)
		self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
		self.set_default_size(250, 100)
		self.set_border_width(10)
		label = Gtk.Label(label="Base world countourn lines are missing,\ndo you want to download them (~140MB)?")
		box = self.get_content_area()
		box.add(label)
		self.show_all()

class GSHHSDownloadDialog(Gtk.Dialog):
	def __init__(self, parent):
		super().__init__(title="Base Map Download", transient_for=parent, flags=0)
		self.parent = parent
		self.set_default_size(250, 60)
		self.set_border_width(10)
		self.pb = Gtk.ProgressBar()
		b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		self.l = Gtk.Label(label="Download in progress")
		b.pack_start(self.l, True, True, 20)
		b.pack_start(self.pb, True, True, 20)
		box = self.get_content_area()
		box.add(b)
		self.show_all()
		
		self.thread = Thread(target=self.download, args=())
		self.thread.start()

	def percentageCallback(self, percentage, d, t):
		Gdk.threads_enter()
		self.pb.set_fraction(percentage / 100)
		self.l.set_text("Downloading: %d%%" % percentage)
		Gdk.threads_leave()

	def callback(self, success):
		Gdk.threads_enter()
		if success:
			edialog = Gtk.MessageDialog (self.parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Done")
			edialog.format_secondary_text ("Base map downloaded")
			edialog.run ()
			edialog.destroy ()
			self.response(Gtk.ResponseType.OK)
		else:
			log.error("Error downloading GSHHS")

			edialog = Gtk.MessageDialog (self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error")
			edialog.format_secondary_text ("Cannot download base map")
			edialog.run ()
			edialog.destroy ()
			self.response(Gtk.ResponseType.CANCEL)
		Gdk.threads_leave()


	def download(self):
		import zipfile

		uri = "https://www.ngdc.noaa.gov/mgg/shorelines/data/gshhg/oldversions/version2.3.6/gshhg-shp-2.3.6.zip"
		logger.info("Downloading gshhs base map")

		response = requests.get(uri, stream=True)
		total_length = response.headers.get("content-length")
		last_signal_percent = -1
		f = open(TEMP_DIR + "/gshhs2.3.6.zip", "wb")

		if total_length is None:
			pass
		else:
			dl = 0
			total_length = int(total_length)
			for data in response.iter_content(chunk_size=4096):
				dl += len(data)
				f.write(data)
				done = int(100 * dl / total_length)

				if last_signal_percent != done:
					self.percentageCallback(done, dl, total_length)
					last_signal_percent = done

		f.close()
		logger.info("GSHHS base map download completed")

		zipfile.ZipFile(TEMP_DIR + "/gshhs2.3.6.zip").extractall(DATA_DIR+'/gshhs/')
		self.callback(True)



# 	GSHHS_shp: Shapefiles (polygons) derived from shorelines.
# 		   These are named GSHHS_<resolution>_L<level>.*
		
# 	WDBII_shp: Political boundaries and rivers (lines).
# 		   These are called
# 		   WDBII_border_<resolution>_L<level>.*
# 		   WDBII_river_<resolution>_L<level>.*

# where <resolution> is one of f,h,i,l,c and <level> is an integer.		

# All data sets come in 5 different resolutions:
# 	f : Full resolution.  These contain the maximum resolution
# 	    of this data and has not been decimated.
# 	h : High resolution.  The Douglas-Peucker line reduction was
# 	    used to reduce data size by ~80% relative to full.
# 	i : Intermediate resolution.  The Douglas-Peucker line reduction was
# 	    used to reduce data size by ~80% relative to high.
# 	l : Low resolution.  The Douglas-Peucker line reduction was
# 	    used to reduce data size by ~80% relative to intermediate.
# 	c : Crude resolution.  The Douglas-Peucker line reduction was
# 	    used to reduce data size by ~80% relative to low.

# For each resolution there are several levels; these depends on the data type.

# The shoreline data are distributed in 6 levels:

# Level 1: Continental land masses and ocean islands, except Antarctica.
# Level 2: Lakes
# Level 3: Islands in lakes
# Level 4: Ponds in islands within lakes
# Level 5: Antarctica based on ice front boundary.
# Level 6: Antarctica based on grounding line boundary.

from .vectordrawer.simplechartdrawer import SimpleChartDrawer

class GSHHSVectorChart(ChartLayer):
	def __init__(self, path, metadata = None):
		super().__init__(path, 'vector', metadata)

		self.drawer = SimpleChartDrawer()
		drv = ogr.GetDriverByName('ESRI Shapefile')
		self.vectorFiles = {}
		for x in ['f','h','i','l','c']:
			for y in [1]: #,2,3,4,5,6]:
				f = drv.Open(path+'/GSHHS_shp/'+x+'/GSHHS_'+x+'_L'+str(y)+'.shp')
				if f != None:
					self.vectorFiles[x+str(y)] = f 

	def onRegister(self, onTickHandler = None):
		pass

	def do_draw(self, gpsmap, cr):
		boundingGeometry = self.getBoundingGeometry(gpsmap)

		# Get the correct quality for zoom level
		scale = gpsmap.get_scale()
		if scale > 5000:
			q = 'c'
		elif scale > 500:
			q = 'l'
		elif scale > 200:
			q = 'i'
		elif scale > 30:
			q = 'h'
		elif scale < 30:
			q = 'h'
		#print(scale, q)
		self.drawer.draw(gpsmap, cr, self.vectorFiles[q+'1'], boundingGeometry)


	def do_render(self, gpsmap):
		pass

	def do_busy(self):
		return False

	def do_button_press(self, gpsmap, gdkeventbutton):
		return False


