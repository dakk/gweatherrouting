"""Wind display cropping, private GRIB handles, and background image reuse."""

from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event, get_ident
from types import SimpleNamespace
import time
import unittest
from unittest.mock import Mock, patch

import cairo
from gi.repository import GLib
import numpy as np
from osgeo import gdal

from gweatherrouting.core.grib import Grib
from gweatherrouting.gtk.maplayers.gribmaplayer import (
    GribMapLayer,
    WindPainter,
    wind_on_ground,
)
from gweatherrouting.gtk.maplayers.windrenderer import DisplayGrib, WindLandMask
from test.map_helpers import MapCanvas as TestMap


class TestDisplayGrib(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = str(Path(temporary.name) / "wind.tif")
        dataset = gdal.GetDriverByName("GTiff").Create(path, 4, 3, 4, gdal.GDT_Float32)
        dataset.SetGeoTransform((-124, 1, 0, 50, 0, -1))
        for index, (hour, element, value) in enumerate(
            ((0, "UGRD", 2), (0, "VGRD", 4), (3, "UGRD", 8), (3, "VGRD", 10)), 1
        ):
            band = dataset.GetRasterBand(index)
            band.SetMetadata(
                {"GRIB_ELEMENT": element, "GRIB_FORECAST_SECONDS": str(hour * 3600)}
            )
            band.WriteArray(np.full((3, 4), value, dtype=np.float32))
        band = None
        dataset = None
        self.source = Grib(path, "wind", "test", [], datetime(2026, 1, 1), 3)
        self.display = DisplayGrib(self.source)

    def test_visible_crop_matches_existing_forecast_interpolation(self):
        bounds = ((48.9, -123.1), (49.1, -121.9))
        forecast = self.source.start_time + timedelta(hours=1)
        expected = self.source.get_wind(forecast, bounds)
        actual = self.display.get_wind(forecast, bounds)
        self.assertEqual(len(actual), 2)
        self.assertEqual(actual, expected)
        self.assertIsNot(self.source.dataset, self.display.dataset)
        # No global list of GRIB tuples is built for the display.
        self.assertEqual(len(self.display._arrays), 2)

    def test_outside_grid_does_not_read_band_arrays(self):
        self.assertEqual(self.display._get_wind_data(0, ((0, 0), (1, 1))), [])
        self.assertFalse(self.display._arrays)

    def test_repeated_crops_reuse_bands_and_four_hour_cache_is_bounded(self):
        bounds = ((48, -124), (50, -121))
        first = self.display._get_wind_data(0, bounds)
        arrays = self.display._arrays[0]
        self.assertEqual(self.display._get_wind_data(0, bounds), first)
        self.assertIs(self.display._arrays[0], arrays)
        self.display._find_bands_for_time = Mock(return_value=(Mock(), Mock()))
        for band in self.display._find_bands_for_time.return_value:
            band.ReadAsArray.return_value = np.ones((3, 4))
        for hour in range(1, 8):
            self.display._get_wind_data(hour, bounds)
        self.assertEqual(len(self.display._arrays), 4)

    def test_prepared_land_mask_matches_known_land_and_water(self):
        mask = WindLandMask()
        for lat, lon, land in (
            (49.28, -123.12, True),
            (48.5, -125, False),
            (40, -100, True),
            (0, -140, False),
            (51.5, -0.1, True),
        ):
            self.assertEqual(mask.contains(lat, lon), land)
            self.assertEqual(mask.contains(lat, lon), land)
        self.assertEqual(mask.contains.cache_info().hits, 5)

    def test_prepared_land_mask_preserves_holes(self):
        shapes = [
            {
                "properties": {"bbox": [[0, 0], [4, 4]]},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]],
                        [[1, 1], [1, 3], [3, 3], [3, 1], [1, 1]],
                    ],
                },
            }
        ]
        with patch("gweatherrouting.gtk.maplayers.windrenderer.COUNTRY_SHAPES", shapes):
            mask = WindLandMask()
            self.assertTrue(mask.contains(0.5, 0.5))
            self.assertFalse(mask.contains(2, 2))


