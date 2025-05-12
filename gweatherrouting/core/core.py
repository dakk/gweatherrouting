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
from typing import Callable, List, Optional

import gpxpy
import weatherrouting

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
    def points_validity(self, latlons):
        raise Exception("Not implemented")

    def lines_validity(self, latlons):
        raise Exception("Not implemented")


class BoatInfo:
    latitude = 0.0
    longitude = 0.0
    speed = 0.0
    heading = 0.0

    def is_valid(self):
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
            e = self.new_element()
            e.name = "log-history"
            return e

        return self.get_by_name("log-history")  # type: ignore

    @property
    def log(self) -> Track:
        "log is the boat track"
        if not self.exists("log"):
            e = self.new_element()
            e.name = "log"
            return e

        return self.get_by_name("log")  # type: ignore


class Core(EventDispatcher):
    def __init__(self):
        self.connectionManager = ConnectionManager()
        self.trackManager = TrackCollection()
        self.routingManager = RoutingCollection()
        self.poiManager = POICollection()
        self.grib_manager = GribManager()
        self.boat_info = BoatInfo()
        self.logManager = LogTrackCollection()

        self.connectionManager.connect("data", self.data_handler)
        logger.info("Initialized")

        self.connectionManager.plug_all()
        self.connectionManager.start_polling()

    def set_boat_position(self, lat, lon):
        self.connectionManager.dispatch(
            "data",
            [
                DataPacket(
                    "position",
                    utils.DotDict(
                        {
                            "latitude": lat,
                            "longitude": lon,
                        }
                    ),
                )
            ],
        )

    def data_handler(self, dps: List[DataPacket]):
        for x in dps:
            if x.is_position():
                self.boat_info.latitude = x.data.latitude
                self.boat_info.longitude = x.data.longitude
                self.dispatch("boat_position", self.boat_info)
            elif x.is_heading():
                self.boat_info.heading = x.data.heading

    # Simulation
    def create_routing(
        self,
        algorithm,
        polar_file,
        track,
        start_datetime,
        start_position,
        validity_providers,
        disable_coastline_checks=False,
    ):
        polar = weatherrouting.Polar(polar_file)

        pval: Optional[Callable] = utils.points_validity
        lval: Optional[Callable] = None

        if len(validity_providers) > 0:
            # pval is a function that checks all points_validity of validity_providers
            pval = validity_providers[0].points_validity
            # lval is a function that checks all lines_validity of validity_providers
            lval = validity_providers[0].lines_validity

        if disable_coastline_checks:
            lval = None
            pval = None

        routing = weatherrouting.Routing(
            algorithm,
            polar,
            track.to_list(),
            self.grib_manager,
            start_datetime=start_datetime,
            start_position=start_position,
            points_validity=pval,
            lines_validity=lval,
        )
        return routing

    # Import a GPX file (tracks, pois and routings)
    def import_gpx(self, path):
        try:
            f = open(path, "r")
            gpx = gpxpy.parse(f)

            # Tracks
            self.trackManager.import_from_gpx(gpx)

            # Routes

            # POI
            self.poiManager.import_from_gpx(gpx)

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
