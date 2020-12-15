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

from ..session import *

defaultSession = {
	'pois': []
}

POI_TYPE_DEFAULT = 1

class POI:
	def __init__(self, name, position, poitype=POI_TYPE_DEFAULT, visible=True):
		self.name = name
		self.position = position
		self.visible = visible
		self.type = poitype

class POIManager(Sessionable):
	def __init__(self):
		Sessionable.__init__(self, 'poi-manager', defaultSession)
		self.pois = []

		for x in self.getSessionVariable('pois'):
			tr = POI(name=x['name'], position=x['position'], visible=x['visible'], poitype=x['type'])
			self.pois.append(tr)


	def remove(self, name):
		for x in self.pois:
			if x.name == name:
				return self.pois.remove(x)

	def savePOI(self):
		ts = []
		for x in self.pois:
			ts.append({'name': x.name, 'position': x.position, 'visible': x.visible, 'type': x.type })

		self.storeSessionVariable('pois', ts)


	def create(self, position):
		nt = POI(name=('poi-%d' % (len(self.pois) + 1)), position=position, poitype=POI_TYPE_DEFAULT)
		self.pois.append (nt)
		self.savePOI()