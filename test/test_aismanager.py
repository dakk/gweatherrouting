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

import time
import unittest

from gweatherrouting.core.aismanager import (
    AISManager,
    AISTarget,
    STALE_TIMEOUT,
    classify_ship_type,
)


class TestClassifyShipType(unittest.TestCase):
    def test_sailing(self):
        self.assertEqual(classify_ship_type(36), "sailing")

    def test_fishing(self):
        for t in (30, 32, 35):
            self.assertEqual(classify_ship_type(t), "fishing")

    def test_cargo(self):
        for t in (70, 75, 79):
            self.assertEqual(classify_ship_type(t), "cargo")

    def test_tanker(self):
        for t in (80, 85, 89):
            self.assertEqual(classify_ship_type(t), "tanker")

    def test_passenger(self):
        for t in (60, 65, 69):
            self.assertEqual(classify_ship_type(t), "passenger")

    def test_other(self):
        self.assertEqual(classify_ship_type(0), "other")
        self.assertEqual(classify_ship_type(99), "other")
        self.assertEqual(classify_ship_type(None), "other")


class TestAISTarget(unittest.TestCase):
    def test_has_valid_position(self):
        t = AISTarget(mmsi=123456789, latitude=45.0, longitude=10.0)
        self.assertTrue(t.has_valid_position())

    def test_no_position(self):
        t = AISTarget(mmsi=123456789)
        self.assertFalse(t.has_valid_position())

    def test_invalid_position_91(self):
        t = AISTarget(mmsi=123456789, latitude=91.0, longitude=10.0)
        self.assertFalse(t.has_valid_position())

    def test_invalid_position_181(self):
        t = AISTarget(mmsi=123456789, latitude=45.0, longitude=181.0)
        self.assertFalse(t.has_valid_position())

    def test_category(self):
        t = AISTarget(mmsi=123456789, ship_type=36)
        self.assertEqual(t.category, "sailing")

    def test_category_none(self):
        t = AISTarget(mmsi=123456789)
        self.assertEqual(t.category, "other")


class TestAISManager(unittest.TestCase):
    # AIS position report type 1 for MMSI 265557232
    AIS_POSITION = "!AIVDM,1,1,,B,13u@Dt002s000000000000000000,0*59"

    def test_init(self):
        mgr = AISManager()
        self.assertEqual(len(mgr.get_active_targets()), 0)

    def test_process_single_sentence(self):
        mgr = AISManager()
        mgr.process_sentence(self.AIS_POSITION)
        targets = mgr.get_active_targets()
        self.assertGreaterEqual(len(targets), 1)

    def test_target_has_mmsi(self):
        mgr = AISManager()
        mgr.process_sentence(self.AIS_POSITION)
        targets = mgr.get_active_targets()
        self.assertTrue(any(t.mmsi == 265557232 for t in targets))

    def test_invalid_sentence(self):
        mgr = AISManager()
        mgr.process_sentence("garbage data")
        self.assertEqual(len(mgr.get_active_targets()), 0)

    def test_stale_targets_removed(self):
        mgr = AISManager()
        mgr.process_sentence(self.AIS_POSITION)
        self.assertEqual(len(mgr.get_active_targets()), 1)

        # Make target stale
        for t in mgr._targets.values():
            t.last_update = time.time() - STALE_TIMEOUT - 1

        self.assertEqual(len(mgr.get_active_targets()), 0)

    def test_orphaned_fragment_ignored(self):
        mgr = AISManager()
        # Send fragment 2 of 2 without fragment 1
        frag2 = "!AIVDM,2,2,3,B,00000000000,2*2A"
        mgr.process_sentence(frag2)
        self.assertEqual(len(mgr.get_active_targets()), 0)
