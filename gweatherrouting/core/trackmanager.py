# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
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
from weatherrouting import IsoPoint
from .track import RoutingTrack, Track
from .utils import uniqueName
try:
	from . import Storage
except:
	from .dummy_storage import Storage


class TrackManagerStorage(Storage):
	def __init__(self):
		Storage.__init__(self, "track-manager")
		self.tracks = []
		self.activeTrack = ''
		self.routings = []
		self.loadOrSaveDefault()


class TrackManager():
	def __init__(self):
		self.storage = TrackManagerStorage()
		self.tracks = []
		self.routings = []
		self.activeTrack = None

		self.log = []

		for x in self.storage.tracks:
			tr = Track(name=x['name'], waypoints=x['waypoints'], visible=x['visible'], trackManager=self)
			self.tracks.append(tr)

		for x in self.storage.routings:
			ic = list(map(lambda x: list(map(IsoPoint.fromList, x)), x['isochrones']))
			tr = RoutingTrack(name=x['name'], waypoints=x['waypoints'], isochrones=ic, visible=x['visible'], trackManager=self)
			self.routings.append(tr)

		self.activate(self.storage.activeTrack)

	def saveTracks(self):
		ts = []
		for x in self.tracks:
			ts.append({'name': x.name, 'waypoints': x.waypoints, 'visible': x.visible })

		self.storage.tracks = ts
		if self.activeTrack:
			self.storage.activeTrack = self.activeTrack.name
		else:
			self.storage.activeTrack = ''

		ts = []
		for x in self.routings:
			ic = list(map(lambda x: list(map(lambda y: y.toList(), x)), x.isochrones))
			ts.append({'name': x.name, 'waypoints': x.waypoints, 'isochrones': ic, 'visible': x.visible })

		self.storage.routings = ts


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
