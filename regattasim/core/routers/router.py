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
from .. import utils

class Router:
	def __init__ (self, polar, grib):
		self.polar = polar
		self.grib = grib


	def calculateIsochrones (self, time, isocrone, level, nextwp):
		dt = level * 50.0

		isocronenew = isocrone
		
		print ('call')
		for x in isocrone[-1]:
				print (x)
				isonew = []
				(TWD,TWS)=self.grib.getWindAt (time, x[0], x[1])
				passo=5#per valori più bassi si rischia instabilità
				for TWA in range(-180,180,passo):
					TWA=math.radians(TWA)
					brg=utils.reduce360(TWD+TWA)
					Speed=self.polar.getRoutageSpeed (TWS,math.copysign(TWA,1))
					print (Speed, TWA, TWD, TWS)
					ptoiso=utils.routagePointDistance(x[0],x[1],Speed*dt,brg)

					#print ('losso',utils.lossodromic (ptoiso[0], ptoiso[1], nextwp[0], nextwp[1])[0], utils.lossodromic (x[0], x[1], nextwp[0], nextwp[1])[0])
					#if utils.ortodromic (ptoiso[0], ptoiso[1], nextwp[0], nextwp[1])[0] < utils.ortodromic (x[0], x[1], nextwp[0], nextwp[1])[0]:
					isonew.append(ptoiso)
				isonew.append(isonew[0])#chiude l'isocrona
				isocronenew.append(isonew)  

		return isocronenew

	# Calculate the Velocity-Made-Good of a boat sailing from
	# start to end at current speed / angle
	def calculateVMG (self, speed, angle, start, end):
		return speed * math.cos (angle)


	def route (self, time, start, end):
		return {
			'time': 0,
			'path': [],
			'isochrones': []
		}
