# -*- coding: utf-8 -*-
# Copyright (C) 2017-2025 Davide Gessa
# Copyright (C) 2012 Riccardo Apolloni
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
import datetime
import logging
import math
from functools import lru_cache
from typing import Optional, Tuple

import weatherrouting
from osgeo import gdal

from gweatherrouting.core import utils

logger = logging.getLogger("gweatherrouting")


class MetaGrib:
    def __init__(self, path, name, centre, bounds, startTime, lastForecast):
        self.name = name
        self.centre = centre.upper()
        self.bounds = bounds
        self.startTime = startTime
        self.lastForecast = lastForecast
        self.path = path


class Grib(weatherrouting.Grib):
    def __init__(
        self,
        path: str,
        name: str,
        centre,
        bounds,
        startTime: datetime.datetime,
        lastForecast,
    ):
        self.name = name
        self.centre = centre.upper()
        self.bounds = bounds
        self.startTime = startTime
        self.lastForecast = lastForecast
        self.endTime = self.startTime + datetime.timedelta(hours=self.lastForecast)
        self.path = path
        self.dataset = gdal.Open(path)

    def _findBandsForTime(self, t):
        """Find bands for U and V wind components at a given time."""
        u_band = None
        v_band = None

        for bidx in range(1, self.dataset.RasterCount + 1):
            band = self.dataset.GetRasterBand(bidx)
            metadata = band.GetMetadata()

            if (
                "GRIB_ELEMENT" not in metadata
                or "GRIB_FORECAST_SECONDS" not in metadata
            ):
                continue

            element = metadata["GRIB_ELEMENT"]
            forecast_seconds = int(metadata["GRIB_FORECAST_SECONDS"])
            forecast_hours = forecast_seconds // 3600

            if forecast_hours == t:
                if element == "UGRD":
                    u_band = band
                elif element == "VGRD":
                    v_band = band

        return u_band, v_band

    @lru_cache(maxsize=2048)
    def getRIndexData(self, t):
        u_band, v_band = self._findBandsForTime(t)
        if u_band is None or v_band is None:
            raise ValueError(f"Wind data not found for forecast hour {t}")

        u = u_band.ReadAsArray()
        v = v_band.ReadAsArray()

        gt = self.dataset.GetGeoTransform()
        uv_data = []

        for y in range(u.shape[0]):
            for x in range(u.shape[1]):
                lon = gt[0] + x * gt[1]
                lat = gt[3] + y * gt[5]
                uv_data.append((lat, lon, u[y, x], v[y, x]))

        return uv_data

    def _getWindData(self, t, bounds):
        try:
            uv = self.getRIndexData(t)
        except Exception as e:
            logger.debug(e)
            return None

        return list(
            filter(
                lambda x: bounds[0][0] <= x[0] <= bounds[1][0]
                and bounds[0][1] <= x[1] <= bounds[1][1],
                uv,
            )
        )

    def getWind(self, tt, bounds):
        t = self._transformTime(tt)
        if t is None:
            return

        t1 = int(int(round(t)) / 3) * 3
        t2 = int(int(round(t + 6)) / 3) * 3

        if t2 == t1:
            t1 -= 3

        lon1 = min(bounds[0][1], bounds[1][1])
        lon2 = max(bounds[0][1], bounds[1][1])

        bounds = [(bounds[0][0], lon1), (bounds[1][0], lon2)]
        uuvv1 = self._getWindData(t1, bounds)
        uuvv2 = self._getWindData(t2, bounds)

        data = []

        for j in range(0, len(uuvv1)):
            lat, lon, uu1, vv1 = uuvv1[j]
            _, _, uu2, vv2 = uuvv2[j]

            if lon > 180.0:
                lon = -180.0 + (lon - 180.0)

            uu = uu1 + (uu2 - uu1) * (t - t1) / (t2 - t1)
            vv = vv1 + (vv2 - vv1) * (t - t1) / (t2 - t1)

            tws = (uu**2 + vv**2) / 2.0
            twd = math.degrees(utils.reduce360(math.atan2(uu, vv) + math.pi))

            data.append((twd, tws, (lat, lon)))

        return data

    def _transformTime(self, t) -> Optional[float]:
        if self.endTime < t:
            return None

        return math.floor((t - self.startTime).total_seconds() / 3600)

    def getWindAt(self, t, lat: float, lon: float) -> Tuple[float, float]:
        bounds = [
            (math.floor(lat * 2) / 2.0, math.floor(lon * 2) / 2.0),
            (math.ceil(lat * 2) / 2.0, math.ceil(lon * 2) / 2.0),
        ]
        data = self.getWind(t, bounds)
        return (data[0][0], data[0][1])

    @staticmethod
    def parseMetadata(path):
        dataset = gdal.Open(path)
        centre = ""
        # TODO: get bounds and timeframe
        bounds = [0, 0, 0, 0]
        startTime = None
        hoursForecasted = None

        for bidx in range(1, dataset.RasterCount + 1):
            band = dataset.GetRasterBand(bidx)
            metadata = band.GetMetadata()

            if metadata.get("GRIB_ELEMENT") in ("UGRD", "VGRD"):
                centre = metadata.get("GRIB_CENTER", "")
                forecast_hours = int(metadata.get("GRIB_FORECAST_SECONDS", 0)) // 3600
                time = datetime.datetime.fromtimestamp(
                    int(metadata.get("GRIB_REF_TIME", 0))
                )

                if startTime is None or time < startTime:
                    startTime = time

                if hoursForecasted is None or forecast_hours > hoursForecasted:
                    hoursForecasted = forecast_hours

        return MetaGrib(
            path, path.split("/")[-1], centre, bounds, startTime, hoursForecasted
        )

    @staticmethod
    def parse(path):
        meta = Grib.parseMetadata(path)
        return Grib(
            path,
            meta.name,
            meta.centre,
            meta.bounds,
            meta.startTime,
            meta.lastForecast,
        )
