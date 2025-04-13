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
import pynmea2
from pynmea2.nmea_utils import LatLonFix


class DataPacket:
    def __init__(self, t, sentence):
        self.t = t
        self.data = sentence

    def isPosition(self):
        return "latitude" in self.data and "longitude" in self.data

    @staticmethod
    def parse(data):
        raise NotImplementedError

    def serialize(self):
        raise NotImplementedError


class NMEADataPacket(DataPacket):
    PROTOCOL = "nmea0183"

    def __init__(self, sentence):
        DataPacket.__init__(self, "nmea", sentence)

    def isPosition(self):
        return (
            isinstance(self.data, LatLonFix)
            and self.data.latitude != 0.0
            and self.data.longitude != 0.0
        )

    @staticmethod
    def parse(data):
        return NMEADataPacket(pynmea2.parse(data))

    def serialize(self):
        return str(self.data)


class DataSource:
    def __init__(self, protocol, direction):
        self.protocol = protocol
        self.direction = direction
        self.connected = False

        if self.protocol == "nmea0183":
            self.parser = NMEADataPacket
        else:
            raise NotImplementedError

    def write(self, packet):
        if not self.connected:
            return False

        if self.direction == "in":
            return False

        return self._write(packet.serialize())

    def read(self):
        if not self.connected:
            return None

        if self.direction == "out":
            return []

        data = self._read()

        if data is None:
            return []

        msgs = []
        for msg in data:
            if len(msg) == 0:
                continue

            try:
                msgs.append(self.parser.parse(msg))
            except Exception as e:
                print("Unable to parse data:", e)
        return msgs

    def _read(self):
        raise NotImplementedError

    def _write(self, data):
        raise NotImplementedError
