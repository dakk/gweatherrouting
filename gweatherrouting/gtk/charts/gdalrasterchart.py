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
import multiprocessing
import time
from os import listdir
from os.path import isfile, join
from threading import Lock, Thread
from typing import List, Optional

import cairo
import gi
import numpy as np
from osgeo import gdal, osr

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("OsmGpsMap", "1.2")
except ValueError:
    gi.require_version("OsmGpsMap", "1.0")

from gi.repository import Gdk, OsmGpsMap

from .chartlayer import ChartLayer

logger = logging.getLogger("gweatherrouting")

# https://gdal.org/tutorials/raster_api_tut.html


def dataset_bbox(dataset):
    old_cs = osr.SpatialReference()
    old_cs.ImportFromWkt(dataset.GetProjectionRef())

    wgs84_wkt = """
    GEOGCS["WGS 84",
        DATUM["WGS_1984",
            SPHEROID["WGS 84",6378137,298.257223563,
                AUTHORITY["EPSG","7030"]],
            AUTHORITY["EPSG","6326"]],
        PRIMEM["Greenwich",0,
            AUTHORITY["EPSG","8901"]],
        UNIT["degree",0.01745329251994328,
            AUTHORITY["EPSG","9122"]],
        AUTHORITY["EPSG","4326"]]"""
    new_cs = osr.SpatialReference()
    new_cs.ImportFromWkt(wgs84_wkt)

    transform = osr.CoordinateTransformation(old_cs, new_cs)

    width = dataset.RasterXSize
    height = dataset.RasterYSize
    gt = dataset.GetGeoTransform()
    minx = gt[0]
    miny = gt[3]

    origin = transform.TransformPoint(minx, miny)

    minx = gt[0] + width * gt[1] + height * gt[2]
    miny = gt[3] + width * gt[4] + height * gt[5]

    originbr = transform.TransformPoint(minx, miny)

    return [origin, originbr]


class GDALSingleRasterChart:
    @staticmethod
    def get_file_info(path):
        dataset = gdal.Open(path, gdal.GA_ReadOnly)

        if not dataset:
            raise Exception(f"Unable to open raster chart {path}")

        bbox = dataset_bbox(dataset)

        return (path, bbox, dataset.RasterXSize, dataset.RasterYSize)

    def __init__(self, path):
        dataset = gdal.Open(path, gdal.GA_ReadOnly)

        if not dataset:
            raise Exception(f"Unable to open raster chart {path}")

        # print("Driver: {}/{}".format(dataset.GetDriver().ShortName,
        # 					dataset.GetDriver().LongName))
        # print("Size is {} x {} x {}".format(dataset.RasterXSize,
        # 									dataset.RasterYSize,
        # 									dataset.RasterCount))
        geotransform = dataset.GetGeoTransform()

        self.geotransform = geotransform
        self.dataset = dataset
        self.bbox = dataset_bbox(dataset)

        def worker(i, return_dict):
            try:
                return_dict["surface"] = self.band_to_surface(i)
            except:
                # Fixes error on quit
                logger.warning(f"Interrupted band to surface process on {i}")

        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        self.process = multiprocessing.Process(target=worker, args=(1, return_dict))
        self.process.start()
        self.process.join()
        surface, band_x_size, band_y_size = return_dict["surface"]
        surf = cairo.ImageSurface.create_for_data(
            surface,
            cairo.Format.ARGB32,
            band_x_size,
            band_y_size,
            cairo.Format.RGB24.stride_for_width(band_x_size),
        )
        self.surface = surf

    def band_to_surface(self, i):
        band = self.dataset.GetRasterBand(i)

        mmin = band.GetMinimum()
        mmax = band.GetMaximum()
        if not mmin or not mmax:
            (mmin, mmax) = band.ComputeRasterMinMax(True)

        colors = {0: 0x00000000}
        ct = band.GetRasterColorTable()

        for x in range(int(mmin), int(mmax) + 1):
            try:
                c = ct.GetColorEntry(x)
                colors[x] = (c[3] << 24) | (c[2] << 16) | (c[1] << 8) | c[0]
            except:
                colors[x] = 0x00000000

        data = np.vectorize(lambda x: colors[x], otypes=[np.uint32])(band.ReadAsArray())
        return data, band.XSize, band.YSize

    def do_draw(self, gpsmap, cr):
        cr.save()
        xx, yy = gpsmap.convert_geographic_to_screen(
            OsmGpsMap.MapPoint.new_degrees(self.bbox[0][0], self.bbox[0][1])
        )
        xx2, yy2 = gpsmap.convert_geographic_to_screen(
            OsmGpsMap.MapPoint.new_degrees(self.bbox[1][0], self.bbox[1][1])
        )
        scalingy = (yy2 - yy) / self.dataset.RasterYSize
        scalingx = (xx2 - xx) / self.dataset.RasterXSize
        cr.translate(xx, yy)
        cr.scale(scalingx, scalingy)
        cr.set_source_surface(self.surface, 0, 0)
        cr.paint()
        cr.restore()


