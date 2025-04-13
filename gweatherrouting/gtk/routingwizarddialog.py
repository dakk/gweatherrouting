# -*- coding: utf-8 -*-
# Copyright (C) 2017-2024 Davide Gessa
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
import datetime
import os

import gi

gi.require_version("Gtk", "3.0")
import weatherrouting
from gi.repository import Gtk

from gweatherrouting.common import resource_path

from ..core import TimeControl
from .timepickerdialog import TimePickerDialog
from .widgets.polar import PolarWidget


class RoutingWizardDialog:
    def __init__(self, core, parent):
        self.core = core
        self.polar = None

        self.paramWidgets = {}
        self.polars = os.listdir(resource_path("gweatherrouting", "data/polars/"))

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

        self.polarWidget = PolarWidget(self.dialog)
        self.builder.get_object("polar-container").add(self.polarWidget)

        start_store = self.builder.get_object("start-store")
        start_store.append(["First track point", "first-track-point"])
        start_store.append(["Boat position", "boat-position"])

        for p in self.core.poiManager:
            start_store.append(["POI: " + p.name, "poi-" + p.name])
        self.builder.get_object("start-select").set_active(0)

        boat_store = self.builder.get_object("boat-store")
        for polar in self.polars:
            boat_store.append([polar])
        self.builder.get_object("boat-select").set_active(0)

        routing_store = self.builder.get_object("routing-store")
        for r in weatherrouting.listRoutingAlgorithms():
            routing_store.append([r["name"]])
        self.builder.get_object("routing-select").set_active(0)

        track_store = self.builder.get_object("track-store")
        for r in self.core.trackManager:
            track_store.append([r.name])
        self.builder.get_object("track-select").set_active(0)

        self.builder.get_object("time-entry").set_text(
            datetime.datetime.today().strftime(TimeControl.DFORMAT)
        )

        self.dialog.show_all()

    def run(self):
        return self.dialog.run()

    def responseCancel(self, widget):
        self.dialog.response(Gtk.ResponseType.CANCEL)

    def destroy(self):
        return self.dialog.destroy()

    def onRoutingAlgoSelect(self, widget):
        ralgo = weatherrouting.listRoutingAlgorithms()[
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
            e.connect("changed", self.onParamChange)
            self.paramWidgets[e] = p
            cb.add(e)

            box.add(cb)

        self.builder.get_object("router-params").show_all()

    def onParamChange(self, widget):
        p = self.paramWidgets[widget]
        p.value = float(widget.get_text())

    def onBoatSelect(self, widget):
        pfile = self.polars[self.builder.get_object("boat-select").get_active()]
        self.polar = weatherrouting.Polar(
            resource_path("gweatherrouting", f"data/polars/{pfile}")
        )
        self.polarWidget.setPolar(self.polar)

    def onTimeSelect(self, widget):
        tp = TimePickerDialog(self.dialog)
        tp.setDateTime(self.builder.get_object("time-entry").get_text())
        response = tp.run()

        if response == Gtk.ResponseType.OK:
            self.builder.get_object("time-entry").set_text(
                tp.getDateTime().strftime(TimeControl.DFORMAT)
            )

        tp.destroy()

    def getCoastlineChecks(self):
        return self.builder.get_object("coastline-check").get_active()

    def getStartDateTime(self):
        return datetime.datetime.strptime(
            self.builder.get_object("time-entry").get_text(), TimeControl.DFORMAT
        )

    def getSelectedTrack(self):
        return self.core.trackManager[
            self.builder.get_object("track-select").get_active()
        ]

    def getSelectedAlgorithm(self):
        return weatherrouting.listRoutingAlgorithms()[
            self.builder.get_object("routing-select").get_active()
        ]["class"]

    def getSelectedPolar(self):
        return self.polars[self.builder.get_object("boat-select").get_active()]

    def getSelectedStartPoint(self):
        s = self.builder.get_object("start-select").get_active()
        if s == 0:
            return None
        elif s == 1:
            if self.core.boatInfo.isValid():
                return [self.core.boatInfo.latitude, self.core.boatInfo.longitude]
            else:
                return None
        else:
            s -= 2
            return self.core.poiManager[s].position
