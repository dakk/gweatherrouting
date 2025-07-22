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
try:
    gi.require_version("OsmGpsMap", "1.2")
except ValueError:
    gi.require_version("OsmGpsMap", "1.0")
from gi.repository import GObject, Gtk, OsmGpsMap

from gweatherrouting.core import TimeControl
from gweatherrouting.gtk.timepickerdialog import TimePickerDialog

TIME_UNITS = {
    "30s": 30,
    "1m": 1 * 60,
    "5m": 5 * 60,
    "15m": 15 * 60,
    "30m": 30 * 60,
    "1h": 60 * 60,
    "3h": 180 * 60,
    "6h": 360 * 60,
    "12h": 720 * 60,
    "24h": 1440 * 60,
    "1d": 1440 * 60,
}


class TimeTravelWidget(Gtk.Box):
    def __init__(
        self,
        parent: Gtk.Window,
        time_control: TimeControl,
        map: OsmGpsMap,
        smaller_unit=False,
    ):
        super(TimeTravelWidget, self).__init__()

        self.play = False
        self.parent = parent
        self.time_control = time_control
        self.map = map

        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            os.path.abspath(os.path.dirname(__file__)) + "/timetravel.glade"
        )
        self.builder.connect_signals(self)

        self.pack_start(self.builder.get_object("timetravel"), True, True, 0)

        self.show_all()

        # self.timeAdjust = self.builder.get_object('time-adjustment')
        self.timeLabel = self.builder.get_object("time-label")
        self.timeUnitCombo = self.builder.get_object("time-unit-combo")
        self.time_control.connect("time_change", self.on_time_change)
        self.on_time_change(self.time_control.time)

        self.seconds = smaller_unit
        if smaller_unit:
            self.timeUnitCombo.set_active(2)
        else:
            self.timeUnitCombo.set_active(3)

    def get_change_unit(self):
        return self.seconds

    def on_time_unit_combo_change(self, widget):
        u = self.timeUnitCombo.get_active_text()
        self.seconds = TIME_UNITS[u]

    def on_time_change(self, t):
        self.timeLabel.set_text("%s" % str(t))
        self.map.queue_draw()

    def on_time_now(self, event):
        self.time_control.now()

    def on_play_click(self, event):
        self.play = True
        GObject.timeout_add(10, self.on_play_step)

    def on_play_step(self):
        self.on_foward_click(None)
        if self.play:
            GObject.timeout_add(1000, self.on_play_step)

    def on_stop_click(self, event):
        self.play = False

    def on_foward_click(self, event):
        self.time_control.increase(seconds=self.seconds)
        self.map.queue_draw()

    def on_backward_click(self, event):
        # if self.time_control.time > 0:
        self.time_control.decrease(seconds=self.seconds)

    def on_time_select(self, event):
        tp = TimePickerDialog(self.parent)
        tp.set_from_date_time(self.time_control.time)
        response = tp.run()

        if response == Gtk.ResponseType.OK:
            self.time_control.set_time(tp.get_date_time())

        tp.destroy()

    # def updateTimeSlider(self):
    # 	self.timeAdjust.set_value(int(self.time_control.time))

    def on_time_slide(self, widget):
        self.time_control.set_time(int(self.timeAdjust.get_value()))
        self.map.queue_draw()
