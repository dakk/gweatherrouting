# -*- coding: utf-8 -*-
# Copyright (C) 2017-2026 Davide Gessa
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
"""

import logging
import os
from collections import OrderedDict

from .cm93parser import (
    SCALE_LEVELS,
    cell_index_to_origin,
    cell_name_to_index,
    parse_cm93_cell,
)

logger = logging.getLogger("gweatherrouting")

# Scale level order from coarsest to finest
SCALE_ORDER = ["Z", "A", "B", "C", "D", "E", "F", "G"]

# Meters-per-pixel thresholds for scale selection
ZOOM_THRESHOLDS = [
    (5000, "Z"),
    (1000, "A"),
    (300, "B"),
    (100, "C"),
    (50, "D"),
    (20, "E"),
    (10, "F"),
    (0, "G"),
]

MAX_CACHE_SIZE = 100


class CM93DataSource:
    """CM93 chart data source. Manages cell indexing, lazy loading, and spatial queries."""

    def __init__(self, root_path, obj_dict, attr_dict):
        self.root_path = root_path
        self.obj_dict = obj_dict
        self.attr_dict = attr_dict
        # {scale_level: [(cell_name, file_path, min_lat, min_lon, max_lat, max_lon), ...]}
        self._cell_index = {}
        # LRU cache: {file_path: CM93Cell}
        self._cell_cache = OrderedDict()
        self._build_cell_index()

    def _build_cell_index(self):
        """Scan the directory tree and index all available cells."""
        for scale in SCALE_ORDER:
            self._cell_index[scale] = []

        try:
            entries = os.listdir(self.root_path)
        except OSError as e:
            logger.error("Cannot list CM93 root %s: %s", self.root_path, e)
            return

        for entry in entries:
            cell_dir = os.path.join(self.root_path, entry)
            if not os.path.isdir(cell_dir):
                continue

            cell_idx = cell_name_to_index(entry)
            if cell_idx is None:
                continue

            # Check which scale subdirectories exist
            for scale in SCALE_ORDER:
                scale_dir = os.path.join(cell_dir, scale)
                if not os.path.isdir(scale_dir):
                    continue

                # Find binary files in the scale directory
                try:
                    files = os.listdir(scale_dir)
                except OSError:
                    continue

                for fname in files:
                    if not fname.upper().endswith("." + scale):
                        continue

                    file_path = os.path.join(scale_dir, fname)
                    file_cell_name = os.path.splitext(fname)[0]
                    file_cell_idx = cell_name_to_index(file_cell_name)

                    if file_cell_idx is not None:
                        lat, lon, elat, elon = cell_index_to_origin(
                            file_cell_idx, scale
                        )
                        self._cell_index[scale].append(
                            (
                                file_cell_name,
                                file_path,
                                lat,
                                lon,
                                lat + elat,
                                lon + elon,
                            )
                        )

        total = sum(len(v) for v in self._cell_index.values())
        logger.info(
            "CM93 cell index built: %d cells across %d scales",
            total,
            sum(1 for v in self._cell_index.values() if v),
        )

    def get_scale_for_zoom(self, meters_per_pixel):
        """Map meters_per_pixel to the appropriate CM93 scale level."""
        for threshold, level in ZOOM_THRESHOLDS:
            if meters_per_pixel > threshold:
                return level
        return "G"

    def get_cells_for_bbox(self, min_lat, min_lon, max_lat, max_lon, scale_level):
        """Return parsed CM93Cells intersecting the bbox at the given scale.

        Falls back to coarser scales if no cells found at the requested level.
        """
        scale_idx = SCALE_ORDER.index(scale_level)

        # Try requested scale and fall back to coarser
        for i in range(scale_idx, -1, -1):
            scale = SCALE_ORDER[i]
            cells = self._get_cells_at_scale(min_lat, min_lon, max_lat, max_lon, scale)
            if cells:
                return cells

        return []

    def _get_cells_at_scale(self, min_lat, min_lon, max_lat, max_lon, scale):
        """Get parsed cells intersecting bbox at a specific scale."""
        matching = []
        for cell_name, file_path, clat_min, clon_min, clat_max, clon_max in (
            self._cell_index.get(scale, [])
        ):
            # Check bbox intersection
            if (
                clat_max < min_lat
                or clat_min > max_lat
                or clon_max < min_lon
                or clon_min > max_lon
            ):
                continue
            matching.append((cell_name, file_path, scale))

        result = []
        for cell_name, file_path, sc in matching:
            cell = self._load_cell(file_path, sc)
            if cell is not None:
                result.append(cell)

        return result

    def _load_cell(self, file_path, scale_level):
        """Load and cache a cell."""
        if file_path in self._cell_cache:
            # Move to end (most recently used)
            self._cell_cache.move_to_end(file_path)
            return self._cell_cache[file_path]

        cell = parse_cm93_cell(file_path, scale_level, self.obj_dict, self.attr_dict)

        if cell is not None:
            # LRU eviction
            while len(self._cell_cache) >= MAX_CACHE_SIZE:
                self._cell_cache.popitem(last=False)
            self._cell_cache[file_path] = cell

        return cell

    def query_point(self, lat, lon, tolerance=0.001):
        """Find features near a given lat/lon.

        Returns list of dicts matching GDALVectorChart.query_point format.
        """
        results = []
        min_lat = lat - tolerance
        max_lat = lat + tolerance
        min_lon = lon - tolerance
        max_lon = lon + tolerance

        # Use the finest available scale
        for scale in reversed(SCALE_ORDER):
            cells = self._get_cells_at_scale(
                min_lat, min_lon, max_lat, max_lon, scale
            )
            if cells:
                for cell in cells:
                    for feat in cell.features:
                        if self._feature_near_point(feat, lat, lon, tolerance):
                            results.append(
                                {
                                    "layer": feat.obj_name,
                                    "geometry": feat.geom_type,
                                    "attributes": feat.attributes,
                                }
                            )
                if results:
                    break

        return results

    def _feature_near_point(self, feature, lat, lon, tolerance):
        """Check if a feature's geometry is within tolerance of a point."""
        if feature.geom_type == "P":
            for pt in feature.geometry:
                if abs(pt[0] - lat) <= tolerance and abs(pt[1] - lon) <= tolerance:
                    return True
        elif feature.geom_type == "L":
            for pt in feature.geometry:
                if abs(pt[0] - lat) <= tolerance and abs(pt[1] - lon) <= tolerance:
                    return True
        elif feature.geom_type == "A":
            for ring in feature.geometry:
                for pt in ring:
                    if abs(pt[0] - lat) <= tolerance and abs(pt[1] - lon) <= tolerance:
                        return True
        return False
