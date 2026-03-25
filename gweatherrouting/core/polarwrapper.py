# -*- coding: utf-8 -*-
# Copyright (C) 2017-2026 Davide Gessa
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

from typing import Tuple


class PolarWrapper:
    """A wrapper around a Polar that scales speed by an efficiency factor.

    The efficiency is a float between 0.0 and 1.0 (e.g. 0.85 = 85% efficiency).
    All speed-related methods return the original speed multiplied by efficiency.
    """

    def __init__(self, polar, efficiency=1.0):
        self._polar = polar
        self._efficiency = efficiency

    @property
    def tws(self):
        return self._polar.tws

    @property
    def twa(self):
        return self._polar.twa

    @property
    def speed_table(self):
        return self._polar.speed_table

    def get_speed(self, tws: float, twa: float) -> float:
        return self._polar.get_speed(tws, twa) * self._efficiency

    def get_reaching(self, tws: float) -> Tuple[float, float]:
        speed, twa = self._polar.get_reaching(tws)
        return (speed * self._efficiency, twa)

    def get_max_vmgtwa(self, tws: float, twa: float) -> Tuple[float, float]:
        vmg, twa_result = self._polar.get_max_vmgtwa(tws, twa)
        return (vmg * self._efficiency, twa_result)

    def get_max_vmg_up(self, tws: float) -> Tuple[float, float]:
        vmg, twa = self._polar.get_max_vmg_up(tws)
        return (vmg * self._efficiency, twa)

    def get_max_vmg_down(self, tws: float) -> Tuple[float, float]:
        vmg, twa = self._polar.get_max_vmg_down(tws)
        return (vmg * self._efficiency, twa)

    def get_routage_speed(self, tws, twa) -> float:
        return self._polar.get_routage_speed(tws, twa) * self._efficiency

    def get_twa_routage(self, tws: float, twa: float) -> float:
        return self._polar.get_twa_routage(tws, twa)
