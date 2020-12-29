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
from . import GribManager, TrackManager, POIManager, EventDispatcher

logger = logging.getLogger ('gweatherrouting')

class BoatInfo:
    latitude = 0.0
    longitude = 0.0
    speed = 0.0
    heading = 0.0

class Core(EventDispatcher):
    def __init__ (self, conn):
        self.conn = conn
        self.trackManager = TrackManager()
        self.gribManager = GribManager()
        self.poiManager = POIManager()
        self.boatInfo = BoatInfo()

        self.conn.connect('data', self.dataHandler)

        logger.info ('Initialized')

    def dataHandler(self, dps):
        for x in dps:
            try:
                self.boatInfo.latitude = x.latitude
                self.boatInfo.longitude = x.longitude

                self.dispatch('boatPosition', self.boatInfo)
            except:
                pass

    # Simulation
    def createRouting (self, algorithm, boatModel, initialTime, track):
        boat = Boat (boatModel)
        routing = Routing (algorithm (boat.polar, self.gribManager), boat, track, self.gribManager, initialTime = initialTime)
        return routing

