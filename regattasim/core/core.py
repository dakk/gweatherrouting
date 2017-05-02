from .. import config
from .track import Track
from .simulation import Simulation
from .boat import Boat
from .grib import Grib

class Core:
    def __init__ (self):
        self.track = Track ()
        self.grib = Grib ()
        self.grib.parse ('/home/dakk/testgrib.grb')

    # Simulation
    def createSimulation (self, boatModel):
        boat = Boat (boatModel)
        sim = Simulation (boat, self.track)
        return sim

    # Track ans save/load
    def getTrack (self):
        return self.track

    def load (self, path):
        return self.track.load (path)

    def save (self, path):
        return self.track.save (path)