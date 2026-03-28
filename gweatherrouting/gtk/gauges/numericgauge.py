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

import math

from .gauge import Gauge

# Color thresholds: (max_value, r, g, b)
# Values below the first threshold get that color; above the last get the last color
_COLOR_RANGES = {
    "SOG": [
        (3, 0.3, 0.7, 1.0),
        (7, 0.2, 0.9, 0.4),
        (12, 1.0, 0.8, 0.2),
        (99, 1.0, 0.3, 0.2),
    ],
    "AWS": [
        (8, 0.3, 0.7, 1.0),
        (15, 0.2, 0.9, 0.4),
        (25, 1.0, 0.8, 0.2),
        (99, 1.0, 0.3, 0.2),
    ],
    "TWS": [
        (8, 0.3, 0.7, 1.0),
        (15, 0.2, 0.9, 0.4),
        (25, 1.0, 0.8, 0.2),
        (99, 1.0, 0.3, 0.2),
    ],
    "Depth": [
        (3, 1.0, 0.3, 0.2),
        (8, 1.0, 0.8, 0.2),
        (15, 0.2, 0.9, 0.4),
        (99, 0.3, 0.7, 1.0),
    ],
}

# Default accent color for gauges without color ranges
_DEFAULT_ACCENT = (0.4, 0.6, 0.9)


def _rounded_rect(cr, x, y, w, h, r):
    """Draw a rounded rectangle path."""
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


class NumericGauge(Gauge):
    """A numeric gauge with color accent bar and rounded design."""

    WIDTH = 110
    HEIGHT = 56

    def __init__(self, label, unit="", fmt="%.1f"):
        super().__init__(label, unit)
        self.fmt = fmt

    def _get_accent_color(self):
        """Get accent color based on current value and label-specific ranges."""
        ranges = _COLOR_RANGES.get(self.label)
        if ranges is None or self.value is None:
            return _DEFAULT_ACCENT
        for threshold, r, g, b in ranges:
            if self.value < threshold:
                return (r, g, b)
        return (ranges[-1][1], ranges[-1][2], ranges[-1][3])

    def draw(self, cr, x, y):
        """Draw a modern numeric gauge cell at (x, y)."""
        w = self.WIDTH
        h = self.HEIGHT
        radius = 6
        accent_h = 3

        # Background with rounded corners
        cr.set_source_rgba(0.1, 0.1, 0.1, 0.75)
        _rounded_rect(cr, x, y, w, h, radius)
        cr.fill()

        # Subtle border
        cr.set_source_rgba(0.35, 0.35, 0.35, 0.6)
        cr.set_line_width(0.8)
        _rounded_rect(cr, x, y, w, h, radius)
        cr.stroke()

        # Color accent bar at top
        ar, ag, ab = self._get_accent_color()
        cr.set_source_rgba(ar, ag, ab, 0.9)
        # Clip to top rounded corners
        cr.save()
        _rounded_rect(cr, x, y, w, h, radius)
        cr.clip()
        cr.rectangle(x, y, w, accent_h)
        cr.fill()
        cr.restore()

        # Label (top area, below accent)
        cr.set_source_rgba(0.6, 0.6, 0.6, 1.0)
        cr.set_font_size(9)
        label_ext = cr.text_extents(self.label)
        cr.move_to(x + (w - label_ext.width) / 2, y + accent_h + 12)
        cr.show_text(self.label)

        # Value (center, large)
        if self.value is not None:
            value_text = self.fmt % self.value
        else:
            value_text = "---"

        cr.set_font_size(20)
        val_ext = cr.text_extents(value_text)

        # Unit measurement
        unit_w = 0
        if self.unit:
            cr.set_font_size(9)
            unit_ext = cr.text_extents(self.unit)
            unit_w = unit_ext.width + 3

        # Center value + unit together
        total_text_w = val_ext.width + unit_w
        text_x = x + (w - total_text_w) / 2

        # Draw value
        cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        cr.set_font_size(20)
        cr.move_to(text_x, y + h - 10)
        cr.show_text(value_text)

        # Draw unit
        if self.unit:
            cr.set_source_rgba(0.55, 0.55, 0.55, 1.0)
            cr.set_font_size(9)
            cr.move_to(text_x + val_ext.width + 3, y + h - 10)
            cr.show_text(self.unit)
