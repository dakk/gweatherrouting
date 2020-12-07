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
import LatLon23
import math
import os
import json
from geojson_utils import point_in_polygon


this_dir, this_fn = os.path.split (__file__)
COUNTRIES = json.load (open (this_dir + '/../data/countries.geojson', 'r'))
COUNTRY_SHAPES = []

for feature in COUNTRIES['features']:
	COUNTRY_SHAPES.append(feature['geometry'])

def pointInCountry (lat, lon):
	for polygon in COUNTRY_SHAPES:
		if point_in_polygon({"type": "Point", "coordinates": [lon, lat]}, polygon):
				return True
	return False




EARTH_RADIUS=60.0*360/(2*math.pi)#nm


def ortodromic2 (lat1, lon1, lat2, lon2):
	p1 = math.radians (lat1)
	p2 = math.radians (lat2)
	dp = math.radians (lat2-lat1)
	dp2 = math.radians (lon2-lon1)

	a = math.sin (dp/2) * math.sin (dp2/2) + math.cos (p1) * math.cos (p2) * math.sin (dp2/2) * math.sin (dp2/2)
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
	return (EARTH_RADIUS * c, a)

def ortodromic (latA,lonA,latB,lonB):
	p1 = LatLon23.LatLon(LatLon23.Latitude(latA), LatLon23.Longitude(lonA))
	p2 = LatLon23.LatLon(LatLon23.Latitude(latB), LatLon23.Longitude(lonB))

	return (p1.distance (p2), math.radians (p1.heading_initial(p2)))

def lossodromic (latA,lonA,latB,lonB):
	p1 = LatLon23.LatLon(LatLon23.Latitude(latA), LatLon23.Longitude(lonA))
	p2 = LatLon23.LatLon(LatLon23.Latitude(latB), LatLon23.Longitude(lonB))

	return (p1.distance (p2, ellipse = 'sphere'), math.radians (p1.heading_initial(p2)))

def pointDistance (latA, lonA, latB, lonB):
	p1 = LatLon23.LatLon(LatLon23.Latitude(latA), LatLon23.Longitude(lonA))
	p2 = LatLon23.LatLon(LatLon23.Latitude(latB), LatLon23.Longitude(lonB))
	return p1.distance (p2)
	

def routagePointDistance (latA,lonA,Distanza,Rotta):
	p = LatLon23.LatLon(LatLon23.Latitude(latA), LatLon23.Longitude(lonA))
	of = p.offset (math.degrees (Rotta), Distanza).to_string('D')
	return (float (of[0]), float (of[1]))


def reduce360 (alfa):
	if math.isnan (alfa):
		return 0.0
		
	n=int(alfa*0.5/math.pi)
	n=math.copysign(n,1)
	if alfa>2.0*math.pi:
		alfa=alfa-n*2.0*math.pi
	if alfa<0:
		alfa=(n+1)*2.0*math.pi+alfa
	if alfa>2.0*math.pi or alfa<0:
		return 0.0
	return alfa

def reduce180 (alfa):
	if alfa>math.pi:
		alfa=alfa-2*math.pi
	if alfa<-math.pi:
		alfa=2*math.pi+alfa
	if alfa>math.pi or alfa<-math.pi:
		return 0.0
	return alfa