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
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from gweatherrouting.core import SerialDataSource

ctypes = ["Network", "Serial"]
ntypes = ["TCP", "UDP"]
directions = ["In", "Out", "Both"]
protocols = ["NMEA0183"]
baudrates = [9600, 19200, 38400, 57600, 115200]


def lower(s):
    return s.lower()


class ConnectionEditDialog:
    def __init__(self, parent, data=None):
        self.parent = parent
        self.data = data
        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            os.path.abspath(os.path.dirname(__file__)) + "/connectioneditdialog.glade"
        )
        self.builder.connect_signals(self)

        self.dialog = self.builder.get_object("connection-edit-dialog")
        self.dialog.set_transient_for(parent)
        self.dialog.set_default_size(550, 300)

        self.dialog.show_all()

        self.builder.get_object("network-frame").hide()
        self.typeCombo = self.builder.get_object("type-combo")
        for x in ctypes:
            self.typeCombo.append_text(x)
        self.typeCombo.set_active(1)

        self.networkTypeCombo = self.builder.get_object("network-type-combo")
        for x in ntypes:
            self.networkTypeCombo.append_text(x)
        self.networkTypeCombo.set_active(0)

        self.directionCombo = self.builder.get_object("direction-combo")
        for x in directions:
            self.directionCombo.append_text(x)
        self.directionCombo.set_active(0)

        self.protocolCombo = self.builder.get_object("protocol-combo")
        for x in protocols:
            self.protocolCombo.append_text(x)
        self.protocolCombo.set_active(0)

        self.serialDataPortCombo = self.builder.get_object("serial-data-port-combo")
        for x in SerialDataSource.detect():
            self.serialDataPortCombo.append_text(x)
        self.serialDataPortCombo.set_active(0)

        self.serialBaudrateCombo = self.builder.get_object("serial-baudrate-combo")
        for xb in baudrates:
            self.serialBaudrateCombo.append_text(str(xb))
        self.serialBaudrateCombo.set_active(0)

        if self.data is not None:
            # Set data
            if self.data["type"] == "serial":
                self.typeCombo.set_active(0)
                self.builder.get_object("serial-data-port").set_text(
                    self.data["data-port"]
                )
                self.serialBaudrateCombo.set_active(
                    list(map(lower, baudrates)).index(self.data["baudrate"])
                )
            elif self.data["type"] == "network":
                self.typeCombo.set_active(1)
                self.networkTypeCombo.set_active(
                    list(map(lower, ntypes)).index(self.data["network"])
                )
                self.builder.get_object("network-host").set_text(self.data["host"])
                self.builder.get_object("network-port").set_text(str(self.data["port"]))
            self.protocolCombo.set_active(
                list(map(lower, protocols)).index(self.data["protocol"])
            )
            self.directionCombo.set_active(
                list(map(lower, directions)).index(self.data["direction"])
            )

    def run(self):
        return self.dialog.run()

    def destroy(self):
        return self.dialog.destroy()

    def on_type_change(self, widget):
        if self.typeCombo.get_active() == 0:
            self.builder.get_object("network-frame").show()
            self.builder.get_object("serial-frame").hide()
        else:
            self.builder.get_object("network-frame").hide()
            self.builder.get_object("serial-frame").show()

    def save_data(self):
        self.data = {
            "type": lower(self.typeCombo.get_active_text()),
            "protocol": lower(self.protocolCombo.get_active_text()),
            "direction": lower(self.directionCombo.get_active_text()),
        }
        if self.data["type"] == "serial":
            self.data["data-port"] = self.serialDataPortCombo.get_active_text()
            self.data["baudrate"] = int(self.serialBaudrateCombo.get_active_text())
        elif self.data["type"] == "network":
            self.data["network"] = lower(self.networkTypeCombo.get_active_text())
            self.data["host"] = self.builder.get_object("network-host").get_text()
            self.data["port"] = int(self.builder.get_object("network-port").get_text())

    def on_save(self, widget):
        try:
            self.save_data()
            self.dialog.response(Gtk.ResponseType.OK)
        except:
            dialog = Gtk.MessageDialog(
                self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error"
            )
            dialog.format_secondary_text("Invalid data")
            dialog.run()
            dialog.destroy()

    def on_close(self, widget):
        self.dialog.response(Gtk.ResponseType.CANCEL)
