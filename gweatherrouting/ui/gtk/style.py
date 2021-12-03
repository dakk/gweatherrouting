# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
'''
import math 

def drawPolar(polar, cr):
    if not polar:
        return

    cr.set_source_rgb (1, 1, 1)
    cr.paint ()

    cr.set_line_width (0.3)
    cr.set_source_rgb (0, 0, 0)
    for x in polar.tws:# [::2]:
        cr.arc (0.0, 100.0, x * 3, math.radians (-180), math.radians (180.0))
        cr.stroke ()

    for x in polar.twa:# [::8]:
        cr.move_to (0.0, 100.0)
        cr.line_to (0 + math.sin (x) * 100.0, 100 + math.cos (x) * 100.0)
        cr.stroke ()

    cr.set_line_width (0.5)
    cr.set_source_rgb (1, 0, 0)

    for i in range (0, len (polar.tws), 1):
        for j in range (0, len (polar.twa), 1):
            cr.line_to (5 * polar.speedTable [j][i] * math.sin (polar.twa[j]), 100 + 5 * polar.speedTable [j][i] * math.cos (polar.twa[j]))
            cr.stroke ()
            cr.move_to (5 * polar.speedTable [j][i] * math.sin (polar.twa[j]), 100 + 5 * polar.speedTable [j][i] * math.cos (polar.twa[j]))




class CairoStyle:
    def __init__(self, color = None, lineWidth = None, fontSize = None, dash = None):
        self.color = color
        self.lineWidth = lineWidth
        self.fontSize = fontSize
        self.dash = dash

    def apply(self, cr):
        if self.lineWidth: 
            cr.set_line_width(self.lineWidth)
        if self.fontSize:
            cr.set_font_size(self.fontSize)

        if self.dash != None and type(self.dash) == float:
            cr.set_dash([self.dash])
        elif self.dash != None and type(self.dash) != float:
            cr.set_dash(self.dash)
            
        if self.color:
            cr.set_source_rgba (self.color[0], self.color[1], self.color[2], self.color[3])


class Style:
    def resetDash(cr):
        cr.set_dash([])

    class GeoJSON:
        Sea = CairoStyle(color=(0xd3 / 255, 0xdc / 255, 0xa4 / 255, 1.0))
        LandStroke = CairoStyle(color=(0xe7 / 255., 0xdd / 255., 0x1d / 255., 1.0))
        LandFill = CairoStyle(color=(0xe7 / 255., 0xdd / 255., 0x1d / 255., 0.6))

    class Track:
        RoutingTrack = CairoStyle(color=(1,0,0,1), lineWidth=2)
        RoutingTrackFont = CairoStyle(color=(1,1,1,1), fontSize=13)
        RoutingTrackCircle = CairoStyle(color=(1,1,1,1), lineWidth=2)

        TrackActive = CairoStyle(color=(0x91/255., 0x4a/255., 0x7c/255., 1), lineWidth=2, dash=8.0)
        TrackActiveFont = CairoStyle(color=(1,1,1,1), fontSize=13)
        TrackActivePoiFont = CairoStyle(color=(1,1,1,1), fontSize=13)

        TrackInactive = CairoStyle(color=(0x91/255., 0x4a/255., 0x7c/255., 0.6), lineWidth=2, dash=8.0)
        TrackInactiveFont = CairoStyle(color=(1,1,1,0.6), fontSize=13)
        TrackInactivePoiFont = CairoStyle(color=(1,1,1,0.7), fontSize=13)

        RoutingBoat = CairoStyle(color=(0, 0.4, 0, 1.0), lineWidth=5)

    class Poi:
        Triangle = CairoStyle(color=(1, 1, 1, 1))
        Font = CairoStyle(color=(1, 1, 1, 1), fontSize=13)
        