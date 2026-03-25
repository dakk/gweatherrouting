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

import logging
import math

import gi
from weatherrouting import Polar

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk

from gweatherrouting.common import resource_path

logger = logging.getLogger("gweatherrouting")


POLAR_COLORS = [
    (1.0, 0.2, 0.2),  # red
    (0.2, 0.6, 1.0),  # blue
    (0.2, 0.8, 0.2),  # green
    (1.0, 0.6, 0.0),  # orange
    (0.8, 0.2, 0.8),  # purple
    (0.0, 0.8, 0.8),  # cyan
    (1.0, 1.0, 0.2),  # yellow
    (1.0, 0.4, 0.6),  # pink
    (0.6, 0.4, 0.2),  # brown
    (0.4, 1.0, 0.6),  # mint
    (0.6, 0.6, 1.0),  # lavender
    (1.0, 0.8, 0.4),  # gold
]


class PolarWidget(Gtk.DrawingArea):
    def __init__(self, parent):
        self.par = parent
        super(PolarWidget, self).__init__()

        self.set_size_request(60, 180)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.connect("draw", self.draw)
        self.polar = None

        self.connect("motion-notify-event", self.on_mouse_move)
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)

        self.mousePos = None

    def on_mouse_move(self, widget, event):
        p = self.get_pointer()
        self.mousePos = (p.x, p.y)
        # self.queue_draw()

    def load_polar(self, polar_file):
        polar = None
        try:
            polar = Polar(resource_path("gweatherrouting", f"data/polars/{polar_file}"))
        except:
            try:
                polar = Polar(polar_file)
            except:
                logger.error("Error loading polar file %s", polar_file)

        self.set_polar(polar)

    def set_polar(self, polar):
        self.polar = polar
        self.queue_draw()

    def draw(self, area, cr):  # noqa: C901
        if not self.polar:
            return

        a = self.get_allocation()
        width = a.width
        height = a.height

        max_r = 80.0
        margin = 25.0
        # Scale based on height only to preserve aspect ratio
        logical_w = max_r + 2 * margin
        logical_h = 2 * max_r + 2 * margin
        s = min(width / logical_w, height / logical_h)
        cr.scale(s, s)
        # Clip to logical bounds so the polar doesn't bleed into extra width
        cr.rectangle(0, 0, logical_w, logical_h)
        cr.clip()

        cx = margin
        cy = max_r + margin

        # Dark background
        cr.set_source_rgb(0.15, 0.17, 0.20)
        cr.paint()

        # Compute max speed for scaling polar curves to fit max_r
        max_speed = 0
        for j in range(len(self.polar.twa)):
            for i in range(len(self.polar.tws)):
                if len(self.polar.speed_table[j]) > i:
                    max_speed = max(max_speed, self.polar.speed_table[j][i])
        if max_speed <= 0:
            max_speed = 1
        speed_scale = max_r / max_speed

        # Speed rings (dashed, subtle)
        tws_step = 1
        if len(self.polar.tws) > 7:
            tws_step = 2

        max_tws = max(self.polar.tws) if self.polar.tws else 1
        for x in self.polar.tws:
            r = (x / max_tws) * max_r
            cr.set_line_width(0.2)
            cr.set_source_rgba(1, 1, 1, 0.15)
            cr.set_dash([2, 2])
            cr.arc(cx, cy, r, math.radians(-90), math.radians(90.0))
            cr.stroke()
            cr.set_dash([])

        # Speed ring labels
        for x in self.polar.tws[::tws_step]:
            r = (x / max_tws) * max_r
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.set_font_size(6)
            cr.move_to(cx - 22, cy - r + 2)
            cr.show_text(str(int(x)) + " kt")

        # TWA radial lines (subtle)
        twa_step = 1
        if len(self.polar.twa) > 20:
            twa_step = int(len(self.polar.twa) / 10)

        for x in self.polar.twa[::twa_step]:
            cr.set_line_width(0.2)
            cr.set_source_rgba(1, 1, 1, 0.12)
            cr.move_to(cx, cy)
            cr.line_to(cx + math.sin(x) * max_r, cy - math.cos(x) * max_r)
            cr.stroke()

        # TWA angle labels
        for x in self.polar.twa[::twa_step]:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.set_font_size(6)
            lx = cx + math.sin(x) * (max_r + 10)
            ly = cy - math.cos(x) * (max_r + 10)
            cr.move_to(lx, ly)
            cr.show_text(str(int(math.degrees(x))) + "°")

        # 0° axis line (slightly brighter)
        cr.set_line_width(0.3)
        cr.set_source_rgba(1, 1, 1, 0.25)
        cr.move_to(cx, cy)
        cr.line_to(cx, cy - max_r)
        cr.stroke()

        # Polar curves
        for i in range(0, len(self.polar.tws), 1):
            color = POLAR_COLORS[i % len(POLAR_COLORS)]
            cr.set_source_rgba(color[0], color[1], color[2], 0.85)
            cr.set_line_width(1.0)

            first = True
            for j in range(0, len(self.polar.twa), 1):
                if len(self.polar.speed_table[j]) <= i:
                    continue

                speed = self.polar.speed_table[j][i]
                if speed <= 0:
                    first = True
                    continue

                px = cx + speed_scale * speed * math.sin(self.polar.twa[j])
                py = cy - speed_scale * speed * math.cos(self.polar.twa[j])

                if first:
                    cr.move_to(px, py)
                    first = False
                else:
                    cr.line_to(px, py)

            cr.stroke()

        # Center dot
        cr.set_source_rgba(1, 1, 1, 0.4)
        cr.arc(cx, cy, 1.2, 0, 2 * math.pi)
        cr.fill()
