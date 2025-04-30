# -*- coding: utf-8 -*-
# Copyright (C) 2017-2025 Davide Gessa
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
from typing import Callable, Optional

import gpxpy
import weatherrouting

from gweatherrouting.common import resource_path
from gweatherrouting.core import GribManager, utils
from gweatherrouting.core.connectionmanager import ConnectionManager
from gweatherrouting.core.datasource import DataPacket
from gweatherrouting.core.geo import (
    POICollection,
    RoutingCollection,
    Track,
    TrackCollection,
)
from gweatherrouting.core.utils import EventDispatcher

logger = logging.getLogger("gweatherrouting")


class LinePointValidityProvider:
    def pointsValidity(self, latlons):
        raise Exception("Not implemented")

    def linesValidity(self, latlons):
        raise Exception("Not implemented")


class BoatInfo:
    latitude = 0.0
    longitude = 0.0
    speed = 0.0
    heading = 0.0

    def isValid(self):
        return self.latitude != 0.0 and self.longitude != 0.0


class LogTrackCollection(TrackCollection):
    def __init__(self):
        super().__init__("log")
        self.log_history
        self.log

    @property
    def log_history(self) -> Track:
        "log-history is the loaded from log tab"
        if not self.exists("log-history"):
            e = self.newElement()
            e.name = "log-history"
            return e

        return self.getByName("log-history")  # type: ignore

    @property
    def log(self) -> Track:
        "log is the boat track"
        if not self.exists("log"):
            e = self.newElement()
            e.name = "log"
            return e

        return self.getByName("log")  # type: ignore


class Core(EventDispatcher):
    def __init__(self):
        self.connectionManager = ConnectionManager()
        self.trackManager = TrackCollection()
        self.routingManager = RoutingCollection()
        self.poiManager = POICollection()
        self.gribManager = GribManager()
        self.boatInfo = BoatInfo()
        self.logManager = LogTrackCollection()

        self.connectionManager.connect("data", self.dataHandler)
        logger.info("Initialized")

        self.connectionManager.plug_all()
        self.connectionManager.start_polling()

    def setBoatPosition(self, lat, lon):
        self.connectionManager.dispatch(
            "data",
            [
                DataPacket(
                    "position",
                    utils.dotdict(
                        {
                            "latitude": lat,
                            "longitude": lon,
                        }
                    ),
                )
            ],
        )

    def dataHandler(self, dps):
        for x in dps:
            if x.is_position():
                self.boatInfo.latitude = x.data.latitude
                self.boatInfo.longitude = x.data.longitude
                self.dispatch("boatPosition", self.boatInfo)

    # Simulation
    def createRouting(
        self,
        algorithm,
        polar_file,
        track,
        startDatetime,
        startPosition,
        validityProviders,
        disableCoastlineChecks=False,
    ):
        polar = weatherrouting.Polar(
            resource_path("gweatherrouting", f"data/polars/{polar_file}")
        )

        pval: Optional[Callable] = utils.pointsValidity
        lval: Optional[Callable] = None

        if len(validityProviders) > 0:
            # pval is a function that checks all pointsValidity of validityProviders
            pval = validityProviders[0].pointsValidity
            # lval is a function that checks all linesValidity of validityProviders
            lval = validityProviders[0].linesValidity

        if disableCoastlineChecks:
            lval = None
            pval = None

        routing = weatherrouting.Routing(
            algorithm,
            polar,
            track.toList(),
            self.gribManager,
            startDatetime=startDatetime,
            startPosition=startPosition,
            pointsValidity=pval,
            linesValidity=lval,
        )
        return routing

    # Import a GPX file (tracks, pois and routings)
    def import_gpx(self, path):
        try:
            f = open(path, "r")
            gpx = gpxpy.parse(f)

            # Tracks
            self.trackManager.importFromGPX(gpx)

            # Routes

            # POI
            self.poiManager.importFromGPX(gpx)

            return True
        except Exception as e:
            logger.error(str(e))
            return False

    def export_gpx(self, path):
        gpx = gpxpy.gpx.GPX()

        for track in self.trackManager:
            gpx_track = track.toGPXTrack()
            gpx.tracks.append(gpx_track)

        for track in self.routingManager:
            gpx_track = track.toGPXTrack()
            gpx.tracks.append(gpx_track)

        for poi in self.poiManager:
            gpx.waypoints.append(poi.toGPXWaypoint())

        try:
            f = open(path, "w")
            f.write(gpx.to_xml())
        except Exception as e:
            logger.error(str(e))

        return True
