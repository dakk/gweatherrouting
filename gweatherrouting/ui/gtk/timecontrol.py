import datetime
from ...core import EventDispatcher


class TimeControl(EventDispatcher):
    DFORMAT = "%Y/%m/%d, %H:%M"

    def __init__(self):
        self.now()

    def now(self):
        self.time = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
        self.dispatch("time-change", self.time)

    def setTime(self, v):
        self.time = v
        self.dispatch("time-change", self.time)

    def decrease(self, hours=0, minutes=0):
        self.time -= datetime.timedelta(hours=hours, minutes=minutes)
        self.dispatch("time-change", self.time)

    def increase(self, hours=0, minutes=0):
        self.time += datetime.timedelta(hours=hours, minutes=minutes)
        self.dispatch("time-change", self.time)
