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
import time
from threading import Thread
from . import SerialDataSource, NetworkDataSource
from ..core import EventDispatcher
from ..storage import Storage

logger = logging.getLogger ('gweatherrouting')


# Every connection can be of type:
# - serial: data port, baudrate, protocol
# - connection: tcpudp, host, data port, protocol

class ConnManagerStorage(Storage):
	def __init__(self):
		Storage.__init__(self, "conn-manager")
		self.connections = []
		self.loadOrSaveDefault()


# { type: 'serial|network', protocol: 'nmea0183', direction: 'in|out|both' }
# Serial: { data-port: '/dev/ttyACM0', baudrate: 9600 }
# Network: { network: 'tcp|udp', host: 'localhost', port: '1234' }


class ConnManager(EventDispatcher):
	def __init__(self):
		self.storage = ConnManagerStorage()
		self.running = True
		self.sources = {}

	def __del__(self):
		self.running = False

	@property
	def connections(self):
		return self.storage.connections

	def plugAll(self):
		logger.info ('Plugging all connections')
		self.sources = {}
		for x in self.storage.connections:
			if x['type'] == 'serial':
				self.sources[x['data-port']] = SerialDataSource(x['protocol'], x['direction'], x['data-port'], x['baudrate'])
			elif x['type'] == 'network':
				self.sources[x['host'] + ':' + str(x['port'])] = NetworkDataSource(x['protocol'], x['direction'], x['host'], x['port'], x['network'])

	def addConnection(self, d):
		if d['type'] == 'serial':
			if list(filter(lambda x: x['data-port'] == d['data-port'], self.connections)) == []:
				self.storage.connections.append(d)
		elif d['type'] == 'network':
			if list(filter(lambda x: x['host'] == d['host'] and x['port'] == d['port'], self.connections)) == []:
				self.storage.connections.append(d)

		self.storage.save()
		self.plugAll()

	def removeConnection(self, d):
		self.storage.connections.remove(d)
		self.storage.save()
		self.plugAll()

	def poll(self):
		dd = []
		todel = []

		for x in self.sources:
			ds = self.sources[x]
			try:
				d = ds.read()
				if len(d): 
					dd += d
			except Exception as e:
				logger.error ('Error reading data from source: ' + str(e))
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
