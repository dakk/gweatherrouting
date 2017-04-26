#Copyright (C) 2012 Riccardo Apolloni
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

import math, struct

#Convenzioni
#lat>0 Nord, lon>0 Est
class Carta:
    def __init__(self,nomefile='GSHH/gshhs_l.b',
                 boxcarta=[(math.radians(90),math.radians(-90)),(math.radians(180),math.radians(-180))]):
        #nomefile stringa
        #boxcarta [(latmax,latmin),(lonmax,lonmin)]
        self.poligoni=[]
        file=open(nomefile,"rb")
        try:
            header=file.read(44)
            while header!="":
                header=struct.unpack(">11i",header)
                idnum=header[0]
                npti=header[1]
                flag=header[2]
                flag_str=str32bit(flag)
                poligono=[]
                if int(flag_str[24:32],2)==1:#livello 1 shoreline
                    for n in range(0,npti):
                        pto=file.read(8)
                        pto=struct.unpack(">2i",pto)
                        lon=math.radians(pto[0]*10**-6)
                        lat=math.radians(pto[1]*10**-6)
                        if lon>math.pi: lon=lon-2*math.pi
                        if lat<boxcarta[0][0] and lat>boxcarta[0][1] and lon<boxcarta[1][0] and lon>boxcarta[1][1]:
                            poligono.append((lat,lon))
                            
                        else:#spezzo il poligono e ne inizio uno nuovo
                            if len(poligono)>0:self.poligoni.append(poligono)
                            poligono=[]
                    if len(poligono)>0:
                        self.poligoni.append(poligono)
                else:
                    file.read(8*npti)
                header=file.read(44)
        finally:
            file.close()

def str32bit(flag):
    #flag 1 integer vs stringa 8 bit
    flag=bin(flag)[2:]#stringa di bit
    if len(flag)<32:
        flag=(32-len(flag))*"0"+flag
    return flag
