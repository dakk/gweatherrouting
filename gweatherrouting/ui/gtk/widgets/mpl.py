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
from threading import Thread
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject, Gdk
import cairo
import matplotlib.pyplot as plt
import io
import numpy
import PIL


class MPLWidget(Gtk.DrawingArea):
    def __init__(self, parent):      
        self.par = parent
        super(MPLWidget, self).__init__()
 
        # self.set_size_request(-1, 30)
        self.connect("expose-event", self.expose)
    

    def expose(self, widget, event):      
        cr = widget.window.cairo_create()

        width = self.allocation.width
        height = self.allocation.height
     

    

       
