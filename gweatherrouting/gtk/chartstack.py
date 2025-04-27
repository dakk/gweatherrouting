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
import logging
import os

import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("OsmGpsMap", "1.2")
except:
    gi.require_version("OsmGpsMap", "1.0")

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
        chartManager: ChartManager,
        core: Core,
        settingsManager: SettingsManager,
    ):
        Gtk.Widget.__init__(self)

        # Keybinder.init()
        # Keybinder.bind('m', self.onMeasure)

        self.parent = parent
        self.chartManager = chartManager
        self.core = core

        self.timeControl = TimeControl()
        self.settingsManager = settingsManager

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

        self.map.layer_add(self.chartManager)
        self.chartManager.addMap(self.map)

        self.gribMapLayer = GribMapLayer(
            self.core.gribManager, self.timeControl, self.settingsManager
        )
        self.map.layer_add(self.gribMapLayer)

        self.toolsMapLayer = ToolsMapLayer(core)
        self.map.layer_add(self.toolsMapLayer)

        self.aisMapLayer = AISMapLayer(core)
        self.map.layer_add(self.aisMapLayer)

        self.geoMapLayer = GeoMapLayer(self.core, self.timeControl)
        self.map.layer_add(self.geoMapLayer)

        # This causes rendering problem
        # self.map.layer_add (OsmGpsMap.MapOsd (show_scale=True, show_dpad=False, show_zoom=False, show_crosshair=False))

        self.statusbar = self.builder.get_object("status-bar")

        ChartStackRouting.__init__(self)
        ChartStackTrack.__init__(self)
        ChartStackPOI.__init__(self)

        self.core.connect("boatPosition", self.boatInfoHandler)

        self.timetravelWidget = TimeTravelWidget(
            self.parent, self.timeControl, self.map
        )
        self.builder.get_object("timetravelcontainer").pack_start(
            self.timetravelWidget, True, True, 0
        )

        self.show_all()

        self.builder.get_object("mob-button").hide()
        self.builder.get_object("stop-routing-button").hide()
        self.progressBar = self.builder.get_object("progressbar")
        self.progressBar.hide()

        routing_page_idx = self.builder.get_object("routing_page")
        self.notebook = self.builder.get_object("notebook")
        if self.notebook and routing_page_idx:
            self.routing_page_index = self.notebook.page_num(routing_page_idx)
        else:
            logger.error("Could not find notebook or routing page widget index in Glade file.")

    def on_map_clicked(self, widget, event):
        # First grab focus for the map
        self.map.grab_focus()
        # Then proceed with your existing click handling
        return False  # Return False to allow other handlers to process the event

    def on_map_mapped(self, widget):
        # Widget is now visible on screen, safe to grab focus
        self.map.grab_focus()

    def getLatLon(self):
        lat = self.builder.get_object("track-add-point-lat").get_text()
        lon = self.builder.get_object("track-add-point-lon").get_text()
        return (float(lat), float(lon))

    def onMoveBoatHere(self, widget):
        lat, lon = self.getLatLon()
        self.core.setBoatPosition(lat, lon)
        # self.toolsMapLayer.gpsAdd(lat, lon)
        # self.map.queue_draw()

    def onMob(self, widget):
        lat, lon = self.getLatLon()
        self.toolsMapLayer.toggleMob(lat, lon)
        self.map.queue_draw()

    def onMeasure(self, widget):
        lat, lon = self.getLatLon()
        self.toolsMapLayer.enableMeasure(lat, lon)
        self.map.queue_draw()

    def onToggleCompass(self, widget):
        self.toolsMapLayer.setCompassVisible(widget.get_active())
        self.map.queue_draw()

    def onToggleGrib(self, widget):
        self.gribMapLayer.setVisible(widget.get_active())
        self.map.queue_draw()

    def onToggleConnections(self, widget):
        s = widget.get_active()
        if s:
            self.core.connectionManager.startPolling()
        else:
            self.core.connectionManager.stopPolling()

    def onToggleAIS(self, widget):
        self.aisMapLayer.setVisible(widget.get_active())
        self.map.queue_draw()

    def onToggleDashboard(self, widget):
        self.toolsMapLayer.setDashboardVisible(widget.get_active())
        self.map.queue_draw()

    def onToggleNotebook(self, widget):
        self.builder.get_object("notebook").set_visible(widget.get_active())

    def boatInfoHandler(self, bi):
        self.toolsMapLayer.gpsAdd(bi.latitude, bi.longitude, bi.heading, bi.speed)
        self.core.logManager.getByName("log").append((bi.latitude, bi.longitude))
        self.map.queue_draw()

    def onMapMouseMove(self, map, event):
        lat, lon = map.convert_screen_to_geographic(event.x, event.y).get_degrees()
        w = self.core.gribManager.getWindAt(self.timeControl.time, lat, lon)

        sstr = ""
        if w:
            sstr += "Wind %.1f°, %.1f kts - " % (w[0], w[1])
        sstr += "Latitude: %f, Longitude: %f" % (lat, lon)

        self.statusbar.push(self.statusbar.get_context_id("Info"), sstr)

        if self.toolsMapLayer.onMouseMove(lat, lon, event.x, event.y):
            self.map.queue_draw()

    def onMapClick(self, map, event):
        lat, lon = map.get_event_location(event).get_degrees()
        self.builder.get_object("track-add-point-lat").set_text(str(lat))
        self.builder.get_object("track-add-point-lon").set_text(str(lon))
        self.statusbar.push(
            self.statusbar.get_context_id("Info"),
            "Clicked on " + str(lat) + " " + str(lon),
        )

        if event.button == 3:
            menu = self.builder.get_object("map-context-menu")
            menu.popup(None, None, None, None, event.button, event.time)
        self.map.queue_draw()

    def onNew(self, widget):
        e = self.core.trackManager.newElement(points=[])
        self.core.trackManager.setActive(e)
        self.updateTrack()
        self.selectLastTrack()
        self.map.queue_draw()

    def onExport(self, widget):
        menu = self.builder.get_object("export-menu")
        menu.popup_at_widget(
            widget, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None
        )

    def exportAsGPX(self, widget):
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
            self.core.exportGPX(filename)

            self.statusbar.push(0, f"Exported as GPX to {filename}")
        else:
            dialog.destroy()

    def onImport(self, widget):
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
                if self.core.importGPX(filepath):
                    # self.builder.get_object('header-bar').set_subtitle (filepath)
                    self.updateTrack()
                    self.updatePOI()

                    edialog = Gtk.MessageDialog(
                        self.parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Done"
                    )
                    edialog.format_secondary_text("GPX file opened and loaded")
                    edialog.run()
                    edialog.destroy()
                    self.statusbar.push(
                        self.statusbar.get_context_id("Info"),
                        f"Loaded {filepath} with {len (self.core.trackManager.getActive())} waypoints",
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
                if self.core.gribManager.importGrib(filepath):
                    edialog = Gtk.MessageDialog(
                        self.parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Done"
                    )
                    edialog.format_secondary_text("File opened, loaded grib")
                    edialog.run()
                    edialog.destroy()
                    self.statusbar.push(
                        self.statusbar.get_context_id("Info"), f"Loaded grib {filepath}"
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
    def onPageSwitched(self, notebook, page, page_num):
        if page_num != self.routing_page_index:
            self.isochronesMapLayer.setIsochrones([], [])
        self.map.queue_draw()
    
        