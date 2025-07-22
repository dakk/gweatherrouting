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

import gi

gi.require_version("Gtk", "3.0")
# try:
#     gi.require_version("OsmGpsMap", "1.2")
# except:
#     gi.require_version("OsmGpsMap", "1.0")

from gi.repository import Gdk, Gtk, OsmGpsMap  # Keybinder

from gweatherrouting.core import Core, TimeControl

from .charts.chartmanager import ChartManager
from .chartstack_poi import ChartStackPOI
from .chartstack_routing import ChartStackRouting
from .chartstack_track import ChartStackTrack
from .gribmanagerwindow import GribFileFilter
from .maplayers import AISMapLayer, GeoMapLayer, GribMapLayer, ToolsMapLayer
from .settings import SettingsManager
from .widgets.timetravel import TimeTravelWidget

logger = logging.getLogger("gweatherrouting")


class ChartStack(Gtk.Box, ChartStackPOI, ChartStackTrack, ChartStackRouting):
    def __init__(
        self,
        parent,
        chart_manager: ChartManager,
        core: Core,
        settings_manager: SettingsManager,
    ):
        Gtk.Widget.__init__(self)

        # Keybinder.init()
        # Keybinder.bind('m', self.on_measure)

        self.parent = parent
        self.chart_manager = chart_manager
        self.core = core

        self.time_control = TimeControl()
        self.settings_manager = settings_manager

        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            os.path.abspath(os.path.dirname(__file__)) + "/chartstack.glade"
        )
        self.builder.connect_signals(self)

        self.pack_start(self.builder.get_object("chartcontent"), True, True, 0)

        self.map = self.builder.get_object("map")
        self.map.set_center_and_zoom(39.0, 9.0, 6)
        self.map.connect("map", self.on_map_mapped)
        self.map.connect("button-press-event", self.on_map_clicked)
        self.map.set_keyboard_shortcut(
            OsmGpsMap.MapKey_t.FULLSCREEN, Gdk.keyval_from_name("F11")
        )
        self.map.set_keyboard_shortcut(
            OsmGpsMap.MapKey_t.UP, Gdk.keyval_from_name("Up")
        )
        self.map.set_keyboard_shortcut(
            OsmGpsMap.MapKey_t.DOWN, Gdk.keyval_from_name("Down")
        )
        self.map.set_keyboard_shortcut(
            OsmGpsMap.MapKey_t.LEFT, Gdk.keyval_from_name("Left")
        )
        self.map.set_keyboard_shortcut(
            OsmGpsMap.MapKey_t.RIGHT, Gdk.keyval_from_name("Right")
        )

        self.map.layer_add(self.chart_manager)
        self.chart_manager.add_map(self.map)

        self.gribMapLayer = GribMapLayer(
            self.core.grib_manager, self.time_control, self.settings_manager
        )
        self.map.layer_add(self.gribMapLayer)

        self.tools_map_layer = ToolsMapLayer(core)
        self.map.layer_add(self.tools_map_layer)

        self.ais_map_layer = AISMapLayer(core)
        self.map.layer_add(self.ais_map_layer)

        self.geo_map_layer = GeoMapLayer(self.core, self.time_control)
        self.map.layer_add(self.geo_map_layer)

        # This causes rendering problem
        # self.map.layer_add (OsmGpsMap.MapOsd (show_scale=True, show_dpad=False,
        # show_zoom=False, show_crosshair=False))

        self.status_bar = self.builder.get_object("status-bar")

        ChartStackRouting.__init__(self)
        ChartStackTrack.__init__(self)
        ChartStackPOI.__init__(self)

        self.core.connect("boat_position", self.boat_info_handler)

        self.timetravel_widget = TimeTravelWidget(
            self.parent, self.time_control, self.map
        )
        self.builder.get_object("timetravelcontainer").pack_start(
            self.timetravel_widget, True, True, 0
        )

        self.show_all()

        self.builder.get_object("mob-button").hide()
        self.builder.get_object("stop-routing-button").hide()
        self.progress_bar = self.builder.get_object("progressbar")
        self.progress_bar.hide()

    def on_map_clicked(self, widget, event):
        # First grab focus for the map
        self.map.grab_focus()
        # Then proceed with your existing click handling
        return False  # Return False to allow other handlers to process the event

    def on_map_mapped(self, widget):
        # Widget is now visible on screen, safe to grab focus
        self.map.grab_focus()

    def get_lat_lon(self):
        lat = self.builder.get_object("track-add-point-lat").get_text()
        lon = self.builder.get_object("track-add-point-lon").get_text()
        return (float(lat), float(lon))

    def on_move_boat_here(self, widget):
        lat, lon = self.get_lat_lon()
        self.core.set_boat_position(lat, lon)
        # self.tools_map_layer.gps_add(lat, lon)
        # self.map.queue_draw()

    def on_mob(self, widget):
        lat, lon = self.get_lat_lon()
        self.tools_map_layer.toggle_mob(lat, lon)
        self.map.queue_draw()

    def on_measure(self, widget):
        lat, lon = self.get_lat_lon()
        self.tools_map_layer.enable_measure(lat, lon)
        self.map.queue_draw()

    def on_toggle_compass(self, widget):
        self.tools_map_layer.set_compass_visible(widget.get_active())
        self.map.queue_draw()

    def on_toggle_grib(self, widget):
        self.gribMapLayer.set_visible(widget.get_active())
        self.map.queue_draw()

    def on_toggle_connections(self, widget):
        s = widget.get_active()
        if s:
            self.core.connectionManager.start_polling()
        else:
            self.core.connectionManager.stop_polling()

    def on_toggle_ais(self, widget):
        self.ais_map_layer.set_visible(widget.get_active())
        self.map.queue_draw()

    def on_toggle_dashboard(self, widget):
        self.tools_map_layer.set_dashboard_visible(widget.get_active())
        self.map.queue_draw()

    def on_toggle_notebook(self, widget):
        self.builder.get_object("notebook").set_visible(widget.get_active())

    def boat_info_handler(self, bi):
        self.tools_map_layer.gps_add(bi.latitude, bi.longitude, bi.heading, bi.speed)

        log = self.core.logManager.log
        if log is not None:
            log.add(bi.latitude, bi.longitude)

        self.map.queue_draw()

    def on_map_mouse_move(self, map, event):
        lat, lon = map.convert_screen_to_geographic(event.x, event.y).get_degrees()
        w = self.core.grib_manager.get_wind_at(self.time_control.time, lat, lon)

        sstr = ""
        if w:
            sstr += "Wind %.1f°, %.1f kts - " % (w[0], w[1])
        sstr += "Latitude: %f, Longitude: %f" % (lat, lon)

        self.status_bar.push(self.status_bar.get_context_id("Info"), sstr)

        if self.tools_map_layer.on_mouse_move(lat, lon, event.x, event.y):
            self.map.queue_draw()

    def on_map_click(self, map, event):
        lat, lon = map.get_event_location(event).get_degrees()
        self.builder.get_object("track-add-point-lat").set_text(str(lat))
        self.builder.get_object("track-add-point-lon").set_text(str(lon))
        self.status_bar.push(
            self.status_bar.get_context_id("Info"),
            "Clicked on " + str(lat) + " " + str(lon),
        )

        if event.button == 3:
            menu = self.builder.get_object("map-context-menu")
            menu.popup(None, None, None, None, event.button, event.time)
        self.map.queue_draw()

    def on_new(self, widget):
        e = self.core.trackManager.new_element(points=[])
        self.core.trackManager.set_active(e)
        self.update_track()
        self.select_last_track()
        self.map.queue_draw()

    def on_export(self, widget):
        menu = self.builder.get_object("export-menu")
        menu.popup_at_widget(
            widget, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None
        )

    def export_as_gpx(self, widget):
        dialog = Gtk.FileChooserDialog(
            "Export as GPX",
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
        filter_gpx.set_name("GPX track")
        filter_gpx.add_mime_type("application/gpx+xml")
        filter_gpx.add_pattern("*.gpx")
        dialog.add_filter(filter_gpx)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            dialog.destroy()
            self.core.export_gpx(filename)

            self.status_bar.push(0, f"Exported as GPX to {filename}")
        else:
            dialog.destroy()

    def on_import(self, widget):
        dialog = Gtk.FileChooserDialog(
            "Please choose a file",
            self.parent,
            Gtk.FileChooserAction.OPEN,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )

        filter_gpx = Gtk.FileFilter()
        filter_gpx.set_name("GPX track")
        filter_gpx.add_mime_type("application/gpx+xml")
        filter_gpx.add_pattern("*.gpx")
        dialog.add_filter(filter_gpx)

        dialog.add_filter(GribFileFilter)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            dialog.destroy()

            extension = filepath.split(".")[-1]

            if extension in ["gpx"]:
                if self.core.import_gpx(filepath):
                    # self.builder.get_object('header-bar').set_subtitle (filepath)
                    self.update_track()
                    self.update_poi()

                    edialog = Gtk.MessageDialog(
                        self.parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Done"
                    )
                    edialog.format_secondary_text("GPX file opened and loaded")
                    edialog.run()
                    edialog.destroy()
                    self.status_bar.push(
                        self.status_bar.get_context_id("Info"),
                        f"Loaded {filepath} with {len(self.core.trackManager.get_active())}"
                        + " waypoints",
                    )

                else:
                    edialog = Gtk.MessageDialog(
                        self.parent,
                        0,
                        Gtk.MessageType.ERROR,
                        Gtk.ButtonsType.CANCEL,
                        "Error",
                    )
                    edialog.format_secondary_text(f"Cannot open file: {filepath}")
                    edialog.run()
                    edialog.destroy()

            elif extension in ["grb", "grb2", "grib"]:
                if self.core.grib_manager.import_grib(filepath):
                    edialog = Gtk.MessageDialog(
                        self.parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Done"
                    )
                    edialog.format_secondary_text("File opened, loaded grib")
                    edialog.run()
                    edialog.destroy()
                    self.status_bar.push(
                        self.status_bar.get_context_id("Info"),
                        f"Loaded grib {filepath}",
                    )

                else:
                    edialog = Gtk.MessageDialog(
                        self.parent,
                        0,
                        Gtk.MessageType.ERROR,
                        Gtk.ButtonsType.CANCEL,
                        "Error",
                    )
                    edialog.format_secondary_text(f"Cannot open grib file: {filepath}")
                    edialog.run()
                    edialog.destroy()

            else:
                edialog = Gtk.MessageDialog(
                    self.parent,
                    0,
                    Gtk.MessageType.ERROR,
                    Gtk.ButtonsType.CANCEL,
                    "Error",
                )
                edialog.format_secondary_text(f"Unrecognize file format: {filepath}")
                edialog.run()
                edialog.destroy()

        else:
            dialog.destroy()
