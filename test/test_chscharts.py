"""CHS tile bounds, caching, background I/O, and zoom preview checks."""

import io
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import cairo
from gi.repository import GLib

from gweatherrouting.core.chscharts import (
    CHSTileSource,
    HALF_WORLD,
    tile_bbox,
    tile_in_canada,
)
from gweatherrouting.gtk.charts.chsrenderer import CHSRenderer
from test.map_helpers import MapCanvas as TestMap


class TestCHSPreferences(unittest.TestCase):
    def test_settings_window_switch_persists(self):
        from gweatherrouting.gtk.settings.settingsmanager import SettingsManager
        from gweatherrouting.gtk.settings.settingswindow import SettingsWindow

        with TemporaryDirectory() as directory:
            with patch("gweatherrouting.core.storage.DATA_DIR", directory):
                settings = SettingsManager()
                parent = SimpleNamespace(chart_manager=SimpleNamespace(charts=[]))
                core = SimpleNamespace(
                    connectionManager=SimpleNamespace(connections=[])
                )
                window = SettingsWindow(parent, settings, core)
                self.addCleanup(window.window.destroy)
                switch = window.builder.get_object("canadian-charts")
                self.assertTrue(switch.get_active())
                switch.set_active(False)
                self.assertFalse(settings.canadianCharts)
                self.assertFalse(SettingsManager().canadianCharts)


def tile_key(lat=49.3, lon=-123.17, zoom=14, factor=1):
    n = 2**zoom
    return (
        zoom,
        int((lon + 180) / 360 * n),
        int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n),
        factor,
    )


def png(factor=1):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 256 * factor, 256 * factor)
    cr = cairo.Context(surface)
    cr.set_source_rgb(1, 0, 0)
    cr.paint()
    output = io.BytesIO()
    surface.write_to_png(output)
    return output.getvalue()


