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

from gweatherrouting.core.polarwrapper import PolarWrapper


class MockPolar:
    """A mock polar with known return values for testing."""

    def __init__(self):
        self.tws = [5.0, 10.0, 15.0, 20.0]
        self.twa = [0, 45, 90, 135, 180]
        self.speed_table = [[1.0, 2.0], [3.0, 4.0]]

    def get_speed(self, tws, twa):
        return 10.0

    def get_reaching(self, tws):
        return (8.0, 90.0)

    def get_max_vmgtwa(self, tws, twa):
        return (6.0, 42.0)

    def get_max_vmg_up(self, tws):
        return (5.0, 40.0)

    def get_max_vmg_down(self, tws):
        return (7.0, 150.0)

    def get_routage_speed(self, tws, twa):
        return 9.0

    def get_twa_routage(self, tws, twa):
        return 120.0


class TestPolarWrapperEfficiency100(unittest.TestCase):
    """Test with efficiency=1.0 (no change)."""

    def setUp(self):
        self.mock = MockPolar()
        self.pw = PolarWrapper(self.mock, efficiency=1.0)

    def test_get_speed(self):
        self.assertEqual(self.pw.get_speed(10, 90), 10.0)

    def test_get_reaching(self):
        speed, twa = self.pw.get_reaching(10)
        self.assertEqual(speed, 8.0)
        self.assertEqual(twa, 90.0)

    def test_get_max_vmgtwa(self):
        vmg, twa = self.pw.get_max_vmgtwa(10, 45)
        self.assertEqual(vmg, 6.0)
        self.assertEqual(twa, 42.0)

    def test_get_max_vmg_up(self):
        vmg, twa = self.pw.get_max_vmg_up(10)
        self.assertEqual(vmg, 5.0)
        self.assertEqual(twa, 40.0)

    def test_get_max_vmg_down(self):
        vmg, twa = self.pw.get_max_vmg_down(10)
        self.assertEqual(vmg, 7.0)
        self.assertEqual(twa, 150.0)

    def test_get_routage_speed(self):
        self.assertEqual(self.pw.get_routage_speed(10, 90), 9.0)

    def test_get_twa_routage(self):
        self.assertEqual(self.pw.get_twa_routage(10, 90), 120.0)


class TestPolarWrapperEfficiency85(unittest.TestCase):
    """Test with efficiency=0.85 (scaled)."""

    def setUp(self):
        self.mock = MockPolar()
        self.pw = PolarWrapper(self.mock, efficiency=0.85)

    def test_get_speed(self):
        self.assertAlmostEqual(self.pw.get_speed(10, 90), 10.0 * 0.85)

    def test_get_reaching(self):
        speed, twa = self.pw.get_reaching(10)
        self.assertAlmostEqual(speed, 8.0 * 0.85)
        self.assertEqual(twa, 90.0)  # TWA not scaled

    def test_get_max_vmgtwa(self):
        vmg, twa = self.pw.get_max_vmgtwa(10, 45)
        self.assertAlmostEqual(vmg, 6.0 * 0.85)
        self.assertEqual(twa, 42.0)  # TWA not scaled

    def test_get_max_vmg_up(self):
        vmg, twa = self.pw.get_max_vmg_up(10)
        self.assertAlmostEqual(vmg, 5.0 * 0.85)
        self.assertEqual(twa, 40.0)  # TWA not scaled

    def test_get_max_vmg_down(self):
        vmg, twa = self.pw.get_max_vmg_down(10)
        self.assertAlmostEqual(vmg, 7.0 * 0.85)
        self.assertEqual(twa, 150.0)  # TWA not scaled

    def test_get_routage_speed(self):
        self.assertAlmostEqual(self.pw.get_routage_speed(10, 90), 9.0 * 0.85)

    def test_get_twa_routage_not_scaled(self):
        # get_twa_routage should NOT be scaled by efficiency
        self.assertEqual(self.pw.get_twa_routage(10, 90), 120.0)


class TestPolarWrapperEfficiencyZero(unittest.TestCase):
    """Test with efficiency=0.0 (zero speed)."""

    def setUp(self):
        self.mock = MockPolar()
        self.pw = PolarWrapper(self.mock, efficiency=0.0)

    def test_get_speed(self):
        self.assertEqual(self.pw.get_speed(10, 90), 0.0)

    def test_get_reaching(self):
        speed, twa = self.pw.get_reaching(10)
        self.assertEqual(speed, 0.0)
        self.assertEqual(twa, 90.0)

    def test_get_max_vmgtwa(self):
        vmg, twa = self.pw.get_max_vmgtwa(10, 45)
        self.assertEqual(vmg, 0.0)
        self.assertEqual(twa, 42.0)

    def test_get_max_vmg_up(self):
        vmg, twa = self.pw.get_max_vmg_up(10)
        self.assertEqual(vmg, 0.0)
        self.assertEqual(twa, 40.0)

    def test_get_max_vmg_down(self):
        vmg, twa = self.pw.get_max_vmg_down(10)
        self.assertEqual(vmg, 0.0)
        self.assertEqual(twa, 150.0)

    def test_get_routage_speed(self):
        self.assertEqual(self.pw.get_routage_speed(10, 90), 0.0)

    def test_get_twa_routage_not_scaled(self):
        # get_twa_routage should NOT be scaled even at zero efficiency
        self.assertEqual(self.pw.get_twa_routage(10, 90), 120.0)


class TestPolarWrapperPassthrough(unittest.TestCase):
    """Test that tws, twa, speed_table pass through to the underlying polar."""

    def setUp(self):
        self.mock = MockPolar()
        self.pw = PolarWrapper(self.mock, efficiency=0.5)

    def test_tws_passthrough(self):
        self.assertEqual(self.pw.tws, self.mock.tws)
        self.assertIs(self.pw.tws, self.mock.tws)

    def test_twa_passthrough(self):
        self.assertEqual(self.pw.twa, self.mock.twa)
        self.assertIs(self.pw.twa, self.mock.twa)

    def test_speed_table_passthrough(self):
        self.assertEqual(self.pw.speed_table, self.mock.speed_table)
        self.assertIs(self.pw.speed_table, self.mock.speed_table)
