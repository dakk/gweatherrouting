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
from gweatherrouting.core.utils import unique_name

T = TypeVar("T", bound=Element)


class CollectionStorage(Storage):
    def __init__(self, name):
        Storage.__init__(self, name)
        self.data = {}
        self.load_or_save_default()


class Collection(Generic[T]):
    def __init__(self, of, base_name):
        self.storage = CollectionStorage(base_name)
        self.of = of
        self.elements: list[T] = []
        self.base_name = base_name

        if self.storage.data is not None:
            self.load_json(self.storage.data)

    def save(self):
        self.storage.data = self.to_json()

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

    def to_json(self):
        return {"elements": [x.to_json() for x in self.elements]}

    def load_json(self, j):
        self.clear()

        if "elements" not in j:
            return

        for x in j["elements"]:
            e = self.of.from_json(x)
            e.collection = self
            self.append(e)

    def get_unique_name(self, base_name=None) -> str:
        if base_name is None:
            base_name = self.base_name
        return unique_name(base_name, self.elements)

    def new_element(self, **kwargs):
        e = self.of(self.get_unique_name(), collection=self, **kwargs)
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

    def remove_by_name(self, name):
        c = self.get_by_name(name)
        if c is not None:
            self.remove(c)

    def get_by_name(self, n) -> Optional[T]:
        for x in self.elements:
            if x.name == n:
                return x
        return None

    def exists(self, n) -> bool:
        for x in self.elements:
            if x.name == n:
                return True
        return False

    def to_gpx_object(self):
        gpx = gpxpy.gpx.GPX()

        for x in self.elements:
            ob = x.to_gpx_object()
            if isinstance(gpx.GPXTrack, ob):
                gpx.tracks.append(ob)
            elif isinstance(gpx.GPXRoute, ob):
                gpx.routes.append(ob)
            elif isinstance(gpx.GPXWaypoint, ob):
                gpx.waypoints.append(ob)

        return gpx

    def export(self, dest, fmt="gpx"):
        if fmt == "gpx":
            gpx = self.to_gpx_object()

            try:
                f = open(dest, "w")
                f.write(gpx.to_xml())
            except Exception as e:
                print(str(e))


class CollectionWithActiveElement(Collection):
    def __init__(self, of, base_name):
        self.activeElement = None

        super().__init__(of, base_name)

    def to_json(self):
        c = super().to_json()
        c["activeElement"] = self.activeElement.name if self.activeElement else None
        return c

    def load_json(self, j):
        super().load_json(j)
        self.activeElement = (
            self.get_by_name(j["activeElement"]) if "activeElement" in j else None
        )

    def has_active(self):
        return self.activeElement is not None

    def get_active(self):
        return self.activeElement

    def set_active(self, element):
        self.activeElement = element
        self.save()

    def activate(self, name):
        self.set_active(self.get_by_name(name))

    def is_active(self, element):
        return self.activeElement == element

    def remove(self, element):
        if self.activeElement == element:
            self.activeElement = None

        Collection.remove(self, element)