class TestWindOverlay(unittest.TestCase):
    def setUp(self):
        self.canvas = TestMap()
        self.canvas.connect = Mock()
        self.settings = SimpleNamespace(gribArrowOpacity=0.8, gribArrowOnGround=True)
        self.clock = SimpleNamespace(time=datetime(2026, 1, 1), connect=Mock())
        self.source = object()
        self.manager = SimpleNamespace(gribs=[self.source])
        self.layer = GribMapLayer(self.manager, self.clock, self.settings)
        self.renderer = self.layer._renderer
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 300)
        self.cr = cairo.Context(self.surface)
        self.renderer._load_wind = Mock(
            return_value=[
                [(180, 6, (47.5 + row * 0.1, -122.5 + col * 0.1)) for row in range(3)]
                for col in range(3)
            ]
        )
        self.addCleanup(self.layer._forget, self.canvas)

    def draw(self):
        self.layer.do_draw(self.canvas, self.cr)

    def drain(self):
        deadline = time.monotonic() + 2
        context = GLib.MainContext.default()
        while self.renderer._running and time.monotonic() < deadline:
            context.iteration(False)
            time.sleep(0.001)
        self.assertFalse(self.renderer._running)

    def test_slow_grib_load_never_blocks_ui_and_uses_one_worker(self):
        started, release = Event(), Event()
        self.addCleanup(release.set)
        ui_thread = get_ident()

        def slow(job):
            self.assertNotEqual(get_ident(), ui_thread)
            started.set()
            release.wait(2)
            return []

        self.renderer._load_wind.side_effect = slow
        self.draw()
        self.assertTrue(started.wait(1))
        for _ in range(20):
            self.canvas._center_lon += 0.00001
            self.draw()
        self.assertEqual(self.renderer._load_wind.call_count, 1)
        self.assertFalse(release.is_set())
        release.set()
        self.drain()
        self.assertIsNotNone(self.renderer._states[self.canvas].frame)

    def test_pan_and_animated_zoom_reuse_frame_without_grib_work(self):
        self.draw()
        self.drain()
        for _ in range(20):
            self.canvas._center_lon += 0.00001
            self.draw()
        self.canvas._zoom_animating = True
        for zoom in (12.1, 12.4, 12.8, 13):
            self.canvas._zoom = zoom
            self.draw()
        self.renderer._load_wind.assert_called_once()
        self.canvas._zoom_animating = False
        self.draw()
        self.drain()
        self.assertEqual(self.renderer._load_wind.call_count, 2)

    def test_forecast_style_sources_and_retina_invalidate_frame(self):
        self.draw()
        self.drain()
        for change in (
            lambda: setattr(self.clock, "time", self.clock.time + timedelta(hours=1)),
            lambda: setattr(self.settings, "gribArrowOpacity", 0.3),
            lambda: setattr(self.settings, "gribArrowOnGround", False),
            lambda: setattr(self.canvas, "factor", 2),
            lambda: setattr(self.manager, "gribs", [object()]),
        ):
            change()
            self.draw()
            self.drain()
        self.assertEqual(self.renderer._load_wind.call_count, 6)
        job, surface = self.renderer._states[self.canvas].frame
        self.assertEqual(surface.get_device_scale(), (2, 2))
        self.assertEqual(surface.get_width(), job.viewport.width * 2)

    def test_disabling_cancels_running_job_and_cannot_publish_stale_frame(self):
        self.renderer._start_next = Mock()
        self.draw()
        job = self.renderer._states[self.canvas].requested
        self.layer.set_visible(False)
        self.assertTrue(job.cancel.is_set())
        self.renderer._completed(self.canvas, job, self.surface, None)
        self.assertNotIn(self.canvas, self.renderer._states)
        self.assertFalse(self.renderer._pending)

    def test_no_sources_clears_overlay_and_destroy_releases_map(self):
        self.draw()
        self.drain()
        self.manager.gribs.clear()
        self.draw()
        self.assertNotIn(self.canvas, self.renderer._states)
        self.layer._forget(self.canvas)
        self.assertNotIn(self.canvas, self.layer._maps)

    def test_time_change_requests_redraw(self):
        self.draw()
        self.drain()
        self.canvas.queue_draw.reset_mock()
        self.layer.on_time_change(self.clock)
        self.canvas.queue_draw.assert_called_once()

    def test_old_forecast_completion_cannot_replace_new_time(self):
        self.renderer._start_next = Mock()
        self.draw()
        old = self.renderer._states[self.canvas].requested
        self.clock.time += timedelta(hours=1)
        self.draw()
        self.assertTrue(old.cancel.is_set())
        self.renderer._completed(self.canvas, old, self.surface, None)
        self.assertIsNone(self.renderer._states[self.canvas].frame)

    def clear_output(self):
        self.cr.save()
        self.cr.set_operator(cairo.OPERATOR_CLEAR)
        self.cr.paint()
        self.cr.restore()

    def test_playback_keeps_gradient_until_latest_forecast_is_complete(self):
        self.draw()
        self.drain()
        self.clear_output()
        self.draw()
        self.surface.flush()
        initial = bytes(self.surface.get_data())
        self.assertTrue(any(initial))
        self.renderer._start_next = Mock()
        jobs = []
        for _ in range(5):
            self.clock.time += timedelta(hours=1)
            self.clear_output()
            self.draw()
            self.surface.flush()
            self.assertEqual(bytes(self.surface.get_data()), initial)
            jobs.append(self.renderer._states[self.canvas].requested)
        # An obsolete forecast must not replace the visible image.
        latest = jobs[-1]
        replacement = cairo.ImageSurface(
            cairo.FORMAT_ARGB32, latest.viewport.width, latest.viewport.height
        )
        context = cairo.Context(replacement)
        context.set_source_rgba(0, 0, 1, 0.3)
        context.paint()
        self.renderer._completed(self.canvas, jobs[0], replacement, None)
        self.clear_output()
        self.draw()
        self.surface.flush()
        self.assertEqual(bytes(self.surface.get_data()), initial)
        self.renderer._completed(self.canvas, latest, replacement, None)
        self.clear_output()
        self.draw()
        self.surface.flush()
        self.assertNotEqual(bytes(self.surface.get_data()), initial)
        self.assertTrue(any(bytes(self.surface.get_data())))

    def test_playback_preview_never_keeps_removed_sources_or_old_style(self):
        self.draw()
        self.drain()
        self.renderer._start_next = Mock()
        for change in (
            lambda: setattr(self.settings, "gribArrowOpacity", 0.2),
            lambda: setattr(self.settings, "gribArrowOnGround", False),
            lambda: setattr(self.canvas, "factor", 2),
            lambda: setattr(self.manager, "gribs", [object()]),
        ):
            self.settings.gribArrowOpacity = 0.8
            self.settings.gribArrowOnGround = True
            self.canvas.factor = 1
            self.manager.gribs = [self.source]
            change()
            self.clear_output()
            self.draw()
            self.surface.flush()
            self.assertFalse(any(bytes(self.surface.get_data())))

    def test_forecast_without_data_replaces_preview_with_empty_image(self):
        self.draw()
        self.drain()
        self.clock.time += timedelta(hours=1000)
        self.renderer._load_wind.return_value = []
        self.clear_output()
        self.draw()
        self.surface.flush()
        self.assertTrue(any(bytes(self.surface.get_data())))
        self.drain()
        self.clear_output()
        self.draw()
        self.surface.flush()
        self.assertFalse(any(bytes(self.surface.get_data())))

    def test_land_mask_is_reused_between_painters(self):
        wind_on_ground.cache_clear()
        self.addCleanup(wind_on_ground.cache_clear)
        with patch(
            "gweatherrouting.gtk.maplayers.gribmaplayer.point_in_country",
            return_value=True,
        ) as mask:
            self.assertTrue(wind_on_ground(49, -123))
            self.assertTrue(wind_on_ground(49, -123))
            mask.assert_called_once()

    def test_bad_forecast_does_not_hide_other_sources(self):
        self.renderer._start_next = Mock()
        self.manager.gribs = [object(), object()]
        self.draw()
        job = self.renderer._states[self.canvas].requested
        unavailable, available = Mock(), Mock()
        unavailable.get_wind.side_effect = ValueError("Missing forecast hour")
        point = (180, 6, (47.6, -122.4))
        available.get_wind.return_value = [point]
        self.renderer._worker_grib = Mock(side_effect=[unavailable, available])
        from gweatherrouting.gtk.maplayers.windrenderer import WindOverlayRenderer

        self.assertEqual(WindOverlayRenderer._load_wind(self.renderer, job), [[point]])

    def test_painter_keeps_colored_fill_and_barbs(self):
        self.draw()
        self.drain()
        job, surface = self.renderer._states[self.canvas].frame
        surface.flush()
        self.assertTrue(any(bytes(surface.get_data())))
        self.assertIsInstance(self.renderer._painter(self.settings), WindPainter)
