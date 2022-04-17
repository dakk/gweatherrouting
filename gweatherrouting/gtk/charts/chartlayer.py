from osgeo import ogr

class ChartLayer:
	def __init__(self, path, ctype, settingsManager, metadata = None, enabled = True):
		self.path = path
		self.ctype = ctype
		self.enabled = enabled
		self.metadata = metadata
		self.settingsManager = settingsManager

	def onRegister(self, onTickHandler = None):
		""" Called when the dataset is registered on the software """
		pass

	def getBoundingWKT(self, gpsmap):
		p1, p2 = gpsmap.get_bbox()

		p1lat, p1lon = p1.get_degrees()
		p2lat, p2lon = p2.get_degrees()
		return "POLYGON((%f %f,%f %f,%f %f,%f %f,%f %f))" % (
			p1lon,
			p1lat,
			p1lon,
			p2lat,
			p2lon,
			p2lat,
			p2lon,
			p1lat,
			p1lon,
			p1lat
		)

	def getBoundingGeometry(self, gpsmap):
		wktbb = self.getBoundingWKT(gpsmap)
		return ogr.CreateGeometryFromWkt(wktbb)