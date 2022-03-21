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

"""
FURUNO PFEC NMEA https://www.manualsdir.com/manuals/100982/furuno-gp-1650.html?page=66
"""

import gpxpy
from .utils import uniqueName
try:
	from . import Storage
except:
	from .dummy_storage import Storage

POI_TYPE_DEFAULT = 1

class POI:
	def __init__(self, name, position, poitype=POI_TYPE_DEFAULT, visible=True):
		self.name = name
		self.position = position
		self.visible = visible
		self.type = poitype

	""" Export POI as PFEC NMEA sentence """
	def toNMEAPFEC(self):
		lat = '{:.2f}'.format(abs(self.position[0]) * 100)
		latns = 'N' if self.position[0] >= 0 else 'S'

		lon = '{:.2f}'.format(abs(self.position[1]) * 100)
		lonew = 'E' if self.position[1] >= 0 else 'W'

		name = self.name.ljust(6)[:6]

		return '$PFEC,GPwpl,%s,%s,%s,%s,%s,%d,@x            ,A' % (lat, latns, lon, lonew, name, 3)


	def toGPXWaypoint(self):
		return gpxpy.gpx.GPXWaypoint(latitude=self.position[0], longitude=self.position[1], name=self.name)

class PoiManagerStorage(Storage):
	def __init__(self):
		Storage.__init__(self, "poi-manager")
		self.pois = []
		self.loadOrSaveDefault()

class POIManager():
	def __init__(self):
		self.storage = PoiManagerStorage()
		self.pois = []

		for x in self.storage.pois:
			tr = POI(name=x['name'], position=x['position'], visible=x['visible'], poitype=x['type'])
			self.pois.append(tr)


	def getByName(self, name):
		for x in self.pois:
			if x.name == name:
				return x
		return None

	def remove(self, name):
		for x in self.pois:
			if x.name == name:
				return self.pois.remove(x)

	def savePOI(self):
		ts = []
		for x in self.pois:
			ts.append({'name': x.name, 'position': x.position, 'visible': x.visible, 'type': x.type })

		self.storage.pois = ts

	def toNMEAPFEC(self):
		s = ''
		for x in self.pois:
			s += x.toNMEAPFEC() + '\n'
		s += '$PFEC,GPxfr,CTL,E'
		return s


	def create(self, position):
		nt = POI(name=uniqueName('poi', self.pois), position=position, poitype=POI_TYPE_DEFAULT)
		self.pois.append (nt)
		self.savePOI()