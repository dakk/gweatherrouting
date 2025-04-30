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
# flake8: noqa: E402
import logging
import time
from threading import Thread

import gi
import requests
from osgeo import ogr

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("OsmGpsMap", "1.2")
except:
    gi.require_version("OsmGpsMap", "1.0")

from gi.repository import Gdk, Gtk, OsmGpsMap

from gweatherrouting.common import resource_path
from gweatherrouting.core.core import LinePointValidityProvider
from gweatherrouting.core.storage import DATA_DIR, TEMP_DIR

from .chartlayer import ChartLayer

logger = logging.getLogger("gweatherrouting")


class OSMAskDownloadDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="OpenSeaMap Download", transient_for=parent, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        self.set_default_size(250, 100)
        self.set_border_width(10)
        label = Gtk.Label(
            label="OpenSeaMap data is missing,\ndo you want to download them (~2MB)?"
        )
        box = self.get_content_area()
        box.add(label)
        self.show_all()


class OSMDownloadDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="OpenSeaMap Download", transient_for=parent, flags=0)
        self.parent = parent
        self.set_default_size(250, 60)
        self.set_border_width(10)
        self.pb = Gtk.ProgressBar()
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.l = Gtk.Label(label="Download in progress")
        b.pack_start(self.l, True, True, 20)
        b.pack_start(self.pb, True, True, 20)
        box = self.get_content_area()
        box.add(b)
        self.show_all()

        self.thread = Thread(target=self.download, args=())
        self.thread.start()

    def percentageCallback(self, percentage, d, t):
        Gdk.threads_enter()
        self.pb.set_fraction(percentage / 100)
        self.l.set_text(f"Downloading: {percentage}%")
        Gdk.threads_leave()

    def callback(self, success):
        Gdk.threads_enter()
        if success:
            edialog = Gtk.MessageDialog(
                self.parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Done"
            )
            edialog.format_secondary_text("OpenSeaMap downloaded")
            edialog.run()
            edialog.destroy()
            self.response(Gtk.ResponseType.OK)
        else:
            logger.error("Error downloading OpenSeaMap")

            edialog = Gtk.MessageDialog(
                self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error"
            )
            edialog.format_secondary_text("Cannot download OpenSeaMap")
            edialog.run()
            edialog.destroy()
            self.response(Gtk.ResponseType.CANCEL)
        Gdk.threads_leave()

    def download(self):
        uri = "https://github.com/dakk/osm-seamarks/raw/master/seamarks.pbf"
        logger.info("Downloading openseamap")

        response = requests.get(uri, stream=True)
        total_length = response.headers.get("content-length")
        last_signal_percent = -1
        f = open(DATA_DIR + "/seamarks.pbf", "wb")

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
                    self.percentageCallback(done, dl, total_length_i)
                    last_signal_percent = done

        f.close()
        logger.info("OpenSeaMap download completed")

        self.callback(True)


class GSHHSAskDownloadDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="Base Map Download", transient_for=parent, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        self.set_default_size(250, 100)
        self.set_border_width(10)
        label = Gtk.Label(
            label="Base world countourn lines are missing,\ndo you want to download them (~140MB)?"
        )
        box = self.get_content_area()
        box.add(label)
        self.show_all()


class GSHHSDownloadDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="Base Map Download", transient_for=parent, flags=0)
        self.parent = parent
        self.set_default_size(250, 60)
        self.set_border_width(10)
        self.pb = Gtk.ProgressBar()
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.l = Gtk.Label(label="Download in progress")
        b.pack_start(self.l, True, True, 20)
        b.pack_start(self.pb, True, True, 20)
        box = self.get_content_area()
        box.add(b)
        self.show_all()

        self.thread = Thread(target=self.download, args=())
        self.thread.start()

    def percentageCallback(self, percentage, d, t):
        Gdk.threads_enter()
        self.pb.set_fraction(percentage / 100)
        self.l.set_text(f"Downloading: {percentage}%")
        Gdk.threads_leave()

    def callback(self, success):
        Gdk.threads_enter()
        if success:
            edialog = Gtk.MessageDialog(
                self.parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Done"
            )
            edialog.format_secondary_text("Base map downloaded")
            edialog.run()
            edialog.destroy()
            self.response(Gtk.ResponseType.OK)
        else:
            logger.error("Error downloading GSHHS")

            edialog = Gtk.MessageDialog(
                self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error"
            )
            edialog.format_secondary_text("Cannot download base map")
            edialog.run()
            edialog.destroy()
            self.response(Gtk.ResponseType.CANCEL)
        Gdk.threads_leave()

    def download(self):
        import zipfile

        # uri = "https://www.ngdc.noaa.gov/mgg/shorelines/data/gshhg/oldversions/version2.3.6/gshhg-shp-2.3.6.zip"
        uri = "https://github.com/dakk/gweatherrouting/releases/download/gshhs2.3.6/gshhg-shp-2.3.6.zip"
        logger.info("Downloading gshhs base map")

        response = requests.get(uri, stream=True)
        total_length = response.headers.get("content-length")
        last_signal_percent = -1
        f = open(TEMP_DIR + "/gshhs2.3.6.zip", "wb")

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
                    self.percentageCallback(done, dl, total_length_i)
                    last_signal_percent = done

        f.close()
        logger.info("GSHHS base map download completed")

        zipfile.ZipFile(TEMP_DIR + "/gshhs2.3.6.zip").extractall(DATA_DIR)
        self.callback(True)


# 	GSHHS_shp: Shapefiles (polygons) derived from shorelines.
# 		   These are named GSHHS_<resolution>_L<level>.*
# 	WDBII_shp: Political boundaries and rivers (lines).
# 		   These are called
# 		   WDBII_border_<resolution>_L<level>.*
# 		   WDBII_river_<resolution>_L<level>.*

# where <resolution> is one of f,h,i,l,c and <level> is an integer.
# All data sets come in 5 different resolutions:
# 	f : Full resolution.  These contain the maximum resolution
# 	    of this data and has not been decimated.
# 	h : High resolution.  The Douglas-Peucker line reduction was
# 	    used to reduce data size by ~80% relative to full.
# 	i : Intermediate resolution.  The Douglas-Peucker line reduction was
# 	    used to reduce data size by ~80% relative to high.
# 	l : Low resolution.  The Douglas-Peucker line reduction was
# 	    used to reduce data size by ~80% relative to intermediate.
# 	c : Crude resolution.  The Douglas-Peucker line reduction was
# 	    used to reduce data size by ~80% relative to low.

# For each resolution there are several levels; these depends on the data type.

# The shoreline data are distributed in 6 levels:

# Level 1: Continental land masses and ocean islands, except Antarctica.
# Level 2: Lakes
# Level 3: Islands in lakes
# Level 4: Ponds in islands within lakes
# Level 5: Antarctica based on ice front boundary.
# Level 6: Antarctica based on grounding line boundary.

from .vectordrawer.simplechartdrawer import SimpleChartDrawer


