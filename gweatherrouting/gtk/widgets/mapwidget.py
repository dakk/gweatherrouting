# -*- coding: utf-8 -*-
# Copyright (C) 2017-2025 Davide Gessa
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

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GObject, Gtk


class MapPoint:
    """Replacement for OsmGpsMap.MapPoint - represents a geographic coordinate."""

    def __init__(self, lat, lon):
        self._lat = float(lat)
        self._lon = float(lon)

    @staticmethod
    def new_degrees(lat, lon):
        return MapPoint(lat, lon)

    def get_degrees(self):
        return (self._lat, self._lon)

    @property
    def rlat(self):
        return math.radians(self._lat)

    @property
    def rlon(self):
        return math.radians(self._lon)


class MapLayer:
    """Base class for map layers, replacement for OsmGpsMap.MapLayer."""

    def do_draw(self, gpsmap, cr):
        pass

    def do_render(self, gpsmap):
        pass

    def do_busy(self):
        return False

    def do_button_press(self, gpsmap, gdkeventbutton):
        return False


class MapWidget(Gtk.DrawingArea):
    """Pure Python/GTK replacement for OsmGpsMap widget.

    Implements a Mercator-projected map canvas with pan, zoom,
    layer compositing, and coordinate conversion.
    """

    # Zoom range
    MIN_ZOOM = 1
    MAX_ZOOM = 20

    # Tile size in the Mercator world model (standard 256px tiles)
    TILE_SIZE = 256

    def __init__(self):
        super().__init__()

        # Map state
        self._center_lat = 0.0
        self._center_lon = 0.0
        self._zoom = 3

        # Layers
        self._layers = []

        # Drag state
        self._dragging = False
        self._drag_start_x = 0.0
        self._drag_start_y = 0.0
        self._drag_start_lat = 0.0
        self._drag_start_lon = 0.0

        # Keyboard shortcuts
        self._key_shortcuts = {}

        # Enable events
        self.set_can_focus(True)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.SCROLL_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
        )

        self.connect("draw", self._on_draw)
        self.connect("button-press-event", self._on_button_press)
        self.connect("button-release-event", self._on_button_release)
        self.connect("motion-notify-event", self._on_motion)
        self.connect("scroll-event", self._on_scroll)
        self.connect("key-press-event", self._on_key_press)

    # --- Mercator projection helpers ---

    # Maximum latitude for Mercator projection (avoids math domain errors at poles)
    MAX_LAT = 85.051129

    def _lat_to_y(self, lat):
        """Convert latitude to Mercator world-pixel Y at current zoom."""
        lat = max(-self.MAX_LAT, min(self.MAX_LAT, lat))
        n = 2.0**self._zoom
        lat_rad = math.radians(lat)
        return (
            (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi)
            / 2.0
            * n
            * self.TILE_SIZE
        )

    def _lon_to_x(self, lon):
        """Convert longitude to Mercator world-pixel X at current zoom."""
        n = 2.0**self._zoom
        return (lon + 180.0) / 360.0 * n * self.TILE_SIZE

    def _y_to_lat(self, y):
        """Convert Mercator world-pixel Y to latitude at current zoom."""
        n = 2.0**self._zoom
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / (n * self.TILE_SIZE))))
        return math.degrees(lat_rad)

    def _x_to_lon(self, x):
        """Convert Mercator world-pixel X to longitude at current zoom."""
        n = 2.0**self._zoom
        return x / (n * self.TILE_SIZE) * 360.0 - 180.0

    # --- Public API (OsmGpsMap compatible) ---

    def set_center_and_zoom(self, lat, lon, zoom):
        self._center_lat = float(lat)
        self._center_lon = float(lon)
        self._zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, int(zoom)))
        self.queue_draw()

    def layer_add(self, layer):
        self._layers.append(layer)

    def get_bbox(self):
        """Return (top-left MapPoint, bottom-right MapPoint) of visible area."""
        w = self.get_allocated_width()
        h = self.get_allocated_height()

        cx = self._lon_to_x(self._center_lon)
        cy = self._lat_to_y(self._center_lat)

        top_lat = self._y_to_lat(cy - h / 2.0)
        left_lon = self._x_to_lon(cx - w / 2.0)
        bottom_lat = self._y_to_lat(cy + h / 2.0)
        right_lon = self._x_to_lon(cx + w / 2.0)

        return (MapPoint(top_lat, left_lon), MapPoint(bottom_lat, right_lon))

    def get_scale(self):
        """Return approximate meters per pixel at the map center.

        This matches OsmGpsMap's get_scale() behaviour used throughout
        the codebase for zoom-dependent rendering decisions.
        """
        lat_rad = math.radians(self._center_lat)
        # Circumference of Earth at this latitude / total pixels at zoom
        meters_per_pixel = (
            math.cos(lat_rad) * 2 * math.pi * 6378137 / (2**self._zoom * self.TILE_SIZE)
        )
        return meters_per_pixel

    def convert_geographic_to_screen(self, map_point):
        """Convert MapPoint to screen (x, y) pixel coordinates."""
        lat, lon = map_point.get_degrees()

        w = self.get_allocated_width()
        h = self.get_allocated_height()

        cx = self._lon_to_x(self._center_lon)
        cy = self._lat_to_y(self._center_lat)

        px = self._lon_to_x(lon)
        py = self._lat_to_y(lat)

        sx = px - cx + w / 2.0
        sy = py - cy + h / 2.0

        return (sx, sy)

    def convert_screen_to_geographic(self, sx, sy):
        """Convert screen (x, y) to MapPoint."""
        w = self.get_allocated_width()
        h = self.get_allocated_height()

        cx = self._lon_to_x(self._center_lon)
        cy = self._lat_to_y(self._center_lat)

        px = cx + sx - w / 2.0
        py = cy + sy - h / 2.0

        lat = self._y_to_lat(py)
        lon = self._x_to_lon(px)

        return MapPoint(lat, lon)

    def get_event_location(self, event):
        """Convert a Gdk event to a MapPoint (like OsmGpsMap.get_event_location)."""
        return self.convert_screen_to_geographic(event.x, event.y)

    def set_keyboard_shortcut(self, key_type, keyval):
        """Register a keyboard shortcut (compatible with OsmGpsMap API)."""
        self._key_shortcuts[keyval] = key_type

    def map_redraw_idle(self):
        """Schedule a redraw in idle (compatible with OsmGpsMap API)."""
        GObject.idle_add(self.queue_draw)

    # --- Internal event handlers ---

    def _on_draw(self, widget, cr):
        # Draw layers in order
        for layer in self._layers:
            cr.save()
            layer.do_draw(self, cr)
            cr.restore()
        return False

    def _on_button_press(self, widget, event):
        # Let layers handle button presses first
        for layer in reversed(self._layers):
            if layer.do_button_press(self, event):
                return True

        if event.button == 1:
            self._dragging = True
            self._drag_start_x = event.x
            self._drag_start_y = event.y
            self._drag_start_lat = self._center_lat
            self._drag_start_lon = self._center_lon
        return False

    def _on_button_release(self, widget, event):
        if event.button == 1:
            self._dragging = False
        return False

    def _on_motion(self, widget, event):
        if self._dragging:
            dx = event.x - self._drag_start_x
            dy = event.y - self._drag_start_y

            # Convert pixel delta to geographic delta
            cx = self._lon_to_x(self._drag_start_lon)
            cy = self._lat_to_y(self._drag_start_lat)

            self._center_lon = self._x_to_lon(cx - dx)
            self._center_lat = self._y_to_lat(cy - dy)

            # Clamp latitude
            self._center_lat = max(-85.0, min(85.0, self._center_lat))

            self.queue_draw()
        return False

    def _on_scroll(self, widget, event):
        # Zoom in/out centred on mouse position
        old_zoom = self._zoom

        if event.direction == Gdk.ScrollDirection.UP:
            self._zoom = min(self.MAX_ZOOM, self._zoom + 1)
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self._zoom = max(self.MIN_ZOOM, self._zoom - 1)
        elif event.direction == Gdk.ScrollDirection.SMOOTH:
            _, dx, dy = event.get_scroll_deltas()
            if dy < 0:
                self._zoom = min(self.MAX_ZOOM, self._zoom + 1)
            elif dy > 0:
                self._zoom = max(self.MIN_ZOOM, self._zoom - 1)

        if self._zoom != old_zoom:
            # Re-center so that the point under the mouse stays fixed
            w = self.get_allocated_width()
            h = self.get_allocated_height()

            # Screen offset of cursor from center
            mx = event.x - w / 2.0
            my = event.y - h / 2.0

            # Geographic point under cursor at old zoom
            old_n = 2.0**old_zoom
            old_cx = (self._center_lon + 180.0) / 360.0 * old_n * self.TILE_SIZE
            old_cy = (
                (
                    1.0
                    - math.log(
                        math.tan(math.radians(self._center_lat))
                        + 1.0 / math.cos(math.radians(self._center_lat))
                    )
                    / math.pi
                )
                / 2.0
                * old_n
                * self.TILE_SIZE
            )
            cursor_world_x = old_cx + mx
            cursor_world_y = old_cy + my

            # Convert cursor world coords to geographic
            cursor_lon = cursor_world_x / (old_n * self.TILE_SIZE) * 360.0 - 180.0
            cursor_lat = math.degrees(
                math.atan(
                    math.sinh(
                        math.pi * (1 - 2 * cursor_world_y / (old_n * self.TILE_SIZE))
                    )
                )
            )

            # At new zoom, where is that geographic point in world coords?
            new_n = 2.0**self._zoom
            cursor_new_x = (cursor_lon + 180.0) / 360.0 * new_n * self.TILE_SIZE
            cursor_new_y = (
                (
                    1.0
                    - math.log(
                        math.tan(math.radians(cursor_lat))
                        + 1.0 / math.cos(math.radians(cursor_lat))
                    )
                    / math.pi
                )
                / 2.0
                * new_n
                * self.TILE_SIZE
            )

            # New center so that cursor point stays at same screen position
            new_cx = cursor_new_x - mx
            new_cy = cursor_new_y - my

            self._center_lon = new_cx / (new_n * self.TILE_SIZE) * 360.0 - 180.0
            self._center_lat = math.degrees(
                math.atan(
                    math.sinh(math.pi * (1 - 2 * new_cy / (new_n * self.TILE_SIZE)))
                )
            )
            self._center_lat = max(-85.0, min(85.0, self._center_lat))

            self.queue_draw()
        return True

    def _on_key_press(self, widget, event):  # noqa: C901
        pan_pixels = 50
        keyval = event.keyval

        key_type = self._key_shortcuts.get(keyval)
        if key_type is not None:
            # Use string comparison for key type names to avoid importing
            # OsmGpsMap enums
            type_name = str(key_type)

            if "UP" in type_name:
                self._pan(0, -pan_pixels)
                return True
            elif "DOWN" in type_name:
                self._pan(0, pan_pixels)
                return True
            elif "LEFT" in type_name:
                self._pan(-pan_pixels, 0)
                return True
            elif "RIGHT" in type_name:
                self._pan(pan_pixels, 0)
                return True
            elif "FULLSCREEN" in type_name:
                toplevel = self.get_toplevel()
                if toplevel and hasattr(toplevel, "fullscreen"):
                    toplevel.fullscreen()
                return True

        # Fallback: handle arrow keys directly
        name = Gdk.keyval_name(keyval)
        if name == "Up":
            self._pan(0, -pan_pixels)
            return True
        elif name == "Down":
            self._pan(0, pan_pixels)
            return True
        elif name == "Left":
            self._pan(-pan_pixels, 0)
            return True
        elif name == "Right":
            self._pan(pan_pixels, 0)
            return True
        elif name in ("plus", "equal", "KP_Add"):
            self._zoom = min(self.MAX_ZOOM, self._zoom + 1)
            self.queue_draw()
            return True
        elif name in ("minus", "KP_Subtract"):
            self._zoom = max(self.MIN_ZOOM, self._zoom - 1)
            self.queue_draw()
            return True

        return False

    def _pan(self, dx, dy):
        """Pan the map by (dx, dy) screen pixels."""
        cx = self._lon_to_x(self._center_lon)
        cy = self._lat_to_y(self._center_lat)

        self._center_lon = self._x_to_lon(cx + dx)
        self._center_lat = self._y_to_lat(cy + dy)
        self._center_lat = max(-85.0, min(85.0, self._center_lat))

        self.queue_draw()
