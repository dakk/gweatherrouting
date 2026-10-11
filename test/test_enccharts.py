import io
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from gweatherrouting.core.enccharts import (
    ENCCatalog,
    ENCCell,
    parse_catalog,
    polygon_contains,
)

PANEL = [(0, 0), (0, 4), (4, 4), (4, 0)]


def catalog_xml():
    vertices = "".join(
        f"<vertex><lat>{y}</lat><long>{x}</long></vertex>" for y, x in PANEL
    )
    cells = ""
    for name, scale, status in [
        ("US5TEST1", 12000, "Active"),
        ("US3TEST1", 80000, "Active"),
        ("US6TEST1", 5000, "Cancelled"),
    ]:
        cells += (
            f"<cell><name>{name}</name><status>{status}</status>"
            f"<cscale>{scale}</cscale><lname>Test chart</lname><cov><panel>"
            f"<type>E</type>{vertices}</panel></cov></cell>"
        )
    return f"<EncProductCatalog>{cells}</EncProductCatalog>".encode()


def response_for_archive(files):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as package:
        for name, content in files.items():
            package.writestr(name, content)
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.url = "https://www.charts.noaa.gov/ENCs/US5TEST1.zip"
    response.iter_content.return_value = [data.getvalue()]
    return response


class TestENCCoverage(unittest.TestCase):
    def test_uses_polygon_not_bounding_box(self):
        triangle = [(0, 0), (4, 0), (0, 4)]
        self.assertTrue(polygon_contains(triangle, 1, 1))
        self.assertFalse(polygon_contains(triangle, 3, 3))
        self.assertTrue(polygon_contains(triangle, 0, 0))

    def test_antimeridian(self):
        panel = [(0, 179), (0, -179), (2, -179), (2, 179)]
        self.assertTrue(polygon_contains(panel, 1, 179.5))
        self.assertTrue(polygon_contains(panel, 1, -179.5))
        self.assertFalse(polygon_contains(panel, 1, 0))
        cell = ENCCell("US5TEST1", "Date line", 12000, 0, [("E", panel)])
        self.assertTrue(cell.contains(1, -179.5))
        self.assertTrue(cell.contains(1, 179.5))
        self.assertFalse(cell.contains(1, 0))

    def test_excludes_holes(self):
        cell = ENCCell(
            "US5TEST1",
            "Test",
            12000,
            0,
            [("E", PANEL), ("I", [(1, 1), (1, 2), (2, 2), (2, 1)])],
        )
        self.assertTrue(cell.contains(3, 3))
        self.assertFalse(cell.contains(1.5, 1.5))

    def test_selects_most_detailed_active_chart(self):
        catalog = ENCCatalog("/unused")
        catalog.cells = parse_catalog(catalog_xml())
        self.assertEqual(catalog.chart_at(1, 1).name, "US5TEST1")
        self.assertIsNone(catalog.chart_at(5, 5))

    def test_empty_catalog_rejected(self):
        with self.assertRaises(ValueError):
            parse_catalog(b"<EncProductCatalog/>")


class TestENCDownloads(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.catalog = ENCCatalog(self.temporary.name)
        self.cell = parse_catalog(catalog_xml())[0]

    @patch("gweatherrouting.core.enccharts.requests.get")
    def test_preserves_updates_and_reuses_download(self, get):
        base = "ENC_ROOT/US5TEST1/US5TEST1"
        get.return_value = response_for_archive(
            {base + ".000": b"base", base + ".001": b"update"}
        )
        path = Path(self.catalog.download(self.cell))
        self.assertEqual(path.read_bytes(), b"base")
        self.assertEqual(path.with_suffix(".001").read_bytes(), b"update")
        self.assertEqual(self.catalog.download(self.cell), str(path))
        get.assert_called_once()

    @patch("gweatherrouting.core.enccharts.requests.get")
    def test_rejects_path_traversal(self, get):
        get.return_value = response_for_archive({"../../escape": b"bad"})
        with self.assertRaisesRegex(ValueError, "archive path"):
            self.catalog.download(self.cell)
        self.assertEqual(list(Path(self.temporary.name).iterdir()), [])

    @patch("gweatherrouting.core.enccharts.requests.get")
    def test_failed_download_leaves_no_installed_chart(self, get):
        get.return_value = response_for_archive({"wrong.000": b"bad"})
        with self.assertRaisesRegex(ValueError, "expected chart"):
            self.catalog.download(self.cell)
        self.assertEqual(list(Path(self.temporary.name).iterdir()), [])

    @patch("gweatherrouting.core.enccharts.requests.get")
    def test_stale_catalog_available_offline(self, get):
        cache = Path(self.temporary.name) / "catalog.xml"
        cache.write_bytes(catalog_xml())
        os.utime(cache, (0, 0))
        get.side_effect = requests.ConnectionError("offline")
        self.catalog.load()
        self.assertEqual(self.catalog.chart_at(1, 1).name, "US5TEST1")

    @patch("gweatherrouting.core.enccharts.requests.get")
    def test_fresh_cache_avoids_network(self, get):
        (Path(self.temporary.name) / "catalog.xml").write_bytes(catalog_xml())
        self.catalog.load()
        self.assertIsNotNone(self.catalog.chart_at(1, 1))
        get.assert_not_called()
