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
import os

import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("OsmGpsMap", "1.2")
except:
    gi.require_version("OsmGpsMap", "1.0")

from gi.repository import GdkPixbuf, Gtk

from gweatherrouting.common import resource_path

from .chartstack_base import ChartStackBase


class ChartStackPOI(ChartStackBase):
    selected_poi = None

    def __init__(self):
        self.poiStore = self.builder.get_object("poi-store")
        self.update_poi()

        poi_symbol_store = self.builder.get_object("poi-symbols-store")
        base_path = resource_path("gweatherrouting", "data/symbols/")

        for x in os.listdir(base_path):
            poi_symbol_store.append(
                [
                    x.split(".svg")[0],
                    GdkPixbuf.Pixbuf.new_from_file_at_size(base_path + x, 32, 32),
                ]
            )

    def on_poi_name_edit(self, widget, i, name):
        self.core.poiManager.elements[int(i)].name = (
            self.core.poiManager.get_unique_name(name)
        )
        self.update_poi()

    def on_select_poi(self, selection):
        store, pathlist = selection.get_selected_rows()
        for path in pathlist:
            tree_iter = store.get_iter(path)
            self.selected_poi = store.get_value(tree_iter, 0)

    def on_poi_move(self, widget):
        if self.selected_poi is not None:
            self.tools_map_layer.enable_poi_moving(
                lambda x, y: self.core.poiManager.move(self.selected_poi, x, y)
            )

    def on_poi_remove(self, widget):
        if self.selected_poi is not None:
            self.core.poiManager.remove_by_name(self.selected_poi)
            self.update_poi()

    def on_poi_toggle(self, widget, i):
        self.core.poiManager.elements[int(i)].visible = (
            not self.core.poiManager.elements[int(i)].visible
        )
        self.update_poi()

    def on_poi_click(self, item, event):
        if event.button == 3 and len(self.core.poiManager.elements) > 0:
            menu = self.builder.get_object("poi-menu")
            menu.popup(None, None, None, None, event.button, event.time)

    def update_poi(self):
        self.poiStore.clear()
        for x in self.core.poiManager.elements:
            self.poiStore.append(
                [x.name, x.position[0], x.position[1], x.visible, x.symbol]
            )
        self.core.poiManager.save()
        self.map.queue_draw()

    def add_poi(self, widget):
        lat = self.builder.get_object("track-add-point-lat").get_text()
        lon = self.builder.get_object("track-add-point-lon").get_text()

        if len(lat) > 1 and len(lon) > 1:
            self.core.poiManager.create((float(lat), float(lon)))
            self.map.queue_draw()
            self.update_poi()

    def export_pois_as_nmea_pfec(self, widget):
        dialog = Gtk.FileChooserDialog(
            "Export POIs as NMEA PFEC",
            self.parent,
            Gtk.FileChooserAction.SAVE,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE,
                Gtk.ResponseType.OK,
            ),
        )
        dialog.set_do_overwrite_confirmation(True)

        filter_gpx = Gtk.FileFilter()
        filter_gpx.set_name("NMEA text file")
        filter_gpx.add_mime_type("text/plain")
        filter_gpx.add_pattern("*.nmea")
        dialog.add_filter(filter_gpx)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            dialog.destroy()
            s = self.core.poiManager.to_nmea_fpec()
            f = open(filename, "w")
            f.write(s)
            f.close()

            self.status_bar.push(0, f"POIs exported as NMEA PFEC to {filename}")
        else:
            dialog.destroy()
