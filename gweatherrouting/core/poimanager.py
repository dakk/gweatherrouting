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

$PFEC, GPwpl, llll.ll, a, yyyyy.yy, a, c—c, c, c—c, a, hhmmss, xx, xx, xxxx <CR><LF>
1 2 3 4 5 6 7 8 9 10 11 12
1: Waypoint latitude (degreeminute.1/10minutes)
2: N/S
3: Waypoint longitude (degreeminute.1/10minutes)
4: E/W
5: Waypoint name (1 to 8 characters)
6: Waypoint color
(NULL/0: black, 1: red, 2: yellow, 3: green, 4: brown, 5: purple, 6: blue)
7: Waypoint comment (”@_ (see below.)” + 0 to 13 characters)
8: Flag marking waypoint (A: displayed, V: Not displayed)
9: UTC (Always NULL)
10: Day (Always NULL)
11: Month (Always NULL)
12: Year (Always NULL)
0x10: @q, 0x11: @r, 0x12: @s:, 0x13: @t, 0x14: @u,
0x15: @v, 0x16: @w, 0x17: @x, 0x18: @y, 0x19: @z
-Internal mark code is 0x10 through 0x19. 0x71 through 0x7A are always
place at 2nd byte of mark code.
-Following characters can be used for comments:
_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789&()+-/=?> (space)
"""

# $PFEC,GPwpl,4012.32,N,958.18,E,WP0000,3,@q00:53 25MAR22,A,,,,
# $PFEC,GPwpl,3912.32,N,1918.18,E,WP0001,3,@q00:55 25MAR22,A,,,,

import math
import gpxpy
from .utils import uniqueName
try:
	from . import Storage
except:
	from .dummy_storage import Storage


class POI:
	def __init__(self, name, position, symbol=None, visible=True):
		self.name = name
		self.position = position
		self.visible = visible
		self.symbol = symbol


	""" Export POI as PFEC NMEA sentence """
	def toNMEAPFEC(self):
		# convert coordinate from signed degree to dddmm.mmmm
		def formatCoordinate(v):
			d = (v - int(v)) * 60
			return '{:d}{}'.format(int(v),'%05.2f' % d)

		lat = formatCoordinate(self.position[0])
		latns = 'N' if self.position[0] >= 0 else 'S'

		lon = formatCoordinate(self.position[1])
		lonew = 'E' if self.position[1] >= 0 else 'W'

		name = self.name.ljust(6)[:6]

		# TODO: handle symbol
		# q: circle; x: anchor

		return '$PFEC,GPwpl,%s,%s,%s,%s,%s,%d,@q00:00 00AAA00,A,,,,' % (lat, latns, lon, lonew, name, 3)


	def toGPXWaypoint(self):
		# TODO: add symbol , sym=self.symb
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
			tr = POI(name=x['name'], position=x['position'], visible=x['visible'], symbol=x['symbol'])
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

	def move(self, name, lat, lon):
		for x in self.pois:
			if x.name == name:
				x.position = (lat, lon)
				return

	def savePOI(self):
		ts = []
		for x in self.pois:
			ts.append({'name': x.name, 'position': x.position, 'visible': x.visible, 'symbol': x.symbol })

		self.storage.pois = ts

	def toNMEAPFEC(self):
		s = ''
		for x in self.pois:
			s += x.toNMEAPFEC() + '\n'
		s += '$PFEC,GPxfr,CTL,E'
		return s


	def create(self, position):
		nt = POI(name=uniqueName('poi', self.pois), position=position, symbol=None)
		self.pois.append (nt)
		self.savePOI()