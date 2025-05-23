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
from typing import Generic, Tuple, TypeVar

from gweatherrouting.core.geo.collection import Collection
from gweatherrouting.core.geo.poi import POI

T = TypeVar("T", bound=POI)


class _POICollection(Collection, Generic[T]):
    def __init__(self):
        super().__init__(POI, "poi")

    def import_from_gpx(self, gpx):
        for waypoint in gpx.waypoints:
            self.append(
                POI(
                    waypoint.name,
                    (waypoint.latitude, waypoint.longitude),
                    collection=self,
                )
            )

    def to_nmea_fpec(self):
        s = ""
        for x in self.elements:
            s += x.to_nmea_fpec() + "\n"
        s += "$PFEC,GPxfr,CTL,E"
        return s

    def move(self, name, lat, lon):
        c = self.get_by_name(name)
        if c is not None:
            c.position = (lat, lon)

    def create(self, position: Tuple[float, float]):
        e = POI(self.get_unique_name(), position=position, collection=self)
        self.append(e)
        self.save()
        return e


POICollection = _POICollection[POI]
