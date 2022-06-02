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

class Element:
	def __init__(self, name = 'any', visible = True, collection = None):
		self.name = name
		self.visible = visible
		self.collection = collection

	def toGPXObject(self):
		raise Exception("Not implemented")

	def toJSON(self):
		return {
			'name': self.name,
			'visible': self.visible
		}

	@staticmethod
	def fromJSON(j):
		return Element(name = j['name'], visible = j['visible'])

	def export(self, dest, format = 'gpx'):
		if format == 'gpx':
			gpx = gpxpy.gpx.GPX()

			ob = self.toGPXObject()
			if isinstance(gpx.GPXTrack, ob):
				gpx.tracks.append(ob)
			elif isinstance(gpx.GPXRoute, ob):
				gpx.routes.append(ob)
			elif isinstance(gpx.GPXWaypoint, ob):
				gpx.waypoints.append(ob)

			try:
				f = open(dest, "w")
				f.write(gpx.to_xml())
			except Exception as e:
				print (str(e))

	def __len__(self):
		return 0