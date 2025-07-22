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
import traceback
from threading import Thread

import gi

from gweatherrouting.core.storage import POLAR_DIR

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("OsmGpsMap", "1.2")
except ValueError:
    gi.require_version("OsmGpsMap", "1.0")

from gi.repository import Gdk, GObject, Gtk
from weatherrouting import RoutingNoWindError

from gweatherrouting.core import utils
from gweatherrouting.core.geo.routing import Routing

from .chartstack_base import ChartStackBase
from .maplayers import IsochronesMapLayer
from .routingwizarddialog import RoutingWizardDialog

logger = logging.getLogger("gweatherrouting")


class ChartStackRouting(ChartStackBase):
    routing_thread = None
    selected_routing = None
    stop_routing = False

    def __init__(self):
        self.currentRouting = None
        self.routingStore = self.builder.get_object("routing-store")

        self.isochronesMapLayer = IsochronesMapLayer()
        self.map.layer_add(self.isochronesMapLayer)

        self.update_routings()

    def __del__(self):
        if self.routing_thread:
            self.stop_routing = True

    def on_route_to(self, widget):
        lat, lon = self.get_lat_lon()
        poi = self.core.poiManager.create(
            (
                lat,
                lon,
            )
        )
        self.on_routing_create(None)
        self.core.poiManager.remove(poi)

    def on_routing_create(self, event):
        dialog = RoutingWizardDialog(self.core, self.parent)
        response = dialog.run()

        polar_file = dialog.get_selected_polar()
        if response == Gtk.ResponseType.OK:
            self.stop_routing = False
            self.currentRouting = self.core.create_routing(
                dialog.get_selected_algorithm(),
                os.path.join(POLAR_DIR, polar_file),
                dialog.get_selected_track_or_poi(),
                dialog.get_start_datetime(),
                dialog.get_selected_start_point(),
                self.chart_manager.get_line_point_validity_providers(),
                not dialog.get_coastline_checks(),
            )
            self.currentRouting.name = "routing-" + polar_file.split(".")[0]
            self.routing_thread = Thread(target=self.on_routing_step, args=())
            self.routing_thread.start()
            self.builder.get_object("stop-routing-button").show()

        dialog.destroy()

    def on_routing_step(self):
        if self.currentRouting is None:
            return

        Gdk.threads_enter()
        self.progress_bar.set_fraction(1.0)
        self.progress_bar.set_text("1%")
        self.progress_bar.show()
        Gdk.threads_leave()

        res = None

        while (not self.currentRouting.end) and (not self.stop_routing):
            try:
                res = self.currentRouting.step()
                logger.debug("Routing step: %s", str(res))

            # This exception is not raised by the algorithm
            except RoutingNoWindError:
                Gdk.threads_enter()
                edialog = Gtk.MessageDialog(
                    self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error"
                )
                edialog.format_secondary_text(
                    "Trying to create a route without wind information"
                )
                edialog.run()
                edialog.destroy()
                self.progress_bar.hide()
                Gdk.threads_leave()
                self.isochronesMapLayer.set_isochrones([], [])
                self.builder.get_object("stop-routing-button").hide()
                return None

            except Exception as e:
                Gdk.threads_enter()
                edialog = Gtk.MessageDialog(
                    self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error"
                )
                edialog.format_secondary_text("Error: " + str(e))
                edialog.run()
                edialog.destroy()
                self.progress_bar.hide()
                Gdk.threads_leave()
                self.isochronesMapLayer.set_isochrones([], [])
                self.builder.get_object("stop-routing-button").hide()
                traceback.print_exc()
                return None

            Gdk.threads_enter()
            self.progress_bar.set_fraction(res.progress / 100.0)
            self.progress_bar.set_text(str(res.progress) + "%")

            self.isochronesMapLayer.set_isochrones(res.isochrones, res.path)
            self.time_control.set_time(res.time)
            # self.map.queue_draw ()
            # self.builder.get_object('time-adjustment').set_value (res.time)
            Gdk.threads_leave()

        if self.stop_routing:
            Gdk.threads_enter()
            GObject.timeout_add(3000, self.progress_bar.hide)
            self.builder.get_object("stop-routing-button").hide()
            self.isochronesMapLayer.set_isochrones([], [])
            Gdk.threads_leave()
            return

        if res is None:
            return

        tr = []
        for wp in res.path:
            tr.append(
                (
                    wp.pos[0],
                    wp.pos[1],
                    wp.time.strftime("%m/%d/%Y, %H:%M:%S"),
                    wp.twd,
                    wp.tws,
                    wp.speed,
                    wp.brg,
                )
            )

        Gdk.threads_enter()
        self.progress_bar.set_fraction(1.0)
        self.progress_bar.set_text("100%")
        GObject.timeout_add(3000, self.progress_bar.hide)
        Gdk.threads_leave()

        self.core.routingManager.append(
            Routing(
                name=self.core.routingManager.get_unique_name(self.currentRouting.name),
                points=tr,
                isochrones=res.isochrones,
                collection=self.core.routingManager,
            )
        )
        self.update_routings()
        self.builder.get_object("stop-routing-button").hide()
        self.isochronesMapLayer.set_isochrones([], res.path)
        self.map.queue_draw()

    def update_routings(self):
        self.routingStore.clear()

        for r in self.core.routingManager:
            riter = self.routingStore.append(
                None, [r.name, "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, r.visible, False, True]
            )

            for x in r:
                self.routingStore.append(
                    riter,
                    ["", x[2], x[0], x[1], x[3], x[4], x[5], x[6], False, True, False],
                )

        self.map.queue_draw()
        self.core.trackManager.save()

    def on_routing_toggle(self, widget, i):
        self.core.routingManager[int(i)].visible = not self.core.routingManager[
            int(i)
        ].visible
        self.update_routings()
        self.update_track()

    def on_routing_name_edit(self, widget, i, name):
        self.core.routingManager[int(i)].name = utils.unique_name(
            name, self.core.routingManager
        )
        self.update_routings()

    def on_routing_remove(self, widget):
        self.core.routingManager.remove_by_name(self.selected_routing)
        self.update_routings()
        self.map.queue_draw()

    def on_routing_export(self, widget):
        routing = self.core.routingManager.get_by_name(self.selected_routing)

        if routing is None:
            return

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

            if routing.export(filepath):
                self.status_bar.push(
                    self.status_bar.get_context_id("Info"),
                    f"Saved {len(routing)} waypoints",
                )
                edialog = Gtk.MessageDialog(
                    self.parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Saved"
                )
                edialog.format_secondary_text(f"Saved {len(routing)} waypoints")
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

    def on_routing_stop(self, widget):
        self.stop_routing = True

    def on_select_routing(self, selection):
        store, pathlist = selection.get_selected_rows()
        for path in pathlist:
            tree_iter = store.get_iter(path)
            value = store.get_value(tree_iter, 0)
            self.geo_map_layer.highlight_routing(value)

            self.map.queue_draw()

            if path.get_depth() == 1:
                self.selected_routing = value

                # Show isochrones
                # routing = self.core.routingManager.get_by_name(self.selected_routing)
                # self.isochronesMapLayer.set_isochrones(routing.isochrones, None)
            else:
                self.selected_routing = None

    def on_routing_click(self, item, event):
        if (
            self.selected_routing is not None
            and event.button == 3
            and len(self.core.routingManager) > 0
        ):
            menu = self.builder.get_object("routing-item-menu")
            menu.popup(None, None, None, None, event.button, event.time)
