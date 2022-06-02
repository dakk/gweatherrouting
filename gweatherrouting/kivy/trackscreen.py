# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
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
from kivy.properties import BooleanProperty, ObjectProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import IRightBodyTouch, TwoLineIconListItem
from kivymd.uix.selectioncontrol import MDCheckbox

class TrackListItem(TwoLineIconListItem):
	visible = BooleanProperty(False)
	trackManager = ObjectProperty()

	# def setVisibility(self, enabled):
	# 	self.gribManager.changeState(self.text, enabled)

class POIListItem(TwoLineIconListItem):
	visible = BooleanProperty(False)
	poiManager = ObjectProperty()

class RightCheckbox(IRightBodyTouch, MDCheckbox):
	pass 

class TrackScreen(MDScreen):
	trackManager = None
	poiManager = None

	def updateTracksAndPois(self):
		trackList = self.ids.trackList

		for x in self.trackManager:
		 	trackList.add_widget(TrackListItem(
				 text=x.name, 
				 trackManager=self.trackManager,
				 visible=x.visible,
				 secondary_text="Distance of %f nm, with %d track points" % (x.length(), len(x.waypoints))
			 ))

		for x in self.poiManager:
		 	trackList.add_widget(POIListItem(
				 text=x.name, 
				 poiManager=self.poiManager,
				 visible=x.visible,
				 secondary_text="Latitude: %f, Longitude: %f" % (x.position[0], x.position[1])
			 ))

	def on_pre_enter(self, *args):
		self.updateTracksAndPois()
