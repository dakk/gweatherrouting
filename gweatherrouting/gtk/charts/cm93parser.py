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

# CM93 binary chart format parser
# Reference: https://github.com/OpenCPN/OpenCPN/blob/master/gui/src/cm93.cpp

import logging
import math
import os
import struct
from dataclasses import dataclass, field

logger = logging.getLogger("gweatherrouting")

# CM93 decryption table (from OpenCPN)
# The CM93 format uses a substitution cipher, not simple XOR
_TABLE_0 = [
    0xCD, 0xEA, 0xDC, 0x48, 0x3E, 0x6D, 0xCA, 0x7B, 0x52, 0xE1, 0xA4,
    0x8E, 0xAB, 0x05, 0xA7, 0x97, 0xB9, 0x60, 0x39, 0x85, 0x7C, 0x56,
    0x7A, 0xBA, 0x68, 0x6E, 0xF5, 0x5D, 0x02, 0x4E, 0x0F, 0xA1, 0x27,
    0x24, 0x41, 0x34, 0x00, 0x5A, 0xFE, 0xCB, 0xD0, 0xFA, 0xF8, 0x6C,
    0x74, 0x96, 0x9E, 0x0E, 0xC2, 0x49, 0xE3, 0xE5, 0xC0, 0x3B, 0x59,
    0x18, 0xA9, 0x86, 0x8F, 0x30, 0xC3, 0xA8, 0x22, 0x0A, 0x14, 0x1A,
    0xB2, 0xC9, 0xC7, 0xED, 0xAA, 0x29, 0x94, 0x75, 0x0D, 0xAC, 0x0C,
    0xF4, 0xBB, 0xC5, 0x3F, 0xFD, 0xD9, 0x9C, 0x4F, 0xD5, 0x84, 0x1E,
    0xB1, 0x81, 0x69, 0xB4, 0x09, 0xB8, 0x3C, 0xAF, 0xA3, 0x08, 0xBF,
    0xE0, 0x9A, 0xD7, 0xF7, 0x8C, 0x67, 0x66, 0xAE, 0xD4, 0x4C, 0xA5,
    0xEC, 0xF9, 0xB6, 0x64, 0x78, 0x06, 0x5B, 0x9B, 0xF2, 0x99, 0xCE,
    0xDB, 0x53, 0x55, 0x65, 0x8D, 0x07, 0x33, 0x04, 0x37, 0x92, 0x26,
    0x23, 0xB5, 0x58, 0xDA, 0x2F, 0xB3, 0x40, 0x5E, 0x7F, 0x4B, 0x62,
    0x80, 0xE4, 0x6F, 0x73, 0x1D, 0xDF, 0x17, 0xCC, 0x28, 0x25, 0x2D,
    0xEE, 0x3A, 0x98, 0xE2, 0x01, 0xEB, 0xDD, 0xBC, 0x90, 0xB0, 0xFC,
    0x95, 0x76, 0x93, 0x46, 0x57, 0x2C, 0x2B, 0x50, 0x11, 0x0B, 0xC1,
    0xF0, 0xE7, 0xD6, 0x21, 0x31, 0xDE, 0xFF, 0xD8, 0x12, 0xA6, 0x4D,
    0x8A, 0x13, 0x43, 0x45, 0x38, 0xD2, 0x87, 0xA0, 0xEF, 0x82, 0xF1,
    0x47, 0x89, 0x6A, 0xC8, 0x54, 0x1B, 0x16, 0x7E, 0x79, 0xBD, 0x6B,
    0x91, 0xA2, 0x71, 0x36, 0xB7, 0x03, 0x3D, 0x72, 0xC6, 0x44, 0x8B,
    0xCF, 0x15, 0x9F, 0x32, 0xC4, 0x77, 0x83, 0x63, 0x20, 0x88, 0xF6,
    0xAD, 0xF3, 0xE8, 0x4A, 0xE9, 0x35, 0x1C, 0x5F, 0x19, 0x1F, 0x7D,
    0x70, 0xFB, 0xD1, 0x51, 0x10, 0xD3, 0x2E, 0x61, 0x9D, 0x5C, 0x2A,
    0x42, 0xBE, 0xE6,
]

