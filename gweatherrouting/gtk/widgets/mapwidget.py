# -*- coding: utf-8 -*-
# Copyright (C) 2017-2026 Davide Gessa
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
from typing import Callable, Protocol

import numpy as np

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib, GObject, Gtk

from .mapmotion import DragVelocity, PanInertia, ZoomAnimation


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


class Projection(Protocol):
    """Projection state shared by the GTK canvas and frozen render viewports."""

    _zoom: float
    TILE_SIZE: int
    MAX_LAT: float


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
        self._zoom = 3.0
        self._smooth_zoom = True
        self._pan_inertia_enabled = True
        self._zoom_animation = None
        self._zoom_animating = False
        self._inertia = None
        self._motion_tick = 0
        self._last_frame_time = None
        self._motion_destroyed = False
        self._display_bound = False
        self._drag_velocity = DragVelocity()

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
            | Gdk.EventMask.SMOOTH_SCROLL_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
        )

        self.connect("draw", self._on_draw)
        self.connect("button-press-event", self._on_button_press)
        self.connect("button-release-event", self._on_button_release)
        self.connect("motion-notify-event", self._on_motion)
        self.connect("scroll-event", self._on_scroll)
        self.connect("key-press-event", self._on_key_press)
        self.connect("unmap", self._cancel_motion)
        self.connect("destroy", self._destroy_motion)

    # --- Mercator projection helpers ---

    # Maximum latitude for Mercator projection (avoids math domain errors at poles)
    MAX_LAT = 85.051129

    def _lat_to_y(self: Projection, lat):
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

    def _lon_to_x(self: Projection, lon):
        """Convert longitude to Mercator world-pixel X at current zoom."""
        n = 2.0**self._zoom
        return (lon + 180.0) / 360.0 * n * self.TILE_SIZE

    def _y_to_lat(self: Projection, y):
        """Convert Mercator world-pixel Y to latitude at current zoom."""
        n = 2.0**self._zoom
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / (n * self.TILE_SIZE))))
        return math.degrees(lat_rad)

    def _x_to_lon(self: Projection, x):
        """Convert Mercator world-pixel X to longitude at current zoom."""
        n = 2.0**self._zoom
        return x / (n * self.TILE_SIZE) * 360.0 - 180.0

    # --- Public API (OsmGpsMap compatible) ---

    def set_center_and_zoom(self, lat, lon, zoom):
        self._cancel_motion()
        self._center_lat = float(lat)
        self._center_lon = float(lon)
        self._zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, float(zoom)))
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

    def convert_geographic_to_screen_batch(self, lats, lons):
        """Batch-convert numpy arrays of lat/lon to screen (x, y) arrays.

        Args:
            lats: numpy float64 array of latitudes
            lons: numpy float64 array of longitudes

        Returns:
            (xs, ys): tuple of numpy float64 arrays of screen coordinates
        """
        w = self.get_allocated_width()
        h = self.get_allocated_height()

        n = 2.0**self._zoom
        tile_n = n * self.TILE_SIZE

        # Center offsets (scalar)
        cx = (self._center_lon + 180.0) / 360.0 * tile_n
        clat_rad = math.radians(max(-self.MAX_LAT, min(self.MAX_LAT, self._center_lat)))
        cy = (
            (1.0 - math.log(math.tan(clat_rad) + 1.0 / math.cos(clat_rad)) / math.pi)
            / 2.0
            * tile_n
        )

        half_w = w / 2.0
        half_h = h / 2.0

        # Batch lon -> x
        px = (lons + 180.0) / 360.0 * tile_n

        # Batch lat -> y (Mercator)
        lat_clamped = np.clip(lats, -self.MAX_LAT, self.MAX_LAT)
        lat_rad = np.radians(lat_clamped)
        py = (
            (1.0 - np.log(np.tan(lat_rad) + 1.0 / np.cos(lat_rad)) / math.pi)
            / 2.0
            * tile_n
        )

        xs = px - cx + half_w
        ys = py - cy + half_h

        return xs, ys

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

    def bind_display_settings(self, settings):
        if not self._display_bound:
            self._display_bound = True
            settings.register_on_change("smoothZoom", self._set_smooth_zoom)
            settings.register_on_change("panInertia", self._set_pan_inertia)

    def _set_smooth_zoom(self, enabled):
        if self._motion_destroyed:
            return
        self._smooth_zoom = bool(enabled)
        if not enabled and self._zoom_animation:
            motion = self._zoom_animation
            self._apply_zoom(motion.target, motion.anchor, motion.pointer)
            self._cancel_motion()
            self.queue_draw()

    def _set_pan_inertia(self, enabled):
        if self._motion_destroyed:
            return
        self._pan_inertia_enabled = bool(enabled)
        if not enabled and self._inertia:
            self._cancel_motion()

    def _cancel_motion(self, *args):
        if self._motion_tick:
            self.remove_tick_callback(self._motion_tick)
            self._motion_tick = 0
        self._zoom_animation = None
        self._zoom_animating = False
        self._inertia = None
        self._last_frame_time = None

    def _destroy_motion(self, *args):
        self._cancel_motion()
        self._motion_destroyed = True

    def _ensure_motion_tick(self):
        if not self._motion_tick:
            self._last_frame_time = None
            self._motion_tick = self.add_tick_callback(self._animate_motion)

    def _animate_motion(self, widget, frame_clock):
        now = frame_clock.get_frame_time() / 1000000
        elapsed = (
            min(0.05, max(0, now - self._last_frame_time))
            if self._last_frame_time
            else 1 / 60
        )
        self._last_frame_time = now
        if self._zoom_animation:
            motion = self._zoom_animation
            zoom, finished = motion.value_at(now)
            self._apply_zoom(zoom, motion.anchor, motion.pointer)
            if finished:
                self._zoom_animation = None
                self._zoom_animating = False
        if self._inertia:
            dx, dy = self._inertia.step(elapsed)
            self._move_pixels(-dx, -dy)
            if not self._inertia.active:
                self._inertia = None
        self.queue_draw()
        if not self._zoom_animation and not self._inertia:
            self._motion_tick = 0
            self._last_frame_time = None
            return False
        return True

    def _apply_zoom(self, zoom, anchor, pointer):
        self._zoom = zoom
        lat, lon = anchor
        x = self._lon_to_x(lon) - (pointer[0] - self.get_allocated_width() / 2)
        y = self._lat_to_y(lat) - (pointer[1] - self.get_allocated_height() / 2)
        self._center_lon = self._x_to_lon(x)
        self._center_lat = max(-85, min(85, self._y_to_lat(y)))

    def _request_zoom(self, amount, x, y):
        target = self._zoom_animation.target if self._zoom_animation else self._zoom
        target = max(self.MIN_ZOOM, min(self.MAX_ZOOM, target + amount))
        anchor = self.convert_screen_to_geographic(x, y).get_degrees()
        self._cancel_motion()
        self._dragging = False
        if abs(target - self._zoom) < 0.000001:
            return
        if self._smooth_zoom:
            now = GLib.get_monotonic_time() / 1000000
            self._zoom_animation = ZoomAnimation(
                self._zoom, target, now, anchor, (x, y)
            )
            self._zoom_animating = True
            self._ensure_motion_tick()
        else:
            self._apply_zoom(target, anchor, (x, y))
            self.queue_draw()

    def _on_draw(self, widget, cr):
        # Draw layers in order
        for layer in self._layers:
            cr.save()
            layer.do_draw(self, cr)
            cr.restore()
        return False

    def _on_button_press(self, widget, event):
        self._cancel_motion()
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
            self._drag_velocity = DragVelocity()
            self._drag_velocity.add(
                GLib.get_monotonic_time() / 1000000, event.x, event.y
            )
        return False

    def _on_button_release(self, widget, event):
        if event.button == 1:
            if self._dragging and self._pan_inertia_enabled:
                vx, vy = self._drag_velocity.release(
                    GLib.get_monotonic_time() / 1000000, event.x, event.y
                )
                self._inertia = PanInertia(vx, vy)
                if self._inertia.active:
                    self._ensure_motion_tick()
                else:
                    self._inertia = None
            self._dragging = False
        return False

    def _on_motion(self, widget, event):
        if self._dragging:
            self._drag_velocity.add(
                GLib.get_monotonic_time() / 1000000, event.x, event.y
            )
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
        amount = 0.0
        if event.direction == Gdk.ScrollDirection.UP:
            amount = 1.0
        elif event.direction == Gdk.ScrollDirection.DOWN:
            amount = -1.0
        elif event.direction == Gdk.ScrollDirection.SMOOTH:
            _, dx, dy = event.get_scroll_deltas()
            if self._smooth_zoom:
                amount = max(-2.0, min(2.0, -dy * 0.35))
            elif dy:
                amount = 1.0 if dy < 0 else -1.0
        if amount:
            self._request_zoom(amount, event.x, event.y)
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
            self._request_zoom(
                1, self.get_allocated_width() / 2, self.get_allocated_height() / 2
            )
            return True
        elif name in ("minus", "KP_Subtract"):
            self._request_zoom(
                -1, self.get_allocated_width() / 2, self.get_allocated_height() / 2
            )
            return True

        return False

    def _pan(self, dx, dy):
        """Pan the map by (dx, dy) screen pixels."""
        self._cancel_motion()
        self._move_pixels(dx, dy)
        self.queue_draw()

    def _move_pixels(self, dx, dy):
        cx = self._lon_to_x(self._center_lon)
        cy = self._lat_to_y(self._center_lat)

        self._center_lon = self._x_to_lon(cx + dx)
        self._center_lat = self._y_to_lat(cy + dy)
        self._center_lat = max(-85.0, min(85.0, self._center_lat))


class MapViewport:
    """Frozen map projection for rendering a reusable chart image with a margin."""

    TILE_SIZE = MapWidget.TILE_SIZE
    MAX_LAT = MapWidget.MAX_LAT
    _lat_to_y = MapWidget._lat_to_y
    _lon_to_x = MapWidget._lon_to_x
    _y_to_lat = MapWidget._y_to_lat
    _x_to_lon = MapWidget._x_to_lon
    get_bbox = MapWidget.get_bbox
    get_scale = MapWidget.get_scale
    convert_screen_to_geographic = MapWidget.convert_screen_to_geographic
    convert_geographic_to_screen = MapWidget.convert_geographic_to_screen
    convert_geographic_to_screen_batch = MapWidget.convert_geographic_to_screen_batch

    def __init__(self, source, margin=0, on_redraw=None):
        self._center_lat = source._center_lat
        self._center_lon = source._center_lon
        self._zoom = source._zoom
        self.width = source.get_allocated_width() + 2 * margin
        self.height = source.get_allocated_height() + 2 * margin
        self.queue_draw = on_redraw or source.queue_draw
        self.render_cancelled: Callable[[], bool] = lambda: False

    def get_allocated_width(self):
        return self.width

    def get_allocated_height(self):
        return self.height
