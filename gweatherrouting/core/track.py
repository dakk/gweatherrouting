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

from xml.etree import ElementTree
from . import utils

class Track:
    def __init__ (self, name = 'noname', waypoints = [], visible=True, trackManager=None):
        self.name = name
        self.waypoints = waypoints
        self.visible = visible
        self.trackManager = trackManager

    def __len__ (self):
        return len (self.waypoints)

    def __getitem__ (self, key):
        return self.waypoints [key]

    def length(self):
        if len(self.waypoints) <= 1:
            return 0.0

        d = 0.0
        prev = self.waypoints[0]
        for x in self.waypoints[1::]:
            d += utils.pointDistance (prev[0],prev[1], x[0], x[1])
            prev = x
    
        return d

    def size(self):
        return len(self)

    def clear (self):
        self.waypoints = []
        self.trackManager.saveTracks()


    def export (self, path):
        try:
            f = open (path, 'w')
        except:
            return False

        # TODO
        
        return True

    def moveUp (self, i):
        if i > 0 and i < len (self):
            sw = self.waypoints [i-1]
            self.waypoints [i-1] = self.waypoints [i]
            self.waypoints [i] = sw
            self.trackManager.saveTracks()

    def moveDown (self, i):
        if i < len (self) - 1 and i >= 0:
            sw = self.waypoints [i+1]
            self.waypoints [i+1] = self.waypoints [i]
            self.waypoints [i] = sw
            self.trackManager.saveTracks()

    def remove (self, i):
        if i >= 0 and i < len (self):
            del self.waypoints [i]
            self.trackManager.saveTracks()

    def duplicate (self, i):
        self.waypoints.append(self.waypoints[i])
        self.trackManager.saveTracks()

    def add (self, lat, lon):
        self.waypoints.append ((lat, lon))
        self.trackManager.saveTracks()