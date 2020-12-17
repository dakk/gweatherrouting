# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
# Copyright (C) 2012 Riccardo Apolloni
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

import logging
import math
import os

from . import utils
from .polar import Polar
from .beizer import Beizer

logger = logging.getLogger ('gweatherrouting')


class Boat:
    def __init__ (self, model):
        self.model = model

        this_dir, this_fn = os.path.split (__file__)
        self.polar = Polar (this_dir + '/../data/boats/' + model + '/polar.pol')

    # Cambio di mura
    def changeTack (self):
        self.twa = -self.twa

    def move (self, dt):
        v=self.getSpeed ()
        pos = puntodistanterotta (self.position[0], self.position[1], v*dt, self.getHDG ())
        self.position = pos
        self.Log = self.Log + v * dt

    def moveRoutage (self, dt):
        v = self.getRoutageSpeed ()
        pos = puntodistanterotta (self.position[0], self.position[1], v*dt, self.getHDG ())
        self.position = pos
        self.Log = self.Log + v * dt
        
    def getSpeed (self):
        twa = math.copysign (self.twa, 1)
        return self.polar.getSpeed (self.tw[1], twa)

    def getRoutageSpeed (self):
        twa = math.copysign(self.twa, 1)
        return self.polar.getRoutageSpeed(self.tw[1], twa)

    def getHDG (self):
        return utils.reduce360 (self.tw[0] - self.twa)

    def BRG (self, wp):
        losso = lossodromica (self.position[0], self.position[1], wp[0], wp[1])
        return losso[1]

    def BRGGPS (self, wp):
        orto = ortodromica (self.position[0], self.position[1], wp[0], wp[1])
        return orto[1]

    def Dist (self, wp):
        losso = lossodromica (self.position[0], self.position[1], wp[0], wp[1])
        return losso[0]

    def CMG (self, rlv):
        scarto=scartorotta (self.getHDG (), rlv)
        return self.getSpeed () * math.cos (scarto)

    def VMGWP (self, wp):
        losso = lossodromica (self.position[0], self.position[1], wp[0], wp[1])
        scarto = scartorotta (self.getHDG(), losso[1])
        return self.getSpeed ()*math.cos(scarto)

    def TWAmaxVMGWP (self, wp):
        rlv = self.BRG (wp)
        return self.twamaxCMG (rlv)

    def TWAmaxCMG (self, rlv):
        twabrg = utils.reduce180 (self.tw[0] - rlv)
        maxtupla = self.polar.getMaxVMGTWA (self.tw[1], math.copysign (twabrg,1))
        return math.copysign (maxtupla[1],twabrg)

    def VMGTWD (self):
        return self.getSpeed () * math.cos (self.twa)


    # Get the apparent wind (direction, speed)
    def getAW (self):
        TWA = math.copysign(self.twa,1)
        TWS = self.tw[1]
        SPEED = self.getSpeed ()
        AWSy = TWS*math.cos(TWA)+SPEED
        AWSx = TWS*math.sin(TWA)
        AWS = (AWSy**2+AWSx**2)**0.5
        AWA = math.pi/2-math.atan2(AWSy,AWSx)
        aw = (AWA, AWS)
        if self.twa<0:
            aw = (-aw[1], aw[0])
        return aw


    def getPolar (self):
        polar = []
        for twa in range(0,185,5):
            twa = math.radians(twa)
            speed = self.polar.getSpeed (self.tw[1], twa)
            if self.twa < 0: #mure a sx
                x = speed * math.sin(twa)
                y = speed * math.cos(twa)
            else: #mure a dx
                x = -speed * math.sin(twa)
                y = speed * math.cos(twa)
            polar.append((x, y))
        return polar
