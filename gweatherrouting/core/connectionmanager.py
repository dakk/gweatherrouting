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
import time
from threading import Thread
from . import SerialDataSource, NetworkDataSource
from .utils import EventDispatcher, Storage

logger = logging.getLogger ('gweatherrouting')


# Every connection can be of type:
# - serial: data port, baudrate, protocol
# - connection: tcpudp, host, data port, protocol

class ConnectionManagerStorage(Storage):
	def __init__(self):
		Storage.__init__(self, "conn-manager")
		self.connections = []
		self.loadOrSaveDefault()


# { type: 'serial|network', protocol: 'nmea0183', direction: 'in|out|both' }
# Serial: { data-port: '/dev/ttyACM0', baudrate: 9600 }
# Network: { network: 'tcp|udp', host: 'localhost', port: '1234' }


class ConnectionManager(EventDispatcher):
	def __init__(self):
		self.storage = ConnectionManagerStorage()
		self.running = True
		self.sources = {}
		self.thread = None

	def __del__(self):
		self.running = False

	def stopPolling(self):
		logger.info ('Polling stopped')
		self.running = False
		self.thread.join()

	@property
	def connections(self):
		return self.storage.connections

	def plugAll(self):
		logger.info ('Plugging all connections')
		self.sources = {}
		for x in self.storage.connections:
			if x['type'] == 'serial':
				self.sources[x['data-port']] = SerialDataSource(x['protocol'], x['direction'], x['data-port'], x['baudrate'])
				if self.sources[x['data-port']].connect():
					logger.info ('Data source %s connected', x['data-port'])


			elif x['type'] == 'network':
				self.sources[x['host'] + ':' + str(x['port'])] = NetworkDataSource(
					x['protocol'], x['direction'], x['host'], x['port'], x['network'])
				if self.sources[x['host'] + ':' + str(x['port'])].connect():
					logger.info ('Data source %s:%d connected', x['host'], x['port'])

	def addConnection(self, d):
		if d['type'] == 'serial':
			if not list(filter(lambda x: x['type'] == 'serial' and x['data-port'] == d['data-port'], self.connections)):
				self.storage.connections.append(d)
		elif d['type'] == 'network':
			if not list(filter(lambda x: x['type'] == 'network'
				and x['host'] == d['host'] and x['port'] == d['port'], self.connections)):
				self.storage.connections.append(d)

		self.storage.save()
		self.plugAll()


	def removeConnection(self, d):
		self.storage.connections.remove(d)
		self.storage.save()
		self.plugAll()

	def poll(self):
		dd = []
		rf = 0

		for _, ds in self.sources.items():
			if not ds.connected:
				continue

			rf += 1
			try:
				d = ds.read()
				if len(d):
					dd += d
			except Exception as e:
				print (e)
				logger.error ('Error reading data from source')

		if len(dd) > 0:
			self.dispatch('data', dd)

		if rf < len(self.sources):
			time.sleep(30)
			self.plugAll()

		return len(dd)


	def pollLoop(self, b):
		while self.running:
			try:
				n = self.poll()
			except Exception as e:
				print(e)
				logger.error ('Error polling data')
			if n > 0:
				time.sleep(0.05)
			else:
				time.sleep(0.5)


	def startPolling(self):
		logger.info ('Polling started')
		self.running = True
		self.thread = Thread(target=self.pollLoop, args=(True, ))
		self.thread.start()
