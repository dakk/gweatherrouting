"""Public CHS chart imagery, cached locally; not a source of routing depths."""

import math
from pathlib import Path
from threading import Lock
import time

import requests

EXPORT_URL = (
    "https://egisp.dfo-mpo.gc.ca/arcgis/rest/services/chs/ENC_MaritimeChartService"
    "/MapServer/exts/MaritimeChartService/MapServer/export"
)
TILE_SIZE = 256
MIN_ZOOM, MAX_ZOOM = 8, 17
HALF_WORLD = math.pi * 6378137
CACHE_SECONDS = 14 * 24 * 60 * 60
MAX_BYTES = 2 * 1024 * 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
# Broad request limits; the CHS service itself determines actual chart coverage.
REGIONS = ((-141, 48, -114, 85), (-95, 41, -50, 85))


def tile_bbox(z, x, y):
    edge = 2 * HALF_WORLD / 2**z
    west, north = -HALF_WORLD + x * edge, HALF_WORLD - y * edge
    return west, north - edge, west + edge, north


def tile_in_canada(z, x, y):
    west, south, east, north = tile_bbox(z, x, y)
    west, east = west / HALF_WORLD * 180, east / HALF_WORLD * 180
    south, north = (
        math.degrees(math.atan(math.sinh(v / 6378137))) for v in (south, north)
    )
    return any(
        west < e and east > w and south < n and north > s for w, s, e, n in REGIONS
    )


class CHSTileSource:
    def __init__(self, directory):
        self.directory = Path(directory)
        self._rate_lock = Lock()
        self._next_request = 0.0
        self._last_prune = 0.0

    def path(self, key):
        z, x, y, factor = key
        if not (
            MIN_ZOOM <= z <= MAX_ZOOM
            and 0 <= x < 2**z
            and 0 <= y < 2**z
            and factor in (1, 2)
        ):
            raise ValueError("Invalid CHS tile")
        return self.directory / str(factor) / str(z) / str(x) / f"{y}.png"

    def cached(self, key):
        path = self.path(key)
        try:
            data = path.read_bytes()
            if data.startswith(PNG_MAGIC) and len(data) <= MAX_BYTES:
                return data, path.stat().st_mtime
        except OSError:
            pass
        return None

    def fetch(self, key):
        """Worker-only network and disk I/O; limit both concurrency and request rate."""
        z, x, y, factor = key
        path = self.path(key)
        if not tile_in_canada(z, x, y):
            raise ValueError("Outside Canadian chart area")
        with self._rate_lock:
            delay = max(0, self._next_request - time.monotonic())
            if delay:
                time.sleep(delay)
            self._next_request = time.monotonic() + 0.25
        params = {
            "bbox": ",".join(str(v) for v in tile_bbox(z, x, y)),
            "bboxSR": "3857",
            "imageSR": "3857",
            "size": f"{TILE_SIZE * factor},{TILE_SIZE * factor}",
            "dpi": 96 * factor,
            "format": "png",
            "f": "image",
            "transparent": "true",
            "layers": "show:0,1,2,3,4,5,6,7",
        }
        with requests.get(
            EXPORT_URL,
            params=params,
            stream=True,
            timeout=(10, 30),
            headers={"User-Agent": "GWeatherRouting-CHS/1.0"},
        ) as response:
            response.raise_for_status()
            chunks, total = [], 0
            for chunk in response.iter_content(65536):
                total += len(chunk)
                if total > MAX_BYTES:
                    raise ValueError("CHS tile is too large")
                chunks.append(chunk)
            data = b"".join(chunks)
        if not data.startswith(PNG_MAGIC):
            raise ValueError("CHS did not return a chart image")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_bytes(data)
        temporary.replace(path)
        self._prune()
        return data, path.stat().st_mtime

    def _prune(self):
        # Bound disk growth without scanning the cache during map drawing.
        now = time.monotonic()
        if now - self._last_prune < 3600:
            return
        self._last_prune = now
        files = []
        for path in self.directory.rglob("*.png"):
            try:
                stat = path.stat()
                files.append((stat.st_mtime, stat.st_size, path))
            except OSError:
                continue
        total = sum(size for _, size, _ in files)
        for _, size, path in sorted(files):
            if total <= 512 * 1024 * 1024:
                break
            try:
                path.unlink()
                total -= size
            except OSError:
                pass
