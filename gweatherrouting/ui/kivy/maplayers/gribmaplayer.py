# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
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
import math
from kivy.graphics import (
	Canvas,
	Color,
	Line,
	MatrixInstruction,
	Mesh,
	PopMatrix,
	PushMatrix,
	Scale,
	Translate,
)
from kivy.graphics.tesselator import TYPE_POLYGONS, WINDING_ODD, Tesselator
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.utils import get_color_from_hex

from kivy_garden.mapview.constants import CACHE_DIR
from kivy_garden.mapview.downloader import Downloader
from kivy_garden.mapview.view import MapLayer

from ...common import windColor


class GribMapLayer(MapLayer):
	def __init__(self, gribManager, timeControl, **kwargs):
		super().__init__(**kwargs)
		self.gribManager = gribManager
		self.timeControl = timeControl
		self.timeControl.connect("time-change", self.onTimeChange)
		self.arrowOpacity = 0.3

		self.first_time = True
		self.initial_zoom = None
		
		with self.canvas:
			self.canvas_polygon = Canvas()
			self.canvas_line = Canvas()
		with self.canvas_polygon.before:
			PushMatrix()
			self.g_matrix = MatrixInstruction()
			self.g_scale = Scale()
			self.g_translate = Translate()
		with self.canvas_polygon:
			self.g_canvas_polygon = Canvas()
		with self.canvas_polygon.after:
			PopMatrix()


	def onTimeChange(self, t):
		self.draw()


	def reposition(self):
		""" Function called when :class:`MapView` is moved. You must recalculate
		the position of your children. """
		self.draw()

	def unload(self):
		""" Called when the view want to completly unload the layer. """
		pass
	
	def drawWindArrow(self, x, y, wdir, wspeed):
		wdir = -math.radians(wdir)

		a, b, c = windColor(wspeed)

		length = 25
		RD = 30
		self.canvas_line.add(Color(a, b, c, self.arrowOpacity))

		xy = [x,y, x + (length * math.sin(wdir)), y + (length * math.cos(wdir))]
		self.canvas_line.add(Line(points=xy, width=1.5))

		xy = [x + (length * math.sin(wdir)), y + (length * math.cos(wdir)), x + (4 * math.sin(wdir - math.radians(RD))), y + (4 * math.cos(wdir - math.radians(RD)))]
		self.canvas_line.add(Line(points=xy, width=1.5))

		xy = [x + (length * math.sin(wdir)), y + (length * math.cos(wdir)), x + (4 * math.sin(wdir + math.radians(RD))), y + (4 * math.cos(wdir + math.radians(RD)))]
		self.canvas_line.add(Line(points=xy, width=1.5))


	def draw(self):
		view = self.parent
		zoom = view.zoom
		bbox = view.get_bbox()

		p1lat, p1lon, p2lat, p2lon = bbox

		bounds = (
			(min(p1lat, p2lat), min(p1lon, p2lon)),
			(max(p1lat, p2lat), max(p1lon, p2lon)),
		)
		data = self.gribManager.getWind2D(self.timeControl.time, bounds)

		self.canvas_line.clear()

		if not data or len(data) == 0:
			return

		# scale = int(math.fabs(zoom - 8))
		if zoom > 8:
			scale = 1
		elif zoom > 7:
			scale = 2
		elif zoom > 6:
			scale = 3
		elif zoom > 5:
			scale = 4
		elif zoom > 4:
			scale = 5
		elif zoom > 3:
			scale = 6
		elif zoom > 2:
			scale = 7
		elif zoom > 1:
			scale = 8
		elif zoom > 0:
			scale = 9


		# Draw arrows
		for x in data[::scale]:
			for y in x[::scale]:
				xx, yy = view.get_window_xy_from(y[2][0], y[2][1], zoom)
				self.drawWindArrow(xx, yy, y[0], y[1])


	# def lonlat_to_xy(self, lonlats):
	# 	view = self.parent
	# 	zoom = view.zoom
	# 	for lon, lat in lonlats:
	# 		p = view.get_window_xy_from(lat, lon, zoom)
	# 		p = p[0] - self.parent.delta_x, p[1] - self.parent.delta_y
	# 		p = self.parent._scatter.to_local(*p)
	# 		yield p


	# def reposition(self):
	# 	vx, vy = self.parent.delta_x, self.parent.delta_y
	# 	pzoom = self.parent.zoom
	# 	zoom = self.initial_zoom
	# 	if zoom is None:
	# 		self.initial_zoom = zoom = pzoom
	# 	if zoom != pzoom:
	# 		diff = 2 ** (pzoom - zoom)
	# 		vx /= diff
	# 		vy /= diff
	# 		self.g_scale.x = self.g_scale.y = diff
	# 	else:
	# 		self.g_scale.x = self.g_scale.y = 1.0
	# 	self.g_translate.xy = vx, vy
	# 	self.g_matrix.matrix = self.parent._scatter.transform

	# 	if self.geojson:
	# 		update = not self.first_time
	# 		self.on_geojson(self, self.geojson, update=update)
	# 		self.first_time = False

	# def traverse_feature(self, func, part=None):
	# 	"""Traverse the whole geojson and call the func with every element
	# 	found.
	# 	"""
	# 	if part is None:
	# 		part = self.geojson
	# 	if not part:
	# 		return
	# 	tp = part["type"]
	# 	if tp == "FeatureCollection":
	# 		for feature in part["features"]:
	# 			func(feature)
	# 	elif tp == "Feature":
	# 		func(part)

	# @property
	# def bounds(self):
	# 	# return the min lon, max lon, min lat, max lat
	# 	bounds = [float("inf"), float("-inf"), float("inf"), float("-inf")]

	# 	def _submit_coordinate(coord):
	# 		lon, lat = coord
	# 		bounds[0] = min(bounds[0], lon)
	# 		bounds[1] = max(bounds[1], lon)
	# 		bounds[2] = min(bounds[2], lat)
	# 		bounds[3] = max(bounds[3], lat)

	# 	def _get_bounds(feature):
	# 		geometry = feature["geometry"]
	# 		tp = geometry["type"]
	# 		if tp == "Point":
	# 			_submit_coordinate(geometry["coordinates"])
	# 		elif tp == "Polygon":
	# 			for coordinate in geometry["coordinates"][0]:
	# 				_submit_coordinate(coordinate)
	# 		elif tp == "MultiPolygon":
	# 			for polygon in geometry["coordinates"]:
	# 				for coordinate in polygon[0]:
	# 					_submit_coordinate(coordinate)

	# 	self.traverse_feature(_get_bounds)
	# 	return bounds

	# @property
	# def center(self):
	# 	min_lon, max_lon, min_lat, max_lat = self.bounds
	# 	cx = (max_lon - min_lon) / 2.0
	# 	cy = (max_lat - min_lat) / 2.0
	# 	return min_lon + cx, min_lat + cy

	# def on_geojson(self, instance, geojson, update=False):
	# 	if self.parent is None:
	# 		return
	# 	if not update:
	# 		self.g_canvas_polygon.clear()
	# 		self._geojson_part(geojson, geotype="Polygon")
	# 	self.canvas_line.clear()
	# 	self._geojson_part(geojson, geotype="LineString")

	# def on_source(self, instance, value):
	# 	if value.startswith(("http://", "https://")):
	# 		Downloader.instance(cache_dir=self.cache_dir).download(
	# 			value, self._load_geojson_url
	# 		)
	# 	else:
	# 		with open(value, "rb") as fd:
	# 			geojson = json.load(fd)
	# 		self.geojson = geojson

	# def _load_geojson_url(self, url, response):
	# 	self.geojson = response.json()

	# def _geojson_part(self, part, geotype=None):
	# 	tp = part["type"]
	# 	if tp == "FeatureCollection":
	# 		for feature in part["features"]:
	# 			if geotype and feature["geometry"]["type"] != geotype:
	# 				continue
	# 			self._geojson_part_f(feature)
	# 	elif tp == "Feature":
	# 		if geotype and part["geometry"]["type"] == geotype:
	# 			self._geojson_part_f(part)
	# 	else:
	# 		# unhandled geojson part
	# 		pass

	# def _geojson_part_f(self, feature):
	# 	properties = feature["properties"]
	# 	geometry = feature["geometry"]
	# 	graphics = self._geojson_part_geometry(geometry, properties)
	# 	for g in graphics:
	# 		tp = geometry["type"]
	# 		if tp == "Polygon":
	# 			self.g_canvas_polygon.add(g)
	# 		else:
	# 			self.canvas_line.add(g)

	# def _geojson_part_geometry(self, geometry, properties):
	# 	tp = geometry["type"]
	# 	graphics = []
	# 	if tp == "Polygon":
	# 		tess = Tesselator()
	# 		for c in geometry["coordinates"]:
	# 			xy = list(self._lonlat_to_xy(c))
	# 			xy = flatten(xy)
	# 			tess.add_contour(xy)

	# 		tess.tesselate(WINDING_ODD, TYPE_POLYGONS)

	# 		color = self._get_color_from(properties.get("color", "FF000088"))
	# 		graphics.append(Color(*color))
	# 		for vertices, indices in tess.meshes:
	# 			graphics.append(
	# 				Mesh(vertices=vertices, indices=indices, mode="triangle_fan")
	# 			)

	# 	elif tp == "LineString":
	# 		stroke = get_color_from_hex(properties.get("stroke", "#ffffff"))
	# 		stroke_width = dp(properties.get("stroke-width"))
	# 		xy = list(self._lonlat_to_xy(geometry["coordinates"]))
	# 		xy = flatten(xy)
	# 		graphics.append(Color(*stroke))
	# 		graphics.append(Line(points=xy, width=stroke_width))

	# 	return graphics


	# def _get_color_from(self, value):
	# 	color = COLORS.get(value.lower(), value)
	# 	color = get_color_from_hex(color)
	# 	return color