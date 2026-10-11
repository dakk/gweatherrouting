"""Debounced cursor weather queries with private, bounded GRIB handles."""

from collections import OrderedDict
from threading import Thread

from gi.repository import GLib

from .windrenderer import DisplayGrib


class WindCursorSampler:
    def __init__(self):
        self._timer = 0
        self._generation = 0
        self._pending = None
        self._running = False
        self._closed = False
        self._gribs = OrderedDict()

    def request(self, sources, forecast, lat, lon, callback):
        self.cancel()
        if self._closed or not sources:
            return
        self._pending = (self._generation, tuple(sources), forecast, lat, lon, callback)
        self._timer = GLib.timeout_add(120, self._start)

    def cancel(self):
        self._generation += 1
        self._pending = None
        if self._timer:
            GLib.source_remove(self._timer)
            self._timer = 0

    def close(self, *args):
        self.cancel()
        self._closed = True
        if not self._running:
            self._gribs.clear()

    def _start(self):
        self._timer = 0
        if self._running or self._pending is None or self._closed:
            return False
        request, self._pending = self._pending, None
        self._running = True

        def worker():
            try:
                result = self._sample(*request[1:5])
            except Exception:
                result = None
            GLib.idle_add(self._ready, request, result)

        Thread(target=worker, name="wind-cursor", daemon=True).start()
        return False

    def _sample(self, sources, forecast, lat, lon):
        for source in sources:
            try:
                grib = self._gribs.get(source)
                if grib is None:
                    grib = DisplayGrib(source)
                    self._gribs[source] = grib
                    if len(self._gribs) > 2:
                        self._gribs.popitem(last=False)
                self._gribs.move_to_end(source)
                wind = grib.get_wind_at(forecast, lat, lon)
                if wind is not None:
                    return wind
            except Exception:
                # Match the manager: try other enabled sources for this point.
                continue
        return None

    def _ready(self, request, result):
        self._running = False
        if not self._closed and request[0] == self._generation:
            request[5](result)
        if self._closed:
            self._gribs.clear()
        elif self._pending is not None and not self._timer:
            self._start()
        return False
