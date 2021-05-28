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

import gi
import math
import dateutil.parser
import datetime
from ....core import utils
from ..constants import *

gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap

class TrackMapLayer (GObject.GObject, OsmGpsMap.MapLayer):
    def __init__ (self, trackManager, timeControl):
        GObject.GObject.__init__ (self)
        self.trackManager = trackManager
        self.timeControl = timeControl

     

    def do_draw (self, gpsmap, cr):
        for tr in self.trackManager.routings:
            if not tr.visible:
                continue 

            prevx = None
            prevy = None 
            prevp = None 
            i = 0

            for p in tr.waypoints:
                i += 1
                x, y = gpsmap.convert_geographic_to_screen (OsmGpsMap.MapPoint.new_degrees (p[0], p[1]))

                if prevp == None:
                    setStyle(cr, ROUTING_TRACK_FONT_COLOR, fontSize=ROUTING_TRACK_FONT_SIZE)
                    cr.move_to(x+10, y)
                    cr.show_text(tr.name)
                    cr.stroke()

                # Draw boat
                if prevp != None:    
                    tprev = dateutil.parser.parse(prevp[2])
                    tcurr = dateutil.parser.parse(p[2])

                    if tcurr >= self.timeControl.time and tprev < self.timeControl.time:
                        dt = (tcurr-tprev).total_seconds()
                        dl = utils.pointDistance(prevp[0], prevp[1], p[0], p[1]) / dt * (self.timeControl.time - tprev).total_seconds()
                        
                        rp = utils.routagePointDistance (prevp[0], prevp[1], dl, math.radians(p[6]))

                        setStyle(cr, ROUTING_BOAT_COLOR, ROUTING_BOAT_WIDTH)
                        xx, yy = gpsmap.convert_geographic_to_screen (OsmGpsMap.MapPoint.new_degrees (rp[0], rp[1]))
                        cr.arc(xx, yy, 7, 0, 2 * math.pi)
                        cr.fill()  

                
                # cr.set_source_rgba (1, 1, 1, 1.0)
                # cr.set_font_size(13)
                # cr.move_to(x-4, y+18)
                # cr.show_text(str(p[2]))
                # cr.stroke()


                if prevx != None and prevy != None:
                    setStyle(cr, ROUTING_TRACK_COLOR, ROUTING_TRACK_WIDTH)
                    cr.move_to (prevx, prevy)
                    cr.line_to (x, y)
                    cr.stroke()

                setStyle(cr, ROUTING_TRACK_COLOR, ROUTING_TRACK_WIDTH)
                cr.arc(x, y, 5, 0, 2 * math.pi)
                cr.stroke()

                prevx = x
                prevy = y
                prevp = p

        for tr in self.trackManager.tracks:
            if not tr.visible:
                continue 

            active = False
            if self.trackManager.activeTrack and self.trackManager.activeTrack.name == tr.name:
                active = True

            prevx = None
            prevy = None 
            i = 0

            for p in tr.waypoints:
                i += 1
                x, y = gpsmap.convert_geographic_to_screen (OsmGpsMap.MapPoint.new_degrees (p[0], p[1]))

                if prevx == None:
                    if active:
                        setStyle(cr, ACTIVE_TRACK_FONT_COLOR, fontSize=ACTIVE_TRACK_FONT_SIZE)
                    else:
                        setStyle(cr, INACTIVE_TRACK_FONT_COLOR, fontSize=INACTIVE_TRACK_FONT_SIZE)

                    cr.move_to(x-10, y-10)
                    cr.show_text(tr.name)
                    cr.stroke()

                
                if active:
                    setStyle(cr, TRACK_POI_FONT_COLOR, fontSize=TRACK_POI_FONT_SIZE)
                else:
                    setStyle(cr, INACTIVE_TRACK_POI_FONT_COLOR, fontSize=TRACK_POI_FONT_SIZE)
                    
                cr.move_to(x-4, y+18)
                cr.show_text(str(i))
                cr.stroke()



                if prevx != None and prevy != None:
                    if active:
                        setStyle(cr, ACTIVE_TRACK_COLOR, ACTIVE_TRACK_WIDTH)
                    else:
                        setStyle(cr, INACTIVE_TRACK_COLOR, INACTIVE_TRACK_WIDTH)

                    cr.move_to (prevx, prevy)
                    cr.line_to (x, y)
                    cr.stroke()

                if active:
                    setStyle(cr, ACTIVE_TRACK_COLOR, ACTIVE_TRACK_WIDTH)
                else:
                    setStyle(cr, INACTIVE_TRACK_COLOR, INACTIVE_TRACK_WIDTH)
                cr.arc(x, y, 5, 0, 2 * math.pi)
                cr.stroke()

                prevx = x
                prevy = y

    def do_render (self, gpsmap):
        pass

    def do_busy (self):
        return False

    def do_button_press (self, gpsmap, gdkeventbutton):
        return False

GObject.type_register (TrackMapLayer)