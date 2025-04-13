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
from .s57symbolprovider import S57SymbolProvider


class VectorChartDrawer:
    def __init__(self, settingsManager):
        self.onChartPaletteChanged(settingsManager.chartPalette)
        settingsManager.register_on_change("chartPalette", self.onChartPaletteChanged)

        self.symbolProvider = S57SymbolProvider(settingsManager)

    # TODO: this will handle object queries
    def onQueryPoint(self, lat, lon):
        raise Exception("Not implemented")

    def onChartPaletteChanged(self, v):
        self.palette = v

    def draw(self, gpsmap, cr, vectorFile, bounding):
        raise Exception("Not implemented")
