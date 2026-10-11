"""Zoom selection, coverage mosaics, and better-chart download offers."""

from pathlib import Path
from tempfile import TemporaryDirectory
from types import MethodType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import cairo
from osgeo import ogr

from gweatherrouting.core.enccharts import ENCCatalog, ENCCell, chart_scale_rank
from gweatherrouting.gtk.charts.chartmanager import ChartManager
from gweatherrouting.gtk.charts.encrenderer import ENCOverlayRenderer
from gweatherrouting.gtk.widgets.overlayrenderer import RenderJob
from gweatherrouting.gtk.charts.gdalvectorchart import GDALVectorChart
from gweatherrouting.gtk.widgets.mapwidget import MapViewport
from test.map_helpers import MapCanvas as TestMap

PANEL = [(0, 0), (0, 4), (4, 4), (4, 0)]


def cell(name, scale):
    return ENCCell(name, name, scale, 100, [("E", PANEL)])


def loaded(name, scale, enabled=True):
    chart = GDALVectorChart.__new__(GDALVectorChart)
    chart.path = "/charts/" + name + ".000"
    chart.enabled = enabled
    chart._native_scale = scale
    chart.vector_file = Mock()
    chart._coverage = [ogr.CreateGeometryFromWkt("POLYGON((0 0,4 0,4 4,0 4,0 0))")]
    return chart


class TestZoomSelection(unittest.TestCase):
    def setUp(self):
        self.catalog = ENCCatalog("/unused")
        self.catalog.cells = [
            cell("US5TEST1", 12000),
            cell("US3TEST1", 80000),
            cell("US2TEST1", 350000),
        ]
        self.manager = SimpleNamespace(charts=[])
        for name in ("detailed_chart_at", "chart_suggestion_at"):
            setattr(
                self.manager,
                name,
                MethodType(getattr(ChartManager, name), self.manager),
            )

    def test_catalog_selects_harbor_coastal_and_overview_by_zoom(self):
        for scale, name in ((3, "US5TEST1"), (20, "US3TEST1"), (100, "US2TEST1")):
            self.assertEqual(self.catalog.chart_at(1, 1, scale).name, name)
        self.assertIsNone(self.catalog.chart_at(5, 5, 3))
        self.assertIsNone(self.catalog.chart_at(1, 1, 10000))

    def test_ranking_treats_zoom_levels_equally_and_unknown_as_fallback(self):
        native = 3779.527559 * 10
        self.assertAlmostEqual(
            chart_scale_rank(native / 4, 10)[0], chart_scale_rank(native * 4, 10)[0]
        )
        self.assertLess(
            chart_scale_rank(native / 4, 10), chart_scale_rank(native * 4, 10)
        )
        self.assertGreater(chart_scale_rank(0, 10), chart_scale_rank(native * 100, 10))

    def test_existing_chart_does_not_suppress_better_download(self):
        self.manager.charts = [loaded("US3TEST1", 80000)]
        recommended, existing = self.manager.chart_suggestion_at(self.catalog, 1, 1, 3)
        self.assertEqual(recommended.name, "US5TEST1")
        self.assertIsNone(existing)
        self.assertEqual(
            self.manager.chart_suggestion_at(self.catalog, 1, 1, 20), (None, None)
        )

    def test_disabled_best_chart_is_offered_without_download(self):
        harbor = loaded("US5TEST1", 12000, False)
        self.manager.charts = [loaded("US3TEST1", 80000), harbor]
        self.assertEqual(
            self.manager.chart_suggestion_at(self.catalog, 1, 1, 3), (None, harbor)
        )
        harbor.enabled = True
        self.assertEqual(
            self.manager.chart_suggestion_at(self.catalog, 1, 1, 3), (None, None)
        )

    def test_zooming_out_can_offer_a_less_detailed_chart(self):
        self.manager.charts = [loaded("US5TEST1", 12000)]
        recommended, existing = self.manager.chart_suggestion_at(
            self.catalog, 1, 1, 100
        )
        self.assertEqual(recommended.name, "US2TEST1")
        self.assertIsNone(existing)

    def test_local_better_chart_and_offline_disabled_chart(self):
        local = loaded("local", 11000)
        self.manager.charts = [local]
        self.assertEqual(
            self.manager.chart_suggestion_at(self.catalog, 1, 1, 3), (None, None)
        )
        self.catalog.cells = []
        local.enabled = False
        self.assertEqual(
            self.manager.chart_suggestion_at(self.catalog, 1, 1, 3), (None, local)
        )

    def test_cache_is_found_even_when_not_imported(self):
        with TemporaryDirectory() as directory:
            catalog = ENCCatalog(directory)
            harbor = self.catalog.cells[0]
            self.assertIsNone(catalog.downloaded_path(harbor))
            path = (
                Path(directory)
                / harbor.name
                / "ENC_ROOT"
                / harbor.name
                / (harbor.name + ".000")
            )
            path.parent.mkdir(parents=True)
            path.write_bytes(b"chart")
            self.assertEqual(catalog.downloaded_path(harbor), str(path))


