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
import math
import os

import gi

from gweatherrouting.core.polarmanager import PolarManager
gi.require_version("Gtk", "3.0")
try:
    gi.require_version("OsmGpsMap", "1.2")
except:
    gi.require_version("OsmGpsMap", "1.0")

from gi.repository import Gtk

from gweatherrouting.core.storage import POLAR_DIR

from .polarmanagerwindow import PolarManagerWindow
from .widgets.polar import PolarWidget

logger = logging.getLogger("gweatherrouting")


class PolarStack(Gtk.Box):
    def __init__(self, parent, core, settings_manager):
        Gtk.Widget.__init__(self)
        self.polar_manager = core.polar_manager
        self.parent = parent
        self.core = core

        # self.core.connectionManager.connect("data", self.data_handler)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            os.path.abspath(os.path.dirname(__file__)) + "/polarstack.glade"
        )
        self.builder.connect_signals(self)
        self.pack_start(self.builder.get_object("polarcontent"), True, True, 0)

        self.statusBar = self.builder.get_object("statusbar")
        
        self.polars = self.polar_manager.polars
        self.polar_manager.connect("polars-list-updated", self.polars_list_updated)

        self.boatselect = self.builder.get_object("boat-select")
        for polar in self.polars:
            self.boatselect.append_text(polar)

        self.polarWidget = PolarWidget(self.parent, self.core)
        self.table = None
        self.boatselect.set_active(0)
        

    def load_polar(self, polar_file):
        polarwidgetcontainer = self.builder.get_object("polarwidgetcontainer")
        for child in polarwidgetcontainer.get_children():
            polarwidgetcontainer.remove(child)
        self.polarWidget.load_polar(polar_file)
        polarwidgetcontainer.pack_start(self.polarWidget, True, True, 0)

        cc = self.builder.get_object("polartablecontainer")
        if self.table:
            cc.remove(self.table)

        p = self.polarWidget.polar

        if p is None:
            return

        twa_step = 1
        if len(p.twa) > 20:
            twa_step = int(len(p.twa) / 10)

        self.table = Gtk.Table(
            n_rows=len(p.tws), n_columns=len(p.twa) / twa_step, homogeneous=False
        )
        cc.pack_start(self.table, False, False, 0)

        self.table.set_col_spacings(5)
        self.table.set_row_spacings(5)

        label = Gtk.Label(str("TWA/TWS"))
        label.set_markup("<b>TWA/TWS</b>")
        self.table.attach(label, 0, 1, 0, 1)

        i = 1
        for x in p.tws:
            label = Gtk.Label()
            label.set_markup("<b>" + str(int(x)) + "</b>")
            self.table.attach(label, i, i + 1, 0, 1)
            i += 1

        i = 1

        for x in p.twa[::twa_step]:
            label = Gtk.Label()
            label.set_markup("<b>" + str(int(math.degrees(x))) + "°</b>")
            self.table.attach(label, 0, 1, i, i + 1)
            i += 1

        for i in range(0, len(p.tws), 1):
            for j in range(0, len(p.twa), twa_step):
                if len(p.speed_table[j]) <= i:
                    continue

                label = Gtk.Label(str(p.speed_table[j][i]))
                self.table.attach(
                    label, i + 1, i + 2, (j / twa_step) + 1, (j / twa_step) + 2
                )

        self.show_all()
    
    def on_boat_select(self, widget):
        polarwidgetcontainer = self.builder.get_object("polarwidgetcontainer")
        try:
            self.load_polar(self.polars[widget.get_active()])
            self.statusBar.push(0, "Polar loaded: " + widget.get_active_text())
        except:
            logger.error("Error loading polar: %s", widget.get_active_text())
            self.statusBar.push(0, "Please select add/enable a polar file by using the Polar Manager")
            return

    def on_polar_manager(self, event):
        w = PolarManagerWindow(self.core.polar_manager)
        w.show()

    def polars_list_updated(self, event):
        self.polars = self.polar_manager.polars
        self.boatselect.get_model().clear()  
        for polar in self.polars:
            self.boatselect.append_text(polar)
        self.boatselect.set_active(0)