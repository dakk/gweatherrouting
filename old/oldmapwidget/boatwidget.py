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
import math
import os
import struct
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

from .. import config


class BoatWidget (Gtk.DrawingArea):
    def __init__ (self):
        Gtk.DrawingArea.__init__(self)
        self.connect ('draw', self.draw)
        self.set_size_request (200, 200)
        self.boat = None

    def update (self, boat):
        self.queue_draw ()
        self.boat = boat

    def draw (self, widget, cr):
        cr.set_source_rgb (1, 1, 1)
        cr.paint()

        if self.boat:
            cr.rotate (self.boat.getHDG ())

        # Draw boat
        cr.set_line_width (0.5)
        cr.set_source_rgb (1,0,0)

        cr.curve_to (100.0,20.0, 50.0,60.0, 70.0,150.0)
        cr.stroke ()
        cr.curve_to (100.0,20.0, 150.0,60.0, 130.0,150.0)
        cr.stroke ()
        cr.move_to (70.0, 150.0)
        cr.line_to (130.0, 150.0)
        cr.stroke ()
        
        if self.boat:
            # Draw mainsail
            ms = self.boat.getMainsail ()

            # Draw jib
            jib = self.boat.getJib ()
        