_ENCODE_TABLE = None
_DECODE_TABLE = None


def _build_decode_table():
    global _ENCODE_TABLE, _DECODE_TABLE
    if _DECODE_TABLE is not None:
        return
    _ENCODE_TABLE = bytearray(256)
    _DECODE_TABLE = bytearray(256)
    for i in range(256):
        _ENCODE_TABLE[i] = _TABLE_0[i] ^ 8
    for i in range(256):
        a = _ENCODE_TABLE[i]
        _DECODE_TABLE[a] = i


def decrypt_cm93(data):
    """Decrypt CM93 binary data using the substitution cipher."""
    _build_decode_table()
    return data.translate(bytes(_DECODE_TABLE))


# Scale level properties
# dval is the grid step size used in cell index calculation
SCALE_LEVELS = {
    "Z": {"name": "Overview", "scale": 20000000, "dval": 120},
    "A": {"name": "General", "scale": 3000000, "dval": 60},
    "B": {"name": "Coastal", "scale": 1000000, "dval": 30},
    "C": {"name": "Approach", "scale": 200000, "dval": 12},
    "D": {"name": "Harbour", "scale": 100000, "dval": 3},
    "E": {"name": "Berthing", "scale": 50000, "dval": 3},
    "F": {"name": "1:20K", "scale": 20000, "dval": 1},
    "G": {"name": "1:7.5K", "scale": 7500, "dval": 1},
}

CM93_SEMIMAJOR = 6378137.0
_RAD_TO_DEG = 180.0 / math.pi
_MERCATOR_SCALE = _RAD_TO_DEG / CM93_SEMIMAJOR
_HALF_PI = math.pi / 2.0


@dataclass
class CM93Feature:
    obj_code: int
    obj_name: str
    geom_type: str  # "P", "L", "A"
    priority: int
    geometry: list  # P: [(lat,lon)], L: [(lat,lon),...], A: [[(lat,lon),...], ...]
    attributes: dict = field(default_factory=dict)


@dataclass
class CM93Cell:
    cell_name: str
    scale_level: str
    origin_lat: float
    origin_lon: float
    extent_lat: float
    extent_lon: float
    features: list = field(default_factory=list)


def load_cm93_obj_dictionary(path):
    """Parse CM93OBJ.DIC -> {code_int: {name, geom_type, priority, description, attrs}}"""
    result = {}
    name_to_code = {}
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) < 5:
                    continue
                name = parts[0]
                try:
                    code = int(parts[1])
                except ValueError:
                    continue
                geom_type = parts[2]
                try:
                    priority = int(parts[3])
                except ValueError:
                    priority = 6
                description = parts[4]
                attrs = parts[5:] if len(parts) > 5 else []
                result[code] = {
                    "name": name,
                    "geom_type": geom_type,
                    "priority": priority,
                    "description": description,
                    "attrs": attrs,
                }
                name_to_code[name] = code
    except Exception as e:
        logger.error("Failed to load CM93OBJ.DIC: %s", e)
    return result, name_to_code


def load_cm93_attr_dictionary(path):
    """Parse CM93ATTR.DIC -> {code_int: {name, type, min, max}}"""
    result = {}
    name_to_code = {}
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) < 3:
                    continue
                name = parts[0]
                try:
                    code = int(parts[1])
                except ValueError:
                    continue
                atype = parts[2]
                amin = float(parts[3]) if len(parts) > 3 and parts[3] else None
                amax = float(parts[4]) if len(parts) > 4 and parts[4] else None
                result[code] = {
                    "name": name,
                    "type": atype,
                    "min": amin,
                    "max": amax,
                }
                name_to_code[name] = code
    except Exception as e:
        logger.error("Failed to load CM93ATTR.DIC: %s", e)
    return result, name_to_code


