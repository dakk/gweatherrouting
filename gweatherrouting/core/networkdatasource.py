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
import socket

from gweatherrouting.core import DataSource

logger = logging.getLogger("gweatherrouting")


class NetworkDataSource(DataSource):
    def __init__(self, protocol, direction, host, port, cnetwork):
        DataSource.__init__(self, protocol, direction)
        self.host = host
        self.port = port
        self.cached = ""

        # Create socket
        if cnetwork == "tcp":
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif cnetwork == "udp":
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.settimeout(5)

    def connect(self):
        try:
            self.s.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception as e:
            logger.error("Error while connecting to the network: %s", e)
            return False

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass
        self.connected = False

    def _read(self):
        dd = self.cached

        while dd.find("\n") == -1 and dd.find("\r") == -1:
            try:
                d = self.s.recv(1024).decode("ascii")
            except socket.timeout:
                logger.debug("Socket timeout on %s:%d", self.host, self.port)
                return []
            except OSError as e:
                logger.warning("Connection lost on %s:%d: %s", self.host, self.port, e)
                self.connected = False
                return []

            if len(d) == 0:
                # Peer closed the connection
                logger.info("Connection closed by peer on %s:%d", self.host, self.port)
                self.connected = False
                return []

            dd += d

        cc = dd.split("\n")
        self.cached = cc[-1]
        return cc[0:-1]

    def _write(self, data):
        self.s.send(data.encode("ascii"))
