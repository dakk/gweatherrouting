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
import time

from .. import utils

# http://www.tecepe.com.br/nav/vrtool/routing.htm

# Le isocrone saranno un albero; deve essere semplice:
# - accedere alla lista delle isocrone dell'ultimo albero
# - aggiungere un layer per il nuovo t
# - fare pruning di foglie

# [[level1], [level2,level2], [level3,level3,level3,level3]]

def interno(poligono,pto):
    #poligono orientato in senso orario
    somma=0
    for i in range(0,len(poligono)-1):
        v1=poligono[i]
        v2=poligono[i+1]
        rlv1=math.atan2((v1[1]-pto[1]),(v1[0]-pto[0]))
        if rlv1<0:rlv1=2*math.pi+rlv1
        rlv2=math.atan2((v2[1]-pto[1]),(v2[0]-pto[0]))
        if rlv2<0:rlv2=2*math.pi+rlv2
        angolo=math.copysign(rlv2-rlv1,1)
        if angolo>math.pi:
            angolo=2*math.pi-angolo
        somma=somma+angolo
    if somma<2*math.pi:
        Interno=False
    else:
        Interno=True
    return Interno

class Router:
	def __init__ (self, polar, grib):
		self.polar = polar
		self.grib = grib


	def calculateIsochrones (self, t, isocrone, nextwp):
		dt = (len (isocrone) + 1) * 15.0
		last = isocrone [-1]

		newisopoints = []

		bt0 = time.time ()

		# foreach point of the iso
		for i in range (0, len (last)):
			p = last[i]

			(TWD,TWS) = self.grib.getWindAt (t, p[0], p[1])
			
			for TWA in range(-180,180,5):
				TWA = math.radians(TWA)
				brg = utils.reduce360(TWD+TWA)
				Speed = self.polar.getRoutageSpeed (TWS,math.copysign(TWA,1))
				ptoiso = utils.routagePointDistance(p[0],p[1],Speed*dt,brg)

				if int (ptoiso[0]) != 0 and int (ptoiso[1]) != 0:
					newisopoints.append ((ptoiso[0], ptoiso[1], i))

		# sort newisopoints based on bearing
		for i in range(0, len (newisopoints)):
			newisopoints[i] = (newisopoints[i][0], newisopoints[i][1], newisopoints[i][2], utils.lossodromic (isocrone[0][0][0],isocrone[0][0][1],newisopoints[i][0],newisopoints[i][1]))

		newisopoints = sorted (newisopoints, key=(lambda a: a[3][1]))

		# remove slow isopoints inside
		bearing = {}
		for x in newisopoints:
			k = str (int (x[3][1] * 10))
			if k in bearing:
				if x[3][0] > bearing[k][3][0]:
					bearing[k] = x
			else:
				bearing[k] = x

		isonew = []
		for x in bearing:	
			isonew.append (bearing[x])


		isonew = sorted (isonew, key=(lambda a: a[3][1]))

		print (len (isonew), len(newisopoints), time.time () - bt0)

		isocrone.append (isonew)

		return isocrone


	# Calculate the Velocity-Made-Good of a boat sailing from
	# start to end at current speed / angle
	def calculateVMG (self, speed, angle, start, end):
		return speed * math.cos (angle)


	def route (self, lastlog, t, start, end):

		return {
			'time': 0,
			'path': [],
			'isochrones': []
		}
