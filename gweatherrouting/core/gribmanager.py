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
import os
from shutil import copyfile
from typing import Dict, List, Tuple

import requests
import weatherrouting

from gweatherrouting.core.grib import Grib
from gweatherrouting.core.storage import GRIB_DIR, TEMP_DIR, Storage

# from bs4 import BeautifulSoup

logger = logging.getLogger("gweatherrouting")


class GribManagerStorage(Storage):
    def __init__(self):
        Storage.__init__(self, "grib-manager")
        self.opened = []
        self.load_or_save_default()


class GribManager(weatherrouting.Grib):
    def __init__(self):
        self.storage = GribManagerStorage()
        self.grib_files = None

        self.gribs: List[Grib] = []
        self.timeframe = [0, 0]

        self.local_gribs = []
        self.refresh_local_gribs()

        for x in self.storage.opened:
            self.enable(x)

    def refresh_local_gribs(self):
        self.local_gribs = []
        for x in os.listdir(GRIB_DIR):
            if x[-5:] != ".grib" and x[-4:] != ".grb":
                continue

            m = Grib.parseMetadata(GRIB_DIR + "/" + x)
            self.local_gribs.append(m)

    def store_opened_gribs(self):
        ss: List = []
        for x in self.gribs:
            try:
                ss.index(x.name)
            except:
                ss.append(x.name)
        self.storage.opened = ss

    def load(self, path):
        logger.info("Loading grib %s", path)
        self.gribs.append(Grib.parse(path))

    def change_state(self, name, state):
        if not state:
            self.disable(name)
        else:
            self.enable(name)

    def enable(self, name):
        self.load(GRIB_DIR + "/" + name)
        self.store_opened_gribs()

    def disable(self, name):
        for x in self.gribs:
            if x.name == name:
                self.gribs.remove(x)
                self.store_opened_gribs()

    def is_enabled(self, name) -> bool:
        for x in self.gribs:
            if x.name == name:
                return True
        return False

    def has_grib(self) -> bool:
        return len(self.gribs) > 0

    def get_wind_at(self, t, lat: float, lon: float):
        for x in self.gribs:
            try:
                return x.get_wind_at(t, lat, lon)
            except:
                pass

    def get_wind(self, t, bounds) -> List:
        # TODO: get the best matching grib for lat/lon at time t
        g: List = []

        for x in self.gribs:
            try:
                g = g + x.get_wind(t, bounds)
            except:
                pass
        return g
    
    def getWindAt(self, t: float, lat: float, lon: float) -> Tuple[float, float]:
        return self.get_wind_at(t, lat, lon)

    def get_wind_2d(self, tt, bounds):
        dd = sorted(self.get_wind(tt, bounds), key=lambda x: x[2][1])

        ddict: Dict = {}
        for x in dd:
            if x[2][1] not in ddict:
                ddict[x[2][1]] = []
            ddict[x[2][1]].append(x)

        ddlist = []
        for x, v in ddict.items():
            ddlist.append(sorted(v, key=lambda x: x[2][0]))

        return ddlist

    def get_download_list(self, force=False):
        from bs4 import BeautifulSoup

        # https://openskiron.org/en/openskiron
        # https://openskiron.org/en/openwrf
        if not self.grib_files or force:
            data = requests.get("https://openskiron.org/en/openskiron").text
            soup = BeautifulSoup(data, "html.parser")
            self.grib_files = []

            for row in soup.find("table").find_all("tr"):
                r = row.find_all("td")

                if len(r) >= 3:
                    # Name, Source, Size, Time, Link
                    self.grib_files.append(
                        [
                            r[0].text.strip(),
                            "OpenSkiron",
                            r[1].text,
                            r[2].text,
                            r[0].find("a", href=True)["href"],
                        ]
                    )

            data = requests.get("https://openskiron.org/en/openwrf").text
            soup = BeautifulSoup(data, "html.parser")

            for row in soup.find("table").find_all("tr"):
                r = row.find_all("td")

                if len(r) >= 3:
                    # Name, Source, Size, Time, Link
                    self.grib_files.append(
                        [
                            r[0].text.strip(),
                            "OpenWRF",
                            r[1].text,
                            r[2].text,
                            r[0].find("a", href=True)["href"],
                        ]
                    )

        return self.grib_files

    def remove(self, name):
        if self.is_enabled(name):
            self.disable(name)
        os.remove(GRIB_DIR + "/" + name)

    def import_grib(self, path):
        try:
            name = path.split("/")[-1]
            logger.info("Importing grib %s", path)
            copyfile(path, GRIB_DIR + "/" + name)
            self.enable(name)
            return True
        except Exception as e:
            logger.error(str(e))

    def download(self, uri, percentageCallback, callback):
        import bz2

        name = uri.split("/")[-1]
        logger.info("Downloading grib %s", uri)

        response = requests.get(uri, stream=True)
        total_length = response.headers.get("content-length")
        last_signal_percent = -1
        f = open(TEMP_DIR + "/" + name, "wb")

        if total_length is None:
            pass
        else:
            dl = 0
            total_length_i = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
                done = int(100 * dl / total_length_i)

                if last_signal_percent != done:
                    percentageCallback(done)
                    last_signal_percent = done

        f.close()
        logger.info("Grib download completed %s", uri)

        bf = bz2.open(TEMP_DIR + "/" + name, "rb")
        f = open(GRIB_DIR + "/" + name.replace(".bz2", ""), "wb")
        f.write(bf.read())
        f.close()
        bf.close()

        self.load(GRIB_DIR + "/" + name.replace(".bz2", ""))
        callback(True)
