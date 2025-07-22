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

import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("OsmGpsMap", "1.2")
except ValueError:
    gi.require_version("OsmGpsMap", "1.0")

from gi.repository import GObject, Gtk

from .chartstack_base import ChartStackBase


class ChartStackTrack(ChartStackBase):
    selected_track_item = None

    def __init__(self):
        self.track_store = self.builder.get_object("track-store")
        self.track_list_store = self.builder.get_object("track-list-store")
        self.update_track()
        self.select_last_track()

    def update_track(self, only_active=False):
        if not only_active:
            self.track_list_store.clear()
            for x in self.core.trackManager:
                self.track_list_store.append([x.name, len(x), x.length(), x.visible])

        self.track_store.clear()

        if self.core.trackManager.has_active():
            i = 0
            for wp in self.core.trackManager.get_active():
                i += 1
                self.track_store.append([i, wp[0], wp[1]])

        self.map.queue_draw()

    def select_last_track(self):
        def _inner():
            treeview = self.builder.get_object("track-list-view")
            selection = treeview.get_selection()
            model = treeview.get_model()

            iter_ = model.get_iter_first()
            last_iter = None

            while iter_ is not None:
                last_iter = iter_
                iter_ = model.iter_next(iter_)

            if last_iter is not None:
                selection.select_iter(last_iter)

                # Optionally scroll to it
                path = model.get_path(last_iter)
                treeview.scroll_to_cell(path, None, False, 0, 0)

        GObject.timeout_add(100, _inner)

    def on_track_export(self, widget):
        dialog = Gtk.FileChooserDialog(
            "Please select a destination",
            self.parent,
            Gtk.FileChooserAction.SAVE,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE,
                Gtk.ResponseType.OK,
            ),
        )

        filter_gpx = Gtk.FileFilter()
        filter_gpx.set_name("GPX track")
        filter_gpx.add_mime_type("application/gpx+xml")
        filter_gpx.add_pattern("*.gpx")
        dialog.add_filter(filter_gpx)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()

            if not filepath.endswith(".gpx"):
                filepath += ".gpx"

            if self.core.trackManager.get_active().export(filepath):
                # self.builder.get_object('header-bar').set_subtitle (filepath)
                self.status_bar.push(
                    self.status_bar.get_context_id("Info"),
                    f"Saved {len(self.core.trackManager.get_active())} waypoints",
                )
                edialog = Gtk.MessageDialog(
                    self.parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Saved"
                )
                edialog.format_secondary_text(
                    f"Saved {len(self.core.trackManager.get_active())} waypoints"
                )
                edialog.run()
                edialog.destroy()
            else:
                edialog = Gtk.MessageDialog(
                    self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error"
                )
                edialog.format_secondary_text(f"Cannot save file: {filepath}")
                edialog.run()
                edialog.destroy()

        dialog.destroy()

    def on_track_name_edit(self, widget, i, name):
        self.core.trackManager[int(i)].name = self.core.trackManager.get_unique_name(
            name
        )
        self.update_track()

    def on_track_toggle(self, widget, i):
        self.core.trackManager[int(i)].visible = not self.core.trackManager[
            int(i)
        ].visible
        self.update_track()

    def on_track_remove(self, widget):
        self.core.trackManager.remove(self.core.trackManager.get_active())
        self.update_track()
        self.map.queue_draw()
        self.select_last_track()

    def on_track_click(self, item, event):
        if event.button == 3 and len(self.core.trackManager) > 0:
            menu = self.builder.get_object("track-list-item-menu")
            menu.popup(None, None, None, None, event.button, event.time)

    def on_track_item_click(self, item, event):
        if event.button == 3 and self.core.trackManager.get_active() is not None:
            menu = self.builder.get_object("track-item-menu")
            menu.popup(None, None, None, None, event.button, event.time)

    def on_select_track(self, selection):
        store, pathlist = selection.get_selected_rows()
        for path in pathlist:
            tree_iter = store.get_iter(path)
            name = store.get_value(tree_iter, 0)
            self.core.trackManager.activate(name)
            self.update_track(only_active=True)
            self.map.queue_draw()

    def on_select_track_item(self, selection):
        store, pathlist = selection.get_selected_rows()
        for path in pathlist:
            tree_iter = store.get_iter(path)
            value = store.get_value(tree_iter, 0)
            self.selected_track_item = int(value) - 1

    def on_track_item_move(self, widget):
        if self.selected_track_item is not None:
            self.tools_map_layer.enable_poi_moving(
                lambda x, y: self.core.trackManager.get_active().move(
                    self.selected_track_item, x, y
                )
            )

    def on_track_item_move_up(self, widget):
        if self.selected_track_item is not None:
            self.core.trackManager.get_active().move_up(self.selected_track_item)
            self.update_track()
            self.map.queue_draw()

    def on_track_item_move_down(self, widget):
        if self.selected_track_item is not None:
            self.core.trackManager.get_active().move_down(self.selected_track_item)
            self.update_track()
            self.map.queue_draw()

    def on_track_item_remove(self, widget):
        if self.selected_track_item is not None:
            self.core.trackManager.get_active().remove(self.selected_track_item)
            self.update_track()
            self.map.queue_draw()

    def on_track_item_duplicate(self, widget):
        if self.selected_track_item is not None:
            self.core.trackManager.get_active().duplicate(self.selected_track_item)
            self.update_track()
            self.map.queue_draw()

    def show_track_point_popover(self, event):
        popover = self.builder.get_object("track-add-point-popover")
        popover.show_all()

    def add_track_point(self, widget):
        lat = self.builder.get_object("track-add-point-lat").get_text()
        lon = self.builder.get_object("track-add-point-lon").get_text()

        if len(lat) > 1 and len(lon) > 1:
            tracks_l = len(self.core.trackManager)

            if tracks_l == 0:
                e = self.core.trackManager.new_element(points=[])
                self.core.trackManager.set_active(e)
                self.select_last_track()
            elif tracks_l == 1 and not self.core.trackManager.has_active():
                self.core.trackManager.set_active(self.core.trackManager[0])
                self.select_last_track()
            elif tracks_l > 1 and not self.core.trackManager.has_active():
                edialog = Gtk.MessageDialog(
                    self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error"
                )
                edialog.format_secondary_text("No track selected")
                edialog.run()
                edialog.destroy()
                return

            self.core.trackManager.get_active().add(float(lat), float(lon))
            self.update_track()

            self.builder.get_object("track-add-point-lat").set_text("")
            self.builder.get_object("track-add-point-lon").set_text("")
            self.builder.get_object("track-add-point-popover").hide()
        self.map.queue_draw()
