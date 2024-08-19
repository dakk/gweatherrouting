# -*- coding: utf-8 -*-
# Copyright (C) 2017-2024 Davide Gessa
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
"""
import gpxpy

from gweatherrouting.core.geo.elementmultipoint import ElementMultiPoint


class Track(ElementMultiPoint):
    def __init__(self, name, points=[], visible=True, collection=None):
        super().__init__(name, points, visible, collection)

    @staticmethod
    def fromJSON(j):
        d = ElementMultiPoint.fromJSON(j)
        return Track(d.name, d.points, d.visible)

    def toGPXObject(self):
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)

        for x in self.points:
            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(x[0], x[1]))

        return gpx_track
