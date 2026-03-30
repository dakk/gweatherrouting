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
import os
import tempfile
import unittest
from datetime import date, datetime
from unittest.mock import MagicMock

from gweatherrouting.core.storage import Storage, json_serial


class TestJsonSerial(unittest.TestCase):
    """Test the json_serial helper function."""

    def test_datetime_returns_isoformat(self):
        dt = datetime(2025, 3, 15, 10, 30, 0)
        self.assertEqual(json_serial(dt), dt.isoformat())

    def test_date_returns_isoformat(self):
        d = date(2025, 3, 15)
        self.assertEqual(json_serial(d), d.isoformat())

    def test_unsupported_type_raises_type_error(self):
        with self.assertRaises(TypeError):
            json_serial(42)

    def test_unsupported_type_string_raises_type_error(self):
        with self.assertRaises(TypeError):
            json_serial("not a date")


class TestStorage(unittest.TestCase):
    """Test the Storage class."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Patch DATA_DIR so save/load operate in our temp directory
        import gweatherrouting.core.storage as storage_mod

        self._orig_data_dir = storage_mod.DATA_DIR
        storage_mod.DATA_DIR = self.tmpdir

    def tearDown(self):
        import gweatherrouting.core.storage as storage_mod

        storage_mod.DATA_DIR = self._orig_data_dir

    def test_setattr_getattr(self):
        s = Storage("teststorage", parent=None)
        s._Storage__init = True
        s["mykey"] = "myval"
        self.assertEqual(s.mykey, "myval")

    def test_setitem_getitem(self):
        s = Storage("teststorage", parent=None)
        s._Storage__init = True
        s["alpha"] = 123
        self.assertEqual(s["alpha"], 123)

    def test_delattr(self):
        s = Storage("teststorage", parent=None)
        s._Storage__init = True
        s["todel"] = "value"
        del s.todel
        self.assertNotIn("todel", s)

    def test_delitem(self):
        s = Storage("teststorage", parent=None)
        s._Storage__init = True
        s["todel"] = "value"
        del s["todel"]
        self.assertNotIn("todel", s)

    def test_save_load_roundtrip(self):
        s = Storage("roundtrip", parent=None)
        s._Storage__init = True
        s["greeting"] = "hello"
        s["count"] = 42

        # Verify the file was written
        path = os.path.join(self.tmpdir, "roundtrip.json")
        self.assertTrue(os.path.exists(path))

        # Load into a new Storage
        s2 = Storage("roundtrip", parent=None)
        s2.load()
        self.assertEqual(s2["greeting"], "hello")
        self.assertEqual(s2["count"], 42)

    def test_load_or_save_default_creates_file(self):
        path = os.path.join(self.tmpdir, "newfile.json")
        self.assertFalse(os.path.exists(path))

        s = Storage("newfile", parent=None)
        s.load_or_save_default()

        self.assertTrue(os.path.exists(path))

    def test_to_dict_excludes_storage_keys(self):
        s = Storage("dicttest", parent=None)
        s._Storage__init = True
        s["normalKey"] = "ok"
        s["myStorageKey"] = "should be excluded"
        d = s.to_dict()
        self.assertIn("normalKey", d)
        self.assertNotIn("myStorageKey", d)

    def test_register_on_change_callback_fires(self):
        s = Storage("changetest", parent=None)
        s._Storage__init = True
        s["watched"] = "initial"

        callback = MagicMock()
        s.register_on_change("watched", callback)
        # register_on_change calls handler immediately with current value
        callback.assert_called_with("initial")

        # Now change the value
        s["watched"] = "updated"
        callback.assert_called_with("updated")
        self.assertEqual(callback.call_count, 2)

    def test_load_data_sets_values(self):
        s = Storage("loaddata", parent=None)
        s._Storage__init = True
        s.load_data({"a": 1, "b": "two"})
        self.assertEqual(s["a"], 1)
        self.assertEqual(s["b"], "two")

    def test_parent_delegates_save(self):
        parent = Storage("parent", parent=None)
        parent._Storage__init = True
        child = Storage(None, parent=parent)
        # child.save() should call parent.save(), not raise
        child["x"] = 10
        # verify the value is set in the child
        self.assertEqual(child["x"], 10)


if __name__ == "__main__":
    unittest.main()
