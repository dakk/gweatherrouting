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

from gweatherrouting.core.core import BoatInfo


class TestBoatInfo(unittest.TestCase):
    def test_defaults(self):
        bi = BoatInfo()
        self.assertEqual(bi.latitude, 0.0)
        self.assertEqual(bi.longitude, 0.0)
        self.assertIsNone(bi.sog)
        self.assertIsNone(bi.cog)
        self.assertIsNone(bi.awa)
        self.assertIsNone(bi.aws)
        self.assertIsNone(bi.twa)
        self.assertIsNone(bi.tws)
        self.assertIsNone(bi.depth)
        self.assertIsNone(bi.water_temp)

    def test_is_valid_false(self):
        bi = BoatInfo()
        self.assertFalse(bi.is_valid())

    def test_is_valid_true(self):
        bi = BoatInfo()
        bi.latitude = 45.0
        bi.longitude = 10.0
        self.assertTrue(bi.is_valid())

    def test_optional_fields_writable(self):
        bi = BoatInfo()
        bi.sog = 6.5
        bi.cog = 180.0
        bi.awa = 45.0
        bi.aws = 12.0
        bi.twa = 120.0
        bi.tws = 15.0
        bi.depth = 8.5
        bi.water_temp = 22.0
        self.assertEqual(bi.sog, 6.5)
        self.assertEqual(bi.cog, 180.0)
        self.assertEqual(bi.depth, 8.5)
