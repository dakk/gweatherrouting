"""A delayed, actionable hover card for missing detailed nautical charts."""

import logging
import math
import time
from pathlib import Path
from threading import Thread

from gi.repository import Gdk, GLib, Gtk

from gweatherrouting.core.enccharts import ENCCatalog
from gweatherrouting.core.storage import DATA_DIR

logger = logging.getLogger("gweatherrouting")


class ChartDownloadHover:
    def __init__(self, map_widget, chart_manager):
        self.map = map_widget
        self.manager = chart_manager
        self.catalog = ENCCatalog(Path(DATA_DIR) / "enc")
        self._timer = 0
        self._leave_timer = 0
        self._position = None
        self._pointer = None
        self._view = None
        self._loading = False
        self._retry_after = 0.0
        self._downloading = False
        self._disposed = False
        self._cell = None
        self._existing = None
        self._download_path = None

        self.card = Gtk.Popover.new(self.map)
        self.card.set_modal(False)
        self.card.set_position(Gtk.PositionType.BOTTOM)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(12)
        self.title = Gtk.Label(label="Detailed chart available")
        self.title.set_xalign(0)
        box.add(self.title)
        self.description = Gtk.Label()
        self.description.set_xalign(0)
        self.description.set_line_wrap(True)
        self.description.set_max_width_chars(42)
        box.add(self.description)
        row = Gtk.Box(spacing=8)
        self.spinner = Gtk.Spinner()
        row.add(self.spinner)
        self.button = Gtk.Button(label="Download chart")
        self.button.connect("clicked", self._download)
        row.add(self.button)
        box.add(row)
        self.card.add(box)
        self.card.add_events(
            Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        self.card.connect("enter-notify-event", self._enter_card)
        self.card.connect("leave-notify-event", self._leave)
        self.map.add_events(Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.map.connect("motion-notify-event", self._motion)
        self.map.connect("leave-notify-event", self._leave)
        self.map.connect("button-press-event", self._cancel)
        self.map.connect("scroll-event", self._cancel)
        self.map.connect("draw", self._on_draw)
        self.map.connect("destroy", self._destroy)

    def _clear_timer(self, name):
        timer = getattr(self, name)
        if timer:
            GLib.source_remove(timer)
            setattr(self, name, 0)

    def _cancel(self, *args):
        self._clear_timer("_timer")
        self._clear_timer("_leave_timer")
        self._position = None
        self.card.hide()
        return False

    def _on_draw(self, widget, cr):
        view = tuple(p.get_degrees() for p in self.map.get_bbox())
        if self._view != view:
            self._view = view
            self._cancel()
            # Recheck a stationary cursor after zooming or coasting stops.
            moving = (
                self.map._dragging
                or getattr(self.map, "_zoom_animating", False)
                or getattr(self.map, "_inertia", None)
            )
            if self._pointer and not moving and not self._downloading:
                self._position = self._pointer
                self._timer = GLib.timeout_add(700, self._hover)
        return False

    def _motion(self, widget, event):
        self._pointer = (event.x, event.y)
        if self.map._dragging or self._downloading:
            return False
        self._clear_timer("_leave_timer")
        if self._position:
            distance = math.hypot(
                event.x - self._position[0], event.y - self._position[1]
            )
            if distance < 8:
                return False
        self._position = (event.x, event.y)
        self._clear_timer("_timer")
        self._timer = GLib.timeout_add(700, self._hover)
        return False

    def _enter_card(self, *args):
        self._clear_timer("_timer")
        self._clear_timer("_leave_timer")
        return False

    def _leave(self, widget, event):
        if event.detail == Gdk.NotifyType.INFERIOR:
            return False
        if widget is self.map:
            self._pointer = None
        self._clear_timer("_timer")
        self._clear_timer("_leave_timer")
        self._leave_timer = GLib.timeout_add(300, self._hide)
        return False

    def _hide(self):
        self._leave_timer = 0
        self._position = None
        self.card.hide()
        return False

    def _hover(self):
        self._timer = 0
        if self._disposed or not self._position or self._downloading:
            return False
        self.card.hide()
        lat, lon = self.map.convert_screen_to_geographic(*self._position).get_degrees()
        lon = (lon + 180) % 360 - 180
        if not self.catalog.cells:
            self._load_catalog()
        self._cell, self._existing = self.manager.chart_suggestion_at(
            self.catalog, lat, lon, self.map.get_scale()
        )
        self._download_path = (
            self.catalog.downloaded_path(self._cell) if self._cell else None
        )
        if not self._cell and not self._existing:
            return False
        if self._existing:
            self.title.set_text("Better chart for this zoom")
            native_scale = getattr(self._existing, "_native_scale", 0)
            scale = f" · 1:{native_scale:,}" if native_scale else ""
            self.description.set_text(
                f"{Path(self._existing.path).stem}{scale}\n"
                "Enable the chart already downloaded for this zoom level."
            )
            self.button.set_label("Enable chart")
        else:
            self.title.set_text("Better chart for this zoom")
            size = (
                f" · {self._cell.size / 1024 / 1024:.1f} MB" if self._cell.size else ""
            )
            action = (
                "Use the chart already downloaded for this zoom level."
                if self._download_path
                else "Download this chart for offline use at this zoom level."
            )
            self.description.set_text(
                f"{self._cell.title}\nNOAA · 1:{self._cell.scale:,}{size}\n" f"{action}"
            )
            self.button.set_label(
                "Use downloaded chart" if self._download_path else "Download chart"
            )
        self.button.set_sensitive(True)
        rectangle = Gdk.Rectangle()
        rectangle.x, rectangle.y = (int(v) for v in self._position)
        rectangle.width = rectangle.height = 1
        self.card.set_pointing_to(rectangle)
        self.card.show_all()
        self.spinner.hide()
        self.card.popup()
        return False

    def _load_catalog(self):
        if self._loading or time.monotonic() < self._retry_after:
            return
        self._loading = True

        def worker():
            error = None
            try:
                self.catalog.load()
            except Exception as exc:
                error = str(exc)
            GLib.idle_add(self._catalog_loaded, error)

        Thread(target=worker, daemon=True).start()

    def _catalog_loaded(self, error):
        self._loading = False
        if self._disposed:
            return False
        if error:
            self._retry_after = time.monotonic() + 60
            logger.warning("Unable to discover NOAA charts: %s", error)
        else:
            self._hover()
        return False

    def _download(self, button):
        if self._downloading:
            return
        if self._existing:
            self._downloaded(self._existing.path, None)
            return
        if self._download_path:
            self._downloaded(self._download_path, None)
            return
        cell = self._cell
        if cell is None:
            return
        self._downloading = True
        self.button.set_sensitive(False)
        self.button.set_label("Downloading…")
        self.spinner.show()
        self.spinner.start()

        def worker():
            path, error = None, None
            try:
                path = self.catalog.download(cell)
            except Exception as exc:
                error = str(exc)
            GLib.idle_add(self._downloaded, path, error)

        Thread(target=worker, daemon=True).start()

    def _downloaded(self, path, error):
        self._downloading = False
        if self._disposed:
            return False
        self.spinner.stop()
        self.spinner.hide()
        if not error:
            try:
                self.manager.enable_downloaded_chart(path)
            except Exception as exc:
                error = str(exc)
        if error:
            self.title.set_text("Couldn’t load the chart")
            self.description.set_text(f"Check your connection and try again.\n{error}")
            self.button.set_label("Retry")
            self.button.set_sensitive(True)
        else:
            self.card.hide()
        return False

    def _destroy(self, *args):
        self._disposed = True
        self._cancel()
        self.card.destroy()
