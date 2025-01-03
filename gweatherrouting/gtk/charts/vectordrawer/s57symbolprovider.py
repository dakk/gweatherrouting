# -*- coding: utf-8 -*-
# Copyright (C) 2017-2024 Davide Gessa
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
# flake8: noqa: E402
import json
import logging
import os

import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("OsmGpsMap", "1.2")
except:
    gi.require_version("OsmGpsMap", "1.0")

from bs4 import BeautifulSoup
from gi.repository import Gdk, GdkPixbuf

from ....core.storage import DATA_DIR

logger = logging.getLogger("gweatherrouting")


class S57SymbolProvider:
    def __init__(self, settingsManager):
        self.settingsManager = settingsManager
        self.symbols = {}

        self.p_day = GdkPixbuf.Pixbuf.new_from_file(
            os.path.abspath(os.path.dirname(__file__))
            + "/../../../data/s57/rastersymbols-day.png"
        )
        self.p_dark = GdkPixbuf.Pixbuf.new_from_file(
            os.path.abspath(os.path.dirname(__file__))
            + "/../../../data/s57/rastersymbols-dark.png"
        )

        self.p_select = self.p_day
        self.onChartPaletteChanged(settingsManager.chartPalette)
        settingsManager.register_on_change("chartPalette", self.onChartPaletteChanged)

        # Try to load cached data
        try:
            with open(DATA_DIR + "/s57_symbols.json", "r") as f:
                self.symbols = json.load(f)
                logger.debug("Loaded cached S57 symbols")
                return
        except:
            logger.warning("Cached S57 symbols not found, loading from XML")
            self.symbols = {}

        # Load symbols
        data = open(
            os.path.abspath(os.path.dirname(__file__))
            + "/../../../data/s57/chartsymbols.xml"
        ).read()

        soup = BeautifulSoup(data, "html.parser")

        for row in soup.find_all("symbol"):
            try:
                name = row.find("name").text
                try:
                    description = row.find("description").text
                except:
                    description = ""

                bm = row.find("bitmap")
                dim = int(bm["width"]), int(bm["height"])
                dist = int(bm.find("distance")["max"]), int(bm.find("distance")["min"])
                pivot = int(bm.find("pivot")["x"]), int(bm.find("pivot")["y"])
                origin = int(bm.find("origin")["x"]), int(bm.find("origin")["y"])
                gloc = int(bm.find("graphics-location")["x"]), int(
                    bm.find("graphics-location")["y"]
                )

                self.symbols[name] = {
                    "description": description,
                    "dim": dim,
                    "dist": dist,
                    "pivot": pivot,
                    "origin": origin,
                    "gloc": gloc,
                }

            except:
                continue

        with open(DATA_DIR + "/s57_symbols.json", "w") as f:
            json.dump(self.symbols, f)
            f.close()
            logger.debug("Saved cached S57 symbols")

    def onChartPaletteChanged(self, v):
        if v == "dark":
            self.p_select = self.p_dark
        else:
            self.p_select = self.p_day

    def draw(self, cr, n, xx, yy):
        s = self.symbols[n]
        img = self.p_select.new_subpixbuf(
            s["gloc"][0], s["gloc"][1], s["dim"][0], s["dim"][1]
        )
        Gdk.cairo_set_source_pixbuf(cr, img, xx - s["pivot"][0], yy - s["pivot"][1])
        cr.paint()

    def drawLight(self, cr, xx, yy, tags, major):
        cr.move_to(xx + 12, yy + 4)
        try:
            txt = (
                tags["seamark:light:character"]
                + "."
                + tags["seamark:light:colour"][0].upper()
                + "."
                + tags["seamark:light:period"]
                + "s"
            )
            cr.show_text(txt)
        except:
            y = yy + 4
            i = 1
            while True:
                try:
                    txt = (
                        tags["seamark:light:" + str(i) + ":character"]
                        + "."
                        + tags["seamark:light:" + str(i) + ":colour"][0].upper()
                        + "."
                        + tags["seamark:light:" + str(i) + ":period"]
                        + "s"
                    )
                except:
                    break
                cr.move_to(xx + 12, y)
                cr.show_text(txt)
                y += 12
                i += 1

        self.draw(cr, "LIGHTS13", xx, yy)
