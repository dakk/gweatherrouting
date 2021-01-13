import datetime
from ...core import EventDispatcher

class TimeControl(EventDispatcher):
    def __init__(self):
        self.now()

    def now(self):
        self.time = datetime.datetime.now().replace(minute = 0, second = 0, microsecond = 0)
        self.dispatch('time-change', self.time)

    def setTime(self, v):
        self.time = v
        self.dispatch('time-change', self.time)

    def decrease(self, u = 1):
        self.time -= datetime.timedelta(hours=u)
        self.dispatch('time-change', self.time)

    def increase(self, u = 1):
        self.time += datetime.timedelta(hours=u)
        self.dispatch('time-change', self.time)