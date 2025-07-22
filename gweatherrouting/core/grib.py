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

logger = logging.getLogger("gweatherrouting")


class MetaGrib:
    def __init__(self, path, name, centre, bounds, start_time, last_forecast):
        self.name = name
        self.centre = centre.upper()
        self.bounds = bounds
        self.start_time = start_time
        self.last_forecast = last_forecast
        self.path = path


class Grib(weatherrouting.Grib):
    def __init__(
        self,
        path: str,
        name: str,
        centre,
        bounds,
        start_time: datetime.datetime,
        last_forecast,
    ):
        self.name = name
        self.centre = centre.upper()
        self.bounds = bounds
        self.start_time = start_time
        self.last_forecast = last_forecast
        self.end_time = self.start_time + datetime.timedelta(hours=self.last_forecast)
        self.path = path
        self.dataset = gdal.Open(path)

    def _find_bands_for_time(self, t):
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
    def get_rindex_data(self, t):
        u_band, v_band = self._find_bands_for_time(t)
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

    def _get_wind_data(self, t, bounds):
        try:
            uv = self.get_rindex_data(t)
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

    def get_wind(self, tt, bounds):
        t = self._transform_time(tt)
        if t is None:
            return

        t1 = int(round(t / 3.0)) * 3
        t2 = t1 + 6

        if t2 == t1:
            t1 -= 3

        lon1 = min(bounds[0][1], bounds[1][1])
        lon2 = max(bounds[0][1], bounds[1][1])

        bounds = [(bounds[0][0], lon1), (bounds[1][0], lon2)]
        uuvv1 = self._get_wind_data(t1, bounds)
        uuvv2 = self._get_wind_data(t2, bounds)

        data = []

        for j in range(0, len(uuvv1)):
            lat, lon, uu1, vv1 = uuvv1[j]
            _, _, uu2, vv2 = uuvv2[j]

            if lon > 180.0:
                lon -= 360.0

            uu = uu1 + (uu2 - uu1) * (t - t1) / (t2 - t1)
            vv = vv1 + (vv2 - vv1) * (t - t1) / (t2 - t1)

            tws = math.sqrt(uu**2 + vv**2)
            twd = (math.degrees(math.atan2(-uu, -vv)) + 360) % 360

            data.append((twd, tws, (lat, lon)))

        return data

    def _transform_time(self, t) -> Optional[float]:
        if self.end_time < t:
            return None

        return math.floor((t - self.start_time).total_seconds() / 3600)

    def get_wind_at(self, t, lat: float, lon: float) -> Tuple[float, float]:
        bounds = [
            (math.floor(lat * 2) / 2.0, math.floor(lon * 2) / 2.0),
            (math.ceil(lat * 2) / 2.0, math.ceil(lon * 2) / 2.0),
        ]
        data = self.get_wind(t, bounds)
        return (data[0][0], data[0][1])

    @staticmethod
    def parse_metadata(path):
        dataset = gdal.Open(path)
        centre = ""
        # TODO: get bounds and timeframe
        bounds = [0, 0, 0, 0]
        start_time = None
        hours_forecasted = None

        for bidx in range(1, dataset.RasterCount + 1):
            band = dataset.GetRasterBand(bidx)
            metadata = band.GetMetadata()

            if metadata.get("GRIB_ELEMENT") in ("UGRD", "VGRD"):
                centre = metadata.get("GRIB_CENTER", "")
                forecast_hours = int(metadata.get("GRIB_FORECAST_SECONDS", 0)) // 3600
                time = datetime.datetime.fromtimestamp(
                    int(metadata.get("GRIB_REF_TIME", 0))
                )

                if start_time is None or time < start_time:
                    start_time = time

                if hours_forecasted is None or forecast_hours > hours_forecasted:
                    hours_forecasted = forecast_hours

        return MetaGrib(
            path, path.split("/")[-1], centre, bounds, start_time, hours_forecasted
        )

    @staticmethod
    def parse(path):
        meta = Grib.parse_metadata(path)
        return Grib(
            path,
            meta.name,
            meta.centre,
            meta.bounds,
            meta.start_time,
            meta.last_forecast,
        )
