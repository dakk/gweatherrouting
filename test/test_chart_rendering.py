"""Rendering cache regression checks using Cairo and a map projection, without windows."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from weakref import WeakKeyDictionary

import cairo

from gweatherrouting.gtk.charts.chartmanager import ChartManager
from gweatherrouting.gtk.charts.gdalvectorchart import GDALVectorChart
from gweatherrouting.gtk.charts.vectordrawer.s57chartdrawer import S57ChartDrawer
from gweatherrouting.gtk.widgets.mapwidget import MapPoint, MapViewport
from test.map_helpers import MapCanvas as TestMap


class DotLayer:
    enabled = True

    def __init__(self):
        self.draws = 0

    def do_draw(self, viewport, cr):
        self.draws += 1
        self.viewport = viewport
        x, y = viewport.convert_geographic_to_screen(MapPoint(47.6, -122.4))
        cr.set_source_rgb(1, 0, 0)
        cr.rectangle(round(x) - 2, round(y) - 2, 4, 4)
        cr.fill()


class TestChartSurfaceCache(unittest.TestCase):
    def setUp(self):
        self.canvas = TestMap()
        self.layer = DotLayer()
        self.manager = SimpleNamespace(
            charts=[self.layer], _chart_surfaces=WeakKeyDictionary()
        )
        self.draw = lambda cr: ChartManager._draw_base(
            self.manager, self.canvas, cr, self.manager.charts
        )

    def render(self):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 300)
        self.draw(cairo.Context(surface))
        surface.flush()
        return surface

    def test_repaint_and_small_pan_reuse_pixels(self):
        self.render()
        self.render()
        self.assertEqual(self.layer.draws, 1)
        self.canvas._center_lon = self.canvas._x_to_lon(
            self.canvas._lon_to_x(-122.4) + 10
        )
        surface = self.render()
        self.assertEqual(self.layer.draws, 1)
        # The world-fixed dot moves ten pixels left, without rendering it again.
        data = bytes(surface.get_data())
        self.assertEqual(data[150 * surface.get_stride() + 190 * 4 + 2], 255)
        self.assertEqual(data[150 * surface.get_stride() + 200 * 4 + 2], 0)

    def test_large_pan_zoom_resize_and_density_invalidate(self):
        self.render()
        self.canvas._center_lon += 1
        self.render()
        self.canvas._zoom += 1
        self.render()
        self.canvas.width += 10
        self.render()
        self.canvas.factor = 2
        self.render()
        self.assertEqual(self.layer.draws, 5)
        cache = self.manager._chart_surfaces[self.canvas]
        self.assertEqual(cache[2].get_device_scale(), (2.0, 2.0))

    def test_layer_toggle_and_async_completion_invalidate(self):
        self.render()
        self.layer.enabled = False
        self.render()
        self.layer.enabled = True
        self.render()
        self.assertEqual(self.layer.draws, 2)
        self.layer.viewport.queue_draw()
        self.assertFalse(self.manager._chart_surfaces)
        self.render()
        self.assertEqual(self.layer.draws, 3)

    def test_palette_invalidates(self):
        self.render()
        self.manager.maps = []
        ChartManager.on_chart_palette_changed(self.manager, "dark")
        self.render()
        self.assertEqual(self.layer.draws, 2)

    def test_zoom_animation_transforms_cache_until_settled(self):
        self.render()
        self.canvas._zoom_animating = True
        for zoom in (12.1, 12.3, 12.7, 12.99):
            self.canvas._zoom = zoom
            self.render()
        self.assertEqual(self.layer.draws, 1)
        self.canvas._zoom_animating = False
        self.canvas._zoom = 13
        self.render()
        self.assertEqual(self.layer.draws, 2)


class TestENCVisibility(unittest.TestCase):
    def setUp(self):
        self.canvas = TestMap()
        self.chart = GDALVectorChart.__new__(GDALVectorChart)
        self.chart.drawer = S57ChartDrawer.__new__(S57ChartDrawer)
        self.chart.drawer.draw = Mock()
        self.chart.vector_file = Mock()
        self.chart._coverage = []
        self.chart._native_scale = 12000

    def test_offscreen_chart_skips_feature_reading(self):
        self.chart._coverage = [Mock()]
        self.chart._coverage[0].Intersects.return_value = False
        self.chart.do_draw(self.canvas, Mock())
        self.chart.drawer.draw.assert_not_called()

    def test_overview_skipped_at_harbor_zoom(self):
        self.chart._native_scale = 3500000
        self.chart.do_draw(self.canvas, Mock())
        self.chart.drawer.draw.assert_not_called()
        self.chart._coverage = [Mock()]
        self.chart._coverage[0].Intersects.return_value = True
        self.assertFalse(self.chart.covers_point(47.6, -122.4, self.canvas.get_scale()))
        self.canvas._zoom = 7
        self.chart.do_draw(self.canvas, Mock())
        self.chart.drawer.draw.assert_called_once()

    def test_harbor_chart_skipped_only_when_zoomed_far_out(self):
        self.canvas._zoom = 5
        self.chart.do_draw(self.canvas, Mock())
        self.chart.drawer.draw.assert_not_called()
        self.canvas._zoom = 16
        self.chart.do_draw(self.canvas, Mock())
        self.chart.drawer.draw.assert_called_once()


class TestSoundingBatches(unittest.TestCase):
    def test_group_preserves_all_depths_in_one_projection_batch(self):
        from osgeo import ogr

        geometry = ogr.Geometry(ogr.wkbMultiPoint25D)
        for index in range(100):
            point = ogr.Geometry(ogr.wkbPoint25D)
            point.AddPoint(-122.4 + index * 0.001, 47.6, index + 0.5)
            geometry.AddGeometry(point)
        drawer = S57ChartDrawer.__new__(S57ChartDrawer)
        areas, lines, points = [], [], []
        drawer._collect("SOUNDG", {}, geometry, areas, lines, points)
        self.assertEqual(len(points), 1)
        self.assertEqual(len(points[0].geometry), 100)
        self.assertEqual(points[0].geometry[0], (47.6, -122.4, 0.5))
        self.assertEqual(points[0].geometry[-1][2], 99.5)

    def test_prepared_geometry_reused_at_same_tolerance(self):
        from collections import OrderedDict
        from osgeo import ogr

        geometry = ogr.CreateGeometryFromWkt("LINESTRING(-122.4 47.6, -122.3 47.7)")
        feature = Mock()
        feature.GetFID.return_value = 10
        feature.GetGeometryRef.return_value = geometry
        drawer = S57ChartDrawer.__new__(S57ChartDrawer)
        drawer._feature_cache = OrderedDict()
        dataset = object()
        first = drawer._prepare_feature(dataset, "DEPCNT", feature, [], 0.00001)
        second = drawer._prepare_feature(dataset, "DEPCNT", feature, [], 0.00001)
        self.assertIs(first, second)
        feature.GetGeometryRef.assert_called_once()
        drawer._prepare_feature(dataset, "DEPCNT", feature, [], 0.000005)
        self.assertEqual(feature.GetGeometryRef.call_count, 2)


class TestBackgroundENC(unittest.TestCase):
    def setUp(self):
        from gweatherrouting.gtk.charts.encrenderer import ENCOverlayRenderer

        self.canvas = TestMap()
        self.renderer = ENCOverlayRenderer()
        self.specs = (("test.000", 12000, ()),)
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 300)
        self.cr = cairo.Context(self.surface)
        self.addCleanup(self.renderer.forget, self.canvas)

    def test_draw_returns_while_background_render_is_blocked(self):
        from threading import Event
        from gi.repository import GLib

        started, release, finished = Event(), Event(), Event()
        self.addCleanup(release.set)

        def slow_render(job):
            started.set()
            release.wait(2)
            finished.set()
            return cairo.ImageSurface(cairo.FORMAT_ARGB32, 912, 812)

        self.renderer._render = slow_render
        self.renderer.draw(self.canvas, self.cr, self.specs, "cm93")
        self.assertTrue(started.wait(1))
        for index in range(20):
            self.canvas._center_lon += 0.00001
            self.renderer.draw(self.canvas, self.cr, self.specs, "cm93")
        self.assertFalse(finished.is_set())
        release.set()
        self.assertTrue(finished.wait(1))
        # Deliver the worker's completion on the main thread.
        context = GLib.MainContext.default()
        import time

        deadline = time.monotonic() + 1
        while self.renderer._running and time.monotonic() < deadline:
            context.iteration(False)
            time.sleep(0.001)
        self.assertFalse(self.renderer._running)
        self.assertIsNotNone(self.renderer._states[self.canvas].frame)

    def test_rapid_pan_and_zoom_keep_only_latest_pending_view(self):
        self.renderer._start_next = Mock()
        jobs = []
        for index in range(20):
            self.canvas._zoom = 10 + index % 4
            self.canvas._center_lon += 0.5
            self.renderer.draw(self.canvas, self.cr, self.specs, "cm93")
            jobs.append(self.renderer._states[self.canvas].requested)
        self.assertEqual(len(self.renderer._pending), 1)
        self.assertTrue(all(job.cancel.is_set() for job in jobs[:-1]))
        self.assertFalse(jobs[-1].cancel.is_set())
        self.assertEqual(jobs[-1].viewport._center_lon, self.canvas._center_lon)

    def test_zoom_animation_waits_until_settled_to_request_detail(self):
        self.renderer._start_next = Mock()
        self.renderer.draw(self.canvas, self.cr, self.specs, "cm93")
        state = self.renderer._states[self.canvas]
        original = state.requested
        self.canvas._zoom_animating = True
        for zoom in (12.1, 12.3, 12.7, 12.99):
            self.canvas._zoom = zoom
            self.renderer.draw(self.canvas, self.cr, self.specs, "cm93")
        self.renderer._start_next.assert_called_once()
        self.canvas._zoom_animating = False
        self.canvas._zoom = 13
        self.renderer.draw(self.canvas, self.cr, self.specs, "cm93")
        self.assertTrue(original.cancel.is_set())
        self.assertEqual(state.requested.viewport._zoom, 13)
        self.assertEqual(self.renderer._start_next.call_count, 2)

    def test_stale_palette_or_destroyed_map_cannot_publish(self):
        self.renderer._start_next = Mock()
        self.renderer.draw(self.canvas, self.cr, self.specs, "cm93")
        old = self.renderer._states[self.canvas].requested
        self.renderer.draw(self.canvas, self.cr, self.specs, "dark")
        self.renderer._completed(self.canvas, old, self.surface, None)
        self.assertIsNone(self.renderer._states[self.canvas].frame)
        new = self.renderer._states[self.canvas].requested
        self.renderer.forget(self.canvas)
        self.renderer._completed(self.canvas, new, self.surface, None)
        self.assertNotIn(self.canvas, self.renderer._states)

    def test_preview_stays_geographically_aligned_during_pan_and_zoom(self):
        from gweatherrouting.gtk.widgets.overlayrenderer import MARGIN

        self.renderer._start_next = Mock()
        self.renderer.draw(self.canvas, self.cr, self.specs, "cm93")
        state = self.renderer._states[self.canvas]
        job = state.requested
        image = cairo.ImageSurface(
            cairo.FORMAT_ARGB32, job.viewport.width, job.viewport.height
        )
        context = cairo.Context(image)
        context.set_source_rgb(1, 0, 0)
        context.rectangle(200 + MARGIN - 2, 150 + MARGIN - 2, 4, 4)
        context.fill()
        state.frame = (job, image)
        self.canvas._zoom += 1
        self.canvas._center_lon = self.canvas._x_to_lon(
            self.canvas._lon_to_x(-122.4) + 10
        )
        self.renderer.draw(self.canvas, self.cr, self.specs, "cm93")
        self.surface.flush()
        data = bytes(self.surface.get_data())
        self.assertEqual(data[150 * self.surface.get_stride() + 190 * 4 + 2], 255)
        self.assertEqual(data[150 * self.surface.get_stride() + 200 * 4 + 2], 0)

    def test_manager_never_draws_enc_features_on_the_ui_thread(self):
        manager = ChartManager(Mock())
        manager._palette = "cm93"
        manager._enc_renderer._start_next = Mock()
        chart = GDALVectorChart.__new__(GDALVectorChart)
        chart.drawer = S57ChartDrawer.__new__(S57ChartDrawer)
        chart.path = "test.000"
        chart.enabled = True
        chart._native_scale = 12000
        chart._coverage_envelopes = ()
        chart.do_draw = Mock(
            side_effect=AssertionError("UI thread rendered chart features")
        )
        manager.charts = [chart]
        manager.do_draw(self.canvas, self.cr)
        chart.do_draw.assert_not_called()
        self.assertEqual(len(manager._enc_renderer._pending), 1)
        manager._enc_renderer.forget(self.canvas)

    def test_background_surface_preserves_retina_resolution(self):
        from gweatherrouting.gtk.widgets.overlayrenderer import MARGIN, RenderJob

        viewport = MapViewport(self.canvas, MARGIN, lambda: None)
        job = RenderJob((), viewport, (), 2, "cm93")
        viewport.render_cancelled = job.cancel.is_set
        surface = self.renderer._render(job)
        self.assertEqual(surface.get_device_scale(), (2.0, 2.0))
        self.assertEqual(surface.get_width(), viewport.width * 2)
        self.assertEqual(surface.get_height(), viewport.height * 2)
