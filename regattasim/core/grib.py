import requests
import logging
import tempfile
import random

from .. import config

logger = logging.getLogger ('regattasim')

class Grib:
	def __init__ (self):
		pass

	def getWind (self, t, lat, lon):
		return [random.random () * 6, random.random () * 10]

	def parse (self):
		pass

	def download (self, uri, percentageCallback, callback):
		logger.info ('starting download of %s' % uri)

		response = requests.get(uri, stream=True)
		total_length = response.headers.get('content-length')
		last_signal_percent = -1
		gribdata = b''
		f = open ('/home/dakk/testgrib.grb', 'wb')

		if total_length is None:
			pass
		else:
			dl = 0
			total_length = int(total_length)
			for data in response.iter_content (chunk_size=4096):
				dl += len (data)
				gribdata += data
				f.write (data)
				done = int (100 * dl / total_length)
				
				if last_signal_percent != done:
					percentageCallback (done)  
					last_signal_percent = done
		
		f.close ()
		logger.info ('download completed %s' % uri)
		callback (True)