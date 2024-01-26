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
from threading import Thread

import gi

from .connectioneditdialog import ConnectionEditDialog

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class ConnectionListBoxRow(Gtk.ListBoxRow):
    def __init__(self, data):
        super().__init__()
        self.data = data

        label = Gtk.Label()

        if self.data["type"] == "serial":
            label.set_markup(
                "<b>Serial [{}, {}]</b> Port: {} (Baudrate: {})".format(
                    data["protocol"],
                    data["direction"],
                    data["data-port"],
                    data["baudrate"],
                )
            )
        elif self.data["type"] == "network":
            label.set_markup(
                "<b>Network [{}, {}]</b> Host: {} (Port: {})".format(
                    data["protocol"], data["direction"], data["host"], data["port"]
                )
            )

        self.add(label)


class SettingsWindowConnections:
    def __init__(self, parent, settingsManager, core):
        self.selectedConnection = None
        self.connectionListBox = self.builder.get_object("connections-listbox")
        self.reloadConnections()

    def reloadConnections(self):
        self.connectionListBox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        for x in self.connectionListBox.get_children():
            self.connectionListBox.remove(x)

        for c in self.core.connectionManager.connections:
            clbr = ConnectionListBoxRow(c)
            self.connectionListBox.add(clbr)
        self.connectionListBox.show_all()

    def onAddConnection(self, widget):
        d = ConnectionEditDialog(self.window, None)
        d.run()
        data = d.data
        d.destroy()
        if data is not None:
            self.core.connectionManager.addConnection(data)
        self.reloadConnections()

    def onConnectionRemove(self, widget):
        if self.selectedConnection is not None:
            self.core.connectionManager.removeConnection(self.selectedConnection.data)
            self.reloadConnections()

    def onConnectionSelected(self, widget, sel):
        self.selectedConnection = sel

    def onConnectionEdit(self, widget):
        d = ConnectionEditDialog(self.window)
        d.run()
        data = d.data
        d.destroy()
        if data is not None:
            self.core.connectionManager.editConnection(data)

    def onConnectionClick(self, widget, event):
        if event.button == 3:
            menu = self.builder.get_object("connection-menu")
            menu.popup(None, None, None, None, event.button, event.time)
