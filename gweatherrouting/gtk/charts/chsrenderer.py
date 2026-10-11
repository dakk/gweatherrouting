"""Cached CHS image tiles with all I/O and PNG decoding off the GTK thread."""

from collections import OrderedDict
import io
import logging
import math
from threading import Thread
import time
from typing import Optional
from weakref import WeakKeyDictionary

import cairo
from gi.repository import GLib

from gweatherrouting.core.chscharts import (
    CACHE_SECONDS,
    CHSTileSource,
    MAX_ZOOM,
    MIN_ZOOM,
    TILE_SIZE,
    tile_in_canada,
)
from gweatherrouting.gtk.widgets.mapwidget import MapViewport, MapWidget

logger = logging.getLogger("gweatherrouting")
FADE_SECONDS = 0.20
TileKey = tuple[int, int, int, int]
TileBlend = tuple[cairo.ImageSurface, float, Optional[cairo.ImageSurface]]


class CHSRenderer:
    def __init__(self, directory):
        self.source = CHSTileSource(directory)
        self.enabled = False
        self._tiles = OrderedDict()
        self._pending = OrderedDict()
        self._inflight = set()
        self._retry = {}
        self._views: WeakKeyDictionary[MapWidget, int] = WeakKeyDictionary()
        self._wanted: WeakKeyDictionary[MapWidget, set[TileKey]] = WeakKeyDictionary()
        self._blends: WeakKeyDictionary[MapWidget, dict[TileKey, TileBlend]] = (
            WeakKeyDictionary()
        )
        self._ticks: WeakKeyDictionary[MapWidget, int] = WeakKeyDictionary()

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        if not enabled:
            for canvas in list(self._ticks):
                self.forget(canvas)
            self._pending.clear()
            self._wanted.clear()
            self._views.clear()
            self._blends.clear()

    def forget(self, canvas):
        tick = self._ticks.pop(canvas, None)
        if tick is not None:
            canvas.remove_tick_callback(tick)
        self._blends.pop(canvas, None)
        self._wanted.pop(canvas, None)
        self._views.pop(canvas, None)
        self._prune_pending()

    def _prune_pending(self):
        wanted = set().union(*self._wanted.values()) if self._wanted else set()
        self._pending = OrderedDict(
            (key, refresh) for key, refresh in self._pending.items() if key in wanted
        )
        return wanted

    def draw(self, canvas, cr):
        if not self.enabled:
            return
        if canvas._zoom < MIN_ZOOM - 0.5:
            self.forget(canvas)
            return
        zoom = self._tile_zoom(canvas)
        visible, ratio, cx, cy = self._visible_tiles(canvas, zoom)
        wanted = {key for key, _, _ in visible}
        self._wanted[canvas] = wanted
        self._prune_pending()
        now = time.time()
        frame_time = time.monotonic()
        blends = self._blends.setdefault(canvas, {})
        for key in list(blends):
            if key not in wanted:
                del blends[key]
        fading, drawn = False, False
        for key, x, y in visible:
            tile_drawn, tile_fading = self._draw_tile(
                cr, key, x, y, ratio, blends, frame_time
            )
            drawn = drawn or tile_drawn
            fading = fading or tile_fading
            self._queue_tile(canvas, key, now)
        # Center tiles first, so useful detail arrives before the map edges.
        self._pending = OrderedDict(
            sorted(
                self._pending.items(),
                key=lambda item: (item[0][1] * TILE_SIZE + TILE_SIZE / 2 - cx) ** 2
                + (item[0][2] * TILE_SIZE + TILE_SIZE / 2 - cy) ** 2,
            )
        )
        self._pump()
        if fading and canvas not in self._ticks:
            self._ticks[canvas] = canvas.add_tick_callback(self._tick)
        if drawn:
            self._attribution(
                cr, canvas.get_allocated_width(), canvas.get_allocated_height()
            )

    def _tile_zoom(self, canvas):
        # Keep a stable tile level while zooming; transform it at every frame.
        zoom = max(MIN_ZOOM, min(MAX_ZOOM, int(math.floor(canvas._zoom + 0.5))))
        if getattr(canvas, "_zoom_animating", False):
            zoom = self._views.get(canvas, zoom)
            # Bound work if repeated input zooms out several levels at once.
            zoom = max(MIN_ZOOM, min(zoom, math.ceil(canvas._zoom + 1)))
        else:
            self._views[canvas] = zoom
        return zoom

    def _visible_tiles(self, canvas, zoom):
        viewport = MapViewport(canvas)
        viewport._zoom = zoom
        cx = viewport._lon_to_x(canvas._center_lon)
        cy = viewport._lat_to_y(canvas._center_lat)
        ratio = 2.0 ** (canvas._zoom - zoom)
        width, height = canvas.get_allocated_width(), canvas.get_allocated_height()
        left, top = cx - width / (2 * ratio), cy - height / (2 * ratio)
        right, bottom = cx + width / (2 * ratio), cy + height / (2 * ratio)
        factor = min(2, max(1, canvas.get_scale_factor()))
        visible = []
        for y in range(
            max(0, math.floor(top / TILE_SIZE)),
            min(2**zoom, math.ceil(bottom / TILE_SIZE)),
        ):
            for x in range(
                max(0, math.floor(left / TILE_SIZE)),
                min(2**zoom, math.ceil(right / TILE_SIZE)),
            ):
                if tile_in_canada(zoom, x, y):
                    key = (zoom, x, y, factor)
                    visible.append(
                        (
                            key,
                            (x * TILE_SIZE - left) * ratio,
                            (y * TILE_SIZE - top) * ratio,
                        )
                    )
        return visible, ratio, cx, cy

    def _draw_tile(self, cr, key, x, y, ratio, blends, frame_time):
        tile = self._tiles.get(key)
        if not tile:
            return self._fallback_preview(cr, key, x, y, ratio), False
        self._tiles.move_to_end(key)
        state = blends.get(key)
        if state is None or state[0] is not tile[0]:
            previous = state[0] if state else self._preview_surface(key)
            state = (tile[0], frame_time, previous)
            blends[key] = state
        progress = min(1, (frame_time - state[1]) / FADE_SECONDS)
        if progress < 1:
            # Smoothstep keeps the beginning and end of the blend gentle.
            alpha = progress * progress * (3 - 2 * progress)
            self._crossfade(cr, state[2], tile[0], x, y, ratio, alpha)
            return True, True
        self._paint(cr, tile[0], x, y, ratio)
        blends[key] = (tile[0], state[1], None)
        return True, False

    def _queue_tile(self, canvas, key, now):
        tile = self._tiles.get(key)
        if not tile or now - tile[1] >= CACHE_SECONDS:
            if (
                key not in self._inflight
                and self._retry.get(key, 0) <= now
                and not getattr(canvas, "_zoom_animating", False)
            ):
                self._pending[key] = bool(tile)

    def _tick(self, canvas, frame_clock):
        canvas.queue_draw()
        now = time.monotonic()
        active = any(
            now - state[1] < FADE_SECONDS
            for state in self._blends.get(canvas, {}).values()
        )
        if not active:
            self._ticks.pop(canvas, None)
        return active

    def _preview_surface(self, key):
        factor = key[3]
        surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32, TILE_SIZE * factor, TILE_SIZE * factor
        )
        surface.set_device_scale(factor, factor)
        self._fallback_preview(cairo.Context(surface), key, 0, 0, 1)
        return surface

    def _crossfade(self, cr, previous, surface, x, y, ratio, alpha):
        cr.save()
        cr.rectangle(x, y, TILE_SIZE * ratio, TILE_SIZE * ratio)
        cr.clip()
        cr.push_group()
        # Add weighted premultiplied pixels, then composite the result once.
        # OVER-ing two translucent images would dim the map halfway through.
        if previous is not None:
            self._paint(cr, previous, x, y, ratio, 1 - alpha)
        cr.set_operator(cairo.OPERATOR_ADD)
        self._paint(cr, surface, x, y, ratio, alpha)
        cr.pop_group_to_source()
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.paint()
        cr.restore()

    @staticmethod
    def _paint(cr, surface, x, y, ratio, alpha=1):
        cr.save()
        cr.rectangle(x, y, TILE_SIZE * ratio, TILE_SIZE * ratio)
        cr.clip()
        cr.translate(x, y)
        cr.scale(ratio, ratio)
        cr.set_source_surface(surface, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        cr.get_source().set_extend(cairo.EXTEND_PAD)
        cr.paint_with_alpha(alpha)
        cr.restore()

    def _parent_preview(self, cr, key, x, y, ratio):
        z, tx, ty, factor = key
        for distance in range(1, 4):
            parent = self._tiles.get(
                (z - distance, tx >> distance, ty >> distance, factor)
            )
            if parent:
                scale = 2**distance
                cr.save()
                cr.rectangle(x, y, TILE_SIZE * ratio, TILE_SIZE * ratio)
                cr.clip()
                self._paint(
                    cr,
                    parent[0],
                    x - (tx % scale) * TILE_SIZE * ratio,
                    y - (ty % scale) * TILE_SIZE * ratio,
                    ratio * scale,
                )
                cr.restore()
                return True
        return False

    def _fallback_preview(self, cr, key, x, y, ratio):
        if self._parent_preview(cr, key, x, y, ratio):
            return True
        # When zooming out, retain the finer tiles until the new level arrives.
        # Fill each quadrant independently, preferring the nearest cached level.
        z, tx, ty, factor = key
        found = False
        for row in range(2):
            for column in range(2):
                child = self._tiles.get((z + 1, tx * 2 + column, ty * 2 + row, factor))
                offset_x = x + column * TILE_SIZE * ratio / 2
                offset_y = y + row * TILE_SIZE * ratio / 2
                if child:
                    self._paint(cr, child[0], offset_x, offset_y, ratio / 2)
                    found = True
                else:
                    for subrow in range(2):
                        for subcolumn in range(2):
                            grandchild = self._tiles.get(
                                (
                                    z + 2,
                                    tx * 4 + column * 2 + subcolumn,
                                    ty * 4 + row * 2 + subrow,
                                    factor,
                                )
                            )
                            if grandchild:
                                self._paint(
                                    cr,
                                    grandchild[0],
                                    offset_x + subcolumn * TILE_SIZE * ratio / 4,
                                    offset_y + subrow * TILE_SIZE * ratio / 4,
                                    ratio / 4,
                                )
                                found = True
        return found

    @staticmethod
    def _attribution(cr, width, height):
        text = "© CHS / Fisheries and Oceans Canada · Viewing only; not for navigation"
        cr.save()
        cr.select_font_face("Sans")
        cr.set_font_size(10)
        text_width = cr.text_extents(text)[2]
        x, y = max(4, width - text_width - 12), max(12, height - 6)
        cr.set_source_rgba(1, 1, 1, 0.85)
        cr.rectangle(x - 4, y - 12, text_width + 8, 16)
        cr.fill()
        cr.set_source_rgb(0.15, 0.15, 0.15)
        cr.move_to(x, y)
        cr.show_text(text)
        cr.restore()

    def _pump(self):
        while self.enabled and len(self._inflight) < 2 and self._pending:
            key, refresh = self._pending.popitem(last=False)
            self._inflight.add(key)

            def worker(key=key, refresh=refresh):
                surface, modified, error = None, 0, None
                try:
                    cached = None if refresh else self.source.cached(key)
                    if cached:
                        try:
                            surface = self._decode(key, cached[0])
                            modified = cached[1]
                        except (cairo.Error, ValueError):
                            surface = None
                    if surface is None:
                        data, modified = self.source.fetch(key)
                        surface = self._decode(key, data)
                except Exception as exc:
                    error = str(exc)
                GLib.idle_add(self._ready, key, surface, modified, error)

            Thread(target=worker, name="chs-tile", daemon=True).start()

    @staticmethod
    def _decode(key, data):
        surface = cairo.ImageSurface.create_from_png(io.BytesIO(data))
        factor = key[3]
        if (
            surface.get_width() != TILE_SIZE * factor
            or surface.get_height() != TILE_SIZE * factor
        ):
            raise ValueError("CHS returned an unexpected image size")
        surface.set_device_scale(factor, factor)
        return surface

    def _ready(self, key, surface, modified, error):
        self._inflight.discard(key)
        if surface is not None:
            self._tiles[key] = (surface, modified)
            self._tiles.move_to_end(key)
            self._retry.pop(key, None)
            if len(self._tiles) > 96:
                self._tiles.popitem(last=False)
        if error:
            self._retry[key] = time.time() + 60
            if len(self._retry) > 512:
                self._retry.pop(next(iter(self._retry)))
            logger.debug("CHS tile unavailable: %s", error)
        if self.enabled:
            for canvas, wanted in list(self._wanted.items()):
                if key in wanted:
                    canvas.queue_draw()
        self._pump()
        return False
