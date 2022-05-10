# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
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

from gweatherrouting.core.connectionmanager import ConnectionManager

from . import utils
from .poimanager import POI
from .track import Track
import weatherrouting
from . import GribManager, TrackManager, POIManager, EventDispatcher

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


class Core(EventDispatcher):
    def __init__(self):
        self.connectionManager = ConnectionManager()
        self.trackManager = TrackManager()
        self.gribManager = GribManager()
        self.poiManager = POIManager()
        self.boatInfo = BoatInfo()

        self.connectionManager.connect("data", self.dataHandler)
        logger.info("Initialized")

        self.connectionManager.plugAll()
        self.connectionManager.startPolling()

    def dataHandler(self, dps):
        for x in dps:
            if x.isPosition():
                self.boatInfo.latitude = x.data.latitude
                self.boatInfo.longitude = x.data.longitude
                self.dispatch("boatPosition", self.boatInfo)

    # Simulation
    def createRouting(self, algorithm, polarFile, track, startDatetime, startPosition, validityProviders, disableCoastlineChecks=False):
        polar = weatherrouting.Polar (os.path.abspath(os.path.dirname(__file__)) + '/../data/polars/' + polarFile)

        pval = utils.pointsValidity
        lval = None 
        
        if len(validityProviders) > 0:
            # pval is a function that checks all pointsValidity of validityProviders
            pval = lambda latlons: validityProviders[0].pointsValidity(latlons)
            # lval is a function that checks all linesValidity of validityProviders
            lval = lambda latlons: validityProviders[0].linesValidity(latlons)

        if disableCoastlineChecks:
            lval = None
            pval = None

        routing = weatherrouting.Routing(
            algorithm,
            polar,
            track,
            self.gribManager,
            startDatetime=startDatetime,
            startPosition=startPosition,
            pointsValidity=pval,
            linesValidity=lval
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

    def exportGPX(self, path):
        gpx = gpxpy.gpx.GPX()

        for track in self.trackManager.tracks:
            gpx_track = track.toGPXTrack()
            gpx.tracks.append(gpx_track)

        for track in self.trackManager.routings:
            gpx_track = track.toGPXTrack()
            gpx.tracks.append(gpx_track)

        for poi in self.poiManager.pois:
            gpx.waypoints.append(poi.toGPXWaypoint())

        try:
            f = open(path, "w")
            f.write(gpx.to_xml())
        except Exception as e:
            logger.error(str(e))

        return True