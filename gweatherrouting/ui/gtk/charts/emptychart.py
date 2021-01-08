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

class EmptyChart:
	def __init__(self):
		pass

	def do_draw(self, gpsmap, cr):
		width = float (gpsmap.get_allocated_width ())
		height = float (gpsmap.get_allocated_height ())
		cr.set_source_rgba(32/255, 125/255, 150/255, 1.0)
		cr.rectangle(0, 0, width, height)
		cr.stroke_preserve()
		cr.fill()

	def do_render(self, gpsmap):
		pass

	def do_busy(self):
		return False

	def do_button_press(self, gpsmap, gdkeventbutton):
		return False
