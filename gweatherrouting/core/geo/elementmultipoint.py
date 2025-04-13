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
from gweatherrouting.core import utils
from gweatherrouting.core.geo.element import Element


class ElementMultiPoint(Element):
    def __init__(self, name, points=[], visible=True, collection=None):
        super().__init__(name, visible, collection)
        self.points = points

    def toGPXObject(self):
        raise Exception("Not implemented")

    def toJSON(self):
        c = super().toJSON()
        c["points"] = self.points
        return c

    @staticmethod
    def fromJSON(j):
        d = Element.fromJSON(j)
        return ElementMultiPoint(d.name, j["points"], d.visible)

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value
        self.collection.save()

    def __delitem__(self, key):
        del self.points[key]
        self.collection.save()

    def __iter__(self):
        return iter(self.points)

    def length(self):
        if len(self.points) <= 1:
            return 0.0

        d = 0.0
        prev = self.points[0]
        for x in self.points[1::]:
            d += utils.pointDistance(prev[0], prev[1], x[0], x[1])
            prev = x

        return d

    def moveUp(self, i):
        if i > 0 and i < len(self):
            sw = self.points[i - 1]
            self.points[i - 1] = self.points[i]
            self.points[i] = sw
            self.collection.save()

    def moveDown(self, i):
        if i < len(self) - 1 and i >= 0:
            sw = self.points[i + 1]
            self.points[i + 1] = self.points[i]
            self.points[i] = sw
            self.collection.save()

    def remove(self, i):
        if i >= 0 and i < len(self):
            del self.points[i]
            self.collection.save()

    def duplicate(self, i):
        self.points.append(self.points[i])
        self.collection.save()

    def add(self, lat, lon, t=None):
        self.points.append((lat, lon, t))
        self.collection.save()

    def move(self, i, lat, lon):
        self.points[i] = (lat, lon, None)
        self.collection.save()

    def clear(self):
        self.points = []
        self.collection.save()
