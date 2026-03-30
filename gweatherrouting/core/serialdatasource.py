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

import logging

import serial
from serial.tools import list_ports

from gweatherrouting.core import DataSource

logger = logging.getLogger("gweatherrouting")


class SerialDataSource(DataSource):
    def __init__(self, protocol, direction, port, baudrate=9600):
        DataSource.__init__(self, protocol, direction)
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None

    def connect(self):
        try:
            self.serial_conn = serial.Serial(self.port, baudrate=self.baudrate)
            self.connected = True
            return True
        except Exception:
            logger.error("Error connecting to serial port %s", self.port)
            return False

    def close(self):
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except Exception:
                pass
            self.serial_conn = None
        self.connected = False

    @staticmethod
    def detect():
        devices = []
        for x in list_ports.comports():
            try:
                devices.append(x.device)
                logger.info(
                    "Detected new data source: %s [%s]", x.device, x.description
                )
            except Exception:
                pass

        return devices

    def _read(self):
        try:
            if self.serial_conn and self.serial_conn.inWaiting() > 0:
                return (
                    self.serial_conn.read(self.serial_conn.inWaiting())
                    .decode("ascii")
                    .split("\n")
                )
        except (OSError, serial.SerialException) as e:
            logger.warning("Serial connection lost on %s: %s", self.port, e)
            self.connected = False

        return []

    def _write(self, msg):
        if self.serial_conn:
            self.serial_conn.write(msg.encode("ascii"))
