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

import logging

from . import utils
from .. import log
from .track import Track
from .routing import Routing
from .boat import Boat
from .grib import Grib
from .gribmanager import GribManager
from .trackmanager import TrackManager

logger = logging.getLogger ('gweatherrouting')

class Core:
    def __init__ (self):
        self.trackManager = TrackManager()
        self.gribManager = GribManager()

        self.trackManager.create()

        logger.debug ('Initialized')

    # Simulation
    def createRouting (self, algorithm, boatModel, initialTime):
        boat = Boat (boatModel)
        routing = Routing (algorithm (boat.polar, self.gribManager), boat, self.track, self.gribManager, initialTime = initialTime)
        return routing

    def getGribManager (self):
        return self.gribManager

    # Track ans save/load
    def getActiveTrack (self):
        return self.trackManager.activeTrack()

    def load (self, path):
        logger.info ('Saved current state to %s' % path)
        return self.track.load (path)

    def save (self, path):
        logger.info ('Loaded state from %s' % path)
        return self.track.save (path)