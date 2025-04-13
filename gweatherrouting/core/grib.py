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

import weatherrouting

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
        self, path, name, centre, bounds, rindex, startTime, lastForecast, timeKey
    ):
        self.name = name
        self.centre = centre.upper()
        self.cache = utils.DictCache(16)
        self.rindex_data = utils.DictCache(16)
        self.rindex = rindex
        self.bounds = bounds
        self.startTime = startTime
        self.lastForecast = lastForecast
        self.path = path
        self.timeKey = timeKey

    def getRIndexData(self, t):
        import eccodes

        if t in self.rindex_data:
            return self.rindex_data[t]

        iid = eccodes.codes_index_read(self.path + ".idx")
        eccodes.codes_index_select(iid, "name", "10 metre U wind component")
        eccodes.codes_index_select(iid, self.timeKey, t)
        gid = eccodes.codes_new_from_index(iid)
        u = eccodes.codes_grib_get_data(gid)

        eccodes.codes_index_select(iid, "name", "10 metre V wind component")
        eccodes.codes_index_select(iid, self.timeKey, t)
        gid = eccodes.codes_new_from_index(iid)
        v = eccodes.codes_grib_get_data(gid)

        self.rindex_data[t] = (u, v)
        return u, v

    # Get Wind data from cache if available (speed up the entire simulation)
    def _getWindDataCached(self, t, bounds):
        h = "%f%f%f%f%f" % (t, bounds[0][0], bounds[0][1], bounds[1][0], bounds[1][1])

        if h in self.cache:
            return self.cache[h]
        else:
            try:
                u, v = self.getRIndexData(t)
            except:  # Exception as _:
                pass  # print('Get wind data cached exception: ', e)

            uu1, latuu, lonuu = [], [], []
            vv1, latvv, lonvv = [], [], []

            for x in u:
                if (
                    x["lat"] >= bounds[0][0]
                    and x["lat"] <= bounds[1][0]
                    and x["lon"] >= bounds[0][1]
                    and x["lon"] <= bounds[1][1]
                ):
                    uu1.append(x["value"])
                    latuu.append(x["lat"])
                    lonuu.append(x["lon"])

            for x in v:
                if (
                    x["lat"] >= bounds[0][0]
                    and x["lat"] <= bounds[1][0]
                    and x["lon"] >= bounds[0][1]
                    and x["lon"] <= bounds[1][1]
                ):
                    vv1.append(x["value"])
                    latvv.append(x["lat"])
                    lonvv.append(x["lon"])

            self.cache[h] = (uu1, vv1, latuu, lonuu)
            return self.cache[h]

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

        otherside = None

        # if lon1 < 0.0 and lon2 < 0.0:
        # 	lon1 = 180. + abs (lon1)
        # 	lon2 = 180. + abs (lon2)
        # elif lon1 < 0.0:
        # 	otherside = (-180.0, lon1)
        # elif lon2 < 0.0:
        # 	otherside = (-180.0, lon2)

        bounds = [(bounds[0][0], min(lon1, lon2)), (bounds[1][0], max(lon1, lon2))]
        (uu1, vv1, latuu, lonuu) = self._getWindDataCached(t1, bounds)
        (uu2, vv2, latuu2, lonuu2) = self._getWindDataCached(t2, bounds)

        if otherside:
            bounds = [
                (bounds[0][0], min(otherside[0], otherside[1])),
                (bounds[1][0], max(otherside[0], otherside[1])),
            ]
            dataotherside = self.getWind(t, bounds)
        else:
            dataotherside = []

        data = []

        for j in range(0, len(uu1)):
            lon = lonuu[j]
            lat = latuu[j]

            if lon > 180.0:
                lon = -180.0 + (lon - 180.0)

            # if utils.pointInCountry (lat, lon):
            # 	continue

            uu = uu1[j] + (uu2[j] - uu1[j]) * (t - t1) * 1.0 / (t2 - t1)
            vv = vv1[j] + (vv2[j] - vv1[j]) * (t - t1) * 1.0 / (t2 - t1)

            tws = (uu**2 + vv**2) / 2.0
            twd = math.degrees(utils.reduce360(math.atan2(uu, vv) + math.pi))

            data.append((twd, tws, (lat, lon)))

        return data + dataotherside

    def _transformTime(self, t):
        if (self.startTime + datetime.timedelta(hours=self.lastForecast)) < t:
            return None

        if t > self.startTime + datetime.timedelta(hours=self.lastForecast):
            return None

        return math.floor((t - self.startTime).total_seconds() / 60 / 60)

    # Get wind direction and speed in a point, used by simulator
    def getWindAt(self, t, lat, lon):
        bounds = [
            (math.floor(lat * 2) / 2.0, math.floor(lon * 2) / 2.0),
            (math.ceil(lat * 2) / 2.0, math.ceil(lon * 2) / 2.0),
        ]
        data = self.getWind(t, bounds)

        wind = (data[0][0], data[0][1])
        return wind

    @staticmethod
    def parseMetadata(path):
        import eccodes

        f = open(path, "rb")

        # TODO: get bounds and timeframe
        bounds = [0, 0, 0, 0]
        hoursForecasted = None
        startTime = None
        centre = ""

        while True:
            msgid = eccodes.codes_grib_new_from_file(f)

            if msgid is None:
                break

            name = eccodes.codes_get(msgid, "name")
            if (
                name != "10 metre U wind component"
                and name != "10 metre V wind component"
            ):
                continue

            vcentre = eccodes.codes_get(msgid, "centre")
            if vcentre:
                centre = vcentre

            try:
                ft = eccodes.codes_get(msgid, "forecastTime")
            except:
                ft = eccodes.codes_get(msgid, "P1")

            startTime = datetime.datetime(
                int(eccodes.codes_get(msgid, "year")),
                int(eccodes.codes_get(msgid, "month")),
                int(eccodes.codes_get(msgid, "day")),
                int(eccodes.codes_get(msgid, "hour")),
                int(eccodes.codes_get(msgid, "minute")),
            )

            if hoursForecasted is None or hoursForecasted < int(ft):
                hoursForecasted = int(ft)

            eccodes.codes_release(msgid)

        f.close()
        return MetaGrib(
            path, path.split("/")[-1], centre, bounds, startTime, hoursForecasted
        )

    @staticmethod
    def parse(path):
        import eccodes

        f = open(path, "rb")

        # TODO: get bounds and timeframe
        bounds = [0, 0, 0, 0]
        hoursForecasted = None
        startTime = None
        rindex = {}
        centre = ""
        timeKey = "P1"

        while True:
            msgid = eccodes.codes_grib_new_from_file(f)

            if msgid is None:
                break

            name = eccodes.codes_get(msgid, "name")
            if (
                name != "10 metre U wind component"
                and name != "10 metre V wind component"
            ):
                continue

            centre = eccodes.codes_get(msgid, "centre")

            try:
                ft = eccodes.codes_get(msgid, "forecastTime")
                timeKey = "forecastTime"
            except:
                ft = eccodes.codes_get(msgid, "P1")
                timeKey = "P1"

            startTime = datetime.datetime(
                int(eccodes.codes_get(msgid, "year")),
                int(eccodes.codes_get(msgid, "month")),
                int(eccodes.codes_get(msgid, "day")),
                int(eccodes.codes_get(msgid, "hour")),
                int(eccodes.codes_get(msgid, "minute")),
            )

            if hoursForecasted is None or hoursForecasted < int(ft):
                hoursForecasted = int(ft)

            # timeIndex = str(r['dataDate'])+str(r['dataTime'])
            if name == "10 metre U wind component":
                rindex[hoursForecasted] = {"u": msgid}
            elif name == "10 metre V wind component":
                rindex[hoursForecasted]["v"] = msgid

            eccodes.codes_release(msgid)

        index_keys = ["name", timeKey]
        iid = eccodes.codes_index_new_from_file(path, index_keys)
        eccodes.codes_index_write(iid, path + ".idx")
        eccodes.codes_index_release(iid)
        f.close()

        return Grib(
            path,
            path.split("/")[-1],
            centre,
            bounds,
            rindex,
            startTime,
            hoursForecasted,
            timeKey,
        )
