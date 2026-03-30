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

import os
import unittest

from gweatherrouting.common import wind_color, resource_path


def _hex_to_tuple(hex_str):
    """Convert a 6-char hex color string to the normalized RGB tuple wind_color returns."""
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0
    return (r, g, b)


# Wind speed bands: (lower_bound_inclusive, upper_bound_exclusive, hex_color)
_BANDS = [
    (0, 2, "0000CC"),
    (2, 4, "0066FF"),
    (4, 6, "00FFFF"),
    (6, 8, "00FF66"),
    (8, 10, "00CC00"),
    (10, 12, "66FF33"),
    (12, 14, "CCFF33"),
    (14, 16, "FFFF66"),
    (16, 18, "FFCC00"),
    (18, 20, "FF9900"),
    (20, 22, "FF6600"),
    (22, 24, "FF3300"),
    (24, 26, "FF0000"),
    (26, 28, "CC6600"),
]


class TestWindColorBands(unittest.TestCase):
    """Test wind_color returns the correct RGB tuple for each wind speed band."""

    def test_mid_values(self):
        for lo, hi, hex_color in _BANDS:
            wspeed = (lo + hi) / 2.0
            with self.subTest(wspeed=wspeed):
                self.assertEqual(wind_color(wspeed), _hex_to_tuple(hex_color))

    def test_band_28_and_above(self):
        """wspeed >= 28 should return the last color."""
        expected = _hex_to_tuple("CC0000")
        self.assertEqual(wind_color(28), expected)
        self.assertEqual(wind_color(30), expected)
        self.assertEqual(wind_color(100), expected)


class TestWindColorBoundaries(unittest.TestCase):
    """Test exact boundary values of wind speed bands."""

    def test_boundaries(self):
        boundaries = [
            (0, "0000CC"),
            (2, "0066FF"),
            (4, "00FFFF"),
            (6, "00FF66"),
            (8, "00CC00"),
            (10, "66FF33"),
            (12, "CCFF33"),
            (14, "FFFF66"),
            (16, "FFCC00"),
            (18, "FF9900"),
            (20, "FF6600"),
            (22, "FF3300"),
            (24, "FF0000"),
            (26, "CC6600"),
            (28, "CC0000"),
        ]
        for wspeed, expected_hex in boundaries:
            with self.subTest(wspeed=wspeed):
                self.assertEqual(wind_color(wspeed), _hex_to_tuple(expected_hex))


class TestWindColorNegative(unittest.TestCase):
    """Negative wind speed falls through all conditions and gets the default color."""

    def test_negative_speed(self):
        # Negative values don't match any band (first band starts at 0),
        # so the default "0000CC" is used.
        expected = _hex_to_tuple("0000CC")
        self.assertEqual(wind_color(-1), expected)
        self.assertEqual(wind_color(-100), expected)


class TestWindColorReturnType(unittest.TestCase):
    """wind_color always returns a 3-tuple of floats in [0.0, 1.0]."""

    def test_return_type(self):
        for wspeed in [0, 1, 5, 10, 15, 20, 25, 28, 50]:
            with self.subTest(wspeed=wspeed):
                result = wind_color(wspeed)
                self.assertIsInstance(result, tuple)
                self.assertEqual(len(result), 3)
                for component in result:
                    self.assertIsInstance(component, float)
                    self.assertGreaterEqual(component, 0.0)
                    self.assertLessEqual(component, 1.0)


class TestResourcePath(unittest.TestCase):
    """Test resource_path returns a valid filesystem path."""

    def test_returns_string(self):
        path = resource_path("gweatherrouting", "data/countries.geojson")
        self.assertIsInstance(path, str)

    def test_known_resource_exists(self):
        path = resource_path("gweatherrouting", "data/countries.geojson")
        self.assertTrue(os.path.exists(path), f"Expected resource to exist: {path}")

    def test_directory_path_ends_with_sep(self):
        path = resource_path("gweatherrouting", "data/")
        self.assertTrue(path.endswith(os.sep))

    def test_file_path_does_not_end_with_sep(self):
        path = resource_path("gweatherrouting", "data/countries.geojson")
        self.assertFalse(path.endswith(os.sep))


if __name__ == "__main__":
    unittest.main()
