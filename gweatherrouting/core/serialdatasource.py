# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
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
from serial.tools import list_ports

from . import DataSource

logger = logging.getLogger ('gweatherrouting')

class SerialDataSource(DataSource):
	def __init__(self, protocol, direction, port, baudrate=9600):
		DataSource.__init__(self, protocol, direction)
		self.port = port
		self.baudrate = baudrate
		self.s = None

	def connect(self):
		try:
			self.s = serial.Serial(self.port, baudrate=self.baudrate)
			self.connected = True
			return True
		except:
			logger.error ('Error connecting to serial port %s' % self.port)
			return False

	@staticmethod
	def detect():
		devices = []
		for x in list_ports.comports():
			try:
				devices.append(x.device)
				logger.info ('Detected new data source: %s [%s]' % (x.device, x.description))
			except:
				pass

		return devices

	def _read(self):
		if self.s.inWaiting() > 0:
			return self.s.read(self.s.inWaiting()).decode('ascii').split('\n')

		return []

	def _write(self, msg):
		self.s.write(msg.encode('ascii'))
