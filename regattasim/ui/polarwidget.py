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
import math
import os
import struct
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

from .. import config


class PolarWidget (Gtk.DrawingArea):
    def __init__ (self, polar):
        Gtk.DrawingArea.__init__(self)
        self.connect ('draw', self.draw)
        self.set_size_request (200, 200)
        self.polar = polar

    def draw (self, widget, cr):
        cr.set_source_rgb (1, 1, 1)
        cr.paint()

        