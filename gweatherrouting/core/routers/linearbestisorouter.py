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

import datetime
from .. import utils
from .router import *

class LinearBestIsoRouter (Router):
	def route (self, lastlog, time, start, end):
		if lastlog != None and len (lastlog.isochrones) > 0:
			isoc = self.calculateIsochrones (time + datetime.timedelta(hours=1), lastlog.isochrones, end)
		else:
			isoc = self.calculateIsochrones (time + datetime.timedelta(hours=1), [[(start[0], start[1], time)]], end)

		position = start
		path = []
		for p in isoc[-1]:
			if utils.pointDistance (end[0],end[1], p[0], p[1]) < 10.0:
				path.append (p)
				for iso in isoc[::-1][1::]:
					path.append (iso[path[-1][2]])

				path = path[::-1]
				position = path[-1]
				break

		return RoutingResult(time=time + datetime.timedelta(hours=1), path=path, position=position, isochrones=isoc)
