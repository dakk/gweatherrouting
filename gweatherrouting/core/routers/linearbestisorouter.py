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
from .. import utils
from .router import *

class LinearBestIsoRouter (Router):
	def route (self, lastlog, time, start, end):
		if lastlog != None and len (lastlog['isochrones']) > 0:
			isoc = self.calculateIsochrones (time, lastlog['isochrones'], end)
		else:
			isoc = self.calculateIsochrones (time, [[(start[0], start[1], 0)]], end)


		position = start
		path = []
		for p in isoc[-1]:
			if utils.pointDistance (end[0],end[1], p[0], p[1]) < 10.0:
				path.append (p)
				for iso in isoc[::-1][1::]:
					# print (path[-1][2], len (iso))
					path.append (iso[path[-1][2]])

				print (path)
				path = path[::-1]
				position = path[-1]
				break


		return {
			'time': time + 1. / 60. * 60.,
			'path': path,
			'position': position,
			'isochrones': isoc
		}
