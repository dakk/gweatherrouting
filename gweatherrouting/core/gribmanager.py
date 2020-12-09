import tempfile
import json
import requests
from bs4 import BeautifulSoup

from .grib import Grib

class GribManager:
	def __init__(self):
		self.gribFiles = None

		self.gribs = []
		self.timeframe = [0, 0]

	def load(self, path):
		self.gribs.append (Grib.parse(path))

	def hasGrib(self):
		return len(self.gribs) > 0

	# Returns the cumulative timeframe of loaded grib files
	def getTimeframe(self):
		return self.timeframe


	def getWindAt(self, t, lat, lon):
		# TODO: get the best matching grib for lat/lon at time t
		if len(self.gribs) > 0:
			return self.gribs[0].getWindAt(t, lat, lon)

		return None


	def getWind (self, t, bounds):
		# TODO: get the best matching grib for lat/lon at time t
		if len(self.gribs) > 0:
			return self.gribs[0].getWind(t, bounds)

		return None


		
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


	# def download (self, uri, percentageCallback, callback):
	# 	logger.info ('starting download of %s' % uri)

	# 	response = requests.get(uri, stream=True)
	# 	total_length = response.headers.get('content-length')
	# 	last_signal_percent = -1
	# 	f = open ('/home/dakk/testgrib.grb', 'wb')

	# 	if total_length is None:
	# 		pass
	# 	else:
	# 		dl = 0
	# 		total_length = int(total_length)
	# 		for data in response.iter_content (chunk_size=4096):
	# 			dl += len (data)
	# 			f.write (data)
	# 			done = int (100 * dl / total_length)
				
	# 			if last_signal_percent != done:
	# 				percentageCallback (done)  
	# 				last_signal_percent = done
		
	# 	f.close ()
	# 	logger.info ('download completed %s' % uri)

	# 	self.parse ('/home/dakk/testgrib.grb')
	# 	callback (True)