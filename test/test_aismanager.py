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

import time
import unittest
from unittest.mock import patch

from gweatherrouting.core.aismanager import (
    AISManager,
    AISTarget,
    SHIP_TYPE_CARGO,
    SHIP_TYPE_FISHING,
    SHIP_TYPE_OTHER,
    SHIP_TYPE_PASSENGER,
    SHIP_TYPE_SAILING,
    SHIP_TYPE_TANKER,
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


class TestUpdatePosition(unittest.TestCase):
    """Tests for AISManager._update_position static method."""

    def _make_target(self):
        return AISTarget(mmsi=123456789)

    def test_sets_lat_lon(self):
        target = self._make_target()
        data = {"lat": 45.5, "lon": 12.3, "course": 180.0, "speed": 5.5, "heading": 90}
        AISManager._update_position(target, data)
        self.assertEqual(target.latitude, 45.5)
        self.assertEqual(target.longitude, 12.3)

    def test_sets_cog_sog_heading(self):
        target = self._make_target()
        data = {"lat": 45.5, "lon": 12.3, "course": 180.0, "speed": 5.5, "heading": 90}
        AISManager._update_position(target, data)
        self.assertEqual(target.cog, 180.0)
        self.assertEqual(target.sog, 5.5)
        self.assertEqual(target.heading, 90)

    def test_sentinel_lat_ignored(self):
        target = self._make_target()
        data = {"lat": 91.0, "lon": 12.3}
        AISManager._update_position(target, data)
        self.assertIsNone(target.latitude)
        self.assertEqual(target.longitude, 12.3)

    def test_sentinel_lon_ignored(self):
        target = self._make_target()
        data = {"lat": 45.5, "lon": 181.0}
        AISManager._update_position(target, data)
        self.assertEqual(target.latitude, 45.5)
        self.assertIsNone(target.longitude)

    def test_sentinel_cog_ignored(self):
        target = self._make_target()
        data = {"course": 360.0}
        AISManager._update_position(target, data)
        self.assertIsNone(target.cog)

    def test_sentinel_heading_ignored(self):
        target = self._make_target()
        data = {"heading": 511}
        AISManager._update_position(target, data)
        self.assertIsNone(target.heading)

    def test_missing_keys_leave_none(self):
        target = self._make_target()
        data = {}
        AISManager._update_position(target, data)
        self.assertIsNone(target.latitude)
        self.assertIsNone(target.longitude)
        self.assertIsNone(target.cog)
        self.assertIsNone(target.sog)
        self.assertIsNone(target.heading)

    def test_speed_zero_is_valid(self):
        target = self._make_target()
        data = {"speed": 0.0}
        AISManager._update_position(target, data)
        self.assertEqual(target.sog, 0.0)


class TestUpdateStatic(unittest.TestCase):
    """Tests for AISManager._update_static static method."""

    def _make_target(self):
        return AISTarget(mmsi=123456789)

    def test_name_stripped_whitespace(self):
        target = self._make_target()
        data = {"shipname": "  MY SHIP  "}
        AISManager._update_static(target, data)
        self.assertEqual(target.name, "MY SHIP")

    def test_name_stripped_at_chars(self):
        target = self._make_target()
        data = {"shipname": "VESSEL@@@@@@@@@@"}
        AISManager._update_static(target, data)
        self.assertEqual(target.name, "VESSEL")

    def test_name_stripped_whitespace_and_at(self):
        target = self._make_target()
        data = {"shipname": "  BOAT@@@  "}
        AISManager._update_static(target, data)
        # strip() then strip("@") => "BOAT@@@" => "BOAT"
        self.assertEqual(target.name, "BOAT")

    def test_ship_type_as_int(self):
        target = self._make_target()
        data = {"ship_type": 70}
        AISManager._update_static(target, data)
        self.assertEqual(target.ship_type, 70)

    def test_ship_type_from_string(self):
        target = self._make_target()
        data = {"ship_type": "36"}
        AISManager._update_static(target, data)
        self.assertEqual(target.ship_type, 36)

    def test_ship_type_invalid_ignored(self):
        target = self._make_target()
        data = {"ship_type": "not_a_number"}
        AISManager._update_static(target, data)
        self.assertIsNone(target.ship_type)

    def test_shiptype_alternate_key(self):
        target = self._make_target()
        data = {"shiptype": 80}
        AISManager._update_static(target, data)
        self.assertEqual(target.ship_type, 80)

    def test_empty_shipname_not_set(self):
        target = self._make_target()
        data = {"shipname": ""}
        AISManager._update_static(target, data)
        self.assertIsNone(target.name)

    def test_no_data_leaves_none(self):
        target = self._make_target()
        data = {}
        AISManager._update_static(target, data)
        self.assertIsNone(target.name)
        self.assertIsNone(target.ship_type)


class TestAISTargetCategory(unittest.TestCase):
    """Tests for AISTarget.category property with different ship_type values."""

    def test_fishing_category(self):
        t = AISTarget(mmsi=1, ship_type=30)
        self.assertEqual(t.category, SHIP_TYPE_FISHING)

    def test_passenger_category(self):
        t = AISTarget(mmsi=1, ship_type=60)
        self.assertEqual(t.category, SHIP_TYPE_PASSENGER)

    def test_cargo_category(self):
        t = AISTarget(mmsi=1, ship_type=70)
        self.assertEqual(t.category, SHIP_TYPE_CARGO)

    def test_tanker_category(self):
        t = AISTarget(mmsi=1, ship_type=80)
        self.assertEqual(t.category, SHIP_TYPE_TANKER)

    def test_sailing_category(self):
        t = AISTarget(mmsi=1, ship_type=36)
        self.assertEqual(t.category, SHIP_TYPE_SAILING)

    def test_other_category_unknown_type(self):
        t = AISTarget(mmsi=1, ship_type=99)
        self.assertEqual(t.category, SHIP_TYPE_OTHER)

    def test_other_category_none_type(self):
        t = AISTarget(mmsi=1, ship_type=None)
        self.assertEqual(t.category, SHIP_TYPE_OTHER)

    def test_fishing_upper_bound(self):
        t = AISTarget(mmsi=1, ship_type=35)
        self.assertEqual(t.category, SHIP_TYPE_FISHING)

    def test_passenger_upper_bound(self):
        t = AISTarget(mmsi=1, ship_type=69)
        self.assertEqual(t.category, SHIP_TYPE_PASSENGER)

    def test_cargo_upper_bound(self):
        t = AISTarget(mmsi=1, ship_type=79)
        self.assertEqual(t.category, SHIP_TYPE_CARGO)

    def test_tanker_upper_bound(self):
        t = AISTarget(mmsi=1, ship_type=89)
        self.assertEqual(t.category, SHIP_TYPE_TANKER)


class TestMultiFragmentMessage(unittest.TestCase):
    """Tests for multi-fragment AIS message processing (type 5)."""

    FRAG1 = "!AIVDM,2,1,3,B,55?MbV02>HFSU<l000000000000010KSCC=p00000015>P1120Ht54000000,0*25"
    FRAG2 = "!AIVDM,2,2,3,B,00000000000,2*2A"

    def test_both_fragments_produce_target(self):
        mgr = AISManager()
        mgr.process_sentence(self.FRAG1)
        # After only the first fragment, the target should not yet exist
        # (multi-fragment messages are buffered until complete)
        self.assertEqual(len(mgr.get_active_targets()), 0)

        mgr.process_sentence(self.FRAG2)
        targets = mgr.get_active_targets()
        self.assertEqual(len(targets), 1)

    def test_multi_fragment_target_has_mmsi(self):
        mgr = AISManager()
        mgr.process_sentence(self.FRAG1)
        mgr.process_sentence(self.FRAG2)
        targets = mgr.get_active_targets()
        self.assertEqual(targets[0].mmsi, 351759000)

    def test_multi_fragment_target_gets_static_data(self):
        mgr = AISManager()
        # Verify _update_static is called when both fragments of a type 5
        # message are processed.
        with patch.object(
            AISManager, "_update_static", wraps=AISManager._update_static
        ) as mock_static:
            mgr.process_sentence(self.FRAG1)
            mgr.process_sentence(self.FRAG2)
            mock_static.assert_called_once()
        targets = mgr.get_active_targets()
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0].mmsi, 351759000)


