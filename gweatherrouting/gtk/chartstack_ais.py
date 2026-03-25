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

import math

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import GLib

from .chartstack_base import ChartStackBase


class ChartStackAIS(ChartStackBase):
    def __init__(self):
        self.ais_store = self.builder.get_object("ais-target-store")
        self.ais_treeview = self.builder.get_object("ais-target-list")
        self.ais_notebook_page = 3

        # Start periodic update
        GLib.timeout_add(3000, self._update_ais_targets)

    def _get_boat_position(self):
        """Get current boat position for distance calculation."""
        try:
            bi = self.core.boat_info
            if bi.is_valid():
                return (bi.latitude, bi.longitude)
        except AttributeError:
            pass
        return None

    @staticmethod
    def _haversine_nm(lat1, lon1, lat2, lon2):
        """Calculate distance in nautical miles between two positions."""
        R = 3440.065  # Earth radius in nautical miles
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def _update_ais_targets(self):
        """Periodically update the AIS target list."""
        targets = self.core.ais_manager.get_active_targets()

        # Show/hide the AIS tab based on whether there are targets
        notebook = self.builder.get_object("notebook")
        page = notebook.get_nth_page(self.ais_notebook_page)
        if page is not None:
            if len(targets) > 0:
                page.show()
            else:
                page.hide()

        boat_pos = self._get_boat_position()

        self.ais_store.clear()
        for t in targets:
            if not t.has_valid_position():
                continue

            name = t.name or ""
            category = t.category or ""
            sog = "%.1f" % t.sog if t.sog is not None else ""
            cog = "%.1f" % t.cog if t.cog is not None else ""

            distance = ""
            if boat_pos is not None:
                d = self._haversine_nm(
                    boat_pos[0], boat_pos[1], t.latitude, t.longitude
                )
                distance = "%.1f" % d

            self.ais_store.append(
                [str(t.mmsi), name, category, sog, cog, distance]
            )

        return True  # Keep the timeout running
