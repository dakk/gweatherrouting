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
from typing import Tuple
from . import POI
from .collection import Collection

class POICollection(Collection):
	def __init__(self):
		super().__init__(POI, 'poi')

	def importFromGPX(self, gpx):
		for waypoint in gpx.waypoints:
			self.append(
				POI(waypoint.name, [waypoint.latitude, waypoint.longitude])
			)

	def toNMEAPFEC(self):
		s = ''
		for x in self.elements:
			s += x.toNMEAPFEC() + '\n'
		s += '$PFEC,GPxfr,CTL,E'
		return s

	def move(self, name, lat, lon):
		c = self.getByName(name)
		if c is not None:
			c.position = (lat, lon)

	def create(self, position: Tuple[float, float]):
		e = POI(self.getUniqueName(), position=position, collection = self)
		self.append(e)
		self.save()
		return e