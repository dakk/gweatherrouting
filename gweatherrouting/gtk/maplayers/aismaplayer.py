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

import gi
import math
from ..style import *

gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.2')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap

class AISMapLayer (GObject.GObject, OsmGpsMap.MapLayer):
    def __init__ (self, core):
        GObject.GObject.__init__ (self)
        self.visible = True

    def setVisible(self, visible):
        self.visible = visible

    def do_draw (self, gpsmap, cr):
        if not self.visible:
            return 


    def do_render (self, gpsmap):
        pass

    def do_busy (self):
        return False

    def do_button_press (self, gpsmap, gdkeventbutton):
        return False

GObject.type_register (AISMapLayer)