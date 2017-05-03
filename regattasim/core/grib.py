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

from .. import config

logger = logging.getLogger ('regattasim')

def riduci360(alfa):
    n=int(alfa*0.5/math.pi)
    n=math.copysign(n,1)
    if alfa>2.0*math.pi:
        alfa=alfa-n*2.0*math.pi
    if alfa<0:
        alfa=(n+1)*2.0*math.pi+alfa
    if alfa>2.0*math.pi or alfa<0:
        return 0.0
    return alfa

class Grib:
	def __init__ (self):
		#self.parse (open ('/home/dakk/testgrib.grb', 'rb'))
		pass

	def getDownloadList ():
		data = requests.get ('http://grib.virtual-loup-de-mer.org/').text
		soup = BeautifulSoup (data, 'html.parser')
		gribStore = []

		for row in soup.find ('table').find_all ('tr'):
			r = row.find_all ('td')

			if len (r) >= 4 and r[1].text.find ('.grb') != -1:
				gribStore.append ([r[1].text, 'NOAA', r[2].text, r[3].text, 'http://grib.virtual-loup-de-mer.org/' + r[1].find ('a', href=True)['href']])
		return gribStore


	def getContinousWind (self, t, bounds):
		print (int (int (round (t)) / 3) * 3, int (int (round (t+3)) / 3) * 3)

		t1 = int (int (round (t)) / 3) * 3
		t2 = int (int (round (t+3)) / 3) * 3
		r1 = self.getWind (t1, bounds)
		r2 = self.getWind (t2, bounds)

		newdata = []

		for i in range (0, len (r1)):
			d2 = []
			for j in range (0, len (r1[i])):
				el1 = r1[i][j]
				el2 = r2[i][j]

				v1 = el1[0]+(el2[0]-el1[0])*(t-t1)*1.0/(t2-t1)
				v2 = el1[1]+(el2[1]-el1[1])*(t-t1)*1.0/(t2-t1)
				d2.append ((v1, v2))
			newdata.append (d2)

		return newdata


	# Get wind direction and speed in a point, used by simulator
	def getExactWind (self, t, lat, lon):
		return ()

	# Return [dir (degree), speed]
	def getWind (self, t, bounds):
		self.grbs.seek(0) 
		u = self.rindex [t]['u']
		v = self.rindex [t]['v']

		uu, lat, lon = u.data (lat1=bounds[0][0],lat2=bounds[1][0],lon1=bounds[0][1],lon2=bounds[1][1])
		vv, lat, lon = v.data (lat1=bounds[0][0],lat2=bounds[1][0],lon1=bounds[0][1],lon2=bounds[1][1])

		data = []		
		for i in range (0, len (uu)):
			data2 = []
			for j in range (0, len (uu[i])):
				tws=0
				twd=0
				#print (u, v)
				tws=(uu[i][j]**2+vv[i][j]**2)/2.
				twd=math.atan2(uu[i][j],vv[i][j])+math.pi
				twd=riduci360(twd)
				data2.append ((math.degrees(twd), tws))
			data.append (data2)
		return data


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