class TestCHSTileSource(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.source = CHSTileSource(self.temporary.name)
        self.key = tile_key()

    def response(self, data):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.iter_content.return_value = [data]
        return response

    def test_bounds_and_geographic_request_limits(self):
        west, south, east, north = tile_bbox(8, 0, 0)
        self.assertEqual(west, -HALF_WORLD)
        self.assertEqual(north, HALF_WORLD)
        self.assertLess(south, north)
        self.assertLess(west, east)
        for lat, lon in ((49.3, -123.17), (43.6, -79.4), (47, -70), (70, -120)):
            self.assertTrue(tile_in_canada(*tile_key(lat, lon)[:3]))
        for lat, lon in ((37.8, -122.4), (51.5, 0), (-33, 151)):
            self.assertFalse(tile_in_canada(*tile_key(lat, lon)[:3]))
        for key in ((14, -1, 0, 1), (25, 1, 1, 1), (14, 1, 1, 5)):
            with self.assertRaises(ValueError):
                self.source.path(key)

    @patch("gweatherrouting.core.chscharts.requests.get")
    def test_fetch_is_atomic_and_retina_requests_keep_logical_scale(self, get):
        get.return_value = self.response(png(2))
        key = tile_key(factor=2)
        data, modified = self.source.fetch(key)
        self.assertEqual(self.source.cached(key)[0], data)
        self.assertGreater(modified, 0)
        params = get.call_args.kwargs["params"]
        self.assertEqual(params["size"], "512,512")
        self.assertEqual(params["dpi"], 192)
        self.assertEqual(params["transparent"], "true")
        self.assertFalse(list(Path(self.temporary.name).rglob("*.tmp")))

    @patch("gweatherrouting.core.chscharts.requests.get")
    def test_rejects_errors_without_overwriting_cached_chart(self, get):
        path = self.source.path(self.key)
        path.parent.mkdir(parents=True)
        path.write_bytes(png())
        get.return_value = self.response(b'{"error":"unavailable"}')
        with self.assertRaises(ValueError):
            self.source.fetch(self.key)
        self.assertEqual(path.read_bytes(), png())


class TestCHSBackgroundRendering(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.renderer = CHSRenderer(self.temporary.name)
        self.renderer.set_enabled(True)
        self.canvas = TestMap()
        self.canvas._center_lat, self.canvas._center_lon, self.canvas._zoom = (
            49.3,
            -123.17,
            14,
        )
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 300)
        self.cr = cairo.Context(self.surface)
        self.addCleanup(self.renderer.set_enabled, False)

    def draw(self):
        self.renderer.draw(self.canvas, self.cr)

    def drain(self, done):
        context = GLib.MainContext.default()
        deadline = time.monotonic() + 2
        while not done() and time.monotonic() < deadline:
            context.iteration(False)
            time.sleep(0.001)
        self.assertTrue(done())

    def test_slow_worker_never_blocks_draw_and_concurrency_is_bounded(self):
        started, release = Event(), Event()

        def slow(key):
            started.set()
            release.wait(2)
            return png(), time.time()

        self.renderer.source.cached = Mock(return_value=None)
        self.renderer.source.fetch = Mock(side_effect=slow)
        self.draw()
        self.assertTrue(started.wait(1))
        try:
            for _ in range(20):
                self.draw()
            self.assertEqual(len(self.renderer._inflight), 2)
            self.assertLessEqual(len(self.renderer._pending), 12)
            self.assertFalse(release.is_set())
            self.renderer.set_enabled(False)
        finally:
            release.set()
        self.drain(lambda: not self.renderer._inflight)

    def test_disk_cache_renders_offline_without_network(self):
        self.renderer.source.cached = Mock(return_value=(png(), time.time()))
        self.renderer.source.fetch = Mock(
            side_effect=AssertionError("Network used for cached tile")
        )
        self.draw()
        self.drain(lambda: not self.renderer._inflight and not self.renderer._pending)
        self.draw()
        with patch(
            "gweatherrouting.gtk.charts.chsrenderer.time.monotonic",
            return_value=time.monotonic() + 1,
        ):
            self.draw()
        self.renderer.source.fetch.assert_not_called()
        self.surface.flush()
        offset = 150 * self.surface.get_stride() + 200 * 4
        self.assertEqual(
            bytes(self.surface.get_data())[offset : offset + 4], b"\x00\x00\xff\xff"
        )

    def test_stale_tiles_stay_visible_when_refresh_fails(self):
        self.renderer._pump = Mock()
        self.draw()
        keys = self.renderer._wanted[self.canvas]
        surface = CHSRenderer._decode(tile_key(), png())
        for key in keys:
            self.renderer._tiles[key] = (surface, 0)
        self.draw()
        self.assertTrue(all(self.renderer._pending.values()))
        key = next(iter(keys))
        self.renderer._ready(key, None, 0, "offline")
        self.assertIn(key, self.renderer._tiles)
        self.assertGreater(self.renderer._retry[key], time.time())

    def test_zoom_animation_uses_cached_parent_without_new_requests(self):
        self.renderer._pump = Mock()
        self.draw()
        self.renderer._pending.clear()
        self.canvas._zoom = 15
        self.canvas._zoom_animating = True
        self.draw()
        self.assertFalse(self.renderer._pending)
        self.assertTrue(all(key[0] == 14 for key in self.renderer._wanted[self.canvas]))
        child = tile_key(zoom=15)
        parent = (14, child[1] // 2, child[2] // 2, 1)
        self.renderer._tiles[parent] = (CHSRenderer._decode(parent, png()), time.time())
        self.assertTrue(self.renderer._parent_preview(self.cr, child, 0, 0, 1))
        self.canvas._zoom_animating = False
        self.draw()
        self.assertTrue(all(key[0] == 15 for key in self.renderer._pending))

    def test_far_outside_canada_never_requests_tiles_and_destroy_clears_work(self):
        self.renderer._pump = Mock()
        self.draw()
        self.assertTrue(self.renderer._pending)
        self.renderer.forget(self.canvas)
        self.assertFalse(self.renderer._pending)
        self.canvas._center_lat = 37.8
        self.canvas._center_lon = -122.4
        self.draw()
        self.assertFalse(self.renderer._pending)
        self.canvas._center_lat = 49.3
        self.canvas._zoom = 4
        self.draw()
        self.assertFalse(self.renderer._pending)

    def test_retina_surface_and_disabled_layer(self):
        key = tile_key(factor=2)
        surface = CHSRenderer._decode(key, png(2))
        self.assertEqual(surface.get_device_scale(), (2, 2))
        with self.assertRaises(ValueError):
            CHSRenderer._decode(key, png(1))
        self.renderer.set_enabled(False)
        self.draw()
        self.assertFalse(self.renderer._pending)

    def test_zooming_out_keeps_cached_detail_until_overview_arrives(self):
        parent = tile_key(zoom=13)
        child = (14, parent[1] * 2, parent[2] * 2, 1)
        self.renderer._tiles[child] = (CHSRenderer._decode(child, png()), time.time())
        self.assertTrue(self.renderer._fallback_preview(self.cr, parent, 0, 0, 1))
        self.surface.flush()
        data = bytes(self.surface.get_data())
        self.assertEqual(
            data[64 * self.surface.get_stride() + 64 * 4 :][:4], b"\x00\x00\xff\xff"
        )
        self.assertEqual(
            data[192 * self.surface.get_stride() + 192 * 4 :][:4], b"\x00\x00\x00\x00"
        )

    def test_large_zoom_out_gesture_bounds_tile_enumeration(self):
        self.renderer._pump = Mock()
        self.canvas._zoom = 17
        self.draw()
        self.renderer._pending.clear()
        self.canvas._zoom = 8
        self.canvas._zoom_animating = True
        self.draw()
        self.assertLess(len(self.renderer._wanted[self.canvas]), 64)
        self.assertFalse(self.renderer._pending)

    def pixel(self, x=64, y=64):
        self.surface.flush()
        offset = y * self.surface.get_stride() + x * 4
        return tuple(bytes(self.surface.get_data())[offset : offset + 4])

    def test_crossfade_preserves_brightness_and_transparent_replacement(self):
        old = CHSRenderer._decode(tile_key(), png())
        new = cairo.ImageSurface(cairo.FORMAT_ARGB32, 256, 256)
        context = cairo.Context(new)
        context.set_source_rgb(0, 0, 1)
        context.rectangle(0, 0, 128, 256)
        context.fill()
        for alpha in (0, 0.5, 1):
            self.cr.set_source_rgb(1, 1, 1)
            self.cr.paint()
            self.renderer._crossfade(self.cr, old, new, 0, 0, 1, alpha)
            blue, green, red, opacity = self.pixel()
            self.assertEqual(opacity, 255)
            self.assertEqual(green, 0)
            self.assertLessEqual(abs(red - 255 * (1 - alpha)), 1)
            self.assertLessEqual(abs(blue - 255 * alpha), 1)
            # The transparent half gradually reveals the white base map.
            blue, green, red, opacity = self.pixel(x=192)
            self.assertEqual((red, opacity), (255, 255))
            self.assertLessEqual(abs(green - 255 * alpha), 1)
            self.assertEqual(blue, green)

    def test_arrival_and_refresh_fade_then_release_previous_image(self):
        self.renderer._pump = Mock()
        self.draw()
        key = tile_key()
        old = CHSRenderer._decode(key, png())
        parent = (key[0] - 1, key[1] // 2, key[2] // 2, 1)
        self.renderer._tiles[parent] = (old, time.time())
        new = cairo.ImageSurface(cairo.FORMAT_ARGB32, 256, 256)
        self.renderer._tiles[key] = (new, time.time())
        with patch(
            "gweatherrouting.gtk.charts.chsrenderer.time.monotonic", return_value=10
        ):
            self.draw()
            previous = self.renderer._blends[self.canvas][key][2]
            self.assertIsNotNone(previous)
            self.canvas.add_tick_callback.assert_called_once()
        with patch(
            "gweatherrouting.gtk.charts.chsrenderer.time.monotonic", return_value=10.1
        ):
            self.assertTrue(self.renderer._tick(self.canvas, None))
        with patch(
            "gweatherrouting.gtk.charts.chsrenderer.time.monotonic", return_value=10.3
        ):
            self.assertFalse(self.renderer._tick(self.canvas, None))
            self.draw()
            self.assertIsNone(self.renderer._blends[self.canvas][key][2])
        replacement = CHSRenderer._decode(key, png())
        self.renderer._tiles[key] = (replacement, time.time())
        self.draw()
        self.assertIs(self.renderer._blends[self.canvas][key][2], new)
        self.renderer.forget(self.canvas)
        self.canvas.remove_tick_callback.assert_called_once_with(1)
        self.assertNotIn(self.canvas, self.renderer._blends)

    def test_cached_zoom_level_crossfades_and_disabling_stops_ticks(self):
        self.renderer._pump = Mock()
        self.draw()
        self.canvas._zoom = 15
        key = tile_key(zoom=15)
        self.renderer._tiles[key] = (CHSRenderer._decode(key, png()), time.time())
        self.draw()
        self.assertIn(key, self.renderer._blends[self.canvas])
        self.assertIn(self.canvas, self.renderer._ticks)
        self.renderer.set_enabled(False)
        self.assertFalse(self.renderer._ticks)
        self.assertFalse(self.renderer._blends)
        self.canvas.remove_tick_callback.assert_called_once_with(1)
