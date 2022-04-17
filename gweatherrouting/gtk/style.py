# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
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

class ChartPalette:
    def __init__(self, shallow, sea, landstroke, landfill):
        self.ShallowSea = shallow
        self.Sea = sea
        self.LandStroke = landstroke
        self.LandFill = landfill


class Style:
    def resetDash(cr):
        cr.set_dash([])

    chartPalettes = {
        'cm93': 
            ChartPalette(
                CairoStyle(color=(0x73 / 255, 0xb6 / 255, 0xef / 255, 1.0)),
                CairoStyle(color=(0xd4 / 255, 0xea / 255, 0xee / 255, 1.0)),
                CairoStyle(color=(0x52 / 255., 0x5a / 255., 0x5c / 255., 1.0)),
                CairoStyle(color=(0xc9 / 255., 0xb9 / 255., 0x7a / 255., 1.0))
            ),
        'navionics': 
            ChartPalette(
                CairoStyle(color=(0x20 / 255, 0xb0 / 255, 0xf8 / 255, 1.0)),
                CairoStyle(color=(0xa0 / 255, 0xd8 / 255, 0xf8 / 255, 1.0)),
                CairoStyle(color=(0x3e / 255., 0x3a / 255., 0x1c / 255., 1.0)),
                CairoStyle(color=(0xf8 / 255., 0xe8 / 255., 0x70 / 255., 1.0))
            ),
        'dark': 
            ChartPalette(
                CairoStyle(color=(0x16 / 255, 0x23 / 255, 0x2f / 255, 1.0)),
                CairoStyle(color=(0x07 / 255, 0x07 / 255, 0x07 / 255, 1.0)),
                CairoStyle(color=(0x36 / 255., 0x3c / 255., 0x3d / 255., 1.0)),
                CairoStyle(color=(0x2c / 255., 0x29 / 255., 0x1b / 255., 1.0))
            ),
        'default': 
            ChartPalette(
                CairoStyle(color=(0x6c / 255, 0x6c / 255, 0xa4 / 255, 1.0)),
                CairoStyle(color=(0x6c / 255, 0x6c / 255, 0xa4 / 255, 1.0)),
                CairoStyle(color=(0xcc / 255., 0x33 / 255., 0x33 / 255., 1.0)),
                CairoStyle(color=(0xe7 / 255., 0xdd / 255., 0x1d / 255., 1.0))
            )
    }

    class Measure:
        Line = CairoStyle(color=(0,0,0,1), lineWidth=0.6)
        InfoFont = CairoStyle(color=(0,0,0,0), fontSize=10)

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
        Triangle = CairoStyle(color=(0x88/255, 0x11/255, 0x8c/255, 1))
        Font = CairoStyle(color=(0x88/255, 0x11/255, 0x8c/255, 1), fontSize=13)
        