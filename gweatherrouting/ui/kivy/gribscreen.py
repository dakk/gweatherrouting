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
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import IRightBodyTouch, OneLineIconListItem, TwoLineIconListItem, ThreeLineAvatarIconListItem, OneLineAvatarIconListItem
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.boxlayout import MDBoxLayout
from threading import Thread

class RemoteGribListItem(ThreeLineAvatarIconListItem):
	callback = ObjectProperty(None)
	url = StringProperty('')

class LocalGribListItem(ThreeLineAvatarIconListItem):
	icon = StringProperty("tailwind")
	active = BooleanProperty(False)
	gribManager = ObjectProperty()
	updateCallback = ObjectProperty()

	def setEnabled(self, enabled):
		self.gribManager.changeState(self.text, enabled)

	def remove(self):
		self.gribManager.remove(self.text)
		self.updateCallback()

class RightBody(IRightBodyTouch, MDBoxLayout):
	pass 

class GribScreen(MDScreen):
	gribManager = None
	gribDownloadDialog = None

	def updateLocalGribs(self):
		gribList = self.ids.gribList
		gribList.clear_widgets()
		self.gribManager.refreshLocalGribs()

		for x in self.gribManager.localGribs:
		 	gribList.add_widget(LocalGribListItem(
				 text=x.name, 
				 updateCallback=self.updateLocalGribs,
				 gribManager=self.gribManager,
				 active=self.gribManager.isEnabled(x.name), 
				 secondary_text="Start at %s and is valid for %s hours" % (str(x.startTime), str(x.lastForecast)),
				 tertiary_text="Centre: %s" % x.centre
			 ))

	def on_pre_enter(self, *args):
		self.updateLocalGribs()

	def onSelectRemoteGrib(self, uri):
		self.gribDownloadDialog.dismiss()
		self.ids.downloadProgress.value = 0

		def onGribDownloadPercentage(percentage):
			self.ids.downloadProgress.value = percentage

		def onGribDownloadCompleted(g):
			self.updateLocalGribs()
		
		t = Thread(target=self.gribManager.download, args=(uri, onGribDownloadPercentage, onGribDownloadCompleted,))
		t.start ()


	def openGribDownloadDialog(self):
		if not self.gribDownloadDialog:
			items = []

			for x in self.gribManager.getDownloadList():
				items.append(RemoteGribListItem(
					text=x[0],
					secondary_text="Start at %s, %s" % (str(x[3]), str(x[2])),
					tertiary_text="Centre: %s" % x[1],
					url=x[4],
					callback=self.onSelectRemoteGrib
				))
			
			self.gribDownloadDialog = MDDialog(
				title="Download a GRIB",
				type="simple",
				items=items
			)

		self.gribDownloadDialog.open()

	def openFileChooserDialog(self):
		pass 