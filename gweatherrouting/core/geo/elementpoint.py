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
from typing import Tuple

from gweatherrouting.core.geo.element import Element


class ElementPoint(Element):
    def __init__(
        self, name, position: Tuple[float, float], visible=True, collection=None
    ):
        super().__init__(name, visible, collection)
        self.position = position

    def toJSON(self):
        c = super().toJSON()
        c["position"] = self.position
        return c

    @staticmethod
    def fromJSON(j):
        d = Element.fromJSON(j)
        return ElementPoint(d.name, j["position"], d.visible)

    def toGPXObject(self):
        raise Exception("Not implemented")
