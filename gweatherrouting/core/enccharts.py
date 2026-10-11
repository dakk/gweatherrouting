"""NOAA ENC coverage discovery and on-demand, offline chart downloads."""

import math
import re
import tempfile
import time
import xml.etree.ElementTree as ElementTree
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests

CATALOG_URL = "https://www.charts.noaa.gov/ENCs/ENCProdCat.xml"
CACHE_SECONDS = 7 * 24 * 60 * 60


def chart_scale_rank(native_scale, meters_per_pixel):
    """Prefer compilation scales closest to the current nominal display scale.

    Logarithmic distance treats each doubling equally. Prefer the more detailed
    source when two scales are equally close; unknown scales are fallbacks.
    """
    if not native_scale or meters_per_pixel <= 0:
        return (math.inf, math.inf)
    display_scale = meters_per_pixel * 3779.527559
    return (abs(math.log2(native_scale / display_scale)), native_scale)


def chart_scale_visible(native_scale, meters_per_pixel):
    """Limit harbor clutter when zoomed out and overview geometry when zoomed in."""
    if not native_scale:
        return True
    display_scale = meters_per_pixel * 3779.527559  # nominal 96 dpi
    if display_scale > native_scale * 16:
        return False
    return native_scale < 1000000 or native_scale <= display_scale * 8


def polygon_contains(vertices, lat, lon):
    """Ray casting, unwrapping longitudes across the antimeridian."""
    points: list[tuple[float, float]] = []
    for y, x in vertices:
        if points:
            x += 360 * round((points[-1][1] - x) / 360)
        points.append((y, x))
    if len(points) < 3:
        return False
    lon += 360 * round((points[0][1] - lon) / 360)
    inside = False
    y1, x1 = points[-1]
    for y2, x2 in points:
        cross = (lon - x1) * (y2 - y1) - (lat - y1) * (x2 - x1)
        if abs(cross) < 1e-10 and min(x1, x2) <= lon <= max(x1, x2):
            if min(y1, y2) <= lat <= max(y1, y2):
                return True
        if (y1 > lat) != (y2 > lat):
            if lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
                inside = not inside
        y1, x1 = y2, x2
    return inside


@dataclass
class ENCCell:
    name: str
    title: str
    scale: int
    size: int
    panels: list

    def __post_init__(self):
        self._bounds = []
        for kind, vertices in self.panels:
            if kind != "E" or len(vertices) < 3:
                continue
            longitudes: list[float] = []
            for _, lon in vertices:
                if longitudes:
                    lon += 360 * round((longitudes[-1] - lon) / 360)
                longitudes.append(lon)
            self._bounds.append(
                (
                    min(y for y, _ in vertices),
                    max(y for y, _ in vertices),
                    min(longitudes),
                    max(longitudes),
                )
            )

    def contains(self, lat, lon):
        # Most catalog cells are far away. Reject them without walking polygons
        # on the GTK thread; exact coverage still decides the remaining matches.
        if not any(
            south <= lat <= north
            and west <= lon + 360 * round(((west + east) / 2 - lon) / 360) <= east
            for south, north, west, east in self._bounds
        ):
            return False
        exterior = any(
            polygon_contains(v, lat, lon) for t, v in self.panels if t == "E"
        )
        excluded = any(
            polygon_contains(v, lat, lon) for t, v in self.panels if t == "I"
        )
        return exterior and not excluded

    @property
    def url(self):
        return f"https://www.charts.noaa.gov/ENCs/{self.name}.zip"


