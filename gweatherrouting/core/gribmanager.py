import tempfile
import json
import bz2
import requests
from ..storage import *
from bs4 import BeautifulSoup

from .grib import Grib

class GribManager:
	def __init__(self):
		self.gribFiles = None

		self.gribs = []
		self.timeframe = [0, 0]

	def load(self, path):
		logger.info ('Loading grib %s' % path)
		self.gribs.append (Grib.parse(path))

	def hasGrib(self):
		return len(self.gribs) > 0

	# Returns the cumulative timeframe of loaded grib files
	def getTimeframe(self):
		return self.timeframe


	def getWindAt(self, t, lat, lon):
		# TODO: get the best matching grib for lat/lon at time t
		g = []
		for x in self.gribs:
			g = g + x.getWindAt(t, lat, lon)

		return g


	def getWind (self, t, bounds):
		# TODO: get the best matching grib for lat/lon at time t
		g = []
		for x in self.gribs:
			g = g + x.getWind(t, bounds)

		return g


		
	def getDownloadList (self, force=False):
		# https://openskiron.org/en/openskiron
		# https://openskiron.org/en/openwrf
		if not self.gribFiles or force:
			data = requests.get ('https://openskiron.org/en/openskiron').text
			soup = BeautifulSoup (data, 'html.parser')
			self.gribFiles = []

			for row in soup.find ('table').find_all ('tr'):
				r = row.find_all ('td')

				if len (r) >= 3:
					# Name, Source, Size, Time, Link
					self.gribFiles.append ([r[0].text.strip(), 'OpenSkiron', r[1].text, r[2].text, r[0].find ('a', href=True)['href']])


			data = requests.get ('https://openskiron.org/en/openwrf').text
			soup = BeautifulSoup (data, 'html.parser')

			for row in soup.find ('table').find_all ('tr'):
				r = row.find_all ('td')

				if len (r) >= 3:
					# Name, Source, Size, Time, Link
					self.gribFiles.append ([r[0].text.strip(), 'OpenWRF', r[1].text, r[2].text, r[0].find ('a', href=True)['href']])

		return self.gribFiles


	def download (self, uri, percentageCallback, callback):
		name = uri.split('/')[-1]
		logger.info ('Downloading grib %s' % uri)

		response = requests.get(uri, stream=True)
		total_length = response.headers.get('content-length')
		last_signal_percent = -1
		f = open (TEMP_DIR + '/' + name, 'wb')

		if total_length is None:
			pass
		else:
			dl = 0
			total_length = int(total_length)
			for data in response.iter_content (chunk_size=4096):
				dl += len (data)
				f.write (data)
				done = int (100 * dl / total_length)
				
				if last_signal_percent != done:
					percentageCallback (done)  
					last_signal_percent = done
		
		f.close ()
		logger.info ('Grib download completed %s' % uri)


		bf = bz2.open(TEMP_DIR + '/' + name, 'rb')
		f = open(GRIB_DIR + '/' + name.replace('.bz2', ''), 'wb')
		f.write(bf.read())
		f.close()
		bf.close()

		self.load (GRIB_DIR + '/' + name.replace('.bz2', ''))
		callback (True)