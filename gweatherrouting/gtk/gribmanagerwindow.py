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
        self.window.set_default_size(550, 300)

        self.gribFilesStore = self.builder.get_object("grib-files-store")
        self.grib_managerStore = self.builder.get_object("grib-manager-store")

        self.update_local_gribs()

        Thread(target=self.download_list, args=()).start()

    def show(self):
        self.window.show_all()

    def close(self):
        self.window.hide()

    def download_list(self):
        Gdk.threads_enter()

        self.builder.get_object("download-progress").show()
        self.builder.get_object("download-progress").set_fraction(50 / 100.0)

        Gdk.threads_leave()

        try:
            for x in self.grib_manager.get_download_list():
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
                # self.status_bar.push(
                #     self.status_bar.get_context_id("Info"), f"Loaded grib {filepath}"
                # )

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
        # self.status_bar.push (self.status_bar.get_context_id ('Info'),
        #  'Downloading grib: %d%% completed' % percentage)

    def on_grib_download_completed(self, status):
        self.builder.get_object("download-progress").set_text("Download completed!")
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
