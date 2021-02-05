# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
'''

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
