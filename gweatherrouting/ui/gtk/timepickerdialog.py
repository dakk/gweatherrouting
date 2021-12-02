# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
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

import gi
import os
import datetime
import dateutil.parser

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class TimePickerDialog:
	def create(parent):
		return TimePickerDialog(parent)

	def __init__(self, parent):
		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.abspath(os.path.dirname(__file__)) + "/timepickerdialog.glade")
		self.builder.connect_signals(self)

		self.dialog = self.builder.get_object("time-picker-dialog")
		self.dialog.set_transient_for(parent)
		self.dialog.set_title("Time Picker")
		# self.dialog.set_default_size (550, 300)

		self.year = self.builder.get_object("year")
		self.month = self.builder.get_object("month")
		self.day = self.builder.get_object("day")
		self.hour = self.builder.get_object("hour")
		self.minute = self.builder.get_object("minute")

		self.dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
		self.dialog.add_button("Set", Gtk.ResponseType.OK)

		self.dialog.show_all()

	def setDateTime(self, date):
		d = dateutil.parser.parse(date)
		self.setFromDateTime(d)

	def setFromDateTime(self, d):
		self.year.set_text(str(d.year))
		self.month.set_text(str(d.month))
		self.day.set_text(str(d.day))
		self.hour.set_text(str(d.hour))
		self.minute.set_text(str(d.minute))

	def getDateTime(self):
		return datetime.datetime(int(self.year.get_text()), int(self.month.get_text()), int(self.day.get_text()), int(self.hour.get_text()), int(self.minute.get_text()))

	def run(self):
		return self.dialog.run()

	def responseCancel(self, widget):
		self.dialog.response(Gtk.ResponseType.CANCEL)

	def destroy(self):
		return self.dialog.destroy()
