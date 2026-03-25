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

import json
import unittest

from gweatherrouting.core.gribsources.noaagfs import (
    GFS_FORECAST_HOURS,
    NOAAGFSSource,
)


class TestNOAAGFSSource(unittest.TestCase):
    def test_name(self):
        source = NOAAGFSSource()
        self.assertEqual(source.name, "NOAA GFS")

    def test_bounds_default_none(self):
        source = NOAAGFSSource()
        self.assertIsNone(source.bounds)

    def test_bounds_setter(self):
        source = NOAAGFSSource()
        source.bounds = (30.0, -10.0, 50.0, 40.0)
        self.assertEqual(source.bounds, (30.0, -10.0, 50.0, 40.0))

    def test_forecast_hours_default(self):
        source = NOAAGFSSource()
        self.assertEqual(source.forecast_hours, 120)

    def test_get_available_cycles(self):
        source = NOAAGFSSource()
        cycles = source._get_available_cycles(4)
        self.assertEqual(len(cycles), 4)
        # Each cycle should be 6h apart
        for i in range(1, len(cycles)):
            diff = (cycles[i - 1] - cycles[i]).total_seconds()
            self.assertEqual(diff, 6 * 3600)

    def test_get_download_list(self):
        source = NOAAGFSSource()
        dl = source.get_download_list()
        self.assertGreater(len(dl), 0)
        # Each entry: [name, source, size, date, identifier]
        for entry in dl:
            self.assertEqual(len(entry), 5)
            self.assertIn("NOAA GFS", entry[1])

    def test_download_list_identifiers_are_valid_json(self):
        source = NOAAGFSSource()
        dl = source.get_download_list()
        for entry in dl:
            config = json.loads(entry[4])
            self.assertIn("date", config)
            self.assertIn("cycle", config)
            self.assertIn("hours", config)

    def test_build_filter_url_no_bounds(self):
        source = NOAAGFSSource()
        params = source._build_filter_url("20260324", "00", 0)
        self.assertEqual(params["file"], "gfs.t00z.pgrb2.0p25.f000")
        self.assertEqual(params["var_UGRD"], "on")
        self.assertEqual(params["var_VGRD"], "on")
        self.assertNotIn("subregion", params)

    def test_build_filter_url_with_bounds(self):
        source = NOAAGFSSource()
        source.bounds = (30.0, -10.0, 50.0, 40.0)
        params = source._build_filter_url("20260324", "00", 6)
        self.assertEqual(params["file"], "gfs.t00z.pgrb2.0p25.f006")
        self.assertEqual(params["bottomlat"], "30.0")
        self.assertEqual(params["toplat"], "50.0")
        self.assertEqual(params["leftlon"], "-10.0")
        self.assertEqual(params["rightlon"], "40.0")

    def test_build_filter_url_negative_lon_preserved(self):
        """Negative longitudes should NOT be converted to 0-360 range."""
        source = NOAAGFSSource()
        source.bounds = (10.0, -80.0, 60.0, -10.0)
        params = source._build_filter_url("20260324", "00", 0)
        self.assertEqual(params["leftlon"], "-80.0")
        self.assertEqual(params["rightlon"], "-10.0")

    def test_estimate_size_with_bounds(self):
        source = NOAAGFSSource()
        source.bounds = (30.0, -10.0, 50.0, 40.0)
        size = source._estimate_size(72)
        self.assertIn("KB", size)  # Small area = KB range

    def test_estimate_size_global(self):
        source = NOAAGFSSource()
        size = source._estimate_size(72)
        self.assertIn("MB", size)  # Global = MB range

    def test_forecast_hours_list(self):
        # 3h steps from 0-240, then 12h steps from 252-384
        self.assertEqual(GFS_FORECAST_HOURS[0], 0)
        self.assertEqual(GFS_FORECAST_HOURS[1], 3)
        self.assertIn(240, GFS_FORECAST_HOURS)
        self.assertIn(252, GFS_FORECAST_HOURS)
        self.assertIn(384, GFS_FORECAST_HOURS)


class TestOpenSkironSource(unittest.TestCase):
    def test_name(self):
        from gweatherrouting.core.gribsources.openskiron import OpenSkironSource

        source = OpenSkironSource()
        self.assertEqual(source.name, "OpenSkiron")
