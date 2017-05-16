# -*- coding: utf-8 -*-
# Copyright (C) 2017 Davide Gessa
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
import logging

from . import utils
from .boat import Boat
from .track import Track
from .routers import linearbestisorouter

logger = logging.getLogger ('regattasim')

ALGORITHMS = [
	{
		'name': 'LinearBestIsoRouter',
		'class': linearbestisorouter.LinearBestIsoRouter
	}
]

class Routing:
	def __init__ (self, algorithm, boat, track, grib, initialTime = 0.0):
		self.end = False
		self.algorithm = algorithm
		self.boat = boat
		self.track = track
		self.wp = 1
		self.steps = 0
		self.path = Track ()    # Simulated points
		self.time = initialTime
		self.grib = grib
		self.log = []           # Log of each simulation step
		self.position = self.track[0]
		logger.debug ('initialized (time: %f)' % (self.time))

	def isEnd (self):
		return self.end

	def getTime (self):
		return self.time



	def step (self):
		self.steps += 1
		#self.t += 0.1

		# Next waypoint
		nextwp = self.track[self.wp]

		# Currentposition
		wind = self.grib.getWindAt (self.time, self.position[0], self.position[1])

		if len (self.log) > 0:
			res = self.algorithm.route (self.log[-1], self.time, self.position, nextwp)
		else:
			res = self.algorithm.route (None, self.time, self.position, nextwp)

		#self.time += 0.2
		progress = len (self.log) * 5
		logger.debug ('step (time: %f, %f%% completed): %f %f' % (self.time, progress, self.position[0], self.position[1]))

		self.time = res['time']
		nlog = {
			'progress': progress,
			'time': res['time'],
			'path': [],
			'isochrones': res['isochrones']
		}

		self.log.append (nlog)
		return nlog
		