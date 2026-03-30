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

from gweatherrouting.core.geo.collection import (
    Collection,
    CollectionWithActiveElement,
)
from gweatherrouting.core.geo.element import Element


class TestCollection(unittest.TestCase):
    """Test the Collection class with Storage I/O patched out."""

    def _make_collection(self):
        with (
            patch(
                "gweatherrouting.core.geo.collection.CollectionStorage.load_or_save_default"
            ),
            patch("gweatherrouting.core.geo.collection.CollectionStorage.save"),
        ):
            return Collection(Element, "elem")

    def test_init_empty(self):
        c = self._make_collection()
        self.assertEqual(len(c), 0)

    def test_append(self):
        c = self._make_collection()
        e = Element("e1")
        c.append(e)
        self.assertEqual(len(c), 1)

    def test_remove(self):
        c = self._make_collection()
        e = Element("e1")
        c.append(e)
        c.remove(e)
        self.assertEqual(len(c), 0)

    def test_iter(self):
        c = self._make_collection()
        e1 = Element("e1")
        e2 = Element("e2")
        c.append(e1)
        c.append(e2)
        items = list(c)
        self.assertEqual(items, [e1, e2])

    def test_getitem(self):
        c = self._make_collection()
        e = Element("e1")
        c.append(e)
        self.assertIs(c[0], e)

    def test_setitem(self):
        c = self._make_collection()
        e1 = Element("e1")
        e2 = Element("e2")
        c.append(e1)
        c[0] = e2
        self.assertIs(c[0], e2)

    def test_delitem(self):
        c = self._make_collection()
        e1 = Element("e1")
        e2 = Element("e2")
        c.append(e1)
        c.append(e2)
        del c[0]
        self.assertEqual(len(c), 1)
        self.assertIs(c[0], e2)

    def test_get_by_name_found(self):
        c = self._make_collection()
        e = Element("target")
        c.append(e)
        self.assertIs(c.get_by_name("target"), e)

    def test_get_by_name_not_found(self):
        c = self._make_collection()
        self.assertIsNone(c.get_by_name("nonexistent"))

    def test_exists_true(self):
        c = self._make_collection()
        c.append(Element("present"))
        self.assertTrue(c.exists("present"))

    def test_exists_false(self):
        c = self._make_collection()
        self.assertFalse(c.exists("absent"))

    def test_get_unique_name_no_conflict(self):
        c = self._make_collection()
        name = c.get_unique_name("track")
        self.assertEqual(name, "track")

    def test_get_unique_name_with_conflict(self):
        c = self._make_collection()
        c.append(Element("track"))
        name = c.get_unique_name("track")
        self.assertEqual(name, "track-1")

    def test_to_json_load_json_roundtrip(self):
        c = self._make_collection()
        c.append(Element("a", visible=True))
        c.append(Element("b", visible=False))
        j = c.to_json()

        c2 = self._make_collection()
        c2.load_json(j)
        self.assertEqual(len(c2), 2)
        self.assertEqual(c2[0].name, "a")
        self.assertTrue(c2[0].visible)
        self.assertEqual(c2[1].name, "b")
        self.assertFalse(c2[1].visible)

    def test_new_element(self):
        c = self._make_collection()
        e = c.new_element()
        self.assertEqual(len(c), 1)
        self.assertEqual(e.name, "elem")


class TestCollectionWithActiveElement(unittest.TestCase):
    """Test the CollectionWithActiveElement class."""

    def _make_collection(self):
        with (
            patch(
                "gweatherrouting.core.geo.collection.CollectionStorage.load_or_save_default"
            ),
            patch("gweatherrouting.core.geo.collection.CollectionStorage.save"),
        ):
            return CollectionWithActiveElement(Element, "elem")

    def test_has_active_initially_false(self):
        c = self._make_collection()
        self.assertFalse(c.has_active())

    def test_set_active(self):
        c = self._make_collection()
        e = Element("e1")
        c.append(e)
        c.set_active(e)
        self.assertTrue(c.has_active())

    def test_get_active(self):
        c = self._make_collection()
        e = Element("e1")
        c.append(e)
        c.set_active(e)
        self.assertIs(c.get_active(), e)

    def test_is_active(self):
        c = self._make_collection()
        e1 = Element("e1")
        e2 = Element("e2")
        c.append(e1)
        c.append(e2)
        c.set_active(e1)
        self.assertTrue(c.is_active(e1))
        self.assertFalse(c.is_active(e2))

    def test_remove_active_element_clears_it(self):
        c = self._make_collection()
        e = Element("e1")
        c.append(e)
        c.set_active(e)
        self.assertTrue(c.has_active())
        c.remove(e)
        self.assertFalse(c.has_active())
        self.assertIsNone(c.get_active())


if __name__ == "__main__":
    unittest.main()
