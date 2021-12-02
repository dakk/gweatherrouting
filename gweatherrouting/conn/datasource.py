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

from pynmea2.nmea_utils import LatLonFix


class DataPacket:
    def __init__(self, t, sentence):
        self.t = t
        self.data = sentence
        
    def isPosition(self):
        return False

class NMEADataPacket(DataPacket):
    def __init__(self, sentence):
        DataPacket.__init__(self, 'nmea', sentence)

    def isPosition(self):
        return isinstance(self.data, LatLonFix)

class DataSource:
    pass