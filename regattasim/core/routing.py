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
		return self.ends

	def getTime (self):
		return self.time

	def _calculateIsochrones (self, isocrone, level, nextwp):
		dt = level * 50.0

		isocronenew = isocrone
		
		print ('call')
		for x in [isocrone[-1][0]]:
			print (x)
			isonew = []
			(TWD,TWS)=self.grib.getWindAt (self.time, x[0], x[1])
			passo=5#per valori più bassi si rischia instabilità
			for TWA in range(-180,180,passo):
				TWA=math.radians(TWA)
				brg=utils.reduce360(TWD+TWA)
				Speed=self.boat.polar.getRoutageSpeed(TWS,math.copysign(TWA,1))
				ptoiso=utils.routagePointDistance(x[0],x[1],Speed*dt,brg)

				#print ('losso',utils.lossodromic (ptoiso[0], ptoiso[1], nextwp[0], nextwp[1])[0], utils.lossodromic (x[0], x[1], nextwp[0], nextwp[1])[0])
				#if utils.ortodromic (ptoiso[0], ptoiso[1], nextwp[0], nextwp[1])[0] < utils.ortodromic (x[0], x[1], nextwp[0], nextwp[1])[0]:
				isonew.append(ptoiso)
			isonew.append(isonew[0])#chiude l'isocrona
			isocronenew.append(isonew)  

		return isocronenew


	def step (self):
		self.steps += 1
		#self.t += 0.1

		# Next waypoint
		nextwp = self.track[self.wp]

		# Currentposition
		wind = self.grib.getWindAt (self.time, self.position[0], self.position[1])

		print (wind)

		isoc = [[self.position]]
		for x in range (3):
			isoc = self._calculateIsochrones (isoc, x+1, nextwp)

		self.time += 0.2
		progress = 12
		logger.debug ('step (time: %f, %f%% completed): %f %f' % (self.time, progress, self.position[0], self.position[1]))

		nlog = {
			'progress': progress,
			'time': self.time,
			'path': [],
			'isochrones': isoc
		}

		self.log.append (nlog)
		return nlog
		