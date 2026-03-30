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

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, List

import requests

from gweatherrouting.core.gribsources.base import GribSource

logger = logging.getLogger("gweatherrouting")

# NOAA NOMADS GFS 0.25 degree filter endpoint
GFS_FILTER_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"

# Available GFS forecast hours (0-384, with 3h steps up to 240, then 12h steps)
GFS_FORECAST_HOURS_SHORT = list(range(0, 241, 3))
GFS_FORECAST_HOURS_LONG = list(range(252, 385, 12))
GFS_FORECAST_HOURS = GFS_FORECAST_HOURS_SHORT + GFS_FORECAST_HOURS_LONG

# GFS runs at 00, 06, 12, 18 UTC
GFS_CYCLES = ["00", "06", "12", "18"]

# Default forecast range presets (in hours)
FORECAST_PRESETS = {
    "3 days": 72,
    "5 days": 120,
    "7 days": 168,
    "10 days": 240,
}


class NOAAGFSSource(GribSource):
    """GRIB source for NOAA GFS global weather forecasts (0.25 degree).

    Downloads wind data (UGRD/VGRD at 10m above ground) from NOAA NOMADS
    for user-specified geographic bounds.
    """

    def __init__(self):
        self._bounds = None  # (lat_south, lon_west, lat_north, lon_east)
        self._forecast_hours = 120  # default 5 days

    @property
    def name(self) -> str:
        return "NOAA GFS"

    @property
    def bounds(self):
        return self._bounds

    @bounds.setter
    def bounds(self, value):
        self._bounds = value

    @property
    def forecast_hours(self):
        return self._forecast_hours

    @forecast_hours.setter
    def forecast_hours(self, value):
        self._forecast_hours = value

    def _get_latest_cycle(self):
        """Find the latest available GFS cycle.

        GFS data is typically available ~4-5 hours after the cycle time.
        """
        now = datetime.now(timezone.utc)
        # Go back 6 hours to ensure data is available
        available_time = now - timedelta(hours=6)

        cycle_hour = (available_time.hour // 6) * 6
        cycle_time = available_time.replace(
            hour=cycle_hour, minute=0, second=0, microsecond=0
        )

        return cycle_time

    def _get_available_cycles(self, num_cycles=4):
        """Get a list of recent available GFS cycles."""
        latest = self._get_latest_cycle()
        cycles = []
        for i in range(num_cycles):
            cycle = latest - timedelta(hours=6 * i)
            cycles.append(cycle)
        return cycles

    def get_download_list(self) -> List:
        """Return list of available GFS download configurations.

        Each entry represents a GFS cycle with a specific forecast range.
        """
        cycles = self._get_available_cycles()
        grib_files = []

        for cycle in cycles:
            date_str = cycle.strftime("%Y%m%d")
            cycle_str = f"{cycle.hour:02d}"

            for preset_name, hours in FORECAST_PRESETS.items():
                size_est = self._estimate_size(hours)
                identifier = json.dumps(
                    {
                        "date": date_str,
                        "cycle": cycle_str,
                        "hours": hours,
                    }
                )

                grib_files.append(
                    [
                        f"GFS 0.25 - {preset_name}",
                        f"NOAA GFS {cycle_str}Z",
                        size_est,
                        cycle.strftime("%Y-%m-%d %H:%M UTC"),
                        identifier,
                    ]
                )

        return grib_files

    def _estimate_size(self, hours):
        """Estimate download size based on forecast hours and bounds."""
        # Rough estimate: ~0.5MB per forecast hour for wind-only, global
        # Smaller with geographic subsetting
        num_steps = len([h for h in GFS_FORECAST_HOURS if h <= hours])
        if self._bounds:
            lat_range = abs(self._bounds[2] - self._bounds[0])
            lon_range = abs(self._bounds[3] - self._bounds[1])
            area_fraction = (lat_range * lon_range) / (180 * 360)
            size_mb = num_steps * 0.5 * area_fraction
        else:
            size_mb = num_steps * 0.5

        if size_mb < 1:
            return f"{size_mb * 1024:.0f} KB"
        return f"{size_mb:.1f} MB"

    def _build_filter_url(self, date_str, cycle, forecast_hour):
        """Build NOAA NOMADS filter URL for a specific forecast hour."""
        params = {
            "file": f"gfs.t{cycle}z.pgrb2.0p25.f{forecast_hour:03d}",
            "lev_10_m_above_ground": "on",
            "var_UGRD": "on",
            "var_VGRD": "on",
            "dir": f"/gfs.{date_str}/{cycle}/atmos",
        }

        if self._bounds:
            lat_south, lon_west, lat_north, lon_east = self._bounds
            # NOMADS accepts negative longitudes directly
            params["subregion"] = ""
            params["leftlon"] = str(lon_west)
            params["rightlon"] = str(lon_east)
            params["toplat"] = str(lat_north)
            params["bottomlat"] = str(lat_south)

        return params

    def download(
        self,
        identifier: str,
        dest_dir: str,
        percentage_callback: Callable[[int], None],
    ) -> str:
        config = json.loads(identifier)
        date_str = config["date"]
        cycle = config["cycle"]
        max_hours = config["hours"]

        forecast_steps = [h for h in GFS_FORECAST_HOURS if h <= max_hours]
        total_steps = len(forecast_steps)

        filename = f"gfs_{date_str}_{cycle}z_{max_hours}h.grib2"
        final_path = dest_dir + "/" + filename

        logger.info(
            "Downloading GFS %s %sz, %d forecast hours (%d steps)",
            date_str,
            cycle,
            max_hours,
            total_steps,
        )

        bytes_written = 0
        with open(final_path, "wb") as outfile:
            for i, fhour in enumerate(forecast_steps):
                params = self._build_filter_url(date_str, cycle, fhour)
                logger.debug("Downloading forecast hour %d", fhour)

                response = requests.get(GFS_FILTER_URL, params=params, stream=True)
                try:
                    response.raise_for_status()

                    for chunk in response.iter_content(chunk_size=8192):
                        outfile.write(chunk)
                        bytes_written += len(chunk)
                finally:
                    response.close()

                percentage = int(100 * (i + 1) / total_steps)
                percentage_callback(percentage)

        if bytes_written == 0:
            import os

            os.remove(final_path)
            raise RuntimeError(
                "GFS download returned empty data. The requested forecast "
                "may not be available yet. Try a different cycle or date."
            )

        logger.info("GFS download completed: %s (%d bytes)", filename, bytes_written)
        return final_path
