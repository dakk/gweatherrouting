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

from kivy.graphics import Color, Line

# from kivy.graphics.tesselator import TYPE_POLYGONS, WINDING_ODD, Tesselator
# from kivy.metrics import dp
# from kivy.properties import ObjectProperty, StringProperty
# from kivy.utils import get_color_from_hex
# from kivy_garden.mapview.constants import CACHE_DIR
# from kivy_garden.mapview.downloader import Downloader
from kivy_garden.mapview.view import MapLayer

from ...common import windColor


class GribMapLayer(MapLayer):
    def __init__(self, gribManager, timeControl, **kwargs):
        super().__init__(**kwargs)
        self.gribManager = gribManager
        self.timeControl = timeControl
        self.timeControl.connect("time-change", self.onTimeChange)
        self.arrowOpacity = 0.3

    def onTimeChange(self, t):
        self.draw()

    def reposition(self):
        """Function called when :class:`MapView` is moved. You must recalculate
        the position of your children."""
        self.draw()

    def unload(self):
        """Called when the view want to completly unload the layer."""
        pass

    def drawWindArrow(self, x, y, wdir, wspeed):
        wdir = -math.radians(wdir)

        a, b, c = windColor(wspeed)

        length = 25
        RD = 30
        self.canvas.add(Color(a, b, c, self.arrowOpacity))

        xy = [x, y, x + (length * math.sin(wdir)), y + (length * math.cos(wdir))]
        self.canvas.add(Line(points=xy, width=1.5))

        xy = [
            x + (length * math.sin(wdir)),
            y + (length * math.cos(wdir)),
            x + (4 * math.sin(wdir - math.radians(RD))),
            y + (4 * math.cos(wdir - math.radians(RD))),
        ]
        self.canvas.add(Line(points=xy, width=1.5))

        xy = [
            x + (length * math.sin(wdir)),
            y + (length * math.cos(wdir)),
            x + (4 * math.sin(wdir + math.radians(RD))),
            y + (4 * math.cos(wdir + math.radians(RD))),
        ]
        self.canvas.add(Line(points=xy, width=1.5))

    def draw(self):  # noqa: C901
        view = self.parent
        zoom = view.zoom
        bbox = view.get_bbox()

        p1lat, p1lon, p2lat, p2lon = bbox

        bounds = (
            (min(p1lat, p2lat), min(p1lon, p2lon)),
            (max(p1lat, p2lat), max(p1lon, p2lon)),
        )
        data = self.gribManager.getWind2D(self.timeControl.time, bounds)

        self.canvas.clear()

        if not data or len(data) == 0:
            return

        # scale = int(math.fabs(zoom - 8))
        if zoom > 8:
            scale = 1
        elif zoom > 7:
            scale = 2
        elif zoom > 6:
            scale = 3
        elif zoom > 5:
            scale = 4
        elif zoom > 4:
            scale = 5
        elif zoom > 3:
            scale = 6
        elif zoom > 2:
            scale = 7
        elif zoom > 1:
            scale = 8
        elif zoom > 0:
            scale = 9

        # Draw arrows
        for x in data[::scale]:
            for y in x[::scale]:
                xx, yy = view.get_window_xy_from(y[2][0], y[2][1], zoom)
                self.drawWindArrow(xx, yy, y[0], y[1])
