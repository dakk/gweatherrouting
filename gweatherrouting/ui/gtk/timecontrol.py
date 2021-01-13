from ...core import EventDispatcher

class TimeControl(EventDispatcher):
    def __init__(self):
        self.time = 0.0

    def setTime(self, v):
        self.time = v
        self.dispatch('time-change', self.time)

    def decrease(self, u = 1):
        self.time -= u
        self.dispatch('time-change', self.time)

    def increase(self, u = 1):
        self.time += u
        self.dispatch('time-change', self.time)