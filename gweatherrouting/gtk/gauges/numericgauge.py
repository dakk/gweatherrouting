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

from .gauge import Gauge


class NumericGauge(Gauge):
    """A simple numeric gauge that displays a value with label and unit."""

    WIDTH = 100
    HEIGHT = 50

    def __init__(self, label, unit="", fmt="%.1f"):
        super().__init__(label, unit)
        self.fmt = fmt

    def draw(self, cr, x, y):
        """Draw a numeric gauge cell at (x, y)."""
        w = self.WIDTH
        h = self.HEIGHT

        # Background
        cr.set_source_rgba(0.1, 0.1, 0.1, 0.7)
        cr.rectangle(x, y, w, h)
        cr.fill()

        # Border
        cr.set_source_rgba(0.4, 0.4, 0.4, 0.8)
        cr.set_line_width(1.0)
        cr.rectangle(x, y, w, h)
        cr.stroke()

        # Label (top, small)
        cr.set_source_rgba(0.7, 0.7, 0.7, 1.0)
        cr.set_font_size(10)
        cr.move_to(x + 5, y + 14)
        cr.show_text(self.label)

        # Value (center, large)
        cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        cr.set_font_size(18)
        if self.value is not None:
            value_text = self.fmt % self.value
        else:
            value_text = "---"
        cr.move_to(x + 5, y + 36)
        cr.show_text(value_text)

        # Unit (right of value, small)
        if self.unit:
            cr.set_source_rgba(0.7, 0.7, 0.7, 1.0)
            cr.set_font_size(10)
            # Position unit after the value text
            cr.set_font_size(18)
            val_width = cr.text_extents(value_text).width
            cr.set_font_size(10)
            cr.move_to(x + 5 + val_width + 4, y + 36)
            cr.show_text(self.unit)
