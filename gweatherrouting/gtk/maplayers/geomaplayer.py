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

import dateutil.parser
import gi

gi.require_version("Gtk", "3.0")

from gi.repository import GObject

from gweatherrouting.core import Core, TimeControl, utils
from gweatherrouting.gtk.style import Style
from gweatherrouting.gtk.widgets.mapwidget import MapPoint


def _speed_color(speed):
    """Map boat speed (kts) to a color gradient: blue (slow) -> green -> yellow -> red (fast)."""
    if speed < 2:
        return (0.3, 0.5, 1.0, 0.9)
    elif speed < 4:
        return (0.2, 0.7, 0.9, 0.9)
    elif speed < 6:
        return (0.2, 0.85, 0.5, 0.9)
    elif speed < 8:
        return (0.5, 0.9, 0.2, 0.9)
    elif speed < 10:
        return (0.9, 0.85, 0.1, 0.9)
    elif speed < 12:
        return (1.0, 0.6, 0.1, 0.9)
    else:
        return (1.0, 0.3, 0.1, 0.9)


class GeoMapLayer(GObject.GObject):
    def __init__(self, core: Core, time_control: TimeControl):
        GObject.GObject.__init__(self)

        self.core = core
        self.time_control = time_control
        self.hl_routing = None
        self.hl_poi = None
        self.hl_track_item = None

    def highlight_routing(self, name):
        self.hl_routing = name

    def highlight_poi(self, name):
        self.hl_poi = name

    def highlight_track_item(self, index):
        self.hl_track_item = index

    def do_draw(self, gpsmap, cr):  # noqa: C901
        prevx = None
        prevy = None
        prevp = None

        for p in self.core.logManager.log:
            x, y = gpsmap.convert_geographic_to_screen(MapPoint.new_degrees(p[0], p[1]))

            if prevx is not None and prevy is not None:
                Style.Track.LogTrack.apply(cr)
                cr.move_to(prevx, prevy)
                cr.line_to(x, y)
                cr.stroke()

            prevx = x
            prevy = y
            prevp = p

        for tr in self.core.routingManager:
            if not tr.visible:
                continue

            highlight = tr.name == self.hl_routing

            prevx = None
            prevy = None
            prevp = None
            points_list = list(tr)
            total_pts = len(points_list)

            for i, p in enumerate(points_list):
                x, y = gpsmap.convert_geographic_to_screen(
                    MapPoint.new_degrees(p[0], p[1])
                )

                # Route name label at start with background
                if prevp is None and highlight:
                    cr.set_font_size(10)
                    ext = cr.text_extents(tr.name)
                    cr.set_source_rgba(0.0, 0.0, 0.0, 0.6)
                    cr.rectangle(x + 8, y - 12, ext.width + 8, 16)
                    cr.fill()
                    cr.set_source_rgba(1.0, 1.0, 1.0, 0.9)
                    cr.move_to(x + 12, y)
                    cr.show_text(tr.name)
                    cr.stroke()
                elif prevp is None:
                    Style.Track.RoutingTrackFont.apply(cr)
                    cr.move_to(x + 10, y)
                    cr.show_text(tr.name)
                    cr.stroke()

                # Interpolated boat position on route
                if prevp is not None:
                    tprev = dateutil.parser.parse(prevp[2])
                    tcurr = dateutil.parser.parse(p[2])

                    if (
                        tcurr >= self.time_control.time
                        and tprev < self.time_control.time
                    ):
                        dt = (tcurr - tprev).total_seconds()
                        dl = (
                            utils.point_distance(prevp[0], prevp[1], p[0], p[1])
                            / dt
                            * (self.time_control.time - tprev).total_seconds()
                        )

                        rp = utils.routage_point_distance(
                            prevp[0], prevp[1], dl, math.radians(p[6])
                        )

                        xx, yy = gpsmap.convert_geographic_to_screen(
                            MapPoint.new_degrees(rp[0], rp[1])
                        )
                        # Boat marker: filled circle with border
                        cr.set_source_rgba(0.1, 0.6, 0.1, 1.0)
                        cr.arc(xx, yy, 8, 0, 2 * math.pi)
                        cr.fill()
                        cr.set_source_rgba(1.0, 1.0, 1.0, 0.9)
                        cr.set_line_width(1.5)
                        cr.arc(xx, yy, 8, 0, 2 * math.pi)
                        cr.stroke()

                # Draw segment line colored by boat speed
                if prevx is not None and prevy is not None:
                    speed = p[5] if p[5] is not None else 0
                    lw = 3.0 if highlight else 2.0

                    r, g, b, a = _speed_color(speed)
                    cr.set_source_rgba(r, g, b, a if highlight else a * 0.7)
                    cr.set_line_width(lw)
                    cr.move_to(prevx, prevy)
                    cr.line_to(x, y)
                    cr.stroke()

                # Waypoint markers
                is_endpoint = i == 0 or i == total_pts - 1
                radius = 5 if is_endpoint else 3
                if highlight:
                    radius += 1

                if is_endpoint:
                    # Start/end: filled circle
                    cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
                    cr.arc(x, y, radius, 0, 2 * math.pi)
                    cr.fill()
                    cr.set_source_rgba(0.2, 0.2, 0.2, 1.0)
                    cr.set_line_width(1.5)
                    cr.arc(x, y, radius, 0, 2 * math.pi)
                    cr.stroke()
                else:
                    # Mid waypoints: small dots
                    speed = p[5] if p[5] is not None else 0
                    r, g, b, a = _speed_color(speed)
                    cr.set_source_rgba(r, g, b, 1.0)
                    cr.arc(x, y, radius, 0, 2 * math.pi)
                    cr.fill()

                prevx = x
                prevy = y
                prevp = p

        for tr in self.core.trackManager:
            if not tr.visible:
                continue

            active = self.core.trackManager.is_active(tr)

            prevx = None
            prevy = None
            i = 0

            for p in tr:
                i += 1
                x, y = gpsmap.convert_geographic_to_screen(
                    MapPoint.new_degrees(p[0], p[1])
                )

                item_hl = active and self.hl_track_item == (i - 1)

                if prevx is None:
                    if active:
                        Style.Track.TrackActiveFont.apply(cr)
                    else:
                        Style.Track.TrackInactiveFont.apply(cr)

                    cr.move_to(x - 10, y - 10)
                    cr.show_text(tr.name)
                    cr.stroke()

                if item_hl:
                    Style.Track.TrackItemHLFont.apply(cr)
                elif active:
                    Style.Track.TrackActivePoiFont.apply(cr)
                else:
                    Style.Track.TrackInactivePoiFont.apply(cr)

                cr.move_to(x - 4, y + 18)
                cr.show_text(str(i))
                cr.stroke()

                if prevx is not None and prevy is not None:
                    if active:
                        Style.Track.TrackActive.apply(cr)
                    else:
                        Style.Track.TrackInactive.apply(cr)

                    cr.move_to(prevx, prevy)
                    cr.line_to(x, y)
                    cr.stroke()

                if item_hl:
                    Style.Track.TrackItemHL.apply(cr)
                elif active:
                    Style.Track.TrackActive.apply(cr)
                else:
                    Style.Track.TrackInactive.apply(cr)

                Style.reset_dash(cr)

                cr.arc(x, y, 7 if item_hl else 5, 0, 2 * math.pi)
                cr.stroke()

                prevx = x
                prevy = y

        for tr in self.core.poiManager:
            if not tr.visible:
                continue

            poi_hl = tr.name == self.hl_poi

            x, y = gpsmap.convert_geographic_to_screen(
                MapPoint.new_degrees(tr.position[0], tr.position[1])
            )

            if poi_hl:
                Style.Poi.QuadHL.apply(cr)
            else:
                Style.Poi.Quad.apply(cr)
            cr.rectangle(x + 3, y - 5, len(tr.name) * 6.7, 12)
            cr.stroke_preserve()
            if poi_hl:
                Style.Poi.QuadIntHL.apply(cr)
            else:
                Style.Poi.QuadInt.apply(cr)
            cr.fill()

            if poi_hl:
                Style.Poi.FontHL.apply(cr)
            else:
                Style.Poi.Font.apply(cr)
            cr.move_to(x + 5, y + 5)
            cr.show_text(tr.name)
            cr.stroke()

            if poi_hl:
                Style.Poi.DotHL.apply(cr)
            else:
                Style.Poi.Dot.apply(cr)
            cr.arc(x, y, 4 if poi_hl else 2, 0, 2 * math.pi)
            cr.fill()

            # Triangle
            # cr.move_to(x-5, y-5)
            # cr.line_to(x,y+5)
            # cr.move_to(x+5, y-5)
            # cr.line_to(x,y+5)
            # cr.move_to(x-5, y-5)
            # cr.line_to(x+5,y-5)
            # cr.stroke()

    def do_render(self, gpsmap):
        pass

    def do_busy(self):
        return False

    def do_button_press(self, gpsmap, gdkeventbutton):
        return False
