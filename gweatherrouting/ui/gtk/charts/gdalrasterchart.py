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

import gi
import cairo
from os import listdir
from os.path import isfile, join
from osgeo import ogr, osr, gdal

gi.require_version("Gtk", "3.0")
gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap
from .chartlayer import ChartLayer

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


	def __init__(self, path, drvName=None):
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
		self.surface = self.bandToSurface(1)

	def bandToSurface(self, i):
		band = self.dataset.GetRasterBand(i)

		min = band.GetMinimum()
		max = band.GetMaximum()
		if not min or not max:
			(min,max) = band.ComputeRasterMinMax(True)

		colors = {}
		ct = band.GetRasterColorTable()
		
		for x in range(0, int(max) + 1):
			try: 
				c = ct.GetColorEntry(x)
			except:
				c = (0, 0, 0, 0)
			
			colors[x] = bytearray([c[0], c[1], c[2], 0])

		data = bytearray()
		for x in band.ReadAsArray():
			for y in x:
				data.extend(colors[int(y)])

		return cairo.ImageSurface.create_for_data(data, cairo.Format.RGB24, band.XSize, band.YSize, cairo.Format.RGB24.stride_for_width(band.XSize))


	def do_draw(self, gpsmap, cr):
		p1, p2 = gpsmap.get_bbox()
		p1lat, p1lon = p1.get_degrees()
		p2lat, p2lon = p2.get_degrees()

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

	def do_render(self, gpsmap):
		pass

	def do_busy(self):
		return False

	def do_button_press(self, gpsmap, gdkeventbutton):
		return False



class GDALRasterChart(ChartLayer):
	def __init__(self, path):
		super().__init__(path, 'raster')
		self.rasters = []

		# Get Info
		# Preload min zoom
		# Offer loading for increased zoom

		# i = 0
		# for x in [f for f in listdir(path) if isfile(join(path, f))]:
		# 	if x.find('L10') == -1:
		# 		continue

		# 	i+=1

		# 	if i > 2:
		# 		continue

		# 	try:
		# 		print ('Loading',x)
		# 		r = GDALSingleRasterChart(path + x)
		# 		self.rasters.append(r)
		# 	except Exception as e:
		# 		print ('error', str(e))

	def onRegister(self, onTickHandler = None):
		files = [f for f in listdir(self.path) if isfile(join(self.path, f))]
		i = 0

		for x in files:
			finfo = GDALSingleRasterChart.getFileInfo(self.path + x)
			print(finfo)

			i += 1
			if onTickHandler:
				onTickHandler(i/len(files))


		# Load also the tiles
		i = 0
		ff = list(filter(lambda x: x.find('L10') != -1, [f for f in listdir(self.path) if isfile(join(self.path, f))]))
		for x in ff:
			i+=1

			try:
				print ('Loading',x)
				r = GDALSingleRasterChart(self.path + x)
				self.rasters.append(r)
			except Exception as e:
				print ('error', str(e))

			if onTickHandler:
				onTickHandler(i/len(ff))


		if onTickHandler:
			onTickHandler(1.0)

		return True

	def do_draw(self, gpsmap, cr):
		for x in self.rasters:
			x.do_draw(gpsmap, cr)

	def do_render(self, gpsmap):
		pass

	def do_busy(self):
		return False

	def do_button_press(self, gpsmap, gdkeventbutton):
		return False
