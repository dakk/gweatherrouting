# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
"""

from .... import log
import logging
import gi
import time
import cairo
import multiprocessing
import numpy as np
from os import listdir
from os.path import isfile, join
from osgeo import ogr, osr, gdal
from threading import Thread, Lock

gi.require_version("Gtk", "3.0")
gi.require_version('OsmGpsMap', '1.2')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap, Gdk
from .chartlayer import ChartLayer

logger = logging.getLogger ('gweatherrouting')

# https://gdal.org/tutorials/raster_api_tut.html

def datasetBBox(dataset):
		old_cs = osr.SpatialReference()
		old_cs.ImportFromWkt(dataset.GetProjectionRef())

		wgs84_wkt = """
		GEOGCS["WGS 84",
			DATUM["WGS_1984",
				SPHEROID["WGS 84",6378137,298.257223563,
					AUTHORITY["EPSG","7030"]],
				AUTHORITY["EPSG","6326"]],
			PRIMEM["Greenwich",0,
				AUTHORITY["EPSG","8901"]],
			UNIT["degree",0.01745329251994328,
				AUTHORITY["EPSG","9122"]],
			AUTHORITY["EPSG","4326"]]"""
		new_cs = osr.SpatialReference()
		new_cs .ImportFromWkt(wgs84_wkt)

		transform = osr.CoordinateTransformation(old_cs,new_cs) 

		width = dataset.RasterXSize
		height = dataset.RasterYSize
		gt = dataset.GetGeoTransform()
		minx = gt[0]
		miny = gt[3]

		origin = transform.TransformPoint(minx,miny) 

		minx = gt[0] + width*gt[1] + height*gt[2] 
		miny = gt[3] + width*gt[4] + height*gt[5] 

		originbr = transform.TransformPoint(minx,miny) 

		return [origin, originbr]
	
class GDALSingleRasterChart:
	def getFileInfo(path):
		dataset = gdal.Open(path, gdal.GA_ReadOnly)

		if not dataset:
			raise ("Unable to open raster chart %s" % path)

		bbox = datasetBBox(dataset)

		return (path, bbox, dataset.RasterXSize, dataset.RasterYSize)


	def __init__(self, path):
		dataset = gdal.Open(path, gdal.GA_ReadOnly)

		if not dataset:
			raise ("Unable to open raster chart %s" % path)

		# print("Driver: {}/{}".format(dataset.GetDriver().ShortName,
		# 					dataset.GetDriver().LongName))
		# print("Size is {} x {} x {}".format(dataset.RasterXSize,
		# 									dataset.RasterYSize,
		# 									dataset.RasterCount))
		geotransform = dataset.GetGeoTransform()

		self.geotransform = geotransform
		self.dataset = dataset
		self.bbox = datasetBBox(dataset)

		def worker(i, return_dict):
			return_dict['surface'] = self.bandToSurface(i)

		manager = multiprocessing.Manager()
		return_dict = manager.dict()
		p = multiprocessing.Process(target=worker, args=(1, return_dict))
		p.start()
		p.join()
		surface, bandXSize, bandYSize = return_dict['surface']
		surf = cairo.ImageSurface.create_for_data(surface, cairo.Format.ARGB32, bandXSize, bandYSize, cairo.Format.RGB24.stride_for_width(bandXSize))
		self.surface = surf

	def bandToSurface(self, i):
		band = self.dataset.GetRasterBand(i)

		min = band.GetMinimum()
		max = band.GetMaximum()
		if not min or not max:
			(min,max) = band.ComputeRasterMinMax(True)

		colors = {}
		ct = band.GetRasterColorTable()
		
		for x in range(int(min), int(max) + 1):
			try: 
				c = ct.GetColorEntry(x)
				colors[x] = (c[3] << 24) | (c[2] << 16) | (c[1] << 8) | c[0]
			except:
				colors[x] = 0x00000000

		data = np.vectorize(lambda x: colors[x], otypes=[np.int32])(band.ReadAsArray())
		return data, band.XSize, band.YSize


	def do_draw(self, gpsmap, cr):
		cr.save()
		xx, yy = gpsmap.convert_geographic_to_screen(
			OsmGpsMap.MapPoint.new_degrees(self.bbox[0][0], self.bbox[0][1])
		)
		xx2, yy2 = gpsmap.convert_geographic_to_screen(
			OsmGpsMap.MapPoint.new_degrees(self.bbox[1][0], self.bbox[1][1])
		)
		scalingy = (yy2 - yy) / self.dataset.RasterYSize
		scalingx = (xx2 - xx) / self.dataset.RasterXSize
		cr.translate(xx, yy)
		cr.scale(scalingx, scalingy)
		cr.set_source_surface(self.surface, 0,0)
		cr.paint()
		cr.restore()



class GDALRasterChart(ChartLayer):
	def __init__(self, path, metadata = None):
		super().__init__(path, 'raster', metadata)
		self.cached = {}
		self.loadLock = Lock()

		if metadata:
			self.onMetadataUpdate()


	def onMetadataUpdate(self):
		pass

	def onRegister(self, onTickHandler = None):
		self.metadata = []

		files = [f for f in listdir(self.path) if isfile(join(self.path, f))]
		i = 0

		for x in files:
			finfo = GDALSingleRasterChart.getFileInfo(self.path + x)
			self.metadata.append(finfo)

			i += 1
			if onTickHandler:
				onTickHandler(i/len(files))

		self.onMetadataUpdate()

		if onTickHandler:
			onTickHandler(1.0)

		return True

	lastRect = None
	lastRasters = None

	def loadRaster(self, gpsmap, path):
		with self.loadLock:
			logger.debug('Loading raster file ' + path)
			try:
				s = time.time()
				r = GDALSingleRasterChart(path)
				self.cached[path] = r
				logger.debug('Done loading raster file ' + path.split('/')[-1] + ' in ' + str(int((time.time() - s)* 10.)/10.) + ' seconds')
			except:
				logger.error('Error loading raster file ' + path.split('/')[-1])
				return None
			Gdk.threads_enter()
			gpsmap.queue_draw()
			Gdk.threads_leave()
			self.lastRasters.append(r)
		
	def do_draw(self, gpsmap, cr):
		p1, p2 = gpsmap.get_bbox()
		p1lat, p1lon = p1.get_degrees()
		p2lat, p2lon = p2.get_degrees()

		# Check if bounds hasn't changed
		if self.lastRasters and self.lastRect == [p1lat, p1lon, p2lat, p2lon]:
			for x in self.lastRasters:
				x.do_draw(gpsmap, cr)
			return

		# Estimate which raster is necessary given bound and zoom
		minBLat = min(p1lat, p2lat)
		maxBLat = max(p1lat, p2lat)
		minBLon = min(p1lon, p2lon)
		maxBLon = max(p1lon, p2lon)

		toload = []
		for x in self.metadata:
			bb, path, sizeX, sizeY = x[1], x[0], x[2], x[3]

			minRLat = min(bb[0][0], bb[1][0])
			maxRLat = max(bb[0][0], bb[1][0])
			minRLon = min(bb[0][1], bb[1][1])
			maxRLon = max(bb[0][1], bb[1][1])

			inside = minRLat > minBLat and maxRLat < maxBLat and minRLon > minBLon and maxRLon < maxBLon
			a = minRLat < minBLat and maxRLat > maxBLat and minRLon > minBLon and minRLon < maxBLon
			b = minRLat < minBLat and maxRLat > maxBLat and minRLon < minBLon and maxRLon > minBLon
			c = minRLat < minBLat and maxRLat > minBLat and minRLon < minBLon and maxRLon > maxBLon
			d = minRLat < maxBLat and maxRLat > maxBLat and minRLon < minBLon and maxRLon > maxBLon

			area = (((maxRLat + 90) - (minRLat + 90))) * (((maxRLon + 180) - (minRLon + 180)))

			if a or b or c or d:
				toload.append([path, bb, area, inside])


		toload.sort(key=lambda x: x[2])
		toload.reverse()

		# Check which rasters are already loaded
		rasters = []

		for x in toload:
			if x[0] in self.cached:
				if self.cached[x[0]] != 'loading':
					rasters.append(self.cached[x[0]])
				continue
			
			self.cached[x[0]] = 'loading'

			t = Thread(target=self.loadRaster, args=(gpsmap, x[0],))
			t.daemon = True
			t.start()

		# Save and render
		self.lastRect = [p1lat, p1lon, p2lat, p2lon]
		self.lastRasters = rasters
		
		# print ('rendering',len(rasters))
		for x in rasters:
			x.do_draw(gpsmap, cr)


		for x in self.metadata:
			# Disable bbox rendering
			continue

			bb = x[1]

			minRLat = min(bb[0][0], bb[1][0])
			maxRLat = max(bb[0][0], bb[1][0])
			minRLon = min(bb[0][1], bb[1][1])
			maxRLon = max(bb[0][1], bb[1][1])
			
			xx, yy = gpsmap.convert_geographic_to_screen(
				OsmGpsMap.MapPoint.new_degrees(minRLat, minRLon)
			)
			xx2, yy2 = gpsmap.convert_geographic_to_screen(
				OsmGpsMap.MapPoint.new_degrees(maxRLat, maxRLon)
			)

			cr.set_source_rgba(1,0,0,0.6)
			cr.set_line_width(0.3)
			cr.move_to(xx, yy)
			cr.line_to(xx, yy2)
			cr.line_to(xx2, yy2)
			cr.line_to(xx2, yy)
			cr.line_to(xx, yy)

			cr.stroke()

	def do_render(self, gpsmap):
		pass

	def do_busy(self):
		return False

	def do_button_press(self, gpsmap, gdkeventbutton):
		return False
