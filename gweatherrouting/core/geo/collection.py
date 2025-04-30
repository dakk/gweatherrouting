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
from typing import Generic, Optional, TypeVar

import gpxpy

from gweatherrouting.core.geo.element import Element
from gweatherrouting.core.storage import Storage
from gweatherrouting.core.utils import uniqueName

T = TypeVar("T", bound=Element)


class CollectionStorage(Storage):
    def __init__(self, name):
        Storage.__init__(self, name)
        self.data = {}
        self.loadOrSaveDefault()


class Collection(Generic[T]):
    def __init__(self, of, baseName):
        self.storage = CollectionStorage(baseName)
        self.of = of
        self.elements: list[T] = []
        self.baseName = baseName

        if self.storage.data is not None:
            self.loadJSON(self.storage.data)

    def save(self):
        self.storage.data = self.toJSON()

    def __iter__(self):
        return iter(self.elements)

    def __len__(self):
        return len(self.elements)

    def __getitem__(self, i):
        return self.elements[i]

    def __setitem__(self, i, v):
        self.elements[i] = v

    def __delitem__(self, i):
        del self.elements[i]

    def toJSON(self):
        return {"elements": [x.toJSON() for x in self.elements]}

    def loadJSON(self, j):
        self.clear()

        if "elements" not in j:
            return

        for x in j["elements"]:
            e = self.of.fromJSON(x)
            e.collection = self
            self.append(e)

    def getUniqueName(self, baseName=None) -> str:
        if baseName is None:
            baseName = self.baseName
        return uniqueName(baseName, self.elements)

    def newElement(self, **kwargs):
        e = self.of(self.getUniqueName(), collection=self, **kwargs)
        self.append(e)
        self.save()
        return e

    def clear(self):
        self.elements = []
        self.save()

    def append(self, element):
        self.elements.append(element)
        self.save()

    def remove(self, element):
        self.elements.remove(element)
        self.save()

    def removeByName(self, name):
        c = self.getByName(name)
        if c is not None:
            self.remove(c)

    def getByName(self, n) -> Optional[T]:
        for x in self.elements:
            if x.name == n:
                return x
        return None

    def exists(self, n) -> bool:
        for x in self.elements:
            if x.name == n:
                return True
        return False

    def toGPXObject(self):
        gpx = gpxpy.gpx.GPX()

        for x in self.elements:
            ob = x.toGPXObject()
            if isinstance(gpx.GPXTrack, ob):
                gpx.tracks.append(ob)
            elif isinstance(gpx.GPXRoute, ob):
                gpx.routes.append(ob)
            elif isinstance(gpx.GPXWaypoint, ob):
                gpx.waypoints.append(ob)

        return gpx

    def export(self, dest, fmt="gpx"):
        if fmt == "gpx":
            gpx = self.toGPXObject()

            try:
                f = open(dest, "w")
                f.write(gpx.to_xml())
            except Exception as e:
                print(str(e))


class CollectionWithActiveElement(Collection):
    def __init__(self, of, baseName):
        self.activeElement = None

        super().__init__(of, baseName)

    def toJSON(self):
        c = super().toJSON()
        c["activeElement"] = self.activeElement.name if self.activeElement else None
        return c

    def loadJSON(self, j):
        super().loadJSON(j)
        self.activeElement = (
            self.getByName(j["activeElement"]) if "activeElement" in j else None
        )

    def hasActive(self):
        return self.activeElement is not None

    def getActive(self):
        return self.activeElement

    def setActive(self, element):
        self.activeElement = element
        self.save()

    def activate(self, name):
        self.setActive(self.getByName(name))

    def isActive(self, element):
        return self.activeElement == element

    def remove(self, element):
        if self.activeElement == element:
            self.activeElement = None

        Collection.remove(self, element)
