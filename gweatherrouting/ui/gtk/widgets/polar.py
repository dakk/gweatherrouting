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

from gweatherrouting.ui.gtk.widgets.mpl import MPLWidget
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject, Gdk

class PolarWidget(Gtk.DrawingArea):
	def __init__(self, parent):      
		self.par = parent
		super(PolarWidget, self).__init__()
 
		self.set_size_request(60,180)
		self.connect("draw", self.draw)
		self.polar = None
	
	def setPolar(self, polar):
		self.polar = polar
		self.queue_draw()


	def draw(self, area, cr):  
		if not self.polar:
			return
	
		# width = self.allocation.width
		# height = self.allocation.height

		cr.set_source_rgb (0.3, 0.3, 0.3)
		cr.paint ()

		cr.set_line_width (0.3)
		cr.set_source_rgb (1, 1, 1)

		for x in self.polar.tws:
			cr.arc (100.0, 100.0, x * 3, math.radians (-90), math.radians (90.0))
			cr.stroke ()

		for x in self.polar.tws:
			cr.set_source_rgb (1, 1, 1)
			cr.set_font_size (7)
			cr.move_to (80.0, 100.0 - x*3)
			cr.show_text (str (x))

		cr.set_source_rgba (1, 1, 1, 0.6)

		for x in self.polar.twa:
			cr.move_to (100.0, 100.0)
			cr.line_to (100 + math.sin (x) * 100.0, 100 - math.cos (x) * 80.0)
			cr.stroke ()

		for x in self.polar.twa:
			cr.set_source_rgb (1, 1, 1)
			cr.set_font_size (7)
			cr.move_to (100 + math.sin (x) * 100.0, 100 - math.cos (x) * 90.0)
			cr.show_text (str (int(math.degrees(x))) + '°')

		# for x in self.polar.twa:
		# 	cr.move_to (100.0, 100.0)
		# 	cr.line_to (100 - math.sin (x) * 100.0, 100 + math.cos (x) * 100.0)
		# 	cr.stroke ()

		cr.set_line_width (0.5)
		cr.set_source_rgb (1, 0, 0)

		cr.move_to (100.0, 100.0)
		for i in range (0, len (self.polar.tws), 1):
			for j in range (0, len (self.polar.twa), 1):
				cr.line_to (100 + 5 * self.polar.speedTable [j][i] * math.sin (self.polar.twa[j]), 100 - 5 * self.polar.speedTable [j][i] * math.cos (self.polar.twa[j]))
				cr.stroke ()
				cr.move_to (100 + 5 * self.polar.speedTable [j][i] * math.sin (self.polar.twa[j]), 100 - 5 * self.polar.speedTable [j][i] * math.cos (self.polar.twa[j]))


		# cr.move_to (100.0, 100.0)
		# for i in range (0, len (self.polar.tws), 1):
		# 	for j in range (0, len (self.polar.twa), 1):
		# 		cr.line_to (100 - 5 * self.polar.speedTable [j][i] * math.sin (self.polar.twa[j]), 100 - 5 * self.polar.speedTable [j][i] * math.cos (self.polar.twa[j]))
		# 		cr.stroke ()
		# 		cr.move_to (100 - 5 * self.polar.speedTable [j][i] * math.sin (self.polar.twa[j]), 100 - 5 * self.polar.speedTable [j][i] * math.cos (self.polar.twa[j]))

		cr.scale(0.8, 0.8)