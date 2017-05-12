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

import math

EARTH_RADIUS=60.0*360/(2*math.pi)#nm

def routagePointDistance (latA,lonA,Distanza,Rotta):
	#non funziona in prossimita' dei poli
	#dove può risultare latC>90, log(tan(latC/...))=log(<0)   (*)
	a=Distanza*1.0/EARTH_RADIUS
	latB=latA+a*math.cos(Rotta)
	if math.copysign(latA-latB,1)<=math.radians(0.1/3600.0):
		q=math.cos(latA)
	else:
		Df=math.log(math.tan(latB/2+math.pi/4)/math.tan(latA/2+math.pi/4),math.e)#(*)
		q=(latB-latA)/Df
	lonB=lonA-a*math.sin(Rotta)/q
	return latB,lonB

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