# -*- coding: utf-8 -*-
# Copyright (C) 2017-2026 Davide Gessa
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


# Abstract class for a single gauge
class Gauge:
    # Width and height of this gauge cell
    WIDTH = 100
    HEIGHT = 50

    def __init__(self, label, unit=""):
        self.label = label
        self.unit = unit
        self.value = None

    def set_value(self, value):
        self.value = value

    def draw(self, cr, x, y):
        """Draw this gauge at position (x, y). Override in subclasses."""
        raise NotImplementedError
