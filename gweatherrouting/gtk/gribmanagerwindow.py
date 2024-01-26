# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
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
# flake8: noqa: E402

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
    def __init__(self, gribManager):
        self.gribManager = gribManager
        self.selectedGrib = None
        self.selectedLocalGrib = None

        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            os.path.abspath(os.path.dirname(__file__)) + "/gribmanagerwindow.glade"
        )
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("grib-manager-window")
        self.window.set_default_size(550, 300)

        self.gribFilesStore = self.builder.get_object("grib-files-store")
        self.gribManagerStore = self.builder.get_object("grib-manager-store")

        self.updateLocalGribs()

        Thread(target=self.downloadList, args=()).start()

    def show(self):
        self.window.show_all()

    def close(self):
        self.window.hide()

    def downloadList(self):
        Gdk.threads_enter()

        self.builder.get_object("download-progress").show()
        self.builder.get_object("download-progress").set_fraction(50 / 100.0)

        Gdk.threads_leave()

        try:
            for x in self.gribManager.getDownloadList():
                Gdk.threads_enter()
                self.gribFilesStore.append(x)
                Gdk.threads_leave()
            Gdk.threads_enter()
        except:
            Gdk.threads_enter()
            logger.error("Failed to download grib file list")
            self.builder.get_object("download-progress").set_text(
                "Failed to download grib list"
            )

        self.builder.get_object("download-progress").hide()
        Gdk.threads_leave()

    def updateLocalGribs(self):
        self.gribManager.refreshLocalGribs()
        self.gribManagerStore.clear()

        for x in self.gribManager.localGribs:
            self.gribManagerStore.append(
                [
                    x.name,
                    x.centre,
                    str(x.startTime),
                    x.lastForecast,
                    self.gribManager.isEnabled(x.name),
                ]
            )

    def onRemoveLocalGrib(self, widget):
        self.gribManager.remove(self.selectedLocalGrib)
        self.updateLocalGribs()

    def onOpen(self, widget):
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

            if self.gribManager.importGrib(filepath):
                edialog = Gtk.MessageDialog(
                    self.window, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Done"
                )
                edialog.format_secondary_text("File opened, loaded grib")
                edialog.run()
                edialog.destroy()
                self.statusbar.push(
                    self.statusbar.get_context_id("Info"), f"Loaded grib {filepath}"
                )

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

    def onGribToggle(self, widget, i):
        n = self.gribManager.localGribs[int(i)].name

        if self.gribManager.isEnabled(n):
            self.gribManager.disable(n)
        else:
            self.gribManager.enable(n)

        self.updateLocalGribs()

    def onGribDownloadPercentage(self, percentage):
        if percentage % 10 == 0:
            logger.info("Downloading grib: %d%% completed", percentage)
        self.builder.get_object("download-progress").set_fraction(percentage / 100.0)
        self.builder.get_object("download-progress").set_text(f"{percentage}%")
        # self.statusbar.push (self.statusbar.get_context_id ('Info'), 'Downloading grib: %d%% completed' % percentage)

    def onGribDownloadCompleted(self, status):
        self.builder.get_object("download-progress").set_text("Download completed!")
        self.updateLocalGribs()

        GObject.timeout_add(3000, self.builder.get_object("download-progress").hide)

    def onGribClick(self, widget, event):
        if event.button == 3:
            menu = self.builder.get_object("remote-grib-menu")
            menu.popup(None, None, None, None, event.button, event.time)

    def onGribSelect(self, selection):
        store, pathlist = selection.get_selected_rows()
        for path in pathlist:
            tree_iter = store.get_iter(path)
            self.selectedGrib = store.get_value(tree_iter, 4)

    def onLocalGribSelect(self, selection):
        store, pathlist = selection.get_selected_rows()
        for path in pathlist:
            tree_iter = store.get_iter(path)
            self.selectedLocalGrib = store.get_value(tree_iter, 0)

    def onLocalGribClick(self, widget, event):
        if event.button == 3:
            menu = self.builder.get_object("local-grib-menu")
            menu.popup(None, None, None, None, event.button, event.time)

    def onGribDownload(self, widget):
        self.builder.get_object("download-progress").show()
        t = Thread(
            target=self.gribManager.download,
            args=(
                self.selectedGrib,
                self.onGribDownloadPercentage,
                self.onGribDownloadCompleted,
            ),
        )
        t.start()