class TestScaleMosaic(unittest.TestCase):
    def setUp(self):
        self.canvas = TestMap()
        self.viewport = MapViewport(self.canvas)
        self.native = int(self.canvas.get_scale() * 3779.527559)
        self.renderer = ENCOverlayRenderer()
        self.charts = {}
        self.renderer._worker_chart = lambda path, scale, palette: self.charts[path]

    def rectangle(self, left, top, right, bottom):
        points = [
            self.viewport.convert_screen_to_geographic(x, y).get_degrees()
            for x, y in (
                (left, top),
                (right, top),
                (right, bottom),
                (left, bottom),
                (left, top),
            )
        ]
        return ogr.CreateGeometryFromWkt(
            "POLYGON((" + ",".join(f"{lon} {lat}" for lat, lon in points) + "))"
        )

    def add_chart(self, name, scale, region, color):
        def draw(viewport, cr):
            cr.set_source_rgb(*color)
            cr.paint()

        chart = SimpleNamespace(_coverage=[region], do_draw=Mock(side_effect=draw))
        self.charts[name] = chart
        return (name, scale, (region.GetEnvelope(),))

    def render(self, specs):
        viewport = MapViewport(self.canvas)
        job = RenderJob((), viewport, specs, 1, "cm93")
        viewport.render_cancelled = job.cancel.is_set
        return self.renderer._render(job)

    def pixel(self, image, x, y):
        image.flush()
        offset = y * image.get_stride() + x * 4
        return tuple(bytes(image.get_data())[offset : offset + 4])

    def test_best_scale_wins_overlap_and_other_chart_fills_gap(self):
        coast = self.add_chart(
            "coast", self.native, self.rectangle(0, 0, 280, 300), (1, 0, 0)
        )
        harbor = self.add_chart(
            "harbor", self.native / 8, self.rectangle(120, 0, 400, 300), (0, 0, 1)
        )
        image = self.render((harbor, coast))
        self.assertEqual(self.pixel(image, 200, 150), (0, 0, 255, 255))
        self.assertEqual(self.pixel(image, 350, 150), (255, 0, 0, 255))
        reverse = self.render((coast, harbor))
        self.assertEqual(bytes(image.get_data()), bytes(reverse.get_data()))
        self.canvas._zoom += 3
        zoomed = self.render((coast, harbor))
        self.assertEqual(self.pixel(zoomed, 200, 150), (255, 0, 0, 255))

    def test_coverage_hole_uses_fallback_without_duplicate_features(self):
        full = self.rectangle(-10, -10, 410, 310)
        region = full.Difference(self.rectangle(160, 110, 240, 190))
        coast = self.add_chart("coast", self.native, region, (1, 0, 0))
        harbor = self.add_chart("harbor", self.native / 8, full, (0, 0, 1))
        image = self.render((coast, harbor))
        self.assertEqual(self.pixel(image, 100, 150), (0, 0, 255, 255))
        self.assertEqual(self.pixel(image, 200, 150), (255, 0, 0, 255))

    def test_fully_covered_lower_priority_chart_is_not_drawn(self):
        full = self.rectangle(-10, -10, 410, 310)
        coast = self.add_chart("coast", self.native, full, (1, 0, 0))
        harbor = self.add_chart("harbor", self.native / 8, full, (0, 0, 1))
        self.render((coast, harbor))
        self.charts["coast"].do_draw.assert_called_once()
        self.charts["harbor"].do_draw.assert_not_called()

    def test_read_coverage_excludes_no_data_panels(self):
        dataset = ogr.GetDriverByName("Memory").CreateDataSource("")
        layer = dataset.CreateLayer("M_COVR", geom_type=ogr.wkbPolygon)
        layer.CreateField(ogr.FieldDefn("CATCOV", ogr.OFTInteger))
        for category, region in (
            (1, self.rectangle(0, 0, 400, 300)),
            (2, self.rectangle(160, 110, 240, 190)),
        ):
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetField("CATCOV", category)
            feature.SetGeometry(region)
            layer.CreateFeature(feature)
        coverage = GDALVectorChart.read_coverage(dataset)
        self.assertEqual(len(coverage), 1)
        center = self.viewport.convert_screen_to_geographic(200, 150)
        lat, lon = center.get_degrees()
        point = ogr.CreateGeometryFromWkt(f"POINT({lon} {lat})")
        self.assertFalse(coverage[0].Intersects(point))


