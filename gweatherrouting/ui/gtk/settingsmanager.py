from ...session import *

defaultSession = {
	'grib': {
		'arrowColor': '#ccc'
	},
	'charts': {
		'directories': []
	},
	'ais': {

	},
	'nmea': {
		
	}
}

class SettingsManager(Sessionable):
	def __init__(self):
		Sessionable.__init__(self, "settings", defaultSession)
