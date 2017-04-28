from .boat import Boat

class Simulation:
    def __init__ (self, boat, track):
        self.mode = 'GPS' # 
        self.boat = boat
        self.track = track
        self.steps = 0


    def reset (self):
        self.steps = 0

    def step (self):
        self.steps += 1

        # Play a tick
        print (self.boat.getJib ())
        print (self.boat.getMainsail ())
