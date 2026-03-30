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
from unittest.mock import MagicMock, patch

import gpxpy.gpx

from gweatherrouting.core.geo.poicollection import POICollection


class TestPOICollection(unittest.TestCase):
    """Test the POICollection class with Storage I/O patched out."""

    def _make_collection(self):
        with (
            patch(
                "gweatherrouting.core.geo.collection.CollectionStorage.load_or_save_default"
            ),
            patch("gweatherrouting.core.geo.collection.CollectionStorage.save"),
        ):
            return POICollection()

    def test_create_adds_poi_with_position(self):
        c = self._make_collection()
        poi = c.create((40.0, 10.0))
        self.assertEqual(len(c), 1)
        self.assertEqual(poi.position, (40.0, 10.0))

    def test_move_updates_position(self):
        c = self._make_collection()
        c.create((40.0, 10.0))
        name = c[0].name
        c.move(name, 50.0, 20.0)
        self.assertEqual(c[0].position, (50.0, 20.0))

    def test_import_from_gpx(self):
        c = self._make_collection()
        gpx = gpxpy.gpx.GPX()
        wp1 = gpxpy.gpx.GPXWaypoint(latitude=41.0, longitude=12.0, name="WP1")
        wp2 = gpxpy.gpx.GPXWaypoint(latitude=42.0, longitude=13.0, name="WP2")
        gpx.waypoints.append(wp1)
        gpx.waypoints.append(wp2)

        c.import_from_gpx(gpx)
        self.assertEqual(len(c), 2)
        self.assertEqual(c[0].name, "WP1")
        self.assertEqual(c[0].position, (41.0, 12.0))
        self.assertEqual(c[1].name, "WP2")
        self.assertEqual(c[1].position, (42.0, 13.0))

    def test_to_nmea_fpec_returns_pfec_lines(self):
        c = self._make_collection()
        c.create((40.0, 10.0))
        c.create((41.0, 11.0))
        result = c.to_nmea_fpec()
        self.assertIsInstance(result, str)
        lines = result.strip().split("\n")
        # Last line should be the terminator
        self.assertTrue(lines[-1].startswith("$PFEC,GPxfr"))
        # All other lines should be $PFEC,GPwpl
        for line in lines[:-1]:
            self.assertTrue(line.startswith("$PFEC,GPwpl"), f"Unexpected line: {line}")


if __name__ == "__main__":
    unittest.main()
