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
import logging
import socket

from gweatherrouting.core import DataSource

logger = logging.getLogger("gweatherrouting")


class NetworkDataSource(DataSource):
    def __init__(self, protocol, direction, host, port, cnetwork):
        DataSource.__init__(self, protocol, direction)
        self.host = host
        self.port = port

        # Create socket
        if cnetwork == "tcp":
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif cnetwork == "udp":
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.settimeout(0.5)

    def connect(self):
        try:
            self.s.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception as e:
            logger.error("Error while connecting to the network: %s", e)
            return False

    cached = ""

    def _read(self):
        dd = self.cached

        while True:
            try:
                d = self.s.recv(128).decode("ascii")
                dd += d
                if dd.find("\n") != -1 or dd.find("\r") != -1:
                    cc = dd.split("\n")
                    self.cached = cc[-1]
                    return cc[0:-1]
            except:
                pass

    def _write(self, data):
        self.s.send(data.encode("ascii"))
