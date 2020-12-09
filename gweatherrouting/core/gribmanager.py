from .grib import Grib

class GribManager:
	def __init__(self):
		self.gribs = []
		self.timeframe = [0, 1]

	def load(self, path):
		self.gribs.append (Grib.parse(path))


	# Returns the cumulative timeframe of loaded grib files
	def getTimeframe(self):
		return self.timeframe


	def getWindAt(self, t, lat, lon):
		# TODO: get the best matching grib for lat/lon at time t
		if len(self.gribs) > 0:
			return self.gribs[0].getWindAt(t, lat, lon)


	def getWind (self, t, bounds):
		# TODO: get the best matching grib for lat/lon at time t
		if len(self.gribs) > 0:
			return self.gribs[0].getWind(t, bounds)