class GDALRasterChart(ChartLayer):
    def __init__(self, path, settings_manager, metadata=None, enabled=True):
        super().__init__(path, "raster", settings_manager, metadata, enabled)
        self.cached = {}
        self.loadLock = Lock()

        if metadata:
            self.on_metadata_update()

    def on_metadata_update(self):
        pass

    def on_register(self, on_tick_handler=None):
        self.metadata = []

        files = [f for f in listdir(self.path) if isfile(join(self.path, f))]
        i = 0

        for x in files:
            finfo = GDALSingleRasterChart.get_file_info(self.path + x)
            self.metadata.append(finfo)

            i += 1
            if on_tick_handler:
                on_tick_handler(i / len(files))

        self.on_metadata_update()

        if on_tick_handler:
            on_tick_handler(1.0)

        return True

    last_rect: Optional[List] = None
    last_rasters: List = []

    def load_raster(self, gpsmap, path):
        with self.loadLock:
            logger.debug("Loading raster file %s", path)
            try:
                s = time.time()
                r = GDALSingleRasterChart(path)
                self.cached[path] = r
                logger.debug(
                    "Done loading raster file %s in %ss",
                    path.split("/")[-1],
                    str(int((time.time() - s) * 10.0) / 10.0),
                )
            except:
                logger.error("Error loading raster file %s", path.split("/")[-1])
                return None
            Gdk.threads_enter()
            gpsmap.queue_draw()
            Gdk.threads_leave()
            self.last_rasters.append(r)

    def do_draw(self, gpsmap, cr):
        p1, p2 = gpsmap.get_bbox()
        p1lat, p1lon = p1.get_degrees()
        p2lat, p2lon = p2.get_degrees()

        # Check if bounds hasn't changed
        if self.last_rasters and self.last_rect == [p1lat, p1lon, p2lat, p2lon]:
            for x in self.last_rasters:
                x.do_draw(gpsmap, cr)
            return

        # Estimate which raster is necessary given bound and zoom
        min_b_lat = min(p1lat, p2lat)
        max_b_lat = max(p1lat, p2lat)
        min_b_lon = min(p1lon, p2lon)
        max_b_lon = max(p1lon, p2lon)

        toload = []
        for x in self.metadata:
            bb, path = x[1], x[0]  # sizeX, sizeY x[2], x[3]

            min_r_lat = min(bb[0][0], bb[1][0])
            max_r_lat = max(bb[0][0], bb[1][0])
            min_r_lon = min(bb[0][1], bb[1][1])
            max_r_lon = max(bb[0][1], bb[1][1])

            inside = (
                min_r_lat > min_b_lat
                and max_r_lat < max_b_lat
                and min_r_lon > min_b_lon
                and max_r_lon < max_b_lon
            )
            a = (
                min_r_lat < min_b_lat
                and max_r_lat > max_b_lat
                and min_r_lon > min_b_lon
                and min_r_lon < max_b_lon
            )
            b = (
                min_r_lat < min_b_lat
                and max_r_lat > max_b_lat
                and min_r_lon < min_b_lon
                and max_r_lon > min_b_lon
            )
            c = (
                min_r_lat < min_b_lat
                and max_r_lat > min_b_lat
                and min_r_lon < min_b_lon
                and max_r_lon > max_b_lon
            )
            d = (
                min_r_lat < max_b_lat
                and max_r_lat > max_b_lat
                and min_r_lon < min_b_lon
                and max_r_lon > max_b_lon
            )

            area = (((max_r_lat + 90) - (min_r_lat + 90))) * (
                ((max_r_lon + 180) - (min_r_lon + 180))
            )

            if a or b or c or d:
                toload.append([path, bb, area, inside])

        toload.sort(key=lambda x: x[2])
        toload.reverse()

        # Check which rasters are already loaded
        rasters = []

        for x in toload:
            if x[0] in self.cached:
                if self.cached[x[0]] != "loading":
                    rasters.append(self.cached[x[0]])
                continue

            self.cached[x[0]] = "loading"

            t = Thread(
                target=self.load_raster,
                args=(
                    gpsmap,
                    x[0],
                ),
            )
            t.daemon = True
            t.start()

        # Save and render
        self.last_rect = [p1lat, p1lon, p2lat, p2lon]
        self.last_rasters = rasters

        # print ('rendering',len(rasters))
        for x in rasters:
            x.do_draw(gpsmap, cr)

        for x in self.metadata:
            # Disable bbox rendering
            # continue

            bb = x[1]

            min_r_lat = min(bb[0][0], bb[1][0])
            max_r_lat = max(bb[0][0], bb[1][0])
            min_r_lon = min(bb[0][1], bb[1][1])
            max_r_lon = max(bb[0][1], bb[1][1])

            xx, yy = gpsmap.convert_geographic_to_screen(
                OsmGpsMap.MapPoint.new_degrees(min_r_lat, min_r_lon)
            )
            xx2, yy2 = gpsmap.convert_geographic_to_screen(
                OsmGpsMap.MapPoint.new_degrees(max_r_lat, max_r_lon)
            )

            cr.set_source_rgba(1, 0, 0, 0.6)
            cr.set_line_width(0.3)
            cr.move_to(xx, yy)
            cr.line_to(xx, yy2)
            cr.line_to(xx2, yy2)
            cr.line_to(xx2, yy)
            cr.line_to(xx, yy)

            cr.stroke()

    def do_render(self, gpsmap):
        pass

    def do_busy(self):
        return False

    def do_button_press(self, gpsmap, gdkeventbutton):
        return False
