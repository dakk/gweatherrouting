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
    latitude: float = 0.0
    longitude: float = 0.0
    speed: float = 0.0
    heading: float = 0.0

    # Speed and course over ground (from GPS/RMC)
    sog: Optional[float] = None
    cog: Optional[float] = None

    # Heading (true)
    hdg: Optional[float] = None

    # Apparent wind
    awa: Optional[float] = None
    aws: Optional[float] = None

    # True wind
    twa: Optional[float] = None
    tws: Optional[float] = None

    # Depth below transducer (meters)
    depth: Optional[float] = None

    # Water temperature (Celsius)
    water_temp: Optional[float] = None

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

                # RMC also provides SOG and COG
                if hasattr(x.data, "spd_over_grnd") and x.data.spd_over_grnd:
                    try:
                        self.boat_info.sog = float(x.data.spd_over_grnd)
                        self.boat_info.speed = self.boat_info.sog
                    except (ValueError, TypeError):
                        pass
                if hasattr(x.data, "true_course") and x.data.true_course:
                    try:
                        self.boat_info.cog = float(x.data.true_course)
                    except (ValueError, TypeError):
                        pass

                self.dispatch("boat_position", self.boat_info)
            elif x.is_heading():
                self.boat_info.heading = x.data.heading

            # Parse additional NMEA sentence types
            self._parse_nmea_extra(x)

        self.dispatch("boat_data", self.boat_info)

    def _parse_nmea_extra(self, x: DataPacket):
        """Parse additional NMEA sentences for instrument data."""
        sentence = x.data
        sentence_type = getattr(sentence, "sentence_type", None)
        if sentence_type is None:
            return

        parsers = {
            "MWV": self._parse_mwv,
            "DBT": self._parse_dbt,
            "VHW": self._parse_vhw,
            "MTW": self._parse_mtw,
            "HDT": self._parse_hdt,
            "HDG": self._parse_hdg,
        }

        parser = parsers.get(sentence_type)
        if parser:
            try:
                parser(sentence)
            except (ValueError, TypeError, AttributeError) as e:
                logger.debug("Error parsing NMEA sentence %s: %s", sentence_type, e)

    def _parse_mwv(self, sentence):
        """Parse MWV (wind speed and angle)."""
        wind_angle = float(sentence.wind_angle) if sentence.wind_angle else None
        wind_speed = float(sentence.wind_speed) if sentence.wind_speed else None

        if wind_angle is None or wind_speed is None:
            return

        units = getattr(sentence, "wind_speed_units", "N")
        if units == "M":  # meters/sec to knots
            wind_speed = wind_speed * 1.94384
        elif units == "K":  # km/h to knots
            wind_speed = wind_speed * 0.539957

        reference = getattr(sentence, "reference", "R")
        if reference == "R":
            self.boat_info.awa = wind_angle
            self.boat_info.aws = wind_speed
        elif reference == "T":
            self.boat_info.twa = wind_angle
            self.boat_info.tws = wind_speed

    def _parse_dbt(self, sentence):
        """Parse DBT (depth below transducer)."""
        depth_meters = getattr(sentence, "depth_meters", None)
        if depth_meters:
            self.boat_info.depth = float(depth_meters)
        elif getattr(sentence, "depth_feet", None):
            self.boat_info.depth = float(sentence.depth_feet) * 0.3048

    def _parse_vhw(self, sentence):
        """Parse VHW (speed through water and heading)."""
        water_speed = getattr(sentence, "water_speed_knots", None)
        if water_speed:
            self.boat_info.speed = float(water_speed)
        heading_true = getattr(sentence, "heading_true", None)
        if heading_true:
            self.boat_info.hdg = float(heading_true)
            self.boat_info.heading = self.boat_info.hdg

    def _parse_mtw(self, sentence):
        """Parse MTW (water temperature)."""
        temperature = getattr(sentence, "temperature", None)
        if temperature:
            temp = float(temperature)
            units = getattr(sentence, "units", "C")
            if units == "F":
                temp = (temp - 32) * 5.0 / 9.0
            self.boat_info.water_temp = temp

    def _parse_hdt(self, sentence):
        """Parse HDT (true heading)."""
        heading = getattr(sentence, "heading", None)
        if heading:
            self.boat_info.hdg = float(heading)
            self.boat_info.heading = self.boat_info.hdg

    def _parse_hdg(self, sentence):
        """Parse HDG (magnetic heading with variation)."""
        heading = getattr(sentence, "heading", None)
        if not heading:
            return
        hdg = float(heading)
        variation = getattr(sentence, "variation", None)
        var_dir = getattr(sentence, "var_dir", None)
        if variation:
            var_val = float(variation)
            if var_dir == "W":
                var_val = -var_val
            hdg = (hdg + var_val) % 360
        if self.boat_info.hdg is None:
            self.boat_info.hdg = hdg
        self.boat_info.heading = hdg

    # Simulation
    def create_routing(
        self,
        algorithm,
        polar_file,
        track_or_poi,
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
            (
                track_or_poi.to_list()
                if isinstance(track_or_poi, Track)
                else [track_or_poi.position]
            ),
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
            gpx_track = track.to_gpx_object()
            gpx.tracks.append(gpx_track)

        for track in self.routingManager:
            gpx_track = track.to_gpx_object()
            gpx.tracks.append(gpx_track)

        for poi in self.poiManager:
            gpx.waypoints.append(poi.to_gpx_object())

        try:
            f = open(path, "w")
            f.write(gpx.to_xml())
        except Exception as e:
            logger.error(str(e))

        return True
