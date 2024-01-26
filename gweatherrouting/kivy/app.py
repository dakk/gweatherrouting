# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
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

from kivy.app import Builder

# from kivy_garden.mapview import MapView
from kivymd.app import MDApp

from ..core import TimeControl
from .maplayers import GribMapLayer, POIMapLayer, TrackMapLayer
from .timepickerdialog import TimePickerDialog


class GWeatherRoutingApp(MDApp):
    def __init__(self, core):
        super(GWeatherRoutingApp, self).__init__()
        self.timeControl = TimeControl()
        self.core = core

    def build(self):
        strs = [
            "gribscreen.kv",
            "trackscreen.kv",
            "regattascreen.kv",
            "settingsscreen.kv",
            "timepickerdialog.kv",
            "app.kv",
        ]

        ss = ""
        for x in strs:
            f = open(os.path.abspath(os.path.dirname(__file__)) + "/" + x, "r")
            ss += f.read() + "\n"
            f.close()

        # self.root = Builder.load_file(os.path.abspath(os.path.dirname(__file__)) + "/app.kv")
        self.root = Builder.load_string(ss)
        return self.root

    def on_start(self):
        # Setup map
        self.root.ids.mapView.add_layer(
            GribMapLayer(self.core.gribManager, self.timeControl)
        )
        self.root.ids.mapView.add_layer(
            POIMapLayer(self.core.poiManager, self.timeControl)
        )
        self.root.ids.mapView.add_layer(
            TrackMapLayer(self.core.trackManager, self.timeControl)
        )

        # Setup grib
        self.root.ids.gribScreen.gribManager = self.core.gribManager
        # self.root.ids.gribScreen.updateLocalGribs()

        self.root.ids.trackScreen.trackManager = self.core.trackManager
        self.root.ids.trackScreen.poiManager = self.core.poiManager

    def onMapTouchDown(self, k):
        # print (k)
        # TODO: open an menu with add poi / point to track
        pass

    def onForwardClick(self, hours):
        self.timeControl.increase(hours=hours)
        self.root.ids.timeLabel.text = str(self.timeControl.time)

    def onBackwardClick(self, hours):
        self.timeControl.decrease(hours=hours)
        self.root.ids.timeLabel.text = str(self.timeControl.time)

    def openTimePickerDialog(self):
        dialog = TimePickerDialog(self.timeControl.time)
        dialog.open()
