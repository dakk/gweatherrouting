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

import logging
import serial
import time
from threading import Thread
import serial.tools.list_ports
from . import SerialDataSource
from ..core import EventDispatcher

logger = logging.getLogger ('gweatherrouting')

class ConnManager(EventDispatcher):
    def __init__(self):
        self.running = True
        self.sources = {}

    def __del__(self):
        self.running = False

    def plugAll(self):
        for x in serial.tools.list_ports.comports():
            try:
                self.sources[x.device] = SerialDataSource(x.device)
                logger.info ('Detected new data source: %s [%s]' % (x.device, x.description))
            except:
                pass 

    def poll(self):
        dd = []
        todel = []

        for x in self.sources:
            ds = self.sources[x]
            try:
                d = ds.read()
                if len(d): 
                    dd += d
            except:
                logger.info ('Data source %s disconnected' % ds.uri)
                todel.append(x)

        if len(dd) > 0:
            self.dispatch('data', dd)

        if len(todel) > 0:
            for x in todel:
                del self.sources[x]
        if len(self.sources) == 0:
            self.plugAll()


    def pollLoop(self):
        while self.running:
            self.poll()
            time.sleep(0.5)

    def startPolling(self):
        logger.info ('Polling started')
        self.thread = Thread(target=self.pollLoop, args=())
        self.thread.start()
