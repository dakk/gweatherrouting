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

import dateutil.parser
import gi

gi.require_version("Gtk", "3.0")
# try:
#     gi.require_version("OsmGpsMap", "1.2")
# except:
#     gi.require_version("OsmGpsMap", "1.0")

from gi.repository import GObject, OsmGpsMap

from gweatherrouting.core import Core, TimeControl, utils
from gweatherrouting.gtk.style import Style


class GeoMapLayer(GObject.GObject, OsmGpsMap.MapLayer):
    def __init__(self, core: Core, time_control: TimeControl):
        GObject.GObject.__init__(self)

        self.core = core
        self.time_control = time_control
        self.hl_routing = None

    def highlight_routing(self, name):
        self.hl_routing = name

    def do_draw(self, gpsmap, cr):  # noqa: C901
        prevx = None
        prevy = None
        prevp = None

        for p in self.core.logManager.log:
            x, y = gpsmap.convert_geographic_to_screen(
                OsmGpsMap.MapPoint.new_degrees(p[0], p[1])
            )

            if prevx is not None and prevy is not None:
                Style.Track.LogTrack.apply(cr)
                cr.move_to(prevx, prevy)
                cr.line_to(x, y)
                cr.stroke()

            prevx = x
            prevy = y
            prevp = p

        for tr in self.core.routingManager:
            highlight = False

            if not tr.visible:
                continue

            if tr.name == self.hl_routing:
                highlight = True

            prevx = None
            prevy = None
            prevp = None
            i = 0

            for p in tr:
                i += 1
                x, y = gpsmap.convert_geographic_to_screen(
                    OsmGpsMap.MapPoint.new_degrees(p[0], p[1])
                )

                if prevp is None:
                    if highlight:
                        Style.Track.RoutingTrackFontHL.apply(cr)
                    else:
                        Style.Track.RoutingTrackFont.apply(cr)
                    cr.move_to(x + 10, y)
                    cr.show_text(tr.name)
                    cr.stroke()

                # Draw boat
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

                        Style.Track.RoutingBoat.apply(cr)
                        xx, yy = gpsmap.convert_geographic_to_screen(
                            OsmGpsMap.MapPoint.new_degrees(rp[0], rp[1])
                        )
                        cr.arc(xx, yy, 7, 0, 2 * math.pi)
                        cr.fill()

                if prevx is not None and prevy is not None:
                    if highlight:
                        Style.Track.RoutingTrackHL.apply(cr)
                    else:
                        Style.Track.RoutingTrack.apply(cr)

                    cr.move_to(prevx, prevy)
                    cr.line_to(x, y)
                    cr.stroke()

                if highlight:
                    Style.Track.RoutingTrackCircleHL.apply(cr)
                else:
                    Style.Track.RoutingTrackCircle.apply(cr)

                cr.arc(x, y, 5, 0, 2 * math.pi)
                cr.stroke()

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
                    OsmGpsMap.MapPoint.new_degrees(p[0], p[1])
                )

                if prevx is None:
                    if active:
                        Style.Track.TrackActiveFont.apply(cr)
                    else:
                        Style.Track.TrackInactiveFont.apply(cr)

                    cr.move_to(x - 10, y - 10)
                    cr.show_text(tr.name)
                    cr.stroke()

                if active:
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

                if active:
                    Style.Track.TrackActive.apply(cr)
                else:
                    Style.Track.TrackInactive.apply(cr)

                Style.reset_dash(cr)

                cr.arc(x, y, 5, 0, 2 * math.pi)
                cr.stroke()

                prevx = x
                prevy = y

        for tr in self.core.poiManager:
            if not tr.visible:
                continue

            x, y = gpsmap.convert_geographic_to_screen(
                OsmGpsMap.MapPoint.new_degrees(tr.position[0], tr.position[1])
            )

            Style.Poi.Quad.apply(cr)
            cr.rectangle(x + 3, y - 5, len(tr.name) * 6.7, 12)
            cr.stroke_preserve()
            Style.Poi.QuadInt.apply(cr)
            cr.fill()

            Style.Poi.Font.apply(cr)
            cr.move_to(x + 5, y + 5)
            cr.show_text(tr.name)
            cr.stroke()

            Style.Poi.Dot.apply(cr)
            cr.arc(x, y, 2, 0, 2 * math.pi)
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


GObject.type_register(GeoMapLayer)
