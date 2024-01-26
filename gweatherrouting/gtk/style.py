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


class CairoStyle:
    def __init__(self, color=None, lineWidth=None, fontSize=None, dash=None):
        self.color = color
        self.lineWidth = lineWidth
        self.fontSize = fontSize
        self.dash = dash

    def withLineWidth(self, lineWidth):
        self.lineWidth = lineWidth
        return self

    def apply(self, cr):
        if self.lineWidth:
            cr.set_line_width(self.lineWidth)
        if self.fontSize:
            cr.set_font_size(self.fontSize)

        if self.dash is not None and type(self.dash) is float:
            cr.set_dash([self.dash])
        elif self.dash is not None and type(self.dash) is not float:
            cr.set_dash(self.dash)

        if self.color:
            cr.set_source_rgba(
                self.color[0], self.color[1], self.color[2], self.color[3]
            )


class ChartPalette:
    def __init__(self, shallow, sea, landstroke, landfill):
        self.ShallowSea = shallow
        self.Sea = sea
        self.LandStroke = landstroke
        self.LandFill = landfill


class Style:
    @staticmethod
    def resetDash(cr):
        cr.set_dash([])

    chartPalettes = {
        "cm93": ChartPalette(
            CairoStyle(color=(0x73 / 255, 0xB6 / 255, 0xEF / 255, 1.0)),
            CairoStyle(color=(0xD4 / 255, 0xEA / 255, 0xEE / 255, 1.0)),
            CairoStyle(color=(0x52 / 255.0, 0x5A / 255.0, 0x5C / 255.0, 1.0)),
            CairoStyle(color=(0xC9 / 255.0, 0xB9 / 255.0, 0x7A / 255.0, 1.0)),
        ),
        "navionics": ChartPalette(
            CairoStyle(color=(0x20 / 255, 0xB0 / 255, 0xF8 / 255, 1.0)),
            CairoStyle(color=(0xA0 / 255, 0xD8 / 255, 0xF8 / 255, 1.0)),
            CairoStyle(color=(0x3E / 255.0, 0x3A / 255.0, 0x1C / 255.0, 1.0)),
            CairoStyle(color=(0xF8 / 255.0, 0xE8 / 255.0, 0x70 / 255.0, 1.0)),
        ),
        "dark": ChartPalette(
            CairoStyle(color=(0x16 / 255, 0x23 / 255, 0x2F / 255, 1.0)),
            CairoStyle(color=(0x07 / 255, 0x07 / 255, 0x07 / 255, 1.0)),
            CairoStyle(color=(0x36 / 255.0, 0x3C / 255.0, 0x3D / 255.0, 1.0)),
            CairoStyle(color=(0x2C / 255.0, 0x29 / 255.0, 0x1B / 255.0, 1.0)),
        ),
        "default": ChartPalette(
            CairoStyle(color=(0x6C / 255, 0x6C / 255, 0xA4 / 255, 1.0)),
            CairoStyle(color=(0x6C / 255, 0x6C / 255, 0xA4 / 255, 1.0)),
            CairoStyle(color=(0xCC / 255.0, 0x33 / 255.0, 0x33 / 255.0, 1.0)),
            CairoStyle(color=(0xE7 / 255.0, 0xDD / 255.0, 0x1D / 255.0, 1.0)),
        ),
    }

    class Measure:
        Line = CairoStyle(color=(0, 0, 0, 1), lineWidth=0.6)
        Font = CairoStyle(color=(0, 0, 0, 1), fontSize=10)

    class Compass:
        Line = CairoStyle(color=(0, 0, 0, 0.3), lineWidth=0.6)
        Font = CairoStyle(color=(0, 0, 0, 1), fontSize=10)

    class Track:
        LogTrack = CairoStyle(color=(1, 0, 0, 1), lineWidth=1)

        TrackActive = CairoStyle(
            color=(0x91 / 255.0, 0x32 / 255.0, 0x1C / 255.0, 1), lineWidth=1, dash=8.0
        )
        TrackActiveFont = CairoStyle(
            color=(0x11 / 255, 0x11 / 255, 0x11 / 255, 0.7), fontSize=10
        )
        TrackActivePoiFont = CairoStyle(
            color=(0x11 / 255, 0x11 / 255, 0x11 / 255, 0.7), fontSize=10
        )

        TrackInactive = CairoStyle(
            color=(0x91 / 255.0, 0x4A / 255.0, 0x7C / 255.0, 0.6),
            lineWidth=0.8,
            dash=8.0,
        )
        TrackInactiveFont = CairoStyle(
            color=(0x11 / 255, 0x11 / 255, 0x11 / 255, 0.7), fontSize=10
        )
        TrackInactivePoiFont = CairoStyle(
            color=(0x11 / 255, 0x11 / 255, 0x11 / 255, 0.3), fontSize=10
        )

        RoutingTrack = CairoStyle(color=(1, 0, 0, 0.8), lineWidth=1)
        RoutingTrackFont = CairoStyle(
            color=(0x11 / 255, 0x11 / 255, 0x11 / 255, 0.7), fontSize=10
        )
        RoutingTrackCircle = CairoStyle(color=(1, 1, 1, 1), lineWidth=1)

        RoutingTrackHL = CairoStyle(color=(1, 0, 0, 1), lineWidth=2)
        RoutingTrackFontHL = CairoStyle(
            color=(0x11 / 255, 0x11 / 255, 0x11 / 255, 0.7), fontSize=10
        )
        RoutingTrackCircleHL = CairoStyle(color=(1, 1, 1, 1), lineWidth=2)

        RoutingBoat = CairoStyle(color=(0, 0.4, 0, 1.0), lineWidth=5)

    class Poi:
        Dot = CairoStyle(color=(0x11 / 255, 0x11 / 255, 0x11 / 255, 1))
        Quad = CairoStyle(color=(0x11 / 255, 0x11 / 255, 0x11 / 255, 1), lineWidth=0.3)
        QuadInt = CairoStyle(color=(0xFF / 255, 0xFF / 255, 0xFF / 255, 0.5))
        Font = CairoStyle(color=(0x11 / 255, 0x11 / 255, 0x11 / 255, 0.7), fontSize=10)
