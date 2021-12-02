# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
'''

import serial
import pynmea2

from gweatherrouting.conn.datasource import NMEADataPacket
from . import DataSource

class SerialDataSource(DataSource):
    def __init__(self, port):
        self.uri = port
        self.s = serial.Serial(port)

    def read(self):
        msgs = []

        if (self.s.inWaiting() > 0):
            d = self.s.read(self.s.inWaiting()).decode('ascii')

            for x in d.split('\n'):
                try:
                    msg = pynmea2.parse(x)
                    msgs.append(NMEADataPacket(msg))
                except:
                    pass
        
        return msgs
