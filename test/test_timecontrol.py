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

import datetime
import unittest
from unittest.mock import MagicMock

from gweatherrouting.core.timecontrol import TimeControl


class TestTimeControlInit(unittest.TestCase):
    def test_init_sets_time_to_current_hour(self):
        tc = TimeControl()
        now = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
        self.assertEqual(tc.time.minute, 0)
        self.assertEqual(tc.time.second, 0)
        self.assertEqual(tc.time.microsecond, 0)
        # Hour should match (allowing for edge case of hour rollover)
        self.assertAlmostEqual(tc.time.timestamp(), now.timestamp(), delta=3600)


class TestTimeControlDFORMAT(unittest.TestCase):
    def test_dformat_value(self):
        self.assertEqual(TimeControl.DFORMAT, "%Y/%m/%d, %H:%M")


class TestTimeControlNow(unittest.TestCase):
    def test_now_resets_to_current_time(self):
        tc = TimeControl()
        # Set to a different time first
        tc._time = datetime.datetime(2000, 1, 1, 12, 0, 0)
        tc.now()
        now = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
        self.assertEqual(tc.time.minute, 0)
        self.assertEqual(tc.time.second, 0)
        self.assertAlmostEqual(tc.time.timestamp(), now.timestamp(), delta=3600)

    def test_now_dispatches_time_change(self):
        tc = TimeControl()
        handler = MagicMock()
        tc.connect("time_change", handler)
        tc.now()
        handler.assert_called_once()
        # The argument should be a datetime
        self.assertIsInstance(handler.call_args[0][0], datetime.datetime)


class TestTimeControlSetTime(unittest.TestCase):
    def test_set_time_sets_specific_datetime(self):
        tc = TimeControl()
        target = datetime.datetime(2025, 6, 15, 10, 30, 0)
        tc.set_time(target)
        self.assertEqual(tc.time, target)

    def test_set_time_dispatches_time_change(self):
        tc = TimeControl()
        handler = MagicMock()
        tc.connect("time_change", handler)
        target = datetime.datetime(2025, 6, 15, 10, 30, 0)
        tc.set_time(target)
        handler.assert_called_once_with(target)


class TestTimeControlIncrease(unittest.TestCase):
    def test_increase_hours(self):
        tc = TimeControl()
        base = datetime.datetime(2025, 1, 1, 12, 0, 0)
        tc.set_time(base)
        tc.increase(hours=3)
        self.assertEqual(tc.time, datetime.datetime(2025, 1, 1, 15, 0, 0))

    def test_increase_minutes(self):
        tc = TimeControl()
        base = datetime.datetime(2025, 1, 1, 12, 0, 0)
        tc.set_time(base)
        tc.increase(minutes=45)
        self.assertEqual(tc.time, datetime.datetime(2025, 1, 1, 12, 45, 0))

    def test_increase_seconds(self):
        tc = TimeControl()
        base = datetime.datetime(2025, 1, 1, 12, 0, 0)
        tc.set_time(base)
        tc.increase(seconds=90)
        self.assertEqual(tc.time, datetime.datetime(2025, 1, 1, 12, 1, 30))

    def test_increase_combined(self):
        tc = TimeControl()
        base = datetime.datetime(2025, 1, 1, 12, 0, 0)
        tc.set_time(base)
        tc.increase(hours=1, minutes=30, seconds=15)
        self.assertEqual(tc.time, datetime.datetime(2025, 1, 1, 13, 30, 15))

    def test_increase_dispatches_time_change(self):
        tc = TimeControl()
        handler = MagicMock()
        tc.connect("time_change", handler)
        tc.increase(hours=1)
        handler.assert_called_once()


class TestTimeControlDecrease(unittest.TestCase):
    def test_decrease_hours(self):
        tc = TimeControl()
        base = datetime.datetime(2025, 1, 1, 12, 0, 0)
        tc.set_time(base)
        tc.decrease(hours=3)
        self.assertEqual(tc.time, datetime.datetime(2025, 1, 1, 9, 0, 0))

    def test_decrease_minutes(self):
        tc = TimeControl()
        base = datetime.datetime(2025, 1, 1, 12, 0, 0)
        tc.set_time(base)
        tc.decrease(minutes=45)
        self.assertEqual(tc.time, datetime.datetime(2025, 1, 1, 11, 15, 0))

    def test_decrease_seconds(self):
        tc = TimeControl()
        base = datetime.datetime(2025, 1, 1, 12, 0, 0)
        tc.set_time(base)
        tc.decrease(seconds=90)
        self.assertEqual(tc.time, datetime.datetime(2025, 1, 1, 11, 58, 30))

    def test_decrease_combined(self):
        tc = TimeControl()
        base = datetime.datetime(2025, 1, 1, 12, 0, 0)
        tc.set_time(base)
        tc.decrease(hours=1, minutes=30, seconds=15)
        self.assertEqual(tc.time, datetime.datetime(2025, 1, 1, 10, 29, 45))

    def test_decrease_dispatches_time_change(self):
        tc = TimeControl()
        handler = MagicMock()
        tc.connect("time_change", handler)
        tc.decrease(hours=1)
        handler.assert_called_once()


class TestTimeControlGetTimestamp(unittest.TestCase):
    def test_get_timestamp_returns_int(self):
        tc = TimeControl()
        ts = tc.get_timestamp()
        self.assertIsInstance(ts, int)

    def test_get_timestamp_correct_value(self):
        tc = TimeControl()
        base = datetime.datetime(2025, 1, 1, 12, 0, 0)
        tc.set_time(base)
        expected = int(base.timestamp())
        self.assertEqual(tc.get_timestamp(), expected)


class TestTimeControlTimeProperty(unittest.TestCase):
    def test_time_has_no_tzinfo(self):
        tc = TimeControl()
        self.assertIsNone(tc.time.tzinfo)
