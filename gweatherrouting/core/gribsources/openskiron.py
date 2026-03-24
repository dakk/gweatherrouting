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

import bz2
import logging
from typing import Callable, List

import requests

from gweatherrouting.core.gribsources.base import GribSource

logger = logging.getLogger("gweatherrouting")


class OpenSkironSource(GribSource):
    """GRIB source for OpenSkiron and OpenWRF Mediterranean forecasts."""

    @property
    def name(self) -> str:
        return "OpenSkiron"

    def get_download_list(self) -> List:
        from bs4 import BeautifulSoup

        grib_files = []

        for source_name, url in [
            ("OpenSkiron", "https://openskiron.org/en/openskiron"),
            ("OpenWRF", "https://openskiron.org/en/openwrf"),
        ]:
            data = requests.get(url).text
            soup = BeautifulSoup(data, "html.parser")

            for row in soup.find("table").find_all("tr"):
                r = row.find_all("td")

                if len(r) >= 3:
                    grib_files.append(
                        [
                            r[0].text.strip(),
                            source_name,
                            r[1].text,
                            r[2].text,
                            r[0].find("a", href=True)["href"],
                        ]
                    )

        return grib_files

    def download(
        self,
        identifier: str,
        dest_dir: str,
        percentage_callback: Callable[[int], None],
    ) -> str:
        import tempfile

        name = identifier.split("/")[-1]
        logger.info("Downloading grib from OpenSkiron: %s", identifier)

        response = requests.get(identifier, stream=True)
        total_length = response.headers.get("content-length")
        last_signal_percent = -1

        tmp_path = tempfile.mktemp(dir=dest_dir, suffix=".bz2")
        with open(tmp_path, "wb") as f:
            if total_length is None:
                f.write(response.content)
            else:
                dl = 0
                total_length_i = int(total_length)
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = int(100 * dl / total_length_i)
                    if last_signal_percent != done:
                        percentage_callback(done)
                        last_signal_percent = done

        logger.info("Download completed, decompressing: %s", name)
        final_name = name.replace(".bz2", "")
        final_path = dest_dir + "/" + final_name

        with bz2.open(tmp_path, "rb") as bf:
            with open(final_path, "wb") as f:
                f.write(bf.read())

        import os

        os.remove(tmp_path)

        return final_path
