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

import logging
import os
from threading import Thread

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GObject, Gtk

logger = logging.getLogger("gweatherrouting")

GribFileFilter = Gtk.FileFilter()
GribFileFilter.set_name("Grib file")
GribFileFilter.add_mime_type("application/grib")
GribFileFilter.add_mime_type("application/x-grib2")
GribFileFilter.add_pattern("*.grib")
GribFileFilter.add_pattern("*.grib2")
GribFileFilter.add_pattern("*.grb")
GribFileFilter.add_pattern("*.grb2")


class GFSBoundsDialog(Gtk.Dialog):
    """Dialog to configure NOAA GFS download bounds."""

    def __init__(self, parent, gfs_source):
        super().__init__(
            title="NOAA GFS Download Settings",
            transient_for=parent,
            flags=0,
        )
        self.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK,
        )
        self.set_default_size(350, 250)
        self.gfs_source = gfs_source

        box = self.get_content_area()
        box.set_spacing(8)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)

        # Info label
        info = Gtk.Label(
            label="Set geographic bounds to reduce download size.\n"
            "Leave at defaults for a wider area."
        )
        info.set_line_wrap(True)
        info.set_xalign(0)
        box.pack_start(info, False, False, 0)

        # Bounds grid
        grid = Gtk.Grid()
        grid.set_column_spacing(8)
        grid.set_row_spacing(6)

        bounds = gfs_source.bounds or (30.0, -10.0, 50.0, 40.0)

        grid.attach(Gtk.Label(label="North Lat:"), 0, 0, 1, 1)
        self.north_entry = Gtk.SpinButton.new_with_range(-90, 90, 0.5)
        self.north_entry.set_value(bounds[2])
        grid.attach(self.north_entry, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="South Lat:"), 0, 1, 1, 1)
        self.south_entry = Gtk.SpinButton.new_with_range(-90, 90, 0.5)
        self.south_entry.set_value(bounds[0])
        grid.attach(self.south_entry, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="West Lon:"), 0, 2, 1, 1)
        self.west_entry = Gtk.SpinButton.new_with_range(-180, 180, 0.5)
        self.west_entry.set_value(bounds[1])
        grid.attach(self.west_entry, 1, 2, 1, 1)

        grid.attach(Gtk.Label(label="East Lon:"), 0, 3, 1, 1)
        self.east_entry = Gtk.SpinButton.new_with_range(-180, 180, 0.5)
        self.east_entry.set_value(bounds[3])
        grid.attach(self.east_entry, 1, 3, 1, 1)

        box.pack_start(grid, False, False, 0)

        # Preset buttons
        preset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for label, bounds_val in [
            ("Mediterranean", (30.0, -6.0, 46.0, 36.0)),
            ("Atlantic", (10.0, -80.0, 60.0, 0.0)),
            ("Caribbean", (8.0, -90.0, 28.0, -58.0)),
            ("Global", (-90.0, -180.0, 90.0, 180.0)),
        ]:
            btn = Gtk.Button(label=label)
            btn.connect("clicked", self._on_preset, bounds_val)
            preset_box.pack_start(btn, True, True, 0)
        box.pack_start(preset_box, False, False, 0)

        self.show_all()

    def _on_preset(self, widget, bounds):
        self.south_entry.set_value(bounds[0])
        self.west_entry.set_value(bounds[1])
        self.north_entry.set_value(bounds[2])
        self.east_entry.set_value(bounds[3])

    def get_bounds(self):
        return (
            self.south_entry.get_value(),
            self.west_entry.get_value(),
            self.north_entry.get_value(),
            self.east_entry.get_value(),
        )


