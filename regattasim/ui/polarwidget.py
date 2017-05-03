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
        #print (self.polar.speedTable)
        cr.set_source_rgb (1, 1, 1)
        cr.paint ()

        cr.set_line_width (1)
        cr.set_source_rgb (0, 0, 0)
        for x in self.polar.tws:# [::2]:
            print (x)
            cr.arc (0.0, 100.0, x * 3, math.radians (-180), math.radians (180.0))
            cr.stroke ()

        for x in self.polar.twa:# [::8]:
            cr.move_to (0.0, 100.0)
            cr.line_to (0 + math.sin (x) * 100.0, 100 + math.cos (x) * 100.0)
            cr.stroke ()

        cr.set_line_width (0.5)
        cr.set_source_rgb (1, 0, 0)

        for i in range (0, len (self.polar.tws), 1):
            for j in range (0, len (self.polar.twa), 1):
                cr.line_to (5 * self.polar.speedTable [j][i] * math.sin (self.polar.twa[j]), 100 + 5 * self.polar.speedTable [j][i] * math.cos (self.polar.twa[j]))
                cr.stroke ()
                cr.move_to (5 * self.polar.speedTable [j][i] * math.sin (self.polar.twa[j]), 100 + 5 * self.polar.speedTable [j][i] * math.cos (self.polar.twa[j]))


        