# -*- coding: utf-8 -*-
# Copyright (C) 2017 Davide Gessa
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

from .polar import Polar
from .beizer import Beizer

logger = logging.getLogger ('regattasim')

def reduce360 (alfa):
    n=int(alfa*0.5/math.pi)
    n=math.copysign(n,1)
    if alfa>2.0*math.pi:
        alfa=alfa-n*2.0*math.pi
    if alfa<0:
        alfa=(n+1)*2.0*math.pi+alfa
    if alfa>2.0*math.pi or alfa<0:
        return 0.0
    return alfa

def reduce180 (alfa):
    if alfa>math.pi:
        alfa=alfa-2*math.pi
    if alfa<-math.pi:
        alfa=2*math.pi+alfa
    if alfa>math.pi or alfa<-math.pi:
        return 0.0
    return alfa

class Boat:
    def __init__ (self, model):
        self.position = (0.0, 0.0)
        self.log = 0.0
        self.twa = 0.0
        self.tw = (0.0,0.0)
        self.model = model

        this_dir, this_fn = os.path.split (__file__)
        self.polar = Polar (this_dir + '/../data/boats/' + model + '/polar.pol')

    def setPosition (self, lat, lon):
        self.position = (lat, lon)

    def getPosition (self):
        return self.position

    # Orza di 1 grado
    def luffUp (self):
        if self.twa-math.radians(1)>0.0 and self.twa<=math.pi:#mure a dx
            self.twa=self.twa-math.radians(1)
        if self.twa+math.radians(1)<0.0 and self.twa>=-math.pi:#mure a sx
            self.twa=self.twa+math.radians(1)

    # Poggia di 1 grado
    def bearAway (self):
        if self.twa>=0 and self.twa<math.pi:#mure a dx
            self.twa=self.twa+math.radians(1)
            if self.twa>math.pi:self.twa=math.pi
        if self.twa<=0 and self.twa>-math.pi:#mure a sx
            self.twa=self.twa-math.radians(1)
            if self.twa<-math.pi:self.twa=-math.pi

    # Cambio di mura
    def changeTack (self):
        self.twa = -self.twa

    def Muovi (self,dt):
        v=self.getSpeed ()
        pos = puntodistanterotta(self.position[0],self.position[1],v*dt,self.getHDG())
        self.position=pos
        self.Log=self.Log+v*dt

    def MuoviRoutage(self,dt):
        v=self.getRoutageSpeed()
        pos=puntodistanterotta(self.position[0],self.position[1],v*dt,self.getHDG())
        self.position=pos
        self.Log=self.Log+v*dt
        
    def getSpeed (self):
        twa=math.copysign(self.twa,1)
        return self.polar.getSpeed (self.tw[1],twa)

    def getRoutageSpeed(self):
        twa=math.copysign(self.twa,1)
        return self.polar.getRoutageSpeed(self.tw[1],twa)

    def getHDG(self):
        return reduce360 (self.tw[0]-self.twa)

    def BRG (self,wp):
        losso=lossodromica(self.position[0],self.position[1],wp[0],wp[1])
        return losso[1]

    def BRGGPS (self,wp):
        orto=ortodromica(self.position[0],self.position[1],wp[0],wp[1])
        return orto[1]

    def Dist (self,wp):
        losso=lossodromica(self.position[0],self.position[1],wp[0],wp[1])
        return losso[0]

    def CMG (self,rlv):
        scarto=scartorotta(self.getHDG(),rlv)
        return self.getSpeed ()*math.cos(scarto)

    def VMGWP (self,wp):
        losso=lossodromica(self.position[0],self.position[1],wp[0],wp[1])
        scarto=scartorotta(self.getHDG(),losso[1])
        return self.getSpeed ()*math.cos(scarto)

    def TWAmaxVMGWP (self,wp):
        rlv=self.BRG(wp)
        return self.twamaxCMG(rlv)

    def TWAmaxCMG (self,rlv):
        twabrg=reduce180(self.tw[0]-rlv)
        maxtupla=self.polar.getMaxVMGTWA (self.tw[1],math.copysign(twabrg,1))
        return math.copysign(maxtupla[1],twabrg)

    def VMGTWD (self):
        return self.getSpeed ()*math.cos(self.twa)

    def AW (self):
        TWA=math.copysign(self.twa,1)
        TWS=self.tw[1]
        SPEED=self.getSpeed ()
        AWSy=TWS*math.cos(TWA)+SPEED
        AWSx=TWS*math.sin(TWA)
        AWS=(AWSy**2+AWSx**2)**0.5
        AWA=math.pi/2-math.atan2(AWSy,AWSx)
        aw=(AWS,AWA)
        if self.twa<0:
            aw=(aw[0],-aw[1])
        return aw


    def getPolar (self):
        polare=[]
        for twa in range(0,185,5):
            twa=math.radians(twa)
            speed=self.polar.getSpeed (self.tw[1],twa)
            if self.twa<0:#mure a sx
                x=speed*math.sin(twa)
                y=speed*math.cos(twa)
            else:#mure a dx
                x=-speed*math.sin(twa)
                y=speed*math.cos(twa)
            polare.append((x,y))
        return polare

    def getJib (self):
        fiocco=[]
        aw=self.AW()
        awa=aw[1]
        if math.copysign(awa,1)>math.radians(60):
            l=125.0
            zero=135
        else:
            l=90
            zero=125
        #if math.copysign(awa,1)<math.radians(25):
        if self.getSpeed ()<=0:
            fiocco=[(0,125.0),(0,35.0)]
        else:
            if awa>0:
                r=l/awa
                cx=+r*math.cos(awa)
                cy=zero-r*math.sin(awa)
                for angolo in range(0,int(math.degrees(awa))):
                    angolo=math.radians(angolo)
                    x=cx-r*math.cos(angolo)
                    y=cy+r*math.sin(angolo)
                    fiocco.append((x,y))
            else:
                awa=math.copysign(awa,1)
                r=l/awa
                cx=-r*math.cos(awa)
                cy=zero-r*math.sin(awa)
                for angolo in range(0,int(math.degrees(awa))):
                    angolo=math.radians(angolo)
                    x=cx+r*math.cos(angolo)
                    y=cy+r*math.sin(angolo)
                    fiocco.append((x,y))
        return fiocco

    def getMainsail (self):
        aw = self.AW ()
        awa = aw[1]
        randa = []
        #if math.copysign(awa,1)<math.radians(25):
        if self.getSpeed () <= 0:
            randa=[(0,35.0),(0,-75.0)]
        else:
            if awa>math.pi/2:
                awa=math.pi/2
            if awa<-math.pi/2:
                awa=-math.pi/2
            segno=awa/math.copysign(awa,1)
            bezier=Beizer([(0,35),
                           (-40*math.sin(awa+segno*math.radians(30)),35-40*math.cos(awa+segno*math.radians(30))),
                           (-110*math.sin(awa-segno*math.radians(25)),35-110*math.cos(awa-segno*math.radians(25)))])
            for i in range(0,11):
                i=i*0.1
                randa.append(bezier.calcolavalore(i)) 
        return randa