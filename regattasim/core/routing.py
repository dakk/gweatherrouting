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

logger = logging.getLogger ('regattasim')

ALGORITHMS = {
	'IsoTree': None,
	'BestIsoList': None
}

class Routing:
	def __init__ (self, algorithm, boat, track, grib, initialTime = 0.0):
		self.algorithm = algorithm
		self.boat = boat
		self.track = track
		self.wp = 1
		self.steps = 0
		self.path = Track ()    # Simulated points
		self.t = initialTime
		self.grib = grib
		self.log = []           # Log of each simulation step
		self.position = (self.track[0]['lat'], self.track[0]['lon'])
		logger.debug ('initialized (time: %f)' % (self.t))


	def getTime (self):
		return self.t

	def reset (self):
		self.steps = 0
		self.path.clear ()
		self.position = (self.track[0]['lat'], self.track[0]['lon'])
		self.wp = 1
		self.log = []


	def _calculateIsochrones (self, isocrone, level, nextwp):
		dt = level * 50.0

		isocronenew = isocrone
		
		print ('call')
		for x in [isocrone[-1][0]]:
			print (x)
			isonew = []
			(TWD,TWS)=self.grib.getWindAt (self.t, x[0], x[1])
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
		nextwp = (self.track[self.wp]['lat'], self.track[self.wp]['lon'])

		# Currentposition
		wind = self.grib.getWindAt (self.t, self.position[0], self.position[1])

		print (wind)

		isoc = [[self.position]]
		for x in range (18):
			isoc = self._calculateIsochrones (isoc, x+1, nextwp)


		logger.debug ('step (mode: %s, time: %f): %f %f' % (self.mode, self.t, self.position[0], self.position[1]))

		nlog = {
			'position': position,
			'isochrones': isoc
		}

		self.log.append (nlog)
		return nlog
		