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

import math

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import GObject

from gweatherrouting.core.aismanager import SHIP_TYPE_COLORS, AISTarget
from gweatherrouting.gtk.widgets.mapwidget import MapPoint

# Triangle size in pixels
TRIANGLE_SIZE = 10


class AISMapLayer(GObject.GObject):
    def __init__(self, core):
        GObject.GObject.__init__(self)
        self.visible = True
        self.ais_manager = core.ais_manager

    def set_visible(self, visible):
        self.visible = visible

    def _draw_target(self, gpsmap, cr, target: AISTarget) -> None:
        """Draw a single AIS target on the map."""
        if not target.has_valid_position():
            return

        x, y = gpsmap.convert_geographic_to_screen(
            MapPoint.new_degrees(target.latitude, target.longitude)
        )

        # Determine orientation: use COG, fall back to heading, default 0
        angle_deg = 0.0
        if target.cog is not None:
            angle_deg = target.cog
        elif target.heading is not None:
            angle_deg = float(target.heading)
        angle = math.radians(angle_deg)

        # Get color for ship type category
        color = SHIP_TYPE_COLORS.get(target.category, (0.5, 0.5, 0.5))

        # Draw oriented triangle (pointing in direction of travel)
        s = TRIANGLE_SIZE
        # Triangle vertices: tip forward, two back corners
        tip_x = x + s * 1.5 * math.sin(angle)
        tip_y = y - s * 1.5 * math.cos(angle)
        left_x = x + s * math.sin(angle - 2.5)
        left_y = y - s * math.cos(angle - 2.5)
        right_x = x + s * math.sin(angle + 2.5)
        right_y = y - s * math.cos(angle + 2.5)

        cr.move_to(tip_x, tip_y)
        cr.line_to(left_x, left_y)
        cr.line_to(right_x, right_y)
        cr.close_path()

        cr.set_source_rgba(color[0], color[1], color[2], 0.7)
        cr.fill_preserve()

        cr.set_source_rgba(color[0], color[1], color[2], 1.0)
        cr.set_line_width(1.0)
        cr.stroke()

        # Draw label (name or MMSI)
        label = target.name if target.name else str(target.mmsi)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.9)
        cr.set_font_size(9)
        cr.move_to(x + TRIANGLE_SIZE + 3, y + 3)
        cr.show_text(label)
        cr.stroke()

    def do_draw(self, gpsmap, cr):
        if not self.visible:
            return

        targets = self.ais_manager.get_active_targets()
        for target in targets:
            self._draw_target(gpsmap, cr, target)

    def do_render(self, gpsmap):
        pass

    def do_busy(self):
        return False

    def do_button_press(self, gpsmap, gdkeventbutton):
        return False
