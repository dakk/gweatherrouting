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

import gpxpy

from gweatherrouting.core.geo.track import Track


class TestTrack(unittest.TestCase):
    def test_from_json_roundtrip(self):
        pts = [(40.0, 13.0, None), (41.0, 14.0, None)]
        t = Track("route1", list(pts), visible=False)
        j = t.to_json()
        t2 = Track.from_json(j)
        self.assertEqual(t2.name, "route1")
        self.assertFalse(t2.visible)
        self.assertEqual(len(t2), 2)
        self.assertEqual(t2[0], (40.0, 13.0, None))
        self.assertEqual(t2[1], (41.0, 14.0, None))

    def test_to_gpx_object(self):
        pts = [(40.0, 13.0, None), (41.0, 14.0, None)]
        t = Track("route1", list(pts))
        gpx_obj = t.to_gpx_object()
        self.assertIsInstance(gpx_obj, gpxpy.gpx.GPXTrack)
        self.assertEqual(len(gpx_obj.segments), 1)
        self.assertEqual(len(gpx_obj.segments[0].points), 2)
        self.assertAlmostEqual(gpx_obj.segments[0].points[0].latitude, 40.0)
        self.assertAlmostEqual(gpx_obj.segments[0].points[0].longitude, 13.0)

    def test_to_list(self):
        pts = [(40.0, 13.0, None), (41.0, 14.0, None)]
        t = Track("route1", list(pts))
        result = t.to_list()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], (40.0, 13.0))
        self.assertEqual(result[1], (41.0, 14.0))

    def test_to_list_empty(self):
        t = Track("empty")
        result = t.to_list()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
