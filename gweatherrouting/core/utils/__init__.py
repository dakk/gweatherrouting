# -*- coding: utf-8 -*-
# Copyright (C) 2017-2025 Davide Gessa
# Copyright (C) 2012 Riccardo Apolloni
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
# isort:skip_file
import json
from geojson_utils import point_in_polygon
from typing import Dict, Callable, List

from gweatherrouting.common import resource_path
from gweatherrouting.core.storage import *  # noqa: F401, F403
from weatherrouting import utils

COUNTRIES = json.load(
    open(resource_path("gweatherrouting", "data/countries.geojson"), "r")
)
COUNTRY_SHAPES = []


def extractCoordinates(coord):
    c = []
    for x in coord:
        if isinstance(x[0], float):
            return coord
        else:
            for xx in extractCoordinates(x):
                c.append(xx)
    return c


for feature in COUNTRIES["features"]:
    # Calculate bbox for every feature
    c = extractCoordinates(feature["geometry"]["coordinates"])
    c2 = [x[0] for x in c]
    c1 = [x[1] for x in c]

    bbox = [[min(c1), min(c2)], [max(c1), max(c2)]]

    feature["properties"]["bbox"] = bbox

    COUNTRY_SHAPES.append(feature)


def point_in_bbox(bbox, lat, lon):
    if (
        lat >= bbox[0][0]
        and lat <= bbox[1][0]
        and lon >= bbox[0][1]
        and lon <= bbox[1][1]
    ):
        return True
    return False


# def bbox_inside(bbox1, bbox2):
# 	if point_in_polygon({"type": "Point", "coordinates": [bbox1[0][0], bbox1[0][1]]},
# {"type": "Polygon", "coordinates": [bbox2]}):
# 		return True
# 	if point_in_polygon({"type": "Point", "coordinates": [bbox1[1][0], bbox1[1][1]]},
# {"type": "Polygon", "coordinates": [bbox2]}):
# 		return True
# 	if point_in_polygon({"type": "Point", "coordinates": [bbox1[2][0], bbox1[2][1]]},
# {"type": "Polygon", "coordinates": [bbox2]}):
# 		return True
# 	if point_in_polygon({"type": "Point", "coordinates": [bbox1[3][0], bbox1[3][1]]},
# {"type": "Polygon", "coordinates": [bbox2]}):
# 		return True

# 	return False

# # Return a list of country geometry that intersecate a bbox
# def countriesInBBox(bbox):
# 	ilist = []

# 	for feature in COUNTRY_SHAPES:
# 		if bbox_inside(bbox, feature['properties']['bbox'][0]):
# 			ilist.append(feature)
# 		elif bbox_inside(feature['properties']['bbox'][0], bbox):
# 			ilist.append(feature)

# 	return ilist


# Return true if the given point is inside a country
def pointInCountry(lat: float, lon: float) -> bool:
    for feature in COUNTRY_SHAPES:
        if point_in_bbox(feature["properties"]["bbox"], lat, lon):
            if point_in_polygon(
                {"type": "Point", "coordinates": [lon, lat]}, feature["geometry"]
            ):
                return True

    return False


def pointValidity(lat: float, lon: float) -> bool:
    return not pointInCountry(lat, lon)


def pointsValidity(latlons):
    return list(map(lambda ll: pointValidity(ll[0], ll[1]), latlons))


def uniqueName(name, collection=None):
    if not collection:
        return name

    names = []
    for x in collection:
        names.append(x.name)
    if name in names:
        for i in range(1, 1000):
            nname = name + "-" + str(i)
            if nname not in names:
                return nname
    return name


def pointDistance(latA, lonA, latB, lonB, unit="nm"):
    return utils.pointDistance(latA, lonA, latB, lonB, "nm")


def routagePointDistance(latA, lonA, Distanza, Rotta):
    return utils.routagePointDistance(latA, lonA, Distanza, Rotta, "nm")


def reduce360(alfa):
    return utils.reduce360(alfa)


def ortodromic(latA, lonA, latB, lonB):
    return utils.ortodromic(latA, lonA, latB, lonB)


class EventDispatcher:
    handlers: Dict[str, List[Callable]] = {}

    def connect(self, evt, f):
        if evt not in self.handlers:
            self.handlers[evt] = []
        self.handlers[evt].append(f)

    def disconnect(self, evt, f):
        self.handlers[evt].remove(f)

    def dispatch(self, evt, e):
        if evt not in self.handlers:
            return

        for x in self.handlers[evt]:
            x(e)


class dotdict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get  # type: ignore
    __setattr__ = dict.__setitem__  # type: ignore
    __delattr__ = dict.__delitem__  # type: ignore
