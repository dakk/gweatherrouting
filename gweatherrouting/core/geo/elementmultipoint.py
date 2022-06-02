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
from .element import Element

class ElementMultiPoint(Element):
	def __init__(self, name, points = [], visible = True, collection = None):
		super().__init__(name, visible, collection)
		self.points = points

	def toGPXObject(self):
		raise Exception("Not implemented")

	def toJSON(self):
		c = super().toJSON()
		c['points'] = self.points
		return c

	@staticmethod
	def fromJSON(j):
		d = super().fromJSON(j)
		d.points = j['points']
		return d

	def __len__(self):
		return len(self.points)

	def __getitem__(self, key):
		return self.points[key]

	def __setitem__(self, key, value):
		self.points[key] = value

	def __delitem__(self, key):
		del self.points[key]

	def __iter__(self):
		return iter(self.points)
