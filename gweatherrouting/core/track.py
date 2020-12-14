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

class Track:
    def __init__ (self, name = 'noname', waypoints = []):
        self.name = name
        self.waypoints = waypoints
        self.distance = 0.0
        self.visible = True

    def __len__ (self):
        return len (self.waypoints)

    def __getitem__ (self, key):
        return self.waypoints [key]

    def size(self):
        return len(self)

    def clear (self):
        self.waypoints = []


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

    def moveDown (self, i):
        if i < len (self) - 1 and i >= 0:
            sw = self.waypoints [i+1]
            self.waypoints [i+1] = self.waypoints [i]
            self.waypoints [i] = sw

    def remove (self, i):
        if i >= 0 and i < len (self):
            del self.waypoints [i]

    def duplicate (self, i):
        self.waypoints.append(self.waypoints[i])

    def add (self, lat, lon):
        self.waypoints.append ((lat, lon))