from .boat import Boat
from .track import Track

class Simulation:
    def __init__ (self, boat, track):
        self.mode = 'wind'      # 'compass' 'gps' 'vmg'
        self.boat = boat
        self.track = track
        self.steps = 0
        self.path = Track ()    # Simulated points

    def reset (self):
        self.steps = 0
        self.path.clear ()

    def step (self):
        self.steps += 1

        # Play a tick
        print (self.boat.getJib ())
        print (self.boat.getMainsail ())
