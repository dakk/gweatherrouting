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
from typing import Generic, TypeVar
from . import Track
from .collection import CollectionWithActiveElement

T = TypeVar('T', bound=Track)

class _TrackCollection (CollectionWithActiveElement, Generic[T]):
	def __init__(self):
		super().__init__(Track, 'track')


	def importFromGPX(self, gpx):
		for track in gpx.tracks:
			waypoints = []

			for segment in track.segments:
				for point in segment.points:
					waypoints.append([point.latitude, point.longitude])

			self.append(Track(track.name, waypoints, collection=self))

TrackCollection = _TrackCollection[Track]
