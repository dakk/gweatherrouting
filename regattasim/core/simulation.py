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
import logging
from .boat import Boat
from .track import Track

logger = logging.getLogger ('regattasim')

class Simulation:
    def __init__ (self, boat, track, grib, initialTime = 0.0):
        self.mode = 'wind'      # 'compass' 'gps' 'vmg'
        self.boat = boat
        self.track = track
        self.steps = 0
        self.path = Track ()    # Simulated points
        self.t = initialTime
        self.grib = grib
        self.log = []           # Log of each simulation step
        self.boat.setPosition (self.track[0]['lat'], self.track[0]['lon'])
        logger.debug ('initialized (mode: %s, time: %f)' % (self.mode, self.t))


    def getTime (self):
        return self.t

    def reset (self):
        self.steps = 0
        self.path.clear ()
        self.boat.setPosition (self.track[0]['lat'], self.track[0]['lon'])
        self.log = []

    def step (self):
        self.steps += 1
        self.t += 0.1

        # Play a tick
        jib = self.boat.getJib ()
        mainsail = self.boat.getMainsail ()
        position = self.boat.getPosition ()

        wind = self.grib.getWindAt (self.t, position[0], position[1])


        logger.debug ('step (mode: %s, time: %f): %f %f' % (self.mode, self.t, position[0], position[1]))

        return {
            'position': position,
            'sails': {
                'mainsail': mainsail,
                'jib': jib
            }
        }
        