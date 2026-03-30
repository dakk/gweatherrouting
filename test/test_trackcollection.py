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
from unittest.mock import patch

import gpxpy.gpx

from gweatherrouting.core.geo.trackcollection import TrackCollection


class TestTrackCollection(unittest.TestCase):
    """Test the TrackCollection class with Storage I/O patched out."""

    def _make_collection(self):
        with (
            patch(
                "gweatherrouting.core.geo.collection.CollectionStorage.load_or_save_default"
            ),
            patch("gweatherrouting.core.geo.collection.CollectionStorage.save"),
        ):
            return TrackCollection()

    def test_import_from_gpx(self):
        c = self._make_collection()

        gpx = gpxpy.gpx.GPX()
        track = gpxpy.gpx.GPXTrack(name="MyTrack")
        segment = gpxpy.gpx.GPXTrackSegment()
        segment.points.append(gpxpy.gpx.GPXTrackPoint(40.0, 10.0))
        segment.points.append(gpxpy.gpx.GPXTrackPoint(41.0, 11.0))
        segment.points.append(gpxpy.gpx.GPXTrackPoint(42.0, 12.0))
        track.segments.append(segment)
        gpx.tracks.append(track)

        c.import_from_gpx(gpx)

        self.assertEqual(len(c), 1)
        self.assertEqual(c[0].name, "MyTrack")
        self.assertEqual(len(c[0].points), 3)
        self.assertEqual(c[0].points[0], [40.0, 10.0])
        self.assertEqual(c[0].points[1], [41.0, 11.0])
        self.assertEqual(c[0].points[2], [42.0, 12.0])

    def test_import_from_gpx_multiple_tracks(self):
        c = self._make_collection()

        gpx = gpxpy.gpx.GPX()
        for i, name in enumerate(["Track A", "Track B"]):
            track = gpxpy.gpx.GPXTrack(name=name)
            seg = gpxpy.gpx.GPXTrackSegment()
            seg.points.append(gpxpy.gpx.GPXTrackPoint(40.0 + i, 10.0 + i))
            track.segments.append(seg)
            gpx.tracks.append(track)

        c.import_from_gpx(gpx)

        self.assertEqual(len(c), 2)
        self.assertEqual(c[0].name, "Track A")
        self.assertEqual(c[1].name, "Track B")

    def test_import_from_gpx_multiple_segments(self):
        c = self._make_collection()

        gpx = gpxpy.gpx.GPX()
        track = gpxpy.gpx.GPXTrack(name="MultiSeg")
        seg1 = gpxpy.gpx.GPXTrackSegment()
        seg1.points.append(gpxpy.gpx.GPXTrackPoint(40.0, 10.0))
        seg2 = gpxpy.gpx.GPXTrackSegment()
        seg2.points.append(gpxpy.gpx.GPXTrackPoint(41.0, 11.0))
        track.segments.append(seg1)
        track.segments.append(seg2)
        gpx.tracks.append(track)

        c.import_from_gpx(gpx)

        self.assertEqual(len(c), 1)
        # Points from both segments are merged into one track
        self.assertEqual(len(c[0].points), 2)
        self.assertEqual(c[0].points[0], [40.0, 10.0])
        self.assertEqual(c[0].points[1], [41.0, 11.0])


if __name__ == "__main__":
    unittest.main()
