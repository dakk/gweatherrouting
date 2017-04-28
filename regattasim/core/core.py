from .. import config
from .track import Track

class Core:
    def __init__ (self):
        self.track = Track ()

    def getTrack (self):
        return self.track

    def load (self, path):
        return self.track.load (path)


    def save (self, path):
        return self.track.save (path)