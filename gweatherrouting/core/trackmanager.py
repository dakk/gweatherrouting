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

from .track import RoutingTrack, Track 
from .utils import uniqueName
from ..session import *
import gpxpy


defaultSession = {
	'tracks': [],
	'activeTrack': '',
	'routings': []
}

class TrackManager(Sessionable):
	def __init__(self):
		Sessionable.__init__(self, 'track-manager', defaultSession)

		self.tracks = []
		self.routings = []
		self.activeTrack = None

		for x in self.getSessionVariable('tracks'):
			tr = Track(name=x['name'], waypoints=x['waypoints'], visible=x['visible'], trackManager=self)
			self.tracks.append(tr)

		for x in self.getSessionVariable('routings'):
			tr = RoutingTrack(name=x['name'], waypoints=x['waypoints'], visible=x['visible'], trackManager=self)
			self.routings.append(tr)

		self.activate(self.getSessionVariable('activeTrack'))

	def saveTracks(self):
		ts = []
		for x in self.tracks:
			ts.append({'name': x.name, 'waypoints': x.waypoints, 'visible': x.visible })

		self.storeSessionVariable('tracks', ts)
		if self.activeTrack:
			self.storeSessionVariable('activeTrack', self.activeTrack.name)
		else:
			self.storeSessionVariable('activeTrack', '')

		ts = []
		for x in self.routings:
			ts.append({'name': x.name, 'waypoints': x.waypoints, 'visible': x.visible })

		self.storeSessionVariable('routings', ts)


	def activate(self, name):
		for x in self.tracks:
			if x.name == name:
				self.activeTrack = x
				self.saveTracks()
				return 

	def create(self):
		nt = Track(name=uniqueName('track', self.tracks), trackManager=self)
		nt.clear()
		self.tracks.append (nt)
		self.activeTrack = nt
		self.saveTracks()

	def getRouting(self, routingName):
		for x in self.routings:
			if x.name == routingName:
				return x


	def removeRouting(self, routingName):
		for x in self.routings:
			if x.name == routingName:
				self.routings.remove(x)
				self.saveTracks()
				return

	def remove(self, track):
		actTremove = False 

		if track == self.activeTrack:
			self.activeTrack = None
			actRemove = True

		self.tracks.remove(track)
		if actRemove and len(self.tracks) > 0:
			self.activeTrack = self.tracks[0]

		self.saveTracks()

	def importTrack (self, path):
		try:
			waypoints = []
			f = open(path, 'r')
			gpxpy.parse(f)

			for track in gpx.tracks:
				for segment in track.segments:
					for point in segment.points:
						waypoints.append([point.latitude, point.longitude])

			self.tracks.append(Track(path.split('/')[-1].split('.')[0], waypoints, trackManager=self))
			self.saveTracks()
			return True

		except:
			return False
