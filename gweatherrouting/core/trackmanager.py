from .track import Track 
from ..session import *


defaultSession = {
	'tracks': [],
	'activeTrack': ''
}

class TrackManager(Sessionable):
	def __init__(self):
		Sessionable.__init__(self, 'track-manager', defaultSession)

		self.tracks = []
		self.activeTrack = None

		for x in self.getSessionVariable('tracks'):
			tr = Track(name=x['name'], waypoints=x['waypoints'], visible=x['visible'], trackManager=self)
			self.tracks.append(tr)
		self.activate(self.getSessionVariable('activeTrack'))

	def saveTracks(self):
		ts = []
		for x in self.tracks:
			ts.append({'name': x.name, 'waypoints': x.waypoints, 'visible': x.visible })

		self.storeSessionVariable('tracks', ts)
		if self.activeTrack:
			self.storeSessionVariable('activeTrack', self.activeTrack.name)
		else:
			self.storeSessionVariable('activeTrack', '')

	def activate(self, name):
		for x in self.tracks:
			if x.name == name:
				self.activeTrack = x
				self.saveTracks()
				return 

	def create(self):
		nt = Track(name=('noname-%d' % (len(self.tracks) + 1)), trackManager=self)
		nt.clear()
		self.tracks.append (nt)
		self.activeTrack = nt
		self.saveTracks()

	def remove(self, track):
		actTremove = False 

		if track == self.activeTrack:
			self.activeTrack = None
			actRemove = True

		self.tracks.remove(track)
		if actRemove and len(self.tracks) > 0:
			self.activeTrack = self.tracks[0]

		self.saveTracks()

	def importTrack (self, path):
		try:
			tree = ElementTree.parse (path)
		except:
			return False

		waypoints = []
		root = tree.getroot ()
		for child in root:
			wp = (float (child.attrib['lat']), float (child.attrib['lon']))
			waypoints.append (wp)

		self.tracks.append(Track(path.split('/')[-1].split('.')[0], waypoints, trackManager=self))
		self.saveTracks()
		return True