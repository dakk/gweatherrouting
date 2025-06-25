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
import datetime
import os

import gi
import weatherrouting

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from gweatherrouting.common import resource_path
from gweatherrouting.core import TimeControl
from gweatherrouting.core.storage import POLAR_DIR

from .timepickerdialog import TimePickerDialog
from .widgets.polar import PolarWidget


class RoutingWizardDialog:
    def __init__(self, core, parent):
        self.core = core
        self.polar_manager = core.polar_manager
        self.polars = self.polar_manager.polars
        self.polar = None

        self.paramWidgets = {}

        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            resource_path("gweatherrouting.gtk", "routingwizarddialog.glade")
        )
        self.builder.connect_signals(self)

        self.dialog = self.builder.get_object("routing-wizard-dialog")
        self.dialog.set_transient_for(parent)
        self.dialog.set_default_size(550, 300)

        self.dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.dialog.add_button("Run", Gtk.ResponseType.OK)

        self.polarWidget = PolarWidget(self.dialog, self.core)
        self.builder.get_object("polar-container").add(self.polarWidget)

        start_store = self.builder.get_object("start-store")
        start_store.append(["First track point", "first-track-point"])
        start_store.append(["Boat position", "boat-position"])

        for p in self.core.poiManager:
            start_store.append(["POI: " + p.name, "poi-" + p.name])

        if len(self.core.trackManager) == 0:
            self.builder.get_object("start-select").set_active(1)

        self.boat_store = self.builder.get_object("boat-store")
        for polar in self.polars:
            self.boat_store.append([polar])
        self.builder.get_object("boat-select").set_active(0)

        routing_store = self.builder.get_object("routing-store")
        for r in weatherrouting.list_routing_algorithms():
            routing_store.append([r["name"]])
        self.builder.get_object("routing-select").set_active(0)

        track_poi_store = self.builder.get_object("track-poi-store")
        for r in self.core.trackManager:
            track_poi_store.append([r.name, f"track-{r.name}"])
        for r in self.core.poiManager:
            track_poi_store.append(["POI: " + r.name, f"poi-{r.name}"])
        self.builder.get_object("track-poi-select").set_active(len(track_poi_store) - 1)

        self.builder.get_object("time-entry").set_text(
            datetime.datetime.today().strftime(TimeControl.DFORMAT)
        )

        self.dialog.show_all()

    def run(self):
        return self.dialog.run()

    def response_cancel(self, widget):
        self.dialog.response(Gtk.ResponseType.CANCEL)

    def destroy(self):
        return self.dialog.destroy()

    def on_routing_algo_select(self, widget):
        ralgo = weatherrouting.list_routing_algorithms()[
            self.builder.get_object("routing-select").get_active()
        ]["class"]

        if len(ralgo.PARAMS.keys()) == 0:
            self.builder.get_object("router-params").hide()
            return

        cont = self.builder.get_object("router-params-container")

        for x in cont.get_children():
            cont.remove(x)

        box = Gtk.VBox()
        cont.add(box)

        self.paramWidgets = {}

        for x in ralgo.PARAMS:
            p = ralgo.PARAMS[x]
            cb = Gtk.HBox()

            cb.add(Gtk.Label(p.name))

            if p.ttype == "float":
                adj = Gtk.Adjustment(
                    value=p.value,
                    step_incr=p.step,
                    page_incr=p.step * 10.0,
                    lower=p.lower,
                    upper=p.upper,
                )
                e = Gtk.SpinButton(adjustment=adj, digits=p.digits)
            elif p.ttype == "int":
                adj = Gtk.Adjustment(
                    value=p.value,
                    step_incr=p.step,
                    page_incr=p.step * 10.0,
                    lower=p.lower,
                    upper=p.upper,
                )
                e = Gtk.SpinButton(adjustment=adj, digits=0)

            e.set_tooltip_text(p.tooltip)
            e.connect("changed", self.on_param_change)
            self.paramWidgets[e] = p
            cb.add(e)

            box.add(cb)

        self.builder.get_object("router-params").show_all()

    def on_param_change(self, widget):
        p = self.paramWidgets[widget]
        p.value = float(widget.get_text())

    def on_boat_select(self, widget):
        pfile = self.polars[self.builder.get_object("boat-select").get_active()]
        self.polar = weatherrouting.Polar(os.path.join(POLAR_DIR, pfile))
        self.polarWidget.set_polar(self.polar)

    def on_time_select(self, widget):
        tp = TimePickerDialog(self.dialog)
        tp.set_date_time(self.builder.get_object("time-entry").get_text())
        response = tp.run()

        if response == Gtk.ResponseType.OK:
            self.builder.get_object("time-entry").set_text(
                tp.get_date_time().strftime(TimeControl.DFORMAT)
            )

        tp.destroy()

    def get_coastline_checks(self):
        return self.builder.get_object("coastline-check").get_active()

    def get_start_datetime(self):
        return datetime.datetime.strptime(
            self.builder.get_object("time-entry").get_text(), TimeControl.DFORMAT
        )

    def get_selected_track_or_poi(self):
        s = self.builder.get_object("track-poi-select").get_active()

        if s >= len(self.core.trackManager):
            return self.core.poiManager[s - len(self.core.trackManager)]
        else:
            return self.core.trackManager[s]

    def get_selected_algorithm(self):
        return weatherrouting.list_routing_algorithms()[
            self.builder.get_object("routing-select").get_active()
        ]["class"]

    def get_selected_polar(self):
        return self.polars[self.builder.get_object("boat-select").get_active()]

    def get_selected_start_point(self):
        s = self.builder.get_object("start-select").get_active()
        if s == 0:
            return None
        elif s == 1:
            if self.core.boat_info.is_valid():
                return [self.core.boat_info.latitude, self.core.boat_info.longitude]
            else:
                return None
        else:
            s -= 2
            return self.core.poiManager[s].position