class GribManagerWindow:
    def __init__(self, grib_manager, refresh_map_callback=None):
        self.grib_manager = grib_manager
        self.refresh_map_callback = refresh_map_callback
        self.selected_grib = None
        self.selectedLocalGrib = None

        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            os.path.abspath(os.path.dirname(__file__)) + "/gribmanagerwindow.glade"
        )
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("grib-manager-window")
        self.window.set_default_size(650, 400)

        self.gribFilesStore = self.builder.get_object("grib-files-store")
        self.grib_managerStore = self.builder.get_object("grib-manager-store")

        # Add source selector to header bar
        self._setup_source_selector()

        self.update_local_gribs()

        Thread(target=self.download_list, args=()).start()

    def _setup_source_selector(self):
        """Add source filter combo and GFS settings button to header bar."""
        header = self.window.get_titlebar()

        # Source combo
        self.source_combo = Gtk.ComboBoxText()
        self.source_combo.append_text("All Sources")
        for source in self.grib_manager.sources:
            self.source_combo.append_text(source.name)
        self.source_combo.set_active(0)
        self.source_combo.connect("changed", self._on_source_changed)
        header.pack_end(self.source_combo)

        # GFS settings button
        gfs_btn = Gtk.Button(label="GFS Settings")
        gfs_btn.set_tooltip_text("Configure NOAA GFS download area")
        gfs_btn.connect("clicked", self._on_gfs_settings)
        header.pack_end(gfs_btn)

    def _on_source_changed(self, widget):
        """Refresh the download list when source filter changes."""
        self.grib_manager.grib_files = None
        self.gribFilesStore.clear()
        Thread(target=self.download_list, args=()).start()

    def _on_gfs_settings(self, widget):
        """Open GFS bounds configuration dialog."""
        gfs_source = self.grib_manager.get_source("NOAA GFS")
        if gfs_source is None:
            return

        dialog = GFSBoundsDialog(self.window, gfs_source)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            gfs_source.bounds = dialog.get_bounds()
            # Refresh to recalculate size estimates
            self.grib_manager.grib_files = None
            self.gribFilesStore.clear()
            Thread(target=self.download_list, args=()).start()

        dialog.destroy()

    def show(self):
        self.window.show_all()

    def close(self):
        self.window.hide()

    def download_list(self):
        Gdk.threads_enter()

        self.builder.get_object("download-progress").show()
        self.builder.get_object("download-progress").set_fraction(50 / 100.0)

        Gdk.threads_leave()

        # Get selected source filter
        active = self.source_combo.get_active()
        source_name = None
        if active > 0:
            source_name = self.grib_manager.sources[active - 1].name

        try:
            for x in self.grib_manager.get_download_list(
                source_name=source_name, force=True
            ):
                Gdk.threads_enter()
                self.gribFilesStore.append(x)
                Gdk.threads_leave()
            Gdk.threads_enter()
        except Exception as e:
            Gdk.threads_enter()
            logger.error(f"Failed to download grib file list: {str(e)}")
            self.builder.get_object("download-progress").set_text(
                "Failed to download grib list"
            )

        self.builder.get_object("download-progress").hide()
        Gdk.threads_leave()

    def update_local_gribs(self):
        self.grib_manager.refresh_local_gribs()
        self.grib_managerStore.clear()

        for x in self.grib_manager.local_gribs:
            self.grib_managerStore.append(
                [
                    x.name,
                    x.centre,
                    str(x.start_time),
                    x.last_forecast,
                    self.grib_manager.is_enabled(x.name),
                ]
            )
        self.refresh_map_callback()

    def on_remove_local_grib(self, widget):
        self.grib_manager.remove(self.selectedLocalGrib)
        self.update_local_gribs()

    def on_open(self, widget):
        dialog = Gtk.FileChooserDialog(
            "Please choose a file",
            self.window,
            Gtk.FileChooserAction.OPEN,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )

        dialog.add_filter(GribFileFilter)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            dialog.destroy()

            if self.grib_manager.import_grib(filepath):
                edialog = Gtk.MessageDialog(
                    self.window, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Done"
                )
                edialog.format_secondary_text("File opened, loaded grib")
                edialog.run()
                edialog.destroy()

            else:
                edialog = Gtk.MessageDialog(
                    self.window,
                    0,
                    Gtk.MessageType.ERROR,
                    Gtk.ButtonsType.CANCEL,
                    "Error",
                )
                edialog.format_secondary_text(f"Cannot open grib file: {filepath}")
                edialog.run()
                edialog.destroy()
        else:
            dialog.destroy()

    def on_grib_toggle(self, widget, i):
        n = self.grib_manager.local_gribs[int(i)].name

        if self.grib_manager.is_enabled(n):
            self.grib_manager.disable(n)
        else:
            self.grib_manager.enable(n)

        self.update_local_gribs()

    def on_grib_download_percentage(self, percentage):
        if percentage % 10 == 0:
            logger.info("Downloading grib: %d%% completed", percentage)
        self.builder.get_object("download-progress").set_fraction(percentage / 100.0)
        self.builder.get_object("download-progress").set_text(f"{percentage}%")

    def on_grib_download_completed(self, status):
        if status:
            self.builder.get_object("download-progress").set_text("Download completed!")
        else:
            self.builder.get_object("download-progress").set_text("Download failed!")
        self.update_local_gribs()

        GObject.timeout_add(3000, self.builder.get_object("download-progress").hide)

    def on_grib_click(self, widget, event):
        if event.button == 3:
            menu = self.builder.get_object("remote-grib-menu")
            menu.popup(None, None, None, None, event.button, event.time)

    def on_grib_select(self, selection):
        store, pathlist = selection.get_selected_rows()
        for path in pathlist:
            tree_iter = store.get_iter(path)
            self.selected_grib = store.get_value(tree_iter, 4)

    def on_local_grib_select(self, selection):
        store, pathlist = selection.get_selected_rows()
        for path in pathlist:
            tree_iter = store.get_iter(path)
            self.selectedLocalGrib = store.get_value(tree_iter, 0)

    def on_local_grib_click(self, widget, event):
        if event.button == 3:
            menu = self.builder.get_object("local-grib-menu")
            menu.popup(None, None, None, None, event.button, event.time)

    def on_grib_download(self, widget):
        if self.selected_grib is None:
            return
        self.builder.get_object("download-progress").show()
        t = Thread(
            target=self.grib_manager.download,
            args=(
                self.selected_grib,
                self.on_grib_download_percentage,
                self.on_grib_download_completed,
            ),
        )
        t.start()