class TestZoomDownloadHover(unittest.TestCase):
    def setUp(self):
        from gweatherrouting.gtk.charts.chartdownload import ChartDownloadHover

        self.hover = ChartDownloadHover.__new__(ChartDownloadHover)
        self.hover.map = TestMap()
        self.hover.map._center_lat = self.hover.map._center_lon = 1
        self.hover.map._zoom = 15
        self.hover.map._dragging = False
        self.hover.map._zoom_animating = False
        self.hover.map._inertia = None
        self.hover._disposed = self.hover._downloading = False
        self.hover._position = self.hover._pointer = (200, 150)
        self.hover._timer = self.hover._leave_timer = 0
        self.hover._view = None
        self.hover.catalog = ENCCatalog("/unused")
        self.hover.catalog.cells = [cell("US5TEST1", 12000), cell("US3TEST1", 80000)]
        self.hover.manager = SimpleNamespace(charts=[loaded("US3TEST1", 80000)])
        for name in ("detailed_chart_at", "chart_suggestion_at"):
            setattr(
                self.hover.manager,
                name,
                MethodType(getattr(ChartManager, name), self.hover.manager),
            )
        for name in (
            "card",
            "title",
            "description",
            "button",
            "spinner",
            "_load_catalog",
        ):
            setattr(self.hover, name, Mock())

    def test_hover_offers_better_chart_despite_existing_coverage(self):
        self.hover._hover()
        self.assertEqual(self.hover._cell.name, "US5TEST1")
        self.hover.button.set_label.assert_called_with("Download chart")
        self.hover.card.popup.assert_called_once()

    def test_hover_uses_cached_chart_without_network(self):
        with patch.object(
            self.hover.catalog, "downloaded_path", return_value="/cached/US5TEST1.000"
        ):
            self.hover._hover()
        self.hover.button.set_label.assert_called_with("Use downloaded chart")
        self.hover._downloaded = Mock()
        self.hover._download(self.hover.button)
        self.hover._downloaded.assert_called_once_with("/cached/US5TEST1.000", None)

    def test_hover_stays_hidden_when_best_chart_enabled(self):
        self.hover.manager.charts.append(loaded("US5TEST1", 12000))
        self.hover._hover()
        self.hover.card.popup.assert_not_called()

    def test_stationary_cursor_rechecked_after_zoom_settles(self):
        self.hover._cancel = Mock()
        with patch(
            "gweatherrouting.gtk.charts.chartdownload.GLib.timeout_add", return_value=7
        ) as timer:
            self.hover.map._zoom_animating = True
            self.hover._on_draw(self.hover.map, None)
            timer.assert_not_called()
            self.hover.map._zoom = 16
            self.hover.map._zoom_animating = False
            self.hover._on_draw(self.hover.map, None)
            timer.assert_called_once_with(700, self.hover._hover)
            self.assertEqual(self.hover._timer, 7)
