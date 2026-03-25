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
from typing import List
import gi

gi.require_version("Gtk", "3.0")

from gi.repository import GLib, GObject

from gweatherrouting.core.aismanager import SHIP_TYPE_COLORS
from gweatherrouting.gtk.widgets.mapwidget import MapPoint

# Ship marker half-size in pixels
MARKER_SIZE = 7
LABEL_FONT_SIZE = 10
# Minimum pixel distance between label centers to avoid overlap
LABEL_MIN_DIST_SQ = 70 * 70


class AISMapLayer(GObject.GObject):
    def __init__(self, core):
        GObject.GObject.__init__(self)
        self.visible = True
        self.ais_manager = core.ais_manager
        self._gpsmap = None
        GLib.timeout_add(3000, self._refresh)

    def set_visible(self, visible):
        self.visible = visible

    def _draw_target(self, gpsmap, cr, target, label_positions):
        """Draw a single AIS target on the map."""
        if not target.has_valid_position():
            return

        x, y = gpsmap.convert_geographic_to_screen(
            MapPoint.new_degrees(target.latitude, target.longitude)
        )

        # Determine orientation
        angle_deg = 0.0
        if target.cog is not None:
            angle_deg = target.cog
        elif target.heading is not None:
            angle_deg = float(target.heading)
        angle = math.radians(angle_deg)

        color = SHIP_TYPE_COLORS.get(target.category, (0.5, 0.5, 0.5))
        s = MARKER_SIZE

        cr.save()
        cr.translate(x, y)
        cr.rotate(angle)

        # Ship shape
        cr.move_to(0, -s * 2)
        cr.line_to(s * 0.8, s)
        cr.line_to(0, s * 0.6)
        cr.line_to(-s * 0.8, s)
        cr.close_path()

        cr.set_source_rgba(color[0], color[1], color[2], 0.7)
        cr.fill_preserve()
        cr.set_source_rgba(color[0], color[1], color[2], 1.0)
        cr.set_line_width(1.0)
        cr.stroke()

        # Speed vector line
        if target.sog is not None and target.sog > 0.5:
            length = min(target.sog * 3, 40)
            cr.set_source_rgba(color[0], color[1], color[2], 0.5)
            cr.set_line_width(0.8)
            cr.move_to(0, -s * 2)
            cr.line_to(0, -s * 2 - length)
            cr.stroke()

        cr.restore()

        # Label — skip if too close to an existing label
        lx = x + s + 4
        ly = y + 4
        for px, py in label_positions:
            if (lx - px) ** 2 + (ly - py) ** 2 < LABEL_MIN_DIST_SQ:
                return
        label_positions.append((lx, ly))

        label = target.name if target.name else str(target.mmsi)
        cr.set_font_size(LABEL_FONT_SIZE)
        extents = cr.text_extents(label)

        cr.set_source_rgba(0.0, 0.0, 0.0, 0.5)
        cr.rectangle(
            lx - 2, ly - extents.height - 2, extents.width + 4, extents.height + 4
        )
        cr.fill()

        cr.set_source_rgba(1.0, 1.0, 1.0, 0.95)
        cr.move_to(lx, ly)
        cr.show_text(label)
        cr.stroke()

    def _refresh(self):
        if self._gpsmap is not None and self.visible:
            self._gpsmap.queue_draw()
        return True

    def do_draw(self, gpsmap, cr):
        self._gpsmap = gpsmap
        if not self.visible:
            return

        targets = self.ais_manager.get_active_targets()
        label_positions: List = []
        for target in targets:
            self._draw_target(gpsmap, cr, target, label_positions)

    def do_render(self, gpsmap):
        pass

    def do_busy(self):
        return False

    def do_button_press(self, gpsmap, gdkeventbutton):
        return False