def parse_catalog(data):
    cells = []
    for node in ElementTree.fromstring(data).findall("cell"):
        name = node.findtext("name", "")
        if node.findtext("status") != "Active" or not re.fullmatch(
            r"US[A-Z0-9]{6}", name
        ):
            continue
        panels = [
            (
                p.findtext("type"),
                [
                    (float(v.findtext("lat") or ""), float(v.findtext("long") or ""))
                    for v in p.findall("vertex")
                ],
            )
            for p in node.findall("cov/panel")
        ]
        scale = int(node.findtext("cscale", "0"))
        if panels and scale > 0:
            cells.append(
                ENCCell(
                    name,
                    node.findtext("lname", name),
                    scale,
                    int(node.findtext("zipfile_size", "0")),
                    panels,
                )
            )
    if not cells:
        raise ValueError("The NOAA chart catalog contains no active chart coverage.")
    return sorted(cells, key=lambda c: (c.scale, c.name))


class ENCCatalog:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.cells = []

    def load(self):
        """Called in a worker; keep a usable catalog when the network is unavailable."""
        self.directory.mkdir(parents=True, exist_ok=True)
        cache = self.directory / "catalog.xml"
        if cache.exists():
            try:
                self.cells = parse_catalog(cache.read_bytes())
                if time.time() - cache.stat().st_mtime < CACHE_SECONDS:
                    return
            except (ValueError, ElementTree.ParseError):
                pass
        try:
            with requests.get(CATALOG_URL, timeout=(10, 45)) as response:
                response.raise_for_status()
                data = response.content
            cells = parse_catalog(data)
            temporary = cache.with_suffix(".tmp")
            temporary.write_bytes(data)
            temporary.replace(cache)
            self.cells = cells
        except (requests.RequestException, ValueError, ElementTree.ParseError, OSError):
            if not self.cells:
                raise

    def chart_at(self, lat, lon, meters_per_pixel=None):
        candidates = (c for c in self.cells if c.contains(lat, lon))
        if meters_per_pixel is None:
            return min(candidates, key=lambda c: (c.scale, c.name), default=None)
        candidates = (
            c for c in candidates if chart_scale_visible(c.scale, meters_per_pixel)
        )
        return min(
            candidates,
            key=lambda c: (chart_scale_rank(c.scale, meters_per_pixel), c.name),
            default=None,
        )

    def downloaded_path(self, cell):
        """Find a cached exchange set even if it hasn't been added to Settings."""
        return next(
            (str(p) for p in (self.directory / cell.name).rglob(cell.name + ".000")),
            None,
        )

    def download(self, cell):
        """Stage a complete exchange set (including updates), then install atomically."""
        if not re.fullmatch(r"US[A-Z0-9]{6}", cell.name):
            raise ValueError("Invalid NOAA chart identifier")
        destination = self.directory / cell.name
        existing = self.downloaded_path(cell)
        if existing:
            return existing
        self.directory.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=self.directory) as temporary:
            staging = Path(temporary)
            archive = staging / "chart.zip"
            with requests.get(cell.url, stream=True, timeout=(10, 60)) as response:
                response.raise_for_status()
                hosts = ("charts.noaa.gov", "www.charts.noaa.gov")
                if urlparse(response.url).hostname not in hosts:
                    raise ValueError("Unexpected chart download host")
                with archive.open("wb") as output:
                    total = 0
                    for chunk in response.iter_content(65536):
                        total += len(chunk)
                        if total > 100 * 1024 * 1024:
                            raise ValueError("Chart download exceeds 100 MB")
                        output.write(chunk)
            unpacked = staging / "unpacked"
            with zipfile.ZipFile(archive) as package:
                if sum(m.file_size for m in package.infolist()) > 300 * 1024 * 1024:
                    raise ValueError("Chart archive is too large")
                for member in package.infolist():
                    target = (unpacked / member.filename).resolve()
                    if not target.is_relative_to(unpacked.resolve()):
                        raise ValueError("Invalid chart archive path")
                package.extractall(unpacked)
            charts = list(unpacked.rglob(cell.name + ".000"))
            if len(charts) != 1:
                raise ValueError("The download does not contain the expected chart")
            relative = charts[0].relative_to(unpacked)
            unpacked.replace(destination)
        return str(destination / relative)
