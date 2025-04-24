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
# flake8: noqa: E402
from threading import Thread

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk

PALETTES = {"cm93": 0, "navionics": 1, "dark": 2}


class SettingsWindowCharts:
    def __init__(self, parent, settingsManager, core):
        self.builder.get_object("chart-progress").hide()
        self.reloadChart()

        self.selectedChart = None

        self.chartPalette = self.builder.get_object("chart-color-palette")
        self.chartPalette.set_active(PALETTES[self.settingsManager["chartPalette"]])

    def onPaletteChange(self, widget):
        self.settingsManager["chartPalette"] = (
            self.chartPalette.get_active_text().lower()
        )
        self.settingsManager.save()

    def reloadChart(self):
        self.chartStore = self.builder.get_object("chart-store")
        self.chartStore.clear()

        for p in self.parent.chartManager.charts:
            self.chartStore.append([p.path, p.enabled, p.ctype])

    def registeringChart(self, l, t):
        def ticker(x):
            Gdk.threads_enter()
            self.builder.get_object("chart-progress").set_fraction(x)
            Gdk.threads_leave()

        Gdk.threads_enter()
        self.builder.get_object("chart-progress").show()
        Gdk.threads_leave()

        if l.onRegister(ticker):
            vc = self.settingsManager[t + "Charts"]
            if not vc:
                vc = []

            vc.append({"path": l.path, "metadata": l.metadata})
            self.settingsManager[t + "Charts"] = vc

            self.reloadChart()
        else:
            # Show error
            pass

        Gdk.threads_enter()
        self.builder.get_object("chart-progress").hide()
        Gdk.threads_leave()

    def onChartToggleEnabler(self, widget, i):
        i = int(i)
        chart = self.parent.chartManager.charts[i]
        chart.enabled = not widget.get_active()

        for x in self.settingsManager[chart.ctype + "Charts"]:
            if x["path"] == chart.path:
                x["enabled"] = chart.enabled

        self.reloadChart()

    def onChartSelect(self, selection):
        store, pathlist = selection.get_selected_rows()
        for path in pathlist:
            tree_iter = store.get_iter(path)
            self.selectedChart = store.get_value(tree_iter, 0)

    def onChartClick(self, widget, event):
        if event.button == 3:
            menu = self.builder.get_object("chart-menu")
            menu.popup(None, None, None, None, event.button, event.time)

    def onRemoveChart(self, widget):
        for ctype in ["vector", "raster"]:
            self.settingsManager[ctype + "Charts"] = list(
                filter(
                    lambda x: x["path"] != self.selectedChart,
                    self.settingsManager[ctype + "Charts"],
                )
            )

        self.parent.chartManager.charts = list(
            filter(
                lambda x: x.path != self.selectedChart, self.parent.chartManager.charts
            )
        )
        self.reloadChart()

    def onAddRasterChart(self, widget):
        dialog = Gtk.FileChooserDialog(
            "Please select a directory",
            self.window,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            path = dialog.get_filename() + "/"
            l = self.parent.chartManager.loadRasterLayer(path)
            dialog.destroy()

            Thread(
                target=self.registeringChart,
                args=(
                    l,
                    "raster",
                ),
            ).start()
        else:
            dialog.destroy()

    def onAddVectorChart(self, widget):
        edialog = Gtk.MessageDialog(
            self.parent.window, 0, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK, "Warning"
        )
        edialog.format_secondary_text(
            "Only the already shown OSM vector data is currently supported."
        )
        edialog.run()
        edialog.destroy()
