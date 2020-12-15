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
from . import GribManager, TrackManager, POIManager

logger = logging.getLogger ('gweatherrouting')

class Core:
    def __init__ (self):
        self.trackManager = TrackManager()
        self.gribManager = GribManager()
        self.poiManager = POIManager()
        self.trackManager.create()

        logger.debug ('Initialized')


    # Simulation
    def createRouting (self, algorithm, boatModel, initialTime, track):
        boat = Boat (boatModel)
        routing = Routing (algorithm (boat.polar, self.gribManager), boat, track, self.gribManager, initialTime = initialTime)
        return routing