def cell_index_to_origin(cell_index, scale_level):
    """Convert a CM93 cell index (int) to geographic origin and extent.

    Cell index = ilon + (ilat + 30) * 10000
    where ilat = lat * 3 + 270 - 30, ilon = (lon + 360) * 3

    Returns (lat, lon, extent_lat, extent_lon) in degrees.
    """
    dval = SCALE_LEVELS[scale_level]["dval"]

    # Decode cell index
    ilat_plus_30 = cell_index // 10000
    ilon = cell_index % 10000

    ilat = ilat_plus_30 - 30

    # Reverse: lat = (ilat - 270 + 30) / 3.0
    lat = (ilat - 270.0 + 30.0) / 3.0
    lon = (ilon / 3.0) - 360.0

    # Normalize longitude
    while lon < -180.0:
        lon += 360.0
    while lon > 180.0:
        lon -= 360.0

    extent_lat = dval / 3.0
    extent_lon = dval / 3.0

    return lat, lon, extent_lat, extent_lon


def cell_name_to_index(cell_name):
    """Convert a cell directory name like '00300000' to a cell index integer."""
    try:
        return int(cell_name)
    except ValueError:
        return None


def _transform_point(x, y, tx_rate, ty_rate, tx_origin, ty_origin):
    """Transform CM93 uint16 coordinates to WGS84 lat/lon."""
    valx = x * tx_rate + tx_origin
    valy = y * ty_rate + ty_origin

    # Inverse Mercator projection (using precomputed constants)
    lon = valx * _MERCATOR_SCALE
    lat = (2.0 * math.atan(math.exp(valy / CM93_SEMIMAJOR)) - _HALF_PI) * _RAD_TO_DEG
    return lat, lon


def _read_ushort(data, offset):
    """Read a little-endian unsigned short from decrypted data."""
    if offset + 2 > len(data):
        return 0, offset + 2
    val = struct.unpack_from("<H", data, offset)[0]
    return val, offset + 2


def _read_int(data, offset):
    """Read a little-endian signed int from decrypted data."""
    if offset + 4 > len(data):
        return 0, offset + 4
    val = struct.unpack_from("<i", data, offset)[0]
    return val, offset + 4


def _read_uint(data, offset):
    """Read a little-endian unsigned int from decrypted data."""
    if offset + 4 > len(data):
        return 0, offset + 4
    val = struct.unpack_from("<I", data, offset)[0]
    return val, offset + 4


def _read_double(data, offset):
    """Read a little-endian double from decrypted data."""
    if offset + 8 > len(data):
        return 0.0, offset + 8
    val = struct.unpack_from("<d", data, offset)[0]
    return val, offset + 8


def _read_byte(data, offset):
    """Read a single byte."""
    if offset >= len(data):
        return 0, offset + 1
    return data[offset], offset + 1


def _parse_attribute_block(data, offset, n_attrs, attr_dict):
    """Parse attribute block from a feature record."""
    attributes = {}
    for _ in range(n_attrs):
        if offset >= len(data):
            break
        attr_code, offset = _read_byte(data, offset)

        attr_info = attr_dict.get(attr_code)
        if attr_info is None:
            # Unknown attribute, skip - we can't determine the size
            break

        atype = attr_info["type"]
        attr_name = attr_info["name"]

        if atype == "aBYTE":
            val, offset = _read_byte(data, offset)
            attributes[attr_name] = val
        elif atype == "aWORD10":
            val, offset = _read_ushort(data, offset)
            attributes[attr_name] = val / 10.0
        elif atype == "aLONG":
            val, offset = _read_int(data, offset)
            attributes[attr_name] = val
        elif atype == "aFLOAT":
            if offset + 4 <= len(data):
                val = struct.unpack_from("<f", data, offset)[0]
                offset += 4
                attributes[attr_name] = val
            else:
                offset += 4
        elif atype == "aSTRING":
            # Null-terminated string
            end = data.find(0, offset)
            if end == -1:
                end = len(data)
            try:
                val = data[offset:end].decode("ascii", errors="replace")
            except Exception:
                val = ""
            offset = end + 1
            attributes[attr_name] = val
        elif atype == "aLIST":
            count, offset = _read_byte(data, offset)
            vals = []
            for _ in range(count):
                v, offset = _read_byte(data, offset)
                vals.append(v)
            attributes[attr_name] = vals
        elif atype == "aCMPLX":
            # Complex: 3-byte header + null-terminated string
            if offset + 3 <= len(data):
                offset += 3
            end = data.find(0, offset)
            if end == -1:
                end = len(data)
            try:
                val = data[offset:end].decode("ascii", errors="replace")
            except Exception:
                val = ""
            offset = end + 1
            attributes[attr_name] = val
        else:
            # Unknown type, try to read as byte
            val, offset = _read_byte(data, offset)
            attributes[attr_name] = val

    return attributes, offset


