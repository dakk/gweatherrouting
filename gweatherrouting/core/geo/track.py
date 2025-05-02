# -*- coding: utf-8 -*-
# Copyright (C) 2017-2025 Davide Gessa
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
from typing import Dict, List, Tuple

import gpxpy

from gweatherrouting.core.geo.elementmultipoint import ElementMultiPoint


class Track(ElementMultiPoint):
    def __init__(self, name, points=[], visible=True, collection=None):
        super().__init__(name, points, visible, collection)

    @staticmethod
    def from_json(j: Dict) -> "Track":
        d = ElementMultiPoint.from_json(j)
        return Track(d.name, d.points, d.visible)

    def to_gpx_object(self):
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)

        for x in self.points:
            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(x[0], x[1]))

        return gpx_track

    def to_list(self) -> List[Tuple[float, float]]:
        return [(x[0], x[1]) for x in self.points]
