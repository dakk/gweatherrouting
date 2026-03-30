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

from gweatherrouting.core.utils import unique_name, EventDispatcher, DotDict


# ---------------------------------------------------------------------------
# Helper: simple object with a .name attribute for unique_name tests
# ---------------------------------------------------------------------------
class _Named:
    def __init__(self, name):
        self.name = name


# ---------------------------------------------------------------------------
# unique_name tests
# ---------------------------------------------------------------------------
class TestUniqueName(unittest.TestCase):
    def test_none_collection(self):
        """When collection is None, the original name is returned."""
        self.assertEqual(unique_name("route", None), "route")

    def test_empty_collection(self):
        """When collection is empty, the original name is returned."""
        self.assertEqual(unique_name("route", []), "route")

    def test_no_conflict(self):
        """When the name does not exist in the collection, return it unchanged."""
        items = [_Named("alpha"), _Named("beta")]
        self.assertEqual(unique_name("gamma", items), "gamma")

    def test_single_conflict(self):
        """When 'name' exists, 'name-1' should be returned."""
        items = [_Named("route")]
        self.assertEqual(unique_name("route", items), "route-1")

    def test_multiple_conflicts(self):
        """When 'name' and 'name-1' exist, 'name-2' should be returned."""
        items = [_Named("route"), _Named("route-1")]
        self.assertEqual(unique_name("route", items), "route-2")

    def test_gap_in_conflicts(self):
        """When 'name' and 'name-2' exist but 'name-1' does not, 'name-1' is returned."""
        items = [_Named("route"), _Named("route-2")]
        self.assertEqual(unique_name("route", items), "route-1")


# ---------------------------------------------------------------------------
# EventDispatcher tests
# ---------------------------------------------------------------------------
class TestEventDispatcher(unittest.TestCase):
    def test_connect_and_dispatch(self):
        """Connecting a handler and dispatching the event triggers it."""
        ed = EventDispatcher()
        received = []
        ed.connect("on_update", lambda e: received.append(e))
        ed.dispatch("on_update", "payload")
        self.assertEqual(received, ["payload"])

    def test_dispatch_unknown_event(self):
        """Dispatching an event with no handlers should not raise."""
        ed = EventDispatcher()
        try:
            ed.dispatch("nonexistent", None)
        except Exception as exc:
            self.fail(f"dispatch raised {exc!r} on unknown event")

    def test_multiple_handlers(self):
        """Multiple handlers on the same event are all called."""
        ed = EventDispatcher()
        results = []
        ed.connect("evt", lambda e: results.append("a"))
        ed.connect("evt", lambda e: results.append("b"))
        ed.dispatch("evt", None)
        self.assertEqual(results, ["a", "b"])

    def test_disconnect(self):
        """After disconnect, the handler is no longer called."""
        ed = EventDispatcher()
        results = []
        handler = lambda e: results.append(e)  # noqa: E731
        ed.connect("evt", handler)
        ed.disconnect("evt", handler)
        ed.dispatch("evt", "data")
        self.assertEqual(results, [])

    def test_disconnect_one_of_many(self):
        """Disconnecting one handler leaves others intact."""
        ed = EventDispatcher()
        results = []
        h1 = lambda e: results.append("h1")  # noqa: E731
        h2 = lambda e: results.append("h2")  # noqa: E731
        ed.connect("evt", h1)
        ed.connect("evt", h2)
        ed.disconnect("evt", h1)
        ed.dispatch("evt", None)
        self.assertEqual(results, ["h2"])


# ---------------------------------------------------------------------------
# DotDict tests
# ---------------------------------------------------------------------------
class TestDotDict(unittest.TestCase):
    def test_dot_access(self):
        """Values set via constructor are accessible via dot notation."""
        d = DotDict({"x": 1, "y": 2})
        self.assertEqual(d.x, 1)
        self.assertEqual(d.y, 2)

    def test_dot_set(self):
        """Setting via dot notation stores the value."""
        d = DotDict()
        d.foo = "bar"
        self.assertEqual(d.foo, "bar")
        self.assertEqual(d["foo"], "bar")

    def test_dot_delete(self):
        """Deleting via dot notation removes the key."""
        d = DotDict({"key": "val"})
        del d.key
        self.assertNotIn("key", d)

    def test_missing_key_returns_none(self):
        """Accessing a missing key via dot notation returns None (dict.get default)."""
        d = DotDict()
        self.assertIsNone(d.nonexistent)

    def test_bracket_access(self):
        """Standard bracket access works as expected."""
        d = DotDict({"a": 10})
        self.assertEqual(d["a"], 10)

    def test_bracket_set(self):
        """Standard bracket set works and is accessible via dot."""
        d = DotDict()
        d["key"] = 42
        self.assertEqual(d.key, 42)

    def test_update_via_dot(self):
        """Overwriting an existing key via dot notation updates the value."""
        d = DotDict({"k": 1})
        d.k = 2
        self.assertEqual(d.k, 2)


# ---------------------------------------------------------------------------
# point_validity — quick smoke test (uses real geojson data)
# ---------------------------------------------------------------------------
class TestPointValidity(unittest.TestCase):
    def test_ocean_point_is_valid(self):
        """A point in the middle of the Atlantic should be valid (not in a country)."""
        from gweatherrouting.core.utils import point_validity

        # Roughly mid-Atlantic
        self.assertTrue(point_validity(30.0, -40.0))

    def test_land_point_is_invalid(self):
        """A point clearly on land should be invalid."""
        from gweatherrouting.core.utils import point_validity

        # Roughly central France
        self.assertFalse(point_validity(46.6, 2.2))


if __name__ == "__main__":
    unittest.main()
