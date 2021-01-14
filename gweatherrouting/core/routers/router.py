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

import math
import time

from .. import utils

# http://www.tecepe.com.br/nav/vrtool/routing.htm

# Le isocrone saranno un albero; deve essere semplice:
# - accedere alla lista delle isocrone dell'ultimo albero
# - aggiungere un layer per il nuovo t
# - fare pruning di foglie

# [[level1], [level2,level2], [level3,level3,level3,level3]]


class RoutingNoWindException(Exception):
	pass

class RoutingResult:
	def __init__(self, time=0, path=[], isochrones=[], position=None, progress=0):
		self.time = time
		self.path = path
		self.isochrones = isochrones
		self.position = position
		self.progress = progress

class Router:
	def __init__ (self, polar, gribManager):
		self.polar = polar
		self.gribManager = gribManager


	def calculateIsochrones (self, t, isocrone, nextwp):
		dt = (1. / 60. * 60.)
		last = isocrone [-1]

		newisopoints = []

		# foreach point of the iso
		for i in range (0, len (last)):
			p = last[i]

			try:
				(twd,tws) = self.gribManager.getWindAt (t, p[0], p[1])
			except:
				raise(RoutingNoWindException())

			for twa in range(-180,180,5):
				twa = math.radians(twa)
				brg = utils.reduce360(twd+twa)

				speed = self.polar.getRoutageSpeed (tws, math.copysign (twa,1))
				ptoiso = utils.routagePointDistance (p[0], p[1], speed*dt*1.85, brg)
				
				if utils.pointDistance (ptoiso[0], ptoiso[1], nextwp[0], nextwp[1]) >= utils.pointDistance (p[0], p[1], nextwp[0], nextwp[1]):
				 	continue
				if utils.pointInCountry (ptoiso[0], ptoiso[1]):
					continue
				
				newisopoints.append ((ptoiso[0], ptoiso[1], i, t, twd, tws, speed, math.degrees(brg)))


		# sort newisopoints based on bearing
		isonew = []
		for i in range(0, len (newisopoints)):
			try:
				newisopoints[i] = (newisopoints[i][0], newisopoints[i][1], newisopoints[i][2], utils.lossodromic (isocrone[0][0][0],isocrone[0][0][1],newisopoints[i][0],newisopoints[i][1]), newisopoints[i][3], newisopoints[i][4], newisopoints[i][5], newisopoints[i][6], newisopoints[i][7])
				isonew.append (newisopoints[i])
			except:
				pass

		newisopoints = sorted (isonew, key=(lambda a: a[3][1]))

		# remove slow isopoints inside
		bearing = {}
		for x in newisopoints:
			k = str (int (x[3][1] * 100))
			if k in bearing:
				if x[3][0] > bearing[k][3][0]:
					bearing[k] = x
			else:
				bearing[k] = x

		isonew = []
		for x in bearing:	
			isonew.append (bearing[x])


		isonew = sorted (isonew, key=(lambda a: a[3][1]))
		isocrone.append (isonew)

		return isocrone


	# Calculate the Velocity-Made-Good of a boat sailing from
	# start to end at current speed / angle
	def calculateVMG (self, speed, angle, start, end):
		return speed * math.cos (angle)


	def route (self, lastlog, t, start, end):
		return RoutingResult()
