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
import itertools
import os
import shutil

import gi
import weatherrouting

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from gweatherrouting.common import resource_path
from gweatherrouting.core import TimeControl
from gweatherrouting.core.storage import POLAR_DIR

from .timepickerdialog import TimePickerDialog
from .widgets.polar import PolarWidget

PolFileFilter = Gtk.FileFilter()
PolFileFilter.set_name("Polar file")
PolFileFilter.add_pattern("*.pol")


class RoutingWizardDialog:
    def __init__(self, core, parent):
        self.core = core
        self.polar = None

        self.paramWidgets = {}
        self.load_default_pol()
        self.polars = os.listdir(POLAR_DIR)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            resource_path("gweatherrouting.gtk", "routingwizarddialog.glade")
        )
        self.builder.connect_signals(self)

        self.dialog = self.builder.get_object("routing-wizard-dialog")
        self.dialog.set_transient_for(parent)
        self.dialog.set_default_size(800, 500)

        self.dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.dialog.add_button("Run", Gtk.ResponseType.OK)

        self.polarWidget = PolarWidget(self.dialog)
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
                e.connect("changed", self.on_param_change)
            elif p.ttype == "int":
                adj = Gtk.Adjustment(
                    value=p.value,
                    step_incr=p.step,
                    page_incr=p.step * 10.0,
                    lower=p.lower,
                    upper=p.upper,
                )
                e = Gtk.SpinButton(adjustment=adj, digits=0)
                e.connect("changed", self.on_param_change)
            elif p.ttype == "bool":
                e = Gtk.CheckButton()
                e.set_active(bool(p.value))
                e.connect("toggled", self.on_bool_param_change)
            else:
                continue

            e.set_tooltip_text(p.tooltip)
            self.paramWidgets[e] = p
            cb.add(e)

            box.add(cb)

        self.builder.get_object("router-params").show_all()

    def on_param_change(self, widget):
        p = self.paramWidgets[widget]
        p.value = float(widget.get_text())

    def on_bool_param_change(self, widget):
        p = self.paramWidgets[widget]
        p.value = widget.get_active()

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

    def add_custom_polar_file(self, polar_path):
        polar_filename = os.path.basename(polar_path)
        target_filepath = os.path.join(POLAR_DIR, polar_filename)
        shutil.copyfile(polar_path, target_filepath)
        self.polars.append(polar_filename)
        self.builder.get_object("boat-select").set_active(len(self.polars) - 1)
        self.polarWidget.set_polar(self.polar)

    def on_open(self, widget):
        parent_window = self.dialog
        dialog = Gtk.FileChooserDialog(
            "Please choose a file",
            parent_window,
            Gtk.FileChooserAction.OPEN,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )

        dialog.add_filter(PolFileFilter)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            dialog.destroy()
            shutil.copyfile(
                filepath, os.path.join(POLAR_DIR, os.path.basename(filepath))
            )
            self.polars.append(os.path.basename(filepath))
            self.boat_store.append([os.path.basename(filepath)])
            self.builder.get_object("boat-select").set_active(len(self.polars) - 1)

    def _parse_csv_floats(self, widget_id):
        """Parse a comma-separated string of floats from a GtkEntry."""
        text = self.builder.get_object(widget_id).get_text().strip()
        if not text:
            return []
        values = []
        for part in text.split(","):
            part = part.strip()
            if part:
                values.append(float(part))
        return values

    def get_comparison_scenarios(self):
        """Return a list of scenario dicts (cartesian product of enabled axes).

        Each dict has keys: time_offset_hours, wind_speed_pct,
        wind_dir_offset, polar_efficiency_pct.
        Returns an empty list if no comparison axis is enabled.
        """
        time_enabled = self.builder.get_object("compare-time-enable").get_active()
        wind_speed_enabled = self.builder.get_object(
            "compare-wind-speed-enable"
        ).get_active()
        wind_dir_enabled = self.builder.get_object(
            "compare-wind-dir-enable"
        ).get_active()
        polar_enabled = self.builder.get_object("compare-polar-enable").get_active()

        if not any([time_enabled, wind_speed_enabled, wind_dir_enabled, polar_enabled]):
            return []

        time_offsets = (
            self._parse_csv_floats("compare-time-values") if time_enabled else [0]
        )
        wind_speed_pcts = (
            self._parse_csv_floats("compare-wind-speed-values")
            if wind_speed_enabled
            else [0]
        )
        wind_dir_offsets = (
            self._parse_csv_floats("compare-wind-dir-values")
            if wind_dir_enabled
            else [0]
        )
        polar_efficiencies = (
            self._parse_csv_floats("compare-polar-values") if polar_enabled else [100]
        )

        scenarios = []
        for t, ws, wd, pe in itertools.product(
            time_offsets, wind_speed_pcts, wind_dir_offsets, polar_efficiencies
        ):
            scenarios.append(
                {
                    "time_offset_hours": t,
                    "wind_speed_pct": ws,
                    "wind_dir_offset": wd,
                    "polar_efficiency_pct": pe,
                }
            )

        return scenarios

    def load_default_pol(self):
        if not os.listdir(POLAR_DIR):
            default_polar = os.listdir(resource_path("gweatherrouting", "data/polars/"))
            for p in default_polar:
                target_filepath = os.path.join(POLAR_DIR, p)
                polar_file_path = resource_path("gweatherrouting", f"data/polars/{p}")
                shutil.copyfile(polar_file_path, target_filepath)
