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
    def __init__ (self):
        self.waypoints = []

    def __len__ (self):
        return len (self.waypoints)

    def __getitem__ (self, key):
        return self.waypoints [key]

    def clear (self):
        self.waypoints = []

    def load (self, path):
        try:
            tree = ElementTree.parse (path)
        except:
            return False

        self.waypoints = []
        root = tree.getroot ()
        for child in root:
            wp = (float (child.attrib['lat']), float (child.attrib['lon']))
            self.waypoints.append (wp)

        return True

    def save (self, path):
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

    def add (self, lat, lon):
        self.waypoints.append ((lat, lon))