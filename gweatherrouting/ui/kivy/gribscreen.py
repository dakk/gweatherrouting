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
import os
from kivy.lang import Builder

from kivy.properties import StringProperty, BooleanProperty, NumericProperty, ObjectProperty
from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp
from kivymd.uix.list import IRightBodyTouch, OneLineIconListItem, TwoLineIconListItem, ThreeLineAvatarIconListItem, OneLineAvatarIconListItem
from kivymd.uix.selectioncontrol import MDCheckbox

class LocalGribListItem(ThreeLineAvatarIconListItem):
	icon = StringProperty("tailwind")
	active = BooleanProperty(False)
	gribManager = ObjectProperty()

	def setEnabled(self, enabled):
		self.gribManager.changeState(self.text, enabled)

class RightCheckbox(IRightBodyTouch, MDCheckbox):
	pass 

class GribScreen(MDScreen):
	gribManager = None

	def updateLocalGribs(self):
		gribList = self.ids.gribList
		self.gribManager.refreshLocalGribs()

		for x in self.gribManager.localGribs:
		 	gribList.add_widget(LocalGribListItem(
				 text=x.name, 
				 gribManager=self.gribManager,
				 active=self.gribManager.isEnabled(x.name), 
				 secondary_text="Start at %s and is valid for %s hours" % (str(x.startTime), str(x.lastForecast)),
				 tertiary_text="Centre: %s" % x.centre
			 ))

	def on_pre_enter(self, *args):
		self.updateLocalGribs()
