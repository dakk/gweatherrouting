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

from . import utils
from .. import config
from .track import Track
from .routing import Routing
from .boat import Boat
from .grib import Grib

logger = logging.getLogger ('regattasim')

class Core:
    def __init__ (self):
        self.track = Track ()
        self.grib = Grib ()
        self.grib.parse ('/home/dakk/testgrib.grb')
        logger.debug ('Initialized')

    # Simulation
    def createRouting (self, algorithm, boatModel, initialTime):
        boat = Boat (boatModel)
        routing = Routing (algorithm (boat.polar, self.grib), boat, self.track, self.grib, initialTime = initialTime)
        return routing

    def getGrib (self):
        return self.grib

    # Track ans save/load
    def getTrack (self):
        return self.track

    def load (self, path):
        logger.info ('Saved current state to %s' % path)
        return self.track.load (path)

    def save (self, path):
        logger.info ('Loaded state from %s' % path)
        return self.track.save (path)