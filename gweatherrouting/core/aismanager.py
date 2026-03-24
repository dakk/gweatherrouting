# -*- coding: utf-8 -*-
# Copyright (C) 2017-2025 Davide Gessa
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
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("gweatherrouting")

# Stale target timeout in seconds (10 minutes)
STALE_TIMEOUT = 600

# Ship type category classification
SHIP_TYPE_SAILING = "sailing"
SHIP_TYPE_FISHING = "fishing"
SHIP_TYPE_CARGO = "cargo"
SHIP_TYPE_TANKER = "tanker"
SHIP_TYPE_PASSENGER = "passenger"
SHIP_TYPE_OTHER = "other"

# Colors for each category (r, g, b)
SHIP_TYPE_COLORS: Dict[str, Tuple[float, float, float]] = {
    SHIP_TYPE_SAILING: (0.2, 0.4, 1.0),
    SHIP_TYPE_FISHING: (0.2, 0.8, 0.2),
    SHIP_TYPE_CARGO: (1.0, 0.6, 0.0),
    SHIP_TYPE_TANKER: (1.0, 0.2, 0.2),
    SHIP_TYPE_PASSENGER: (0.6, 0.2, 0.8),
    SHIP_TYPE_OTHER: (0.5, 0.5, 0.5),
}


def classify_ship_type(ship_type: Optional[int]) -> str:
    """Classify a numeric AIS ship type into a category."""
    if ship_type is None:
        return SHIP_TYPE_OTHER
    if ship_type == 36:
        return SHIP_TYPE_SAILING
    if 30 <= ship_type <= 35:
        return SHIP_TYPE_FISHING
    if 70 <= ship_type <= 79:
        return SHIP_TYPE_CARGO
    if 80 <= ship_type <= 89:
        return SHIP_TYPE_TANKER
    if 60 <= ship_type <= 69:
        return SHIP_TYPE_PASSENGER
    return SHIP_TYPE_OTHER


@dataclass
class AISTarget:
    mmsi: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    cog: Optional[float] = None
    sog: Optional[float] = None
    heading: Optional[int] = None
    name: Optional[str] = None
    ship_type: Optional[int] = None
    last_update: float = field(default_factory=time.time)

    @property
    def category(self) -> str:
        return classify_ship_type(self.ship_type)

    def has_valid_position(self) -> bool:
        return (
            self.latitude is not None
            and self.longitude is not None
            and self.latitude != 91.0
            and self.longitude != 181.0
        )


class AISManager:
    """Manages AIS targets decoded from AIVDM/AIVDO sentences."""

    def __init__(self):
        self._targets: Dict[int, AISTarget] = {}
        self._fragment_buffer: Dict[Tuple[int, int], List[bytes]] = {}

    def process_sentence(self, raw_sentence: str) -> None:
        """Process a raw AIS NMEA sentence (!AIVDM/!AIVDO)."""
        try:
            from pyais import NMEAMessage
        except ImportError:
            logger.debug("pyais not available, skipping AIS sentence")
            return

        try:
            nmea_msg = NMEAMessage(raw_sentence.encode("ascii"))
        except Exception as e:
            logger.debug("Failed to parse AIS NMEA message: %s", e)
            return

        frag_cnt = nmea_msg.frag_cnt
        frag_num = nmea_msg.frag_num
        seq_id = nmea_msg.seq_id or 0

        if frag_cnt == 1:
            # Single-fragment message
            self._decode_and_update(raw_sentence.encode("ascii"))
        else:
            # Multi-fragment message: buffer fragments
            key = (seq_id, frag_cnt)
            if frag_num == 1:
                self._fragment_buffer[key] = [raw_sentence.encode("ascii")]
            elif key in self._fragment_buffer:
                self._fragment_buffer[key].append(raw_sentence.encode("ascii"))
                if len(self._fragment_buffer[key]) == frag_cnt:
                    # All fragments received
                    fragments = self._fragment_buffer.pop(key)
                    self._decode_and_update(*fragments)
            else:
                # Got a non-first fragment without the first; discard
                logger.debug("Orphaned AIS fragment %d/%d", frag_num, frag_cnt)

    def _decode_and_update(self, *fragments: bytes) -> None:
        """Decode AIS message fragments and update the target."""
        try:
            from pyais import decode
        except ImportError:
            return

        try:
            decoded = decode(*fragments)
            data = decoded.asdict()
        except Exception as e:
            logger.debug("Failed to decode AIS message: %s", e)
            return

        mmsi = data.get("mmsi")
        if mmsi is None:
            return

        msg_type = data.get("msg_type")
        if mmsi not in self._targets:
            self._targets[mmsi] = AISTarget(mmsi=mmsi)

        target = self._targets[mmsi]
        target.last_update = time.time()

        if msg_type in (1, 2, 3, 18, 19):
            self._update_position(target, data)
        elif msg_type in (5, 24):
            self._update_static(target, data)

    @staticmethod
    def _update_position(target: AISTarget, data: dict) -> None:
        """Update target position from a position report message."""
        lat = data.get("lat")
        if lat is not None and lat != 91.0:
            target.latitude = lat

        lon = data.get("lon")
        if lon is not None and lon != 181.0:
            target.longitude = lon

        course = data.get("course")
        if course is not None and course != 360.0:
            target.cog = course

        speed = data.get("speed")
        if speed is not None:
            target.sog = speed

        heading = data.get("heading")
        if heading is not None and heading != 511:
            target.heading = heading

    @staticmethod
    def _update_static(target: AISTarget, data: dict) -> None:
        """Update target static data (name, ship type)."""
        shipname = data.get("shipname")
        if shipname:
            target.name = shipname.strip().strip("@")

        shiptype = data.get("shiptype")
        if shiptype is not None:
            try:
                target.ship_type = int(shiptype)
            except (ValueError, TypeError):
                pass

    def get_active_targets(self) -> List[AISTarget]:
        """Return active targets, removing stale ones (>10 min old)."""
        now = time.time()
        stale_mmsis = [
            mmsi
            for mmsi, t in self._targets.items()
            if now - t.last_update > STALE_TIMEOUT
        ]
        for mmsi in stale_mmsis:
            del self._targets[mmsi]

        return list(self._targets.values())
