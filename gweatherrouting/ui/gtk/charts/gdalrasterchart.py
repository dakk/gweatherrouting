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
import math
import json
import numpy
import struct
import cairo
from osgeo import ogr, osr, gdal

gi.require_version("Gtk", "3.0")
gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap

# https://gdal.org/tutorials/raster_api_tut.html

class GDALRasterChart:
	def __init__(self, path, drvName=None):
		dataset = gdal.Open(path, gdal.GA_ReadOnly)

		if not dataset:
			raise ("Unable to open raster chart %s" % path)

		# print("Driver: {}/{}".format(dataset.GetDriver().ShortName,
		# 					dataset.GetDriver().LongName))
		# print("Size is {} x {} x {}".format(dataset.RasterXSize,
		# 									dataset.RasterYSize,
		# 									dataset.RasterCount))
		# print("Projection is {}".format(dataset.GetProjection()))
		geotransform = dataset.GetGeoTransform()
		# if geotransform:
		# 	print("Origin = ({}, {})".format(geotransform[0], geotransform[3]))
		# 	print("Pixel Size = ({}, {})".format(geotransform[1], geotransform[5]))

		self.geotransform = geotransform
		self.dataset = dataset



		# Calc origin
		old_cs= osr.SpatialReference()
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
		miny = gt[3] # + width*gt[4] + height*gt[5] 

		self.origin = transform.TransformPoint(minx,miny) 

		minx = gt[0]
		miny = gt[3] + width*gt[4] + height*gt[5] 

		self.originbl = transform.TransformPoint(minx,miny) 
		self.s = self.bandToSurface(1)

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
			OsmGpsMap.MapPoint.new_degrees(self.origin[0], self.origin[1])
		)
		xx2, yy2 = gpsmap.convert_geographic_to_screen(
			OsmGpsMap.MapPoint.new_degrees(self.originbl[0], self.originbl[1])
		)
		scaling = (yy2 - yy)/self.dataset.RasterYSize
		cr.translate(xx, yy)
		cr.scale(scaling, scaling)
		cr.set_source_surface(self.s, 0,0)
		cr.paint()
		cr.restore()

	def do_render(self, gpsmap):
		pass

	def do_busy(self):
		return False

	def do_button_press(self, gpsmap, gdkeventbutton):
		return False
