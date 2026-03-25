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

from abc import ABC, abstractmethod
from typing import Callable, List


class GribSource(ABC):
    """Abstract base class for GRIB data sources."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this source."""
        pass

    @abstractmethod
    def get_download_list(self) -> List:
        """Return list of available GRIB files.

        Each entry is [filename, source_name, size, date, download_identifier].
        """
        pass

    @abstractmethod
    def download(
        self,
        identifier: str,
        dest_dir: str,
        percentage_callback: Callable[[int], None],
    ) -> str:
        """Download a GRIB file and return the local path.

        Args:
            identifier: Source-specific download identifier (URL or config).
            dest_dir: Directory to save the downloaded file.
            percentage_callback: Called with download percentage (0-100).

        Returns:
            Path to the downloaded GRIB file.
        """
        pass