class GSHHSVectorChart(ChartLayer, LinePointValidityProvider):
    def __init__(self, path, settingsManager, metadata=None):
        super().__init__(path, "vector", settingsManager, metadata)

        self.lastTime = {"c": 0, "l": 0, "i": 0, "h": 0, "f": 0}
        self.forceDownscale = False

        self.drawer = SimpleChartDrawer(settingsManager)
        drv = ogr.GetDriverByName("ESRI Shapefile")
        self.vectorFiles = {}
        for x in ["f", "h", "i", "l", "c"]:
            for y in [1]:  # ,2,3,4,5,6]:
                f = drv.Open(
                    path + "/GSHHS_shp/" + x + "/GSHHS_" + x + "_L" + str(y) + ".shp"
                )
                if f is not None:
                    self.vectorFiles[x + str(y)] = f

        self.lpvFile = drv.Open(path + "/GSHHS_shp/h/GSHHS_h_L1.shp")

        f = open(
            resource_path("gweatherrouting", "data/countries_en.txt"),
            "r",
        )
        self.countries = list(
            filter(
                lambda x: len(x) == 4, map(lambda x: x.split(";"), f.read().split("\n"))
            )
        )
        f.close()

    def onRegister(self, onTickHandler=None):
        pass

    def pointsValidity(self, latlons):
        vf = self.lpvFile

        points = ogr.Geometry(ogr.wkbLinearRing)
        pointsa = []
        res = [True for x in latlons]

        for x in latlons:
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(x[1], x[0])
            points.AddPoint(x[1], x[0])
            pointsa.append(point)
        points.AddPoint(latlons[0][1], latlons[0][0])

        ev = points.GetEnvelope()
        boundingGeometry = ogr.CreateGeometryFromWkt(
            self.getBoundingWKTOfCoords(
                ev[1] - 0.1, ev[0] - 0.1, ev[3] + 0.1, ev[2] + 0.1
            )
        )

        for i in range(vf.GetLayerCount()):
            layer = vf.GetLayerByIndex(i)
            layer.SetSpatialFilter(boundingGeometry)

            feat = layer.GetNextFeature()
            while feat is not None:
                if not feat:
                    continue

                geom = feat.GetGeometryRef()
                geom = boundingGeometry.Intersection(geom)

                for ii, x in enumerate(pointsa):
                    if not res[ii]:
                        continue
                    if geom.Contains(x):
                        res[ii] = False

                del geom
                del feat

                if len(list(filter(lambda x: x, res))) == 0:
                    return res

                feat = layer.GetNextFeature()
            del layer

        return res

    def linesValidity(self, latlons):
        vf = self.lpvFile

        lines = ogr.Geometry(ogr.wkbLinearRing)
        linesa = []
        res = [True for x in latlons]

        for x in latlons:
            line = ogr.Geometry(ogr.wkbLineString)
            line.AddPoint(x[1], x[0])
            line.AddPoint(x[3], x[2])
            lines.AddGeometry(line)
            linesa.append(line)
        lines.AddPoint(latlons[0][1], latlons[0][0])

        ev = lines.GetEnvelope()
        boundingGeometry = ogr.CreateGeometryFromWkt(
            self.getBoundingWKTOfCoords(
                ev[1] - 0.1, ev[0] - 0.1, ev[3] + 0.1, ev[2] + 0.1
            )
        )

        for i in range(vf.GetLayerCount()):
            layer = vf.GetLayerByIndex(i)
            layer.SetSpatialFilter(boundingGeometry)

            feat = layer.GetNextFeature()
            while feat is not None:
                if not feat:
                    continue

                geom = feat.GetGeometryRef()

                for ii, x in enumerate(linesa):
                    if not res[ii]:
                        continue
                    if geom.Intersects(x):
                        res[ii] = False

                del geom
                del feat

                if len(list(filter(lambda x: x, res))) == 0:
                    return res

                feat = layer.GetNextFeature()
            del layer

        return res

    def do_draw(self, gpsmap, cr):
        boundingGeometry = self.getBoundingGeometry(gpsmap)

        # Get the correct quality for zoom level
        scale = gpsmap.get_scale()
        if scale > 5000:
            q = "c"
        elif scale > 500:  # or self.lastTime['i'] > 1.0:
            q = "l"
        elif scale > 200 or self.forceDownscale:  # or self.lastTime['h'] > 1.0
            q = "i"
        elif scale >= 15 or self.lastTime["f"] > 0.25:
            q = "h"
        elif scale < 15:
            q = "f"

        t = time.time()
        self.drawer.draw(gpsmap, cr, self.vectorFiles[q + "1"], boundingGeometry)
        self.lastTime[q] = int(time.time() - t)

        if scale < 4500:
            for c in self.countries:
                # TODO: check if x[2],x[3] is inside the boundingGeometry

                # render country name
                cr.set_source_rgba(0, 0, 0, 0.8)
                cr.set_font_size(9)
                x, y = gpsmap.convert_geographic_to_screen(
                    OsmGpsMap.MapPoint.new_degrees(float(c[2]), float(c[3]))
                )
                cr.move_to(x, y)
                cr.show_text(c[1])

    def do_render(self, gpsmap):
        pass

    def do_busy(self):
        return False

    def do_button_press(self, gpsmap, gdkeventbutton):
        return False
