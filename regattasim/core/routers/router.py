# -*- coding: utf-8 -*-
# Copyright (C) 2017 Davide Gessa
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

class Router:
    def __init__ (self):
        pass

    # Calculate the Velocity-Made-Good of a boat sailing from
    # start to end at current speed / angle
    def calculateVMG (self, speed, angle, start, end):
        return speed * math.cos (angle)


    def route (self, t, start, end, polar, grib):
        return {
            'time': 0,
            'path': [],
            'isochrones': []
        }
