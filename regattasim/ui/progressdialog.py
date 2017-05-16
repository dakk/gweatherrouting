# -*- coding: utf-8 -*-
# Copyright (C) 2017 Davide Gessa
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
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject

class ProgressDialog (Gtk.Dialog):
	def __init__(self, parent, title, description):
		Gtk.Dialog.__init__(self, title, parent, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

		box = self.get_content_area ()

		boxcontent = Gtk.Box (orientation=Gtk.Orientation.VERTICAL)
		box.pack_start (boxcontent, True, True, 10)

        self.progress = Gtk.ProgressBar ()
        boxcontent.pack_start (self.progress, True, True, 10)

		self.show_all ()


    def setProgress (self, percentage, label):
        self.progress.set_value (percentage)

        if percentage >= 100:
            self.destroy ()