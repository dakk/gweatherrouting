# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
'''

from kivy_garden.mapview import MapView
import os
from kivymd.app import MDApp
from kivy.app import Builder
from .maplayers import GribMapLayer
from ...core import TimeControl

class GWeatherRoutingApp(MDApp):
	def __init__(self, core, conn):
		super(GWeatherRoutingApp, self).__init__()
		self.timeControl = TimeControl()
		self.core = core
		self.conn = conn
		
	def build(self):
		root = Builder.load_file(os.path.abspath(os.path.dirname(__file__)) + "/app.kv")
		mapView = root.ids.mapView
		mapView.add_layer(GribMapLayer(self.core.gribManager, self.timeControl))

		return root
