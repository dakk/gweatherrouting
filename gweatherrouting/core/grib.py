# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
# Copyright (C) 2012 Riccardo Apolloni
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

import logging
import random
import struct
import math
import datetime
import eccodes

from . import utils
from .. import log

logger = logging.getLogger ('gweatherrouting')

class MetaGrib:
	def __init__(self, name, centre, bounds, startTime, lastForecast):
		self.name = name
		self.centre = centre.upper()
		self.bounds = bounds
		self.startTime = startTime
		self.lastForecast = lastForecast


class Grib:
	def __init__ (self, name, centre, bounds, rindex, startTime, lastForecast):
		self.name = name
		self.centre = centre.upper()
		self.cache = utils.DictCache(16)
		self.rindex = rindex
		self.bounds = bounds
		self.startTime = startTime
		self.lastForecast = lastForecast



	# Get Wind data from cache if available (speed up the entire simulation)
	def _getWindDataCached (self, t, bounds):
		h = ('%f%f%f%f%f' % (t, bounds[0][0], bounds[0][1], bounds[1][0], bounds[1][1]))

		if h in self.cache:
			return self.cache [h]
		else:
			u = self.rindex [t]['u']
			v = self.rindex [t]['v']

			uu1, latuu, lonuu = [],[],[]
			vv1, latvv, lonvv = [],[],[]
			
			for x in u:
				if x['lat'] >= bounds[0][0] and x['lat'] <= bounds[1][0] and x['lon'] >= bounds[0][1] and x['lon'] <= bounds[1][1]: 
					uu1.append(x['value'])
					latuu.append(x['lat'])
					lonuu.append(x['lon'])

			for x in v:
				if x['lat'] >= bounds[0][0] and x['lat'] <= bounds[1][0] and x['lon'] >= bounds[0][1] and x['lon'] <= bounds[1][1]: 
					vv1.append(x['value'])
					latvv.append(x['lat'])
					lonvv.append(x['lon'])


			self.cache [h] = (uu1, vv1, latuu, lonuu)
			return self.cache [h]


	def getWind (self, t, bounds):
		t1 = int (int (round (t)) / 3) * 3
		t2 = int (int (round (t+6)) / 3) * 3

		if t2 == t1: t1 -= 3

		lon1 = min (bounds[0][1], bounds[1][1])
		lon2 = max (bounds[0][1], bounds[1][1])

		otherside = None

		if lon1 < 0.0 and lon2 < 0.0:
			lon1 = 180. + abs (lon1)
			lon2 = 180. + abs (lon2)
		elif lon1 < 0.0:
			otherside = (-180.0, lon1)
		elif lon2 < 0.0:
			otherside = (-180.0, lon2)

		bounds = [(bounds[0][0], min (lon1, lon2)), (bounds[1][0], max (lon1, lon2))]
		(uu1, vv1, latuu, lonuu) = self._getWindDataCached (t1, bounds)
		(uu2, vv2, latuu2, lonuu2) = self._getWindDataCached (t2, bounds)

		if otherside:
			bounds = [(bounds[0][0], min (otherside[0], otherside[1])), (bounds[1][0], max (otherside[0], otherside[1]))]
			dataotherside = self.getWind (t, bounds)
		else:
			dataotherside = []

		data = []		

		for j in range (0, len (uu1)):
			lon = lonuu[j]
			lat = latuu[j]

			if lon > 180.0:
				lon = -180. + (lon - 180.)

			#if utils.pointInCountry (lat, lon):
			#	continue

			uu = uu1[j] + (uu2[j] - uu1[j]) * (t - t1) * 1.0 / (t2 - t1)
			vv = vv1[j] + (vv2[j] - vv1[j]) * (t - t1) * 1.0 / (t2 - t1)
			
			tws=0
			twd=0
			tws=(uu**2+vv**2)/2.
			twd=math.atan2(uu,vv)+math.pi
			twd=utils.reduce360(twd)

			data.append ((math.degrees(twd), tws, (lat, lon)))
		
		
		return [data] + dataotherside



	# Get wind direction and speed in a point, used by simulator
	def getWindAt (self, t, lat, lon):	
		bounds = [(math.floor (lat * 2) / 2., math.floor (lon * 2) / 2.), (math.ceil (lat * 2) / 2., math.ceil (lon * 2) / 2.)]
		data = self.getWind (t, bounds)

		wind = (data[0][0][0], data[0][0][1])
		return wind


	def parseMetadata(path):
		grbs = eccodes.GribFile (path) 

		# TODO: get bounds and timeframe
		bounds = [0, 0, 0, 0]
		hoursForecasted = None
		startTime = None
		rindex = {}			
		centre = ''

		for r in grbs:
			if r['name'] != '10 metre U wind component' and r['name'] != '10 metre V wind component':
				continue

			if 'centre' in r.keys():
				centre = r['centre']

			if 'forecastTime' in r.keys():
				ft = r['forecastTime']
			else:
				ft = r['P1']

			startTime = datetime.datetime(int(r['year']), int(r['month']), int(r['day']), int(r['hour']), int(r['minute']))

			if hoursForecasted == None or hoursForecasted < int(ft):
				hoursForecasted = int(ft)

		return MetaGrib(path.split('/')[-1], centre, bounds, startTime, hoursForecasted)


	def parse (path):
		grbs = eccodes.GribFile (path) 

		# TODO: get bounds and timeframe
		bounds = [0, 0, 0, 0]
		hoursForecasted = None
		startTime = None
		rindex = {}			
		centre = ''

		for r in grbs:
			if r['name'] != '10 metre U wind component' and r['name'] != '10 metre V wind component':
				continue

			if 'centre' in r.keys():
				centre = r['centre']

			if 'forecastTime' in r.keys():
				ft = r['forecastTime']
			else:
				ft = r['P1']

			startTime = datetime.datetime(int(r['year']), int(r['month']), int(r['day']), int(r['hour']), int(r['minute']))

			if hoursForecasted == None or hoursForecasted < int(ft):
				hoursForecasted = int(ft)

			# timeIndex = str(r['dataDate'])+str(r['dataTime'])
			if r['name'] == '10 metre U wind component':
				rindex [hoursForecasted] = { 'u': eccodes.codes_grib_get_data(r.gid) }
			elif r['name'] == '10 metre V wind component':
				rindex [hoursForecasted]['v'] = eccodes.codes_grib_get_data(r.gid)

		print(startTime, hoursForecasted)
		return Grib(path.split('/')[-1], centre, bounds, rindex, startTime, hoursForecasted)
			
