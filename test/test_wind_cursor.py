"""Pointer handling stays responsive with weather hidden, moving, or loading."""

from datetime import datetime, timedelta
from threading import Event, get_ident
from types import SimpleNamespace
import time
import unittest
from unittest.mock import Mock, patch

from gi.repository import GLib

from gweatherrouting.gtk.chartstack import ChartStack
from gweatherrouting.gtk.maplayers.windcursor import WindCursorSampler
from test.map_helpers import MapCanvas as TestMap


class TestCursorEvents(unittest.TestCase):
    def setUp(self):
        self.canvas = TestMap()
        self.canvas._dragging = False
        manager = SimpleNamespace(
            gribs=[object()],
            get_wind_at=Mock(side_effect=AssertionError("UI GRIB query")),
        )
        self.stack = SimpleNamespace(
            core=SimpleNamespace(grib_manager=manager),
            time_control=SimpleNamespace(time=datetime(2026, 1, 1)),
            status_bar=Mock(),
            tools_map_layer=Mock(),
            map=self.canvas,
            gribMapLayer=SimpleNamespace(visible=False),
            _wind_cursor=Mock(),
        )
        self.stack.tools_map_layer.on_mouse_move.return_value = False
        self.event = SimpleNamespace(x=200, y=150)

    def move(self):
        ChartStack.on_map_mouse_move(self.stack, self.canvas, self.event)

    def test_wind_hidden_never_queries_weather_and_updates_position(self):
        for _ in range(50):
            self.move()
        self.stack.core.grib_manager.get_wind_at.assert_not_called()
        self.stack._wind_cursor.request.assert_not_called()
        self.assertIn("Latitude:", self.stack.status_bar.push.call_args.args[1])

    def test_drag_zoom_and_inertia_never_start_weather_queries(self):
        self.stack.gribMapLayer.visible = True
        for field in ("_dragging", "_zoom_animating", "_inertia"):
            setattr(self.canvas, field, True)
            self.move()
            setattr(self.canvas, field, False)
        self.stack._wind_cursor.request.assert_not_called()
        self.stack.core.grib_manager.get_wind_at.assert_not_called()

    def test_frame_motion_cancels_hover_queued_before_zoom(self):
        self.canvas._dragging = False
        self.canvas._zoom_animating = True
        self.canvas._inertia = None
        self.assertFalse(
            ChartStack._cancel_cursor_during_motion(self.stack, self.canvas, None)
        )
        self.stack._wind_cursor.cancel.assert_called_once()

    def test_frame_motion_supports_canvas_without_animation_settings(self):
        self.assertFalse(
            ChartStack._cancel_cursor_during_motion(self.stack, self.canvas, None)
        )
        self.stack._wind_cursor.cancel.assert_not_called()

    def test_stationary_hover_uses_async_readout_and_converts_knots(self):
        self.stack.gribMapLayer.visible = True
        self.move()
        callback = self.stack._wind_cursor.request.call_args.args[-1]
        callback((180, 10))
        self.assertIn("19.4 kts", self.stack.status_bar.push.call_args.args[1])

    def test_late_readout_cannot_publish_after_view_time_or_visibility_changes(self):
        self.stack.gribMapLayer.visible = True
        for change in (
            lambda: setattr(self.canvas, "_zoom", self.canvas._zoom + 1),
            lambda: setattr(
                self.stack.time_control,
                "time",
                self.stack.time_control.time + timedelta(hours=1),
            ),
            lambda: setattr(self.stack.gribMapLayer, "visible", False),
        ):
            self.move()
            callback = self.stack._wind_cursor.request.call_args.args[-1]
            before = self.stack.status_bar.push.call_count
            change()
            callback((180, 10))
            self.assertEqual(self.stack.status_bar.push.call_count, before)


class TestBackgroundCursor(unittest.TestCase):
    def setUp(self):
        self.sampler = WindCursorSampler()
        self.sampler._sample = Mock(return_value=(180, 10))
        self.addCleanup(self.sampler.close)
        self.forecast = datetime(2026, 1, 1)
        self.source = object()

    def request(self, callback, lon=-123):
        self.sampler.request([self.source], self.forecast, 49, lon, callback)

    def drain_until(self, done):
        context = GLib.MainContext.default()
        deadline = time.monotonic() + 2
        while not done() and time.monotonic() < deadline:
            context.iteration(False)
            time.sleep(0.001)
        self.assertTrue(done())

    def test_rapid_pointer_events_debounce_to_one_query(self):
        callbacks = [Mock() for _ in range(30)]
        for index, callback in enumerate(callbacks):
            self.request(callback, lon=-123 + index * 0.01)
        self.drain_until(lambda: callbacks[-1].called)
        self.sampler._sample.assert_called_once()
        self.assertTrue(all(not callback.called for callback in callbacks[:-1]))

    def test_blocked_worker_coalesces_requests_and_only_publishes_latest(self):
        started, release = Event(), Event()
        self.addCleanup(release.set)
        ui_thread = get_ident()

        def slow(*args):
            self.assertNotEqual(get_ident(), ui_thread)
            started.set()
            release.wait(2)
            return (180, 10)

        self.sampler._sample.side_effect = slow
        old, latest = Mock(), Mock()
        self.request(old)
        self.drain_until(started.is_set)
        for _ in range(20):
            self.request(latest)
        self.assertEqual(self.sampler._sample.call_count, 1)
        self.assertFalse(release.is_set())
        release.set()
        self.drain_until(lambda: latest.called)
        old.assert_not_called()
        self.assertEqual(self.sampler._sample.call_count, 2)

    def test_cancel_and_close_suppress_pending_queries(self):
        callback = Mock()
        self.request(callback)
        self.sampler.cancel()
        self.assertFalse(self.sampler._timer)
        self.assertIsNone(self.sampler._pending)
        self.request(callback)
        self.sampler.close()
        self.request(callback)
        self.assertFalse(self.sampler._timer)
        self.sampler._sample.assert_not_called()

    def test_exception_clears_running_state(self):
        callback = Mock()
        self.sampler._sample.side_effect = ValueError("Invalid forecast")
        self.request(callback)
        self.drain_until(lambda: callback.called)
        callback.assert_called_once_with(None)
        self.assertFalse(self.sampler._running)

    def test_private_sources_are_reused_and_bounded(self):
        from gweatherrouting.gtk.maplayers.windcursor import WindCursorSampler

        with patch("gweatherrouting.gtk.maplayers.windcursor.DisplayGrib") as display:
            display.return_value.get_wind_at.return_value = (180, 10)
            for _ in range(2):
                self.assertEqual(
                    WindCursorSampler._sample(
                        self.sampler, [self.source], self.forecast, 49, -123
                    ),
                    (180, 10),
                )
            display.assert_called_once_with(self.source)
            for _ in range(5):
                WindCursorSampler._sample(
                    self.sampler, [object()], self.forecast, 49, -123
                )
            self.assertEqual(len(self.sampler._gribs), 2)
