# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
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
import math
from kivy.graphics import (
	Canvas,
	Color,
	Line,
	Rectangle,
	Triangle,
	MatrixInstruction,
	Mesh,
	PopMatrix,
	PushMatrix,
	Scale,
	Translate,
)
from kivy.core.text import Label as CoreLabel
from kivy.graphics.tesselator import TYPE_POLYGONS, WINDING_ODD, Tesselator
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.utils import get_color_from_hex

from kivy_garden.mapview.constants import CACHE_DIR
from kivy_garden.mapview.downloader import Downloader
from kivy_garden.mapview.view import MapLayer

from ...common import windColor


class POIMapLayer(MapLayer):
	def __init__(self, poiManager, timeControl, **kwargs):
		super().__init__(**kwargs)
		self.poiManager = poiManager
		self.timeControl = timeControl
		self.timeControl.connect("time-change", self.onTimeChange)

	def onTimeChange(self, t):
		self.draw()

	def reposition(self):
		"""Function called when :class:`MapView` is moved. You must recalculate
		the position of your children."""
		self.draw()

	def unload(self):
		""" Called when the view want to completly unload the layer. """
		pass

	def draw(self):
		view = self.parent
		zoom = view.zoom
		bbox = view.get_bbox()
		self.canvas.clear()

		for tr in self.poiManager.pois:
			if not tr.visible:
				continue

			x, y = view.get_window_xy_from(tr.position[0], tr.position[1], zoom)

			# self.canvas.add(Color(1-self.colour, self.colour, 0, 1))
			# self.rect = Rectangle(size=self.size, pos=self.pos)
			# self.canvas.add(self.rect)
			self.canvas.add(Color(1, 1, 1))
			label = CoreLabel(text=tr.name, font_size=16)
			label.refresh()
			text = label.texture
			self.canvas.add(Rectangle(size=text.size, pos=[x - 20, y - 20], texture=text))
			# self.canvas.ask_update()

			# self.canvas.add(Triangle([x - 5, y - 5, x, y + 5, x + 5, y - 5]))

			# Style.Poi.Font.apply(cr)
			# cr.move_to(x - 10, y - 10)
			# cr.show_text(tr.name)
			# cr.stroke()

			# Style.Poi.Triangle.apply(cr)

			self.canvas.add(Line(points=[x - 5, y - 5, x, y + 5]))
			self.canvas.add(Line(points=[x + 5, y - 5, x, y + 5]))
			self.canvas.add(Line(points=[x - 5, y - 5, x + 5, y - 5]))