class TestStaleTargetWithCustomTimeout(unittest.TestCase):
    """Tests for stale target removal with various timeout scenarios."""

    AIS_POSITION = "!AIVDM,1,1,,B,13u@Dt002s000000000000000000,0*59"

    def test_target_not_stale_within_timeout(self):
        mgr = AISManager()
        mgr.process_sentence(self.AIS_POSITION)
        # Target was just created, should still be active
        self.assertEqual(len(mgr.get_active_targets()), 1)

    def test_target_stale_just_past_timeout(self):
        mgr = AISManager()
        mgr.process_sentence(self.AIS_POSITION)
        for t in mgr._targets.values():
            t.last_update = time.time() - STALE_TIMEOUT - 0.1
        self.assertEqual(len(mgr.get_active_targets()), 0)

    def test_target_not_stale_just_before_timeout(self):
        mgr = AISManager()
        mgr.process_sentence(self.AIS_POSITION)
        for t in mgr._targets.values():
            t.last_update = time.time() - STALE_TIMEOUT + 10
        self.assertEqual(len(mgr.get_active_targets()), 1)

    def test_multiple_targets_only_stale_removed(self):
        mgr = AISManager()
        mgr.process_sentence(self.AIS_POSITION)
        # Manually add a second target
        fresh_target = AISTarget(mmsi=999999999, last_update=time.time())
        mgr._targets[999999999] = fresh_target

        # Make only the first target stale
        for mmsi, t in mgr._targets.items():
            if mmsi != 999999999:
                t.last_update = time.time() - STALE_TIMEOUT - 1

        targets = mgr.get_active_targets()
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0].mmsi, 999999999)
