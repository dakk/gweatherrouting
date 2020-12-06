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
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject

class AboutDialog (Gtk.Dialog):
	def __init__(self, parent):
		Gtk.Dialog.__init__(self, "About", parent, 0, (Gtk.STOCK_OK, Gtk.ResponseType.OK))

		box = self.get_content_area ()

		boxcontent = Gtk.Box (orientation=Gtk.Orientation.VERTICAL)
		box.pack_start (boxcontent, True, True, 10)

		boxcontent.pack_start (Gtk.Label ("gweatherrouting is created by Davide Gessa and Riccardo Apolloni.\nThe software is released under the GNU General Public License version 3"), True, True, 10)

		textview = Gtk.TextView ()
		textbuffer = textview.get_buffer ()
		textbuffer.set_text("""Copyright (C) 2017-2021 Davide Gessa
Copyright (C) 2012 Riccardo Apolloni
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.""")

		boxcontent.pack_start (textview, True, True, 10)

		self.show_all ()

