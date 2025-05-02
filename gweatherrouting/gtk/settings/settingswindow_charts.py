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
from threading import Thread

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk

from gweatherrouting.gtk.charts.chartlayer import ChartLayer

from .settingswindow_base import SettingsWindowBase

PALETTES = {"cm93": 0, "navionics": 1, "dark": 2}


class SettingsWindowCharts(SettingsWindowBase):
    def __init__(self):
        self.builder.get_object("chart-progress").hide()
        self.reload_chart()

        self.selectedChart = None

        self.chartPalette = self.builder.get_object("chart-color-palette")
        self.chartPalette.set_active(PALETTES[self.settings_manager["chartPalette"]])

    def on_palette_change(self, widget):
        self.settings_manager["chartPalette"] = (
            self.chartPalette.get_active_text().lower()
        )
        self.settings_manager.save()

    def reload_chart(self):
        self.chartStore = self.builder.get_object("chart-store")
        self.chartStore.clear()

        for p in self.parent.chart_manager.charts:
            self.chartStore.append([p.path, p.enabled, p.ctype])

    def registering_chart(self, layer: ChartLayer, t):
        def ticker(x):
            Gdk.threads_enter()
            self.builder.get_object("chart-progress").set_fraction(x)
            Gdk.threads_leave()

        Gdk.threads_enter()
        self.builder.get_object("chart-progress").show()
        Gdk.threads_leave()

        if layer.on_register(ticker):
            vc = self.settings_manager[t + "Charts"]
            if not vc:
                vc = []

            vc.append({"path": layer.path, "metadata": layer.metadata, "enabled": True})
            self.settings_manager[t + "Charts"] = vc

            self.reload_chart()
        else:
            # Show error
            pass

        Gdk.threads_enter()
        self.builder.get_object("chart-progress").hide()
        Gdk.threads_leave()

    def on_chart_toggle_enabler(self, widget, i):
        i = int(i)
        chart = self.parent.chart_manager.charts[i]
        chart.enabled = not widget.get_active()

        for x in self.settings_manager[chart.ctype + "Charts"]:
            if x["path"] == chart.path:
                x["enabled"] = chart.enabled

        self.reload_chart()

    def on_chart_select(self, selection):
        store, pathlist = selection.get_selected_rows()
        for path in pathlist:
            tree_iter = store.get_iter(path)
            self.selectedChart = store.get_value(tree_iter, 0)

    def on_chart_click(self, widget, event):
        if event.button == 3:
            menu = self.builder.get_object("chart-menu")
            menu.popup(None, None, None, None, event.button, event.time)

    def on_remove_chart(self, widget):
        for ctype in ["vector", "raster"]:
            self.settings_manager[ctype + "Charts"] = list(
                filter(
                    lambda x: x["path"] != self.selectedChart,
                    self.settings_manager[ctype + "Charts"],
                )
            )

        self.parent.chart_manager.charts = list(
            filter(
                lambda x: x.path != self.selectedChart, self.parent.chart_manager.charts
            )
        )
        self.reload_chart()

    def on_add_raster_chart(self, widget):
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
            rast_l = self.parent.chart_manager.load_raster_layer(path)
            dialog.destroy()

            Thread(
                target=self.registering_chart,
                args=(
                    rast_l,
                    "raster",
                ),
            ).start()
        else:
            dialog.destroy()

    def on_add_vector_chart(self, widget):
        edialog = Gtk.MessageDialog(
            self.parent.window,
            0,
            Gtk.MessageType.WARNING,
            Gtk.ButtonsType.OK,
            "Warning",
        )
        edialog.format_secondary_text(
            "Only the already shown OSM vector data is currently supported."
        )
        edialog.run()
        edialog.destroy()
