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
import gpxpy
from .. import utils

class Collection:
	def __init__(self, of, baseName):
		self.of = of
		self.elements = []
		self.baseName = baseName

	def __iter__(self):
		return iter(self.elements)

	def __len__(self):
		return len(self.elements)

	def __getitem__(self, i):
		return self.elements[i]

	def __setitem__(self, i, v):
		self.elements[i] = v

	def __delitem__(self, i):
		del self.elements[i]

	def toJSON(self):
		return {
			'elements': [x.toJSON() for x in self.elements]
		}

	def getUniqueName(self, baseName = None):
		if baseName is None:
			baseName = self.baseName
		return utils.uniqueName(baseName, self.elements)

	def newElement(self):
		e = self.of(self.getUniqueName(), collection = self)
		self.append(e)
		return e

	def clear(self):
		self.elements = []

	def append(self, element):
		self.elements.append(element)

	def remove(self, element):
		self.elements.remove(element)

	def removeByName(self, name):
		c = self.getByName(name)
		if c is not None:
			self.remove(c)

	def getByName(self, n):
		for x in self.elements:
			if x.name == n:
				return x
		return None

	def toGPXObject(self):
		gpx = gpxpy.gpx.GPX()

		for x in self.elements:
			ob = x.toGPXObject()
			if isinstance(gpx.GPXTrack, ob):
				gpx.tracks.append(ob)
			elif isinstance(gpx.GPXRoute, ob):
				gpx.routes.append(ob)
			elif isinstance(gpx.GPXWaypoint, ob):
				gpx.waypoints.append(ob)

		return gpx 

	def export(self, dest, format = 'gpx'):
		if format == 'gpx':
			gpx = self.toGPXObject()

			try:
				f = open(dest, "w")
				f.write(gpx.to_xml())
			except Exception as e:
				print (str(e))


class CollectionWithActiveElement(Collection):
	def __init__(self, of, baseName):
		super().__init__(of, baseName)
		self.activeElement = None

	def toJSON(self):
		c = super().toJSON()
		c['activeElement'] = self.activeElement.name
		return c

	def getActive(self):
		return self.activeElement

	def setActive(self, element):
		self.activeElement = element
