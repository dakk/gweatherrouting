# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
"""

import logging
import gpxpy
import os

from . import utils
from .poimanager import POI
from .track import Track
import weatherrouting
from . import GribManager, TrackManager, POIManager, EventDispatcher

logger = logging.getLogger("gweatherrouting")


class BoatInfo:
    latitude = 0.0
    longitude = 0.0
    speed = 0.0
    heading = 0.0

    def isValid(self):
        return self.latitude != 0.0 and self.longitude != 0.0


class Core(EventDispatcher):
    def __init__(self, conn):
        self.conn = conn
        self.trackManager = TrackManager()
        self.gribManager = GribManager()
        self.poiManager = POIManager()
        self.boatInfo = BoatInfo()

        self.conn.connect("data", self.dataHandler)

        logger.info("Initialized")

    def dataHandler(self, dps):
        for x in dps:
            if x.isPosition():
                self.boatInfo.latitude = x.data.latitude
                self.boatInfo.longitude = x.data.longitude
                self.dispatch("boatPosition", self.boatInfo)

    # Simulation
    def createRouting(self, algorithm, boatModel, track, startDatetime, startPosition):
        polar = weatherrouting.Polar (os.path.abspath(os.path.dirname(__file__)) + '/../data/boats/' + boatModel + '/polar.pol')

        routing = weatherrouting.Routing(
            algorithm,
            polar,
            track,
            self.gribManager,
            startDatetime=startDatetime,
            startPosition=startPosition,
            pointValidity=utils.pointValidity
        )
        return routing

    # Import a GPX file (tracks, pois and routings)
    def importGPX(self, path):
        try:
            f = open(path, "r")
            gpx = gpxpy.parse(f)

            # Tracks
            for track in gpx.tracks:
                waypoints = []

                for segment in track.segments:
                    for point in segment.points:
                        waypoints.append([point.latitude, point.longitude])

                self.trackManager.tracks.append(
                    Track(
                        path.split("/")[-1].split(".")[0],
                        waypoints,
                        trackManager=self.trackManager,
                    )
                )

            self.trackManager.saveTracks()

            # Routes

            # POI
            for waypoint in gpx.waypoints:
                self.poiManager.pois.append(
                    POI(waypoint.name, [waypoint.latitude, waypoint.longitude])
                )

            self.poiManager.savePOI()

            return True
        except Exception as e:
            logger.error(str(e))
            return False
