"""Bounded background rendering and cached image reuse for map overlays."""

import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from threading import Event, Thread

import cairo
from gi.repository import GLib

from .mapwidget import MapViewport

logger = logging.getLogger("gweatherrouting")
MARGIN = 256


@dataclass
class RenderJob:
    key: tuple
    viewport: MapViewport
    charts: tuple
    factor: int
    palette: str
    cancel: Event = field(default_factory=Event)


@dataclass
class RenderState:
    key: tuple = ()
    frame: object = None
    requested: object = None
    retry_after: float = 0.0


def fits(viewport, canvas):
    if viewport._zoom != canvas._zoom:
        return False
    if viewport.width != canvas.get_allocated_width() + 2 * MARGIN:
        return False
    if viewport.height != canvas.get_allocated_height() + 2 * MARGIN:
        return False
    dx = viewport._lon_to_x(viewport._center_lon) - viewport._lon_to_x(
        canvas._center_lon
    )
    dy = viewport._lat_to_y(viewport._center_lat) - viewport._lat_to_y(
        canvas._center_lat
    )
    return max(abs(dx), abs(dy)) <= MARGIN / 2


def paint_viewport(canvas, cr, viewport, surface):
    ratio = 2.0 ** (canvas._zoom - viewport._zoom)
    x = canvas._lon_to_x(viewport._center_lon) - canvas._lon_to_x(canvas._center_lon)
    y = canvas._lat_to_y(viewport._center_lat) - canvas._lat_to_y(canvas._center_lat)
    x += canvas.get_allocated_width() / 2 - viewport.width * ratio / 2
    y += canvas.get_allocated_height() / 2 - viewport.height * ratio / 2
    cr.save()
    cr.translate(x, y)
    cr.scale(ratio, ratio)
    cr.set_source_surface(surface, 0, 0)
    cr.get_source().set_filter(cairo.FILTER_BILINEAR)
    cr.paint()
    cr.restore()


class OverlayRenderer:
    def __init__(self):
        self._states = {}
        self._pending = OrderedDict()
        self._running = False

    def forget(self, canvas):
        state = self._states.pop(canvas, None)
        self._pending.pop(canvas, None)
        if state and state.requested:
            state.requested.cancel.set()

    def draw(self, canvas, cr, charts, palette):
        if not charts:
            self.forget(canvas)
            return
        factor = canvas.get_scale_factor()
        key = (palette, factor, tuple(c[0] for c in charts))
        state = self._states.setdefault(canvas, RenderState())
        state.key = key
        frame = state.frame
        fresh = frame and frame[0].key == key and fits(frame[0].viewport, canvas)
        requested = state.requested
        pending = (
            requested and requested.key == key and fits(requested.viewport, canvas)
        )
        if fresh and requested and not pending:
            requested.cancel.set()
            self._pending.pop(canvas, None)
            state.requested = None
        if (
            not fresh
            and not pending
            and not getattr(canvas, "_zoom_animating", False)
            and time.monotonic() >= state.retry_after
        ):
            if requested:
                requested.cancel.set()
            viewport = MapViewport(canvas, MARGIN, lambda: None)
            job = RenderJob(key, viewport, charts, factor, palette)
            viewport.render_cancelled = job.cancel.is_set
            state.requested = job
            self._pending[canvas] = job
            self._start_next()
        if frame and self._can_preview(frame[0], key):
            self._paint(canvas, cr, *frame)

    def _can_preview(self, job, key):
        return job.key == key

    @staticmethod
    def _paint(canvas, cr, job, surface):
        paint_viewport(canvas, cr, job.viewport, surface)

    def _start_next(self):
        if self._running or not self._pending:
            return
        canvas, job = self._pending.popitem(last=False)
        self._running = True

        def worker():
            surface, error = None, None
            try:
                surface = self._render(job)
            except Exception as exc:
                error = str(exc)
            GLib.idle_add(self._completed, canvas, job, surface, error)

        Thread(target=worker, name="overlay-render", daemon=True).start()

    def _render(self, job):
        raise NotImplementedError

    def _completed(self, canvas, job, surface, error):
        self._running = False
        state = self._states.get(canvas)
        if state:
            if state.requested is job:
                state.requested = None
            if error:
                state.retry_after = time.monotonic() + 1
                logger.warning("Unable to render map overlay: %s", error)
            if surface is not None and not job.cancel.is_set() and state.key == job.key:
                state.frame = (job, surface)
                canvas.queue_draw()
        self._start_next()
        return False
