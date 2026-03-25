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

from typing import List, Optional, Tuple

import weatherrouting


class ModifiedGribManager(weatherrouting.Grib):
    """A wrapper around a Grib provider that applies wind modifications.

    Allows scaling wind speed by a factor and offsetting wind direction,
    useful for scenario comparison routing.
    """

    def __init__(self, grib_manager, wind_speed_factor=1.0, wind_dir_offset=0.0):
        self._grib = grib_manager
        self._speed_factor = wind_speed_factor
        self._dir_offset = wind_dir_offset

    def get_wind_at(self, t, lat: float, lon: float) -> Optional[Tuple[float, float]]:
        result = self._grib.get_wind_at(t, lat, lon)
        if result is None:
            return None
        twd, tws = result
        tws = tws * self._speed_factor
        twd = (twd + self._dir_offset) % 360
        return (twd, tws)

    def get_wind(self, t, bounds) -> List:
        result = self._grib.get_wind(t, bounds)
        if result is None:
            return []
        modified = []
        for twd, tws, pos in result:
            tws = tws * self._speed_factor
            twd = (twd + self._dir_offset) % 360
            modified.append((twd, tws, pos))
        return modified

    def has_grib(self) -> bool:
        return self._grib.has_grib()
