# -*- coding: utf-8 -*-
# Copyright (C) 2017-2024 Davide Gessa
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
import math
import os
import json
import latlon
from geojson_utils import point_in_polygon

try:
    from .storage import *  # noqa: F401, F403
except:
    from .dummy_storage import *  # noqa: F401, F403

this_dir, this_fn = os.path.split(__file__)
COUNTRIES = json.load(open(this_dir + "/../../data/countries.geojson", "r"))
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
def pointInCountry(lat, lon):
    for feature in COUNTRY_SHAPES:
        if point_in_bbox(feature["properties"]["bbox"], lat, lon):
            if point_in_polygon(
                {"type": "Point", "coordinates": [lon, lat]}, feature["geometry"]
            ):
                return True

    return False


def pointValidity(lat, lon):
    return not pointInCountry(lat, lon)


def pointsValidity(latlons):
    return list(map(pointValidity, latlons))


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


EARTH_RADIUS = 60.0 * 360 / (2 * math.pi)  # nm


def pointDistance(latA, lonA, latB, lonB):
    p1 = latlon.LatLon(latlon.Latitude(latA), latlon.Longitude(lonA))
    p2 = latlon.LatLon(latlon.Latitude(latB), latlon.Longitude(lonB))
    return p1.distance(p2)


def routagePointDistance(latA, lonA, Distanza, Rotta):
    p = latlon.LatLon(latlon.Latitude(latA), latlon.Longitude(lonA))
    of = p.offset(math.degrees(Rotta), Distanza).to_string("D")
    return (float(of[0]), float(of[1]))


def reduce360(alfa):
    if math.isnan(alfa):
        return 0.0

    n = int(alfa * 0.5 / math.pi)
    n = math.copysign(n, 1)
    if alfa > 2.0 * math.pi:
        alfa = alfa - n * 2.0 * math.pi
    if alfa < 0:
        alfa = (n + 1) * 2.0 * math.pi + alfa
    if alfa > 2.0 * math.pi or alfa < 0:
        return 0.0
    return alfa


class DictCache(dict):
    def __init__(self, max_entries=50):
        self.entries = []
        self.max_entries = max_entries

    def __setitem__(self, key, value):
        super(DictCache, self).__setitem__(key, value)
        self.__dict__.update({key: value})
        self.entries.append(key)

        if len(self.entries) > self.max_entries:
            # TODO:? never used # td = self.entries[0]
            self.entries = self.entries[1::]

    def __delitem__(self, key):
        super(DictCache, self).__delitem__(key)
        del self.__dict__[key]
        self.entries.remove(key)


class EventDispatcher:
    handlers = {}

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

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