def parse_cm93_cell(file_path, scale_level, obj_dict, attr_dict):
    """Parse a single CM93 binary cell file.

    Args:
        file_path: Path to the binary cell file (e.g., .../00300000/Z/00300000.Z)
        scale_level: Scale level character (Z, A, B, ..., G)
        obj_dict: Parsed CM93OBJ dictionary {code: {name, geom_type, priority, ...}}
        attr_dict: Parsed CM93ATTR dictionary {code: {name, type, ...}}

    Returns:
        CM93Cell with parsed features, or None on failure.
    """
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read()
    except Exception as e:
        logger.error("Failed to read CM93 cell %s: %s", file_path, e)
        return None

    if len(raw_data) < 10:
        logger.warning("CM93 cell too small: %s (%d bytes)", file_path, len(raw_data))
        return None

    # Decrypt the entire file
    data = decrypt_cm93(raw_data)

    # Extract cell name from file path
    basename = os.path.basename(file_path)
    cell_name = os.path.splitext(basename)[0]

    # Parse the 10-byte prolog
    # header_len: total bytes for prolog+header (includes the 10-byte prolog)
    # table1_len: bytes for vector/point geometry tables
    # table2_len: bytes for feature record table
    # File layout: [0:header_len] [header_len:header_len+table1] [header_len+table1:]
    offset = 0
    header_len, offset = _read_ushort(data, offset)
    table1_len, offset = _read_int(data, offset)
    table2_len, offset = _read_int(data, offset)

    prolog_end = offset  # = 10

    # Validate file structure
    if header_len + table1_len + table2_len != len(data):
        logger.warning(
            "CM93 cell size mismatch: %s (header=%d + t1=%d + t2=%d != %d)",
            file_path, header_len, table1_len, table2_len, len(data),
        )

    # Parse the header (128 bytes starting at offset 10)
    if len(data) < prolog_end + 128:
        logger.warning("CM93 cell header too short: %s", file_path)
        return None

    ho = prolog_end  # header offset
    lon_min, _ = _read_double(data, ho + 0)
    lat_min, _ = _read_double(data, ho + 8)
    lon_max, _ = _read_double(data, ho + 16)
    lat_max, _ = _read_double(data, ho + 24)
    easting_min, _ = _read_double(data, ho + 32)
    northing_min, _ = _read_double(data, ho + 40)
    easting_max, _ = _read_double(data, ho + 48)
    northing_max, _ = _read_double(data, ho + 56)

    n_vector_records, _ = _read_ushort(data, ho + 64)
    n_vector_record_points, _ = _read_int(data, ho + 66)

    n_point3d_records, _ = _read_ushort(data, ho + 78)

    n_point2d_records, _ = _read_ushort(data, ho + 88)

    n_feature_records, _ = _read_ushort(data, ho + 94)

    # Compute coordinate transform rates (CM93 uint16 -> Mercator meters)
    if easting_max != easting_min:
        tx_rate = (easting_max - easting_min) / 65535.0
    else:
        tx_rate = 1.0
    if northing_max != northing_min:
        ty_rate = (northing_max - northing_min) / 65535.0
    else:
        ty_rate = 1.0
    tx_origin = easting_min
    ty_origin = northing_min

    # ---- Parse table1: geometry data ----
    # Starts at header_len (which includes the 10-byte prolog)
    off = header_len

    # Vector records (edges): each has ushort npoints, then npoints * (ushort x, ushort y)
    # Store both raw integer coords (for endpoint matching) and transformed coords
    edges = []       # list of [(lat, lon), ...]
    edges_raw = []   # list of [(px, py), ...] raw uint16 coords
    for _ in range(n_vector_records):
        if off + 2 > header_len + table1_len:
            break
        npts, off = _read_ushort(data, off)
        points = []
        raw_points = []
        for _ in range(npts):
            if off + 4 > header_len + table1_len:
                break
            px, off = _read_ushort(data, off)
            py, off = _read_ushort(data, off)
            raw_points.append((px, py))
            lat, lon = _transform_point(px, py, tx_rate, ty_rate, tx_origin, ty_origin)
            points.append((lat, lon))
        edges.append(points)
        edges_raw.append(raw_points)

    # 3D point records: each has ushort npoints, then npoints * (ushort x, ushort y, ushort z)
    point3d_records = []
    for _ in range(n_point3d_records):
        if off + 2 > header_len + table1_len:
            break
        npts, off = _read_ushort(data, off)
        points = []
        for _ in range(npts):
            if off + 6 > header_len + table1_len:
                break
            px, off = _read_ushort(data, off)
            py, off = _read_ushort(data, off)
            pz, off = _read_ushort(data, off)
            lat, lon = _transform_point(px, py, tx_rate, ty_rate, tx_origin, ty_origin)
            points.append((lat, lon, pz / 10.0))
        point3d_records.append(points)

    # 2D point records: n_point2d_records * (ushort x, ushort y)
    point2d_array = []
    for _ in range(n_point2d_records):
        if off + 4 > header_len + table1_len:
            break
        px, off = _read_ushort(data, off)
        py, off = _read_ushort(data, off)
        lat, lon = _transform_point(px, py, tx_rate, ty_rate, tx_origin, ty_origin)
        point2d_array.append((lat, lon))

    # ---- Parse table2: feature records ----
    # Starts at header_len + table1_len
    feat_off = header_len + table1_len
    feat_end = feat_off + table2_len
    features = []

    for _ in range(n_feature_records):
        if feat_off + 4 > feat_end:
            break

        record_start = feat_off
        otype = data[feat_off]
        geotype_raw = data[feat_off + 1]
        record_size = struct.unpack_from("<H", data, feat_off + 2)[0]
        feat_off += 4  # Skip past otype + geom_prim + record_size

        # record_size includes the 4-byte header
        record_end = record_start + record_size

        geotype_flag = geotype_raw & 0x0F
        has_related = (geotype_raw & 0x10) != 0
        has_attrs = (geotype_raw & 0x80) != 0

        # Determine geometry type string
        if geotype_flag == 1:
            gt = "P"
        elif geotype_flag == 2:
            gt = "L"
        elif geotype_flag == 4:
            gt = "A"
        elif geotype_flag == 8:
            gt = "P"  # 3D point
        else:
            gt = "P"

        # Parse geometry reference
        geometry = []
        try:
            if geotype_flag == 1:
                # Point: ushort index into 2D point array
                idx, feat_off = _read_ushort(data, feat_off)
                if idx < len(point2d_array):
                    geometry = [point2d_array[idx]]

            elif geotype_flag == 2:
                # Line: ushort n_elements, then n_elements * ushort edge_index
                n_elems, feat_off = _read_ushort(data, feat_off)
                line_points = []
                for _ in range(n_elems):
                    edge_ref, feat_off = _read_ushort(data, feat_off)
                    real_idx = edge_ref & 0x1FFF
                    direction = (edge_ref >> 13) & 0x04
                    if real_idx < len(edges):
                        edge_pts = edges[real_idx]
                        if direction != 0:
                            edge_pts = list(reversed(edge_pts))
                        if line_points and edge_pts and line_points[-1] == edge_pts[0]:
                            line_points.extend(edge_pts[1:])
                        else:
                            line_points.extend(edge_pts)
                geometry = line_points

            elif geotype_flag == 4:
                # Area: ushort n_elements, then n_elements * ushort edge_index
                # Build rings by chaining edges via raw integer endpoints
                # following OpenCPN's approach: direction bit is bit 2 of
                # upper 3 bits, dedup junction points, detect closure on
                # raw integer coords.
                n_elems, feat_off = _read_ushort(data, feat_off)

                # Read all edge refs first
                area_edge_refs = []
                for _ in range(n_elems):
                    edge_ref, feat_off = _read_ushort(data, feat_off)
                    area_edge_refs.append(edge_ref)

                rings = []
                ring = []        # transformed (lat, lon) points
                ring_raw = []    # raw (px, py) integer points
                start_raw = None # raw start point of current ring

                for edge_ref in area_edge_refs:
                    real_idx = edge_ref & 0x1FFF
                    direction = (edge_ref >> 13) & 0x04

                    if real_idx >= len(edges) or not edges[real_idx]:
                        continue

                    edge_pts = edges[real_idx]
                    edge_raw = edges_raw[real_idx]

                    if direction != 0:
                        edge_pts = edge_pts[::-1]
                        edge_raw = edge_raw[::-1]

                    # Record start of ring
                    if start_raw is None and edge_raw:
                        start_raw = edge_raw[0]

                    # Get the end point of this edge (before dedup)
                    cur_end_raw = edge_raw[-1] if edge_raw else None

                    # Append points, deduplicating junction vertex
                    if ring_raw and edge_raw and ring_raw[-1] == edge_raw[0]:
                        ring.extend(edge_pts[1:])
                        ring_raw.extend(edge_raw[1:])
                    else:
                        ring.extend(edge_pts)
                        ring_raw.extend(edge_raw)

                    # Check ring closure using raw integer coords
                    if (start_raw is not None and cur_end_raw is not None
                            and len(ring) >= 3 and cur_end_raw == start_raw):
                        rings.append(ring)
                        ring = []
                        ring_raw = []
                        start_raw = None

                if ring and len(ring) >= 3:
                    rings.append(ring)
                geometry = rings

            elif geotype_flag == 8:
                # 3D point descriptor
                idx, feat_off = _read_ushort(data, feat_off)
                if idx < len(point3d_records) and point3d_records[idx]:
                    for pt in point3d_records[idx]:
                        geometry.append((pt[0], pt[1]))

        except Exception as e:
            logger.debug("Geometry parse error in %s: %s", file_path, e)

        # Parse related objects (skip)
        if has_related and feat_off < record_end:
            n_rel, feat_off = _read_byte(data, feat_off)
            feat_off += n_rel * 2

        # Parse attributes
        attributes = {}
        if has_attrs and feat_off < record_end:
            n_attrs, feat_off = _read_byte(data, feat_off)
            attributes, _ = _parse_attribute_block(
                data, feat_off, n_attrs, attr_dict
            )

        # Advance to next record (record_size includes header)
        feat_off = record_end

        # Look up object info
        obj_info = obj_dict.get(otype, {})
        obj_name = obj_info.get("name", f"UNKNOWN_{otype}")
        priority = obj_info.get("priority", 6)

        if geometry:
            features.append(
                CM93Feature(
                    obj_code=otype,
                    obj_name=obj_name,
                    geom_type=gt,
                    priority=priority,
                    geometry=geometry,
                    attributes=attributes,
                )
            )

    # Get cell origin from cell name
    cell_idx = cell_name_to_index(cell_name)
    if cell_idx is not None:
        origin_lat, origin_lon, extent_lat, extent_lon = cell_index_to_origin(
            cell_idx, scale_level
        )
    else:
        origin_lat, origin_lon = lat_min, lon_min
        extent_lat = lat_max - lat_min
        extent_lon = lon_max - lon_min

    logger.debug(
        "Parsed CM93 cell %s/%s: %d features, bounds=(%.2f,%.2f)-(%.2f,%.2f)",
        cell_name,
        scale_level,
        len(features),
        lat_min,
        lon_min,
        lat_max,
        lon_max,
    )

    return CM93Cell(
        cell_name=cell_name,
        scale_level=scale_level,
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        extent_lat=extent_lat,
        extent_lon=extent_lon,
        features=features,
    )
