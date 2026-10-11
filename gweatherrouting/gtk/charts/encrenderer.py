"""Render ENC detail off the GTK thread; transform the last image during gestures."""

from collections import OrderedDict

import cairo
from osgeo import ogr

from gweatherrouting.core.enccharts import chart_scale_rank, chart_scale_visible
from gweatherrouting.gtk.widgets.mapwidget import MapPoint
from gweatherrouting.gtk.widgets.overlayrenderer import OverlayRenderer

from .chartlayer import ChartLayer
from .gdalvectorchart import GDALVectorChart
from .vectordrawer.s57chartdrawer import S57ChartDrawer


def coverage_path(cr, viewport, geometry):
    """Append polygon rings to a Cairo clip, including islands and holes."""
    kind = ogr.GT_Flatten(geometry.GetGeometryType())
    if kind == ogr.wkbPolygon:
        for index in range(geometry.GetGeometryCount()):
            ring = geometry.GetGeometryRef(index)
            for point_index, (lon, lat, *_) in enumerate(ring.GetPoints()):
                x, y = viewport.convert_geographic_to_screen(MapPoint(lat, lon))
                if point_index == 0:
                    cr.move_to(x, y)
                else:
                    cr.line_to(x, y)
            cr.close_path()
    elif kind in (ogr.wkbMultiPolygon, ogr.wkbGeometryCollection):
        for index in range(geometry.GetGeometryCount()):
            coverage_path(cr, viewport, geometry.GetGeometryRef(index))


class ENCOverlayRenderer(OverlayRenderer):
    def __init__(self):
        super().__init__()
        # These GDAL handles belong exclusively to the rendering worker.
        self._charts = OrderedDict()

    def _render(self, job):
        viewport = job.viewport
        surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32,
            viewport.width * job.factor,
            viewport.height * job.factor,
        )
        surface.set_device_scale(job.factor, job.factor)
        cr = cairo.Context(surface)
        p1, p2 = viewport.get_bbox()
        bounding = ogr.CreateGeometryFromWkt(
            ChartLayer.get_bounding_wkt_of_coords(*p1.get_degrees(), *p2.get_degrees())
        )
        min_lon, max_lon, min_lat, max_lat = bounding.GetEnvelope()
        # Fill each location with its best available scale, independent of import
        # order. Other charts contribute only where that coverage ends.
        covered = None
        charts = sorted(
            job.charts,
            key=lambda c: (chart_scale_rank(c[1], viewport.get_scale()), c[0]),
        )
        for path, native_scale, envelopes in charts:
            if job.cancel.is_set():
                return None
            if not chart_scale_visible(native_scale, viewport.get_scale()):
                continue
            if envelopes and not any(
                a <= max_lon and b >= min_lon and c <= max_lat and d >= min_lat
                for a, b, c, d in envelopes
            ):
                continue
            chart = self._worker_chart(path, native_scale, job.palette)
            region = None
            for geometry in chart._coverage:
                region = geometry.Clone() if region is None else region.Union(geometry)
            known_coverage = region is not None
            region = (
                region.Intersection(bounding)
                if region is not None
                else bounding.Clone()
            )
            if covered is not None:
                region = region.Difference(covered)
            if region.IsEmpty():
                continue
            cr.save()
            cr.new_path()
            coverage_path(cr, viewport, region)
            cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            cr.clip()
            chart.do_draw(viewport, cr)
            cr.restore()
            if known_coverage:
                covered = region if covered is None else covered.Union(region)
        surface.flush()
        return None if job.cancel.is_set() else surface

    def _worker_chart(self, path, native_scale, palette):
        chart = self._charts.get(path)
        if chart is None:
            # No GTK objects, symbol-provider initialization or settings callbacks here.
            chart = GDALVectorChart.__new__(GDALVectorChart)
            chart.vector_file = ogr.Open(path)
            if chart.vector_file is None:
                raise ValueError(f"Cannot open chart {path}")
            chart._coverage = GDALVectorChart.read_coverage(chart.vector_file)
            chart._native_scale = native_scale
            chart.drawer = S57ChartDrawer.__new__(S57ChartDrawer)
            self._charts[path] = chart
            if len(self._charts) > 8:
                self._charts.popitem(last=False)
        self._charts.move_to_end(path)
        chart.drawer.palette = palette
        return chart
