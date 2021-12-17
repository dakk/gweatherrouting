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

import gi
import os
import json
import math
import datetime
import numpy as np
from threading import Thread
from ..timepickerdialog import TimePickerDialog

from gweatherrouting.ui.gtk.widgets.mpl import MPLWidget
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject, Gdk


TIME_UNITS = {
	'30s': 30,
	'1m': 1 * 60,
	'5m': 5 * 60,
	'15m': 15 * 60,
	'30m': 30 * 60,
	'1h': 60 * 60,
	'3h': 180 * 60,
	'6h': 360 * 60,
	'12h': 720 * 60,
	'1d': 1440 * 60
}

class TimeTravelWidget(Gtk.Box):
	def __init__(self, parent, timeControl, map, smallerUnit = False):  
		super(TimeTravelWidget, self).__init__()
			
		self.play = False
		self.par = parent
		self.timeControl = timeControl
		self.map = map

		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.abspath(os.path.dirname(__file__)) + "/timetravel.glade")
		self.builder.connect_signals(self)

		self.pack_start(self.builder.get_object('timetravel'), True, True, 0)

		self.show_all()

		# self.timeAdjust = self.builder.get_object('time-adjustment')
		self.timeLabel = self.builder.get_object('time-label')
		self.timeUnitCombo = self.builder.get_object('time-unit-combo')
		self.timeControl.connect('time-change', self.onTimeChange)
		self.onTimeChange(self.timeControl.time)

		self.seconds = smallerUnit
		if smallerUnit:
			self.timeUnitCombo.set_active(0)
		else:
			self.timeUnitCombo.set_active(3)

	def getChangeUnit(self):
		return self.seconds

	def onTimeUnitComboChange(self, widget):
		u = self.timeUnitCombo.get_active_text()
		self.seconds = TIME_UNITS[u]


	def onTimeChange(self, t):
		self.timeLabel.set_text("%s" % str(t))
		self.map.queue_draw ()

	def onTimeNow(self, event):
		self.timeControl.now()

	def onPlayClick(self, event):
		self.play = True
		GObject.timeout_add (10, self.onPlayStep)

	def onPlayStep(self):
		self.onFowardClick(None)
		if self.play:
			GObject.timeout_add (1000, self.onPlayStep)

	def onStopClick(self, event):
		self.play = False

	def onFowardClick(self, event):
		self.timeControl.increase(seconds=self.seconds)
		self.map.queue_draw ()

	def onBackwardClick(self, event):
		# if self.timeControl.time > 0:
		self.timeControl.decrease(seconds=self.seconds)

	def onTimeSelect(self, event):
		tp = TimePickerDialog.create(self.window)
		tp.setFromDateTime(self.timeControl.time)
		response = tp.run()

		if response == Gtk.ResponseType.OK:
			self.timeControl.setTime(tp.getDateTime())
		
		tp.destroy()


	# def updateTimeSlider(self):
	# 	self.timeAdjust.set_value(int(self.timeControl.time))

	def onTimeSlide (self, widget):
		self.timeControl.setTime(int (self.timeAdjust.get_value()))
		self.map.queue_draw ()