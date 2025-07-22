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
import io
import logging
import os
import time
from threading import Thread
from typing import List, Optional

import cairo
import gi
import nmeatoolkit as nt
import numpy
import PIL

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("OsmGpsMap", "1.2")
except ValueError:
    gi.require_version("OsmGpsMap", "1.0")

from gi.repository import Gdk, Gtk

from gweatherrouting.core import Core
from gweatherrouting.core.timecontrol import TimeControl
from gweatherrouting.gtk.charts import ChartManager
from gweatherrouting.gtk.settings import SettingsManager

from .maplayers.geomaplayer import GeoMapLayer
from .maplayers.toolsmaplayer import ToolsMapLayer
from .widgets.timetravel import TimeTravelWidget

logger = logging.getLogger("gweatherrouting")

LOG_TEMP_FILE = "/tmp/gwr-recording.log"


class LogsStack(Gtk.Box, nt.Output, nt.Input):
    def __init__(
        self,
        parent,
        chart_manager: ChartManager,
        core: Core,
        settings_manager: SettingsManager,
    ):
        Gtk.Widget.__init__(self)

        self.parent = parent
        self.core = core
        self.recording = False
        self.loading = False
        self.data: List[nt.TrackPoint] = []
        self.recorded_data: Optional[io.TextIOWrapper] = None
        self.to_send: List = []

        self.depth_chart = False
        self.speed_chart = True
        self.apparent_wind_chart = False
        self.true_wind_chart = True
        self.hdg_chart = True
        self.rw_chart = False

        self.highlighted_value: Optional[nt.TrackPoint] = None
        self.crop_a = None
        self.crop_b = None

        self.core.connectionManager.connect("data", self.data_handler)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            os.path.abspath(os.path.dirname(__file__)) + "/logsstack.glade"
        )
        self.builder.connect_signals(self)

        self.pack_start(self.builder.get_object("logscontent"), True, True, 0)
        self.graph_area = self.builder.get_object("grapharea")

        self.status_bar = self.builder.get_object("statusbar")

        self.show_all()

        self.map = self.builder.get_object("map")
        self.map.set_center_and_zoom(39.0, 9.0, 6)
        self.map.layer_add(chart_manager)
        chart_manager.add_map(self.map)

        self.tools_map_layer = ToolsMapLayer(self.core)
        self.map.layer_add(self.tools_map_layer)

        self.time_control = TimeControl()
        self.selected_time = self.time_control.time
        self.timetravel_widget = TimeTravelWidget(
            self.parent, self.time_control, self.map, True
        )
        self.time_control.connect("time_change", self.on_time_change)
        self.builder.get_object("timetravelcontainer").pack_start(
            self.timetravel_widget, True, True, 0
        )

        self.geo_map_layer = GeoMapLayer(self.core, self.time_control)
        self.map.layer_add(self.geo_map_layer)

        self.show_all()

        self.builder.get_object("stop-button").hide()

        self.recording_thread: Optional[Thread] = None
        self.loading_thread: Optional[Thread] = None

        try:
            self.loading_thread = Thread(
                target=self.load_from_file, args=(LOG_TEMP_FILE,)
            )
            self.loading_thread.start()
        except:
            pass

    def on_time_change(self, time):
        self.selected_time = time
        if not self.recording and not self.loading:
            self.graph_area.queue_draw()
            self.map.queue_draw()

    def on_load_click(self, widget):
        dialog = Gtk.FileChooserDialog(
            "Please choose a file",
            self.parent,
            Gtk.FileChooserAction.OPEN,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )

        filter_nmea = Gtk.FileFilter()
        filter_nmea.set_name("NMEA log")
        # filter_nmea.add_mime_type ("application/gpx+xml")
        filter_nmea.add_pattern("*.nmea")
        dialog.add_filter(filter_nmea)

        # filter_gpx = Gtk.FileFilter ()
        # filter_gpx.set_name ("GPX track file")
        # filter_gpx.add_mime_type ("application/gpx+xml")
        # filter_gpx.add_pattern ('*.gpx')
        # dialog.add_filter (filter_gpx)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            dialog.destroy()

            try:
                self.status_bar.push(0, f"Loading {filepath}")
                self.loading_thread = Thread(
                    target=self.load_from_file, args=(filepath,)
                )
                self.loading_thread.start()
            except Exception as e:
                print(e)
                edialog = Gtk.MessageDialog(
                    self.parent,
                    0,
                    Gtk.MessageType.ERROR,
                    Gtk.ButtonsType.CANCEL,
                    "Error",
                )
                edialog.format_secondary_text(f"Cannot open file: {filepath}")
                edialog.run()
                edialog.destroy()
        else:
            dialog.destroy()

    def __del__(self):
        if self.recording:
            self.stopRecording()
            if self.recording_thread:
                self.recording_thread.join()

        if self.loading_thread:
            self.loading_thread.join()

    def set_crop_a(self, widget):
        self.crop_a = self.selected_time
        self.graph_area.queue_draw()

    def set_crop_b(self, widget):
        self.crop_b = self.selected_time
        self.graph_area.queue_draw()

    def crop_data(self, widget):
        if self.crop_a is None and self.crop_b is None:
            return

        if self.crop_a is None:
            self.crop_a = self.data[0].time

        if self.crop_b is None:
            self.crop_b = self.data[-1].time

        self.data = [
            d for d in self.data if d.time >= self.crop_a and d.time <= self.crop_b
        ]

        self.rebuild_track()
        self.graph_area.queue_draw()

        if self.recorded_data:
            self.recorded_data.flush()
            self.recorded_data.close()

        os.system(f"mv {LOG_TEMP_FILE} {LOG_TEMP_FILE}.2")

        pip = nt.Pipeline(
            nt.FileInput(LOG_TEMP_FILE + ".2"),
            nt.FileOutput(LOG_TEMP_FILE),
            nt.ToStringTranslator(),
            [nt.CropPipe(self.crop_a, self.crop_b)],
        )
        pip.run()

        os.system(f"rm {LOG_TEMP_FILE}.2")
        self.crop_a = None
        self.crop_b = None

    def on_recording_click(self, widget):
        if self.recording:
            return

        self.builder.get_object("record-button").hide()
        self.builder.get_object("stop-button").show()

        self.status_bar.push(0, "Recording from devices...")
        self.recording_thread = Thread(target=self.start_recording, args=())
        self.recording_thread.start()

    def on_stop_recording_click(self, widget):
        self.recording = False
        if self.recorded_data:
            self.recorded_data.close()
        self.to_send = []
        logger.debug("Stopping recording...")

        self.builder.get_object("record-button").show()
        self.builder.get_object("stop-button").hide()
        self.status_bar.push(0, "Recording stopped")

        if self.recording_thread:
            self.recording_thread.join()

    def toggle_speed_chart(self, widget):
        self.speed_chart = not self.speed_chart
        self.graph_area.queue_draw()

    def toggle_apparent_wind_chart(self, widget):
        self.apparent_wind_chart = not self.apparent_wind_chart
        self.graph_area.queue_draw()

    def toggle_true_wind_chart(self, widget):
        self.true_wind_chart = not self.true_wind_chart
        self.graph_area.queue_draw()

    def toggle_depth_chart(self, widget):
        self.depth_chart = not self.depth_chart
        self.graph_area.queue_draw()

    def toggle_hdg_chart(self, widget):
        self.hdg_chart = not self.hdg_chart
        self.graph_area.queue_draw()

    def toggle_rw_chart(self, widget):
        self.rw_chart = not self.rw_chart
        self.graph_area.queue_draw()

    def data_handler(self, d):
        if self.recording:
            for x in d:
                if self.recorded_data:
                    self.recorded_data.write(str(x.data) + "\n")
                self.to_send.append(x.data)

    def read_sentence(self):
        if len(self.to_send) > 0:
            return self.to_send.pop(0)
        return None

    def end(self):
        return not self.recording

    def write(self, data):
        if not data or not isinstance(data, nt.TrackPoint):
            return None

        self.data.append(data)

        if len(self.data) % 150 == 0 or (self.recording or len(self.data) % 5000 == 0):
            Gdk.threads_enter()
            self.time_control.set_time(data.time)

            if len(self.data) % 150 == 0:
                self.core.logManager.log_history.add(data.lat, data.lon)

            if self.recording or len(self.data) % 5000 == 0:
                # self.map.set_center_and_zoom(data.lat, data.lon, 12)
                logger.debug("Recorded %d points", len(self.data))
                self.status_bar.push(0, f"{len(self.data)} track points")

            Gdk.threads_leave()

    def close(self):
        if len(self.data) < 2:
            return

        self.data = self.data[1::]

        Gdk.threads_enter()
        self.map.set_center_and_zoom(self.data[0].lat, self.data[0].lon, 12)
        self.map.queue_draw()
        self.graph_area.queue_draw()
        self.loading = False
        Gdk.threads_leave()

    def on_save_click(self, widget):
        dialog = Gtk.FileChooserDialog(
            "Save log",
            self.parent,
            Gtk.FileChooserAction.SAVE,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE,
                Gtk.ResponseType.OK,
            ),
        )
        dialog.set_do_overwrite_confirmation(True)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            dialog.destroy()
            os.system(f"cp {LOG_TEMP_FILE} {filename}")

            self.status_bar.push(0, f"Saved to {filename}")
        else:
            dialog.destroy()

    def load_from_file(self, filepath):
        self.loading = True
        self.data = []
        # ext = filepath.split('.')[-1]

        # TODO: support for gpx files
        self.core.logManager.log_history.clear()

        try:
            fi = nt.FileInput(filepath)
        except:
            logger.error("Error loading file %s", filepath)
            self.loading = False
            return

        pip = nt.Pipeline(
            fi,
            self,
            nt.TrackPointTranslator(),
            [
                # nt.SeatalkPipe(),
                nt.FilterPipe(exclude=["ALK", "VDM"]),
                nt.TrueWindPipe(),
            ],
        )
        pip.run()

        if filepath != LOG_TEMP_FILE:
            os.system(f"cp {filepath} {LOG_TEMP_FILE}")
        # self.status_bar.push(0, "Load completed!")

    def save_to_file(self, filepath):
        pass

    def clear_data(self, widget):
        self.data = []

        if self.recorded_data:
            self.recorded_data.close()
        self.recorded_data = open(LOG_TEMP_FILE, "w")
        self.to_send = []
        self.core.logManager.log_history.clear()
        self.map.queue_draw()
        self.graph_area.queue_draw()
        logger.debug("Data cleared")

    def rebuild_track(self):
        self.core.logManager.log_history.clear()
        for x in self.data[0::150]:
            self.core.logManager.log_history.add(x.lat, x.lon)
        self.map.queue_draw()

    def start_recording(self):
        logger.debug("Recording started")
        self.recording = True
        self.recorded_data = open(LOG_TEMP_FILE, "w")

        pip = nt.Pipeline(
            self,
            self,
            nt.TrackPointTranslator(),
            [
                # nt.SeatalkPipe(),
                nt.FilterPipe(exclude=["ALK", "VDM"]),
                nt.TrueWindPipe(),
            ],
        )

        r = True
        while self.recording and r:
            r = pip.run_once()
            time.sleep(0.01)
        logger.debug("Recording stopped")

    def on_graph_draw(self, widget, ctx):  # noqa: C901
        s = 20
        a = widget.get_allocation()
        width = a.width

        if len(self.data) == 0:
            return

        import matplotlib.pyplot as plt

        plt.style.use("dark_background")
        plt.rcParams.update({"font.size": 8})
        y = self.data[::s]
        x = numpy.array([x.time for x in y])

        nplots = 1

        if self.hdg_chart or self.apparent_wind_chart or self.true_wind_chart:
            nplots += 1

        if self.speed_chart:
            nplots += 1

        if self.depth_chart:
            nplots += 1

        fig, ax1 = plt.subplots(nplots)
        try:
            ax1[0]
        except:
            ax1 = [ax1]
        fig.set_size_inches((width / 100), (a.height / 100.0))

        i = 0
        ii = -1
        self.highlighted_value = None
        self.status_bar.push(0, "")

        if not self.recording and not self.loading:
            x = list(map(lambda x: x.replace(tzinfo=None), x))

            ii = numpy.where(
                (x > (numpy.datetime64(self.selected_time)))
                & (
                    x
                    < (
                        numpy.datetime64(self.selected_time)
                        + numpy.timedelta64(
                            self.timetravel_widget.get_change_unit(), "s"
                        )
                    )
                )
            )
            try:
                ii = ii[0][0]  # type: ignore
                self.highlighted_value = y[ii]
                self.tools_map_layer.gps_add(
                    self.highlighted_value.lat,
                    self.highlighted_value.lon,
                    self.highlighted_value.hdg,
                    self.highlighted_value.speed,
                )

                self.status_bar.push(
                    0,
                    f"Time: {self.selected_time}, "
                    + f"Position: ({self.highlighted_value.lat:.2f}, "
                    + f"{self.highlighted_value.lon:.2f}), "
                    + f"Speed: {self.highlighted_value.speed:.1f}kn, "
                    + f"Heading: {self.highlighted_value.hdg}, "
                    + f"TWS: {self.highlighted_value.tws:.1f}kn, "
                    + f"TWA: {self.highlighted_value.twa}, "
                    + f"TWD: {(self.highlighted_value.twa + self.highlighted_value.hdg) % 360}, "
                    + f"Depth: {self.highlighted_value.depth:.2f}",
                )

            except Exception as e:
                print(e)
                ii = -1

        def highlight(i, data):
            if ii != -1:
                ax1[i].plot(x[ii], data[ii], color="#f00", marker="o", markersize=4)
                # ax1[i].axvline(x=ii)

        if self.speed_chart:
            if i < nplots - 1:
                plt.setp(ax1[i].get_xticklabels(), visible=False)

            data = list(map(lambda x: x.speed if x.speed else 0, y))
            ax1[i].plot(x, data, color="#8dd3c7", linewidth=0.6, label="Speed")

            highlight(i, data)

            ax1[i].legend()
            i += 1

        if self.apparent_wind_chart or self.true_wind_chart:
            if i < nplots - 1:
                plt.setp(ax1[i].get_xticklabels(), visible=False)

            if self.apparent_wind_chart:
                data = list(map(lambda x: x.aws if x.aws else 0, y))
                ax1[i].plot(x, data, color="#feffb3", linewidth=0.6, label="AWS")
                ax1[i].legend()

                highlight(i, data)
            if self.true_wind_chart:
                data = list(map(lambda x: x.tws if x.tws else 0, y))
                ax1[i].plot(x, data, color="#bfbbd9", linewidth=0.6, label="TWS")
                ax1[i].legend()

                highlight(i, data)
            i += 1

        if self.depth_chart:
            if i < nplots - 1:
                plt.setp(ax1[i].get_xticklabels(), visible=False)

            data = list(map(lambda x: x.depth if x.depth else 0, y))
            ax1[i].plot(x, data, color="#fa8174", linewidth=0.6, label="Depth")
            ax1[i].legend()

            highlight(i, data)
            i += 1

        if self.hdg_chart or self.apparent_wind_chart or self.true_wind_chart:
            if i < nplots - 1:
                plt.setp(ax1[i].get_xticklabels(), visible=False)

            ax2 = ax1[i]

            if self.apparent_wind_chart:
                if self.rw_chart:
                    data = list(map(lambda x: x.awa if x.awa else 0, y))
                    ax2.plot(x, data, color="#fe11b3", linewidth=0.3, label="AWA")
                    highlight(i, data)

                data = list(map(lambda x: (x.awa + x.hdg) % 360 if x.awa else 0, y))
                ax2.plot(x, data, color="#feffb3", linewidth=0.6, label="AWD")
                highlight(i, data)
            if self.true_wind_chart:
                if self.rw_chart:
                    data = list(map(lambda x: x.twa if x.twa else 0, y))
                    ax2.plot(x, data, color="#bf11d9", linewidth=0.3, label="TWA")
                    highlight(i, data)

                data = list(map(lambda x: (x.twa + x.hdg) % 360 if x.twa else 0, y))
                ax2.plot(x, data, color="#bfbbd9", linewidth=0.6, label="TWD")

                highlight(i, data)
            if self.hdg_chart:
                data = list(map(lambda x: x.hdg if x.hdg else 0, y))
                ax2.plot(x, data, color="#81b1d2", linewidth=0.6, label="HDG")

                highlight(i, data)

            ax2.legend()

        if self.crop_a is not None:
            try:
                ii = numpy.where(
                    (x > (numpy.datetime64(self.crop_a)))
                    & (
                        x
                        < (
                            numpy.datetime64(self.crop_a)
                            + numpy.timedelta64(
                                self.timetravel_widget.get_change_unit(), "s"
                            )
                        )
                    )
                )
                for axx in ax1:
                    axx.axvline(x=x[ii[0][0]], color="#ffffff", linewidth=0.5)
            except:
                pass

        if self.crop_b is not None:
            try:
                ii = numpy.where(
                    (x > (numpy.datetime64(self.crop_b)))
                    & (
                        x
                        < (
                            numpy.datetime64(self.crop_b)
                            + numpy.timedelta64(
                                self.timetravel_widget.get_change_unit(), "s"
                            )
                        )
                    )
                )
                for axx in ax1:
                    axx.axvline(x=x[ii[0][0]], color="#ffffff", linewidth=0.5)
            except:
                pass

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, dpi=100)
        buf.seek(0)
        buf2 = PIL.Image.open(buf)

        arr = numpy.array(buf2)
        height, width, _ = arr.shape
        surface = cairo.ImageSurface.create_for_data(
            arr, cairo.FORMAT_RGB24, width, height
        )

        ctx.save()
        ctx.set_source_surface(surface, 0, 0)
        ctx.paint()
        ctx.restore()

        fig.clf()
        plt.close(fig)
