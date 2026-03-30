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

import unittest

from gweatherrouting.core.modifiedgrib import ModifiedGribManager


class MockGrib:
    """A mock grib with known return values for testing."""

    def __init__(self, wind_at_result=None, wind_result=None, has=True):
        self._wind_at_result = wind_at_result
        self._wind_result = wind_result
        self._has = has

    def get_wind_at(self, t, lat, lon):
        return self._wind_at_result

    def get_wind(self, t, bounds):
        return self._wind_result

    def has_grib(self):
        return self._has


class TestModifiedGribGetWindAt(unittest.TestCase):
    def test_speed_factor(self):
        mock = MockGrib(wind_at_result=(180.0, 10.0))
        mgm = ModifiedGribManager(mock, wind_speed_factor=1.5)
        result = mgm.get_wind_at(0, 45.0, 10.0)
        self.assertIsNotNone(result)
        twd, tws = result
        self.assertAlmostEqual(tws, 15.0)
        self.assertAlmostEqual(twd, 180.0)

    def test_direction_offset(self):
        mock = MockGrib(wind_at_result=(180.0, 10.0))
        mgm = ModifiedGribManager(mock, wind_dir_offset=45.0)
        result = mgm.get_wind_at(0, 45.0, 10.0)
        self.assertIsNotNone(result)
        twd, tws = result
        self.assertAlmostEqual(twd, 225.0)
        self.assertAlmostEqual(tws, 10.0)

    def test_direction_wraps_around_360(self):
        mock = MockGrib(wind_at_result=(350.0, 10.0))
        mgm = ModifiedGribManager(mock, wind_dir_offset=20.0)
        result = mgm.get_wind_at(0, 45.0, 10.0)
        self.assertIsNotNone(result)
        twd, tws = result
        self.assertAlmostEqual(twd, 10.0)  # (350 + 20) % 360 = 10

    def test_direction_wraps_large_offset(self):
        mock = MockGrib(wind_at_result=(300.0, 5.0))
        mgm = ModifiedGribManager(mock, wind_dir_offset=180.0)
        result = mgm.get_wind_at(0, 45.0, 10.0)
        self.assertIsNotNone(result)
        twd, tws = result
        self.assertAlmostEqual(twd, 120.0)  # (300 + 180) % 360 = 120

    def test_speed_factor_and_direction_offset_combined(self):
        mock = MockGrib(wind_at_result=(350.0, 10.0))
        mgm = ModifiedGribManager(mock, wind_speed_factor=2.0, wind_dir_offset=30.0)
        result = mgm.get_wind_at(0, 45.0, 10.0)
        self.assertIsNotNone(result)
        twd, tws = result
        self.assertAlmostEqual(tws, 20.0)
        self.assertAlmostEqual(twd, 20.0)  # (350 + 30) % 360 = 20

    def test_none_return_from_underlying(self):
        mock = MockGrib(wind_at_result=None)
        mgm = ModifiedGribManager(mock, wind_speed_factor=1.5, wind_dir_offset=45.0)
        result = mgm.get_wind_at(0, 45.0, 10.0)
        self.assertIsNone(result)

    def test_default_no_modification(self):
        mock = MockGrib(wind_at_result=(270.0, 12.0))
        mgm = ModifiedGribManager(mock)
        result = mgm.get_wind_at(0, 45.0, 10.0)
        self.assertIsNotNone(result)
        twd, tws = result
        self.assertAlmostEqual(twd, 270.0)
        self.assertAlmostEqual(tws, 12.0)


class TestModifiedGribGetWind(unittest.TestCase):
    def test_applies_modification_to_all_entries(self):
        wind_data = [
            (90.0, 10.0, (45.0, 10.0)),
            (180.0, 20.0, (46.0, 11.0)),
            (270.0, 5.0, (47.0, 12.0)),
        ]
        mock = MockGrib(wind_result=wind_data)
        mgm = ModifiedGribManager(mock, wind_speed_factor=1.5, wind_dir_offset=45.0)
        result = mgm.get_wind(0, None)

        self.assertEqual(len(result), 3)

        # Entry 0: (90+45)%360=135, 10*1.5=15
        self.assertAlmostEqual(result[0][0], 135.0)
        self.assertAlmostEqual(result[0][1], 15.0)
        self.assertEqual(result[0][2], (45.0, 10.0))

        # Entry 1: (180+45)%360=225, 20*1.5=30
        self.assertAlmostEqual(result[1][0], 225.0)
        self.assertAlmostEqual(result[1][1], 30.0)
        self.assertEqual(result[1][2], (46.0, 11.0))

        # Entry 2: (270+45)%360=315, 5*1.5=7.5
        self.assertAlmostEqual(result[2][0], 315.0)
        self.assertAlmostEqual(result[2][1], 7.5)
        self.assertEqual(result[2][2], (47.0, 12.0))

    def test_none_return_gives_empty_list(self):
        mock = MockGrib(wind_result=None)
        mgm = ModifiedGribManager(mock, wind_speed_factor=1.5)
        result = mgm.get_wind(0, None)
        self.assertEqual(result, [])

    def test_empty_list(self):
        mock = MockGrib(wind_result=[])
        mgm = ModifiedGribManager(mock, wind_speed_factor=2.0)
        result = mgm.get_wind(0, None)
        self.assertEqual(result, [])

    def test_direction_wraps_in_list(self):
        wind_data = [(350.0, 10.0, (45.0, 10.0))]
        mock = MockGrib(wind_result=wind_data)
        mgm = ModifiedGribManager(mock, wind_dir_offset=20.0)
        result = mgm.get_wind(0, None)
        self.assertAlmostEqual(result[0][0], 10.0)


class TestModifiedGribHasGrib(unittest.TestCase):
    def test_has_grib_true(self):
        mock = MockGrib(has=True)
        mgm = ModifiedGribManager(mock)
        self.assertTrue(mgm.has_grib())

    def test_has_grib_false(self):
        mock = MockGrib(has=False)
        mgm = ModifiedGribManager(mock)
        self.assertFalse(mgm.has_grib())
