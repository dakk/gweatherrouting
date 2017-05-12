# -*- coding: utf-8 -*-
# Copyright (C) 2017 Davide Gessa
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

import requests
import logging
import tempfile
import random
import struct
import math
import json
import pygrib
import requests
from bs4 import BeautifulSoup

from . import utils
from .. import config

logger = logging.getLogger ('regattasim')


class Grib:
	def __init__ (self):
		#self.parse (open ('/home/dakk/testgrib.grb', 'rb'))
		self.cache = {}

	def getDownloadList ():
		data = requests.get ('http://grib.virtual-loup-de-mer.org/').text
		soup = BeautifulSoup (data, 'html.parser')
		gribStore = []

		for row in soup.find ('table').find_all ('tr'):
			r = row.find_all ('td')

			if len (r) >= 4 and r[1].text.find ('.grb') != -1:
				gribStore.append ([r[1].text, 'NOAA', r[2].text, r[3].text, 'http://grib.virtual-loup-de-mer.org/' + r[1].find ('a', href=True)['href']])
		return gribStore


	def getWind (self, t, bounds):
		t1 = int (int (round (t)) / 3) * 3
		t2 = int (int (round (t+3)) / 3) * 3

		self.grbs.seek(0) 
		u1 = self.rindex [t1]['u']
		v1 = self.rindex [t1]['v']
		self.grbs.seek(0) 
		u2 = self.rindex [t2]['u']
		v2 = self.rindex [t2]['v']

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
		uu1, latuu, lonuu = u1.data (lat1=bounds[0][0],lat2=bounds[1][0],lon1=bounds[0][1],lon2=bounds[1][1])
		vv1, latvv, lonvv = v1.data (lat1=bounds[0][0],lat2=bounds[1][0],lon1=bounds[0][1],lon2=bounds[1][1])
		uu2, latuu2, lonuu2 = u2.data (lat1=bounds[0][0],lat2=bounds[1][0],lon1=bounds[0][1],lon2=bounds[1][1])
		vv2, latvv2, lonvv2 = v2.data (lat1=bounds[0][0],lat2=bounds[1][0],lon1=bounds[0][1],lon2=bounds[1][1])

		if otherside:
			bounds = [(bounds[0][0], min (otherside[0], otherside[1])), (bounds[1][0], max (otherside[0], otherside[1]))]
			dataotherside = self.getWind (t, bounds)
		else:
			dataotherside = []

		data = []		
		for i in range (0, len (uu1)):
			data2 = []
			for j in range (0, len (uu1[i])):
				lon = lonuu[i][j]
				lat = latuu[i][j]

				uu = uu1[i][j] + (uu2[i][j] - uu1[i][j]) * (t - t1) * 1.0 / (t2 - t1)
				vv = vv1[i][j] + (vv2[i][j] - vv1[i][j]) * (t - t1) * 1.0 / (t2 - t1)

				if lon > 180.0:
					lon = -180. + (lon - 180.)

				
				tws=0
				twd=0
				tws=(uu**2+vv**2)/2.
				twd=math.atan2(uu,vv)+math.pi
				twd=utils.reduce360(twd)

				data2.append ((math.degrees(twd), tws, (lat, lon)))
			data.append (data2)

		return data + dataotherside



	# Get wind direction and speed in a point, used by simulator
	def getWindAt (self, t, lat, lon):			
		data = self.getWind (t, [(lat-0.5, lon-0.5), (lat+0.5, lon+0.5)])
		wind = (data[0][0][0], data[0][0][1])
		return wind



	def parse (self, path):
		self.grbs = pygrib.open (path) 

		self.rindex = {}

		for r in self.grbs.select (name='10 metre U wind component'):
			self.rindex [r['P2']] = { 'u': r }

		for r in self.grbs.select (name='10 metre V wind component'):
			self.rindex [r['P2']]['v'] = r
			

		

	def download (self, uri, percentageCallback, callback):
		logger.info ('starting download of %s' % uri)

		response = requests.get(uri, stream=True)
		total_length = response.headers.get('content-length')
		last_signal_percent = -1
		f = open ('/home/dakk/testgrib.grb', 'wb')

		if total_length is None:
			pass
		else:
			dl = 0
			total_length = int(total_length)
			for data in response.iter_content (chunk_size=4096):
				dl += len (data)
				f.write (data)
				done = int (100 * dl / total_length)
				
				if last_signal_percent != done:
					percentageCallback (done)  
					last_signal_percent = done
		
		f.close ()
		logger.info ('download completed %s' % uri)

		self.parse ('/home/dakk/testgrib.grb')
		callback (True)