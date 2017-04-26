# -*- coding: utf-8 -*-
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

import math, struct,os

class gribrecord:
    #parametri definiti su una griglia equidistante di punti
    #in formato Y*10**D=R+X*2**E
    def __init__(self,lenght=0,center="",parametro="",livello="",altezza="",data="",timeunits="",P1=0,P2=0,
                 drtype="",LA1=0.0,LO1=0.0,LA2=0.0,LO2=0.0,flagscanmode="",NI=0,NJ=0,DI=0.0,DJ=0.0,flaguvcomp=""):
        self.lenght=lenght#integer lunghezza del record
        #attributi della Product Definition Section
        self.center=center#stringa centro di emissione del bollettino
        self.parameter=parametro#stringa parametro
        self.level=livello#stringa quota di riferimeno
        self.height=altezza#stringa altezza di riferimento
        self.data=data#stringa data emissione del bollettino nel formato anno.mese.giorno.ora.minuto
        self.timeunits=timeunits#stringa unita' di tempo
        self.P1=P1#integer
        self.P2=P2#integer tempo di validità del record (ex +24ore dall'emissione)
        #attributi della Grid Definition Section
        self.DRType=drtype#integer Data Rappresentation Type atteso 0 per griglia equidistante
        self.LA1=LA1#float latitude of first grid point in gradi.dec [-90.0,90.0]
        self.LO1=LO1#float longitudine of first grid point in gradi.dec ]-180.0,180.0]
        self.flaguvcomp=flaguvcomp#stringa 8 caratteri
        self.LA2=LA2#float latitude of last grid point in gradi.dec
        self.LO2=LO2#float longitudine of last grid point in gradi.dec
        self.flagscanmode=flagscanmode#stringa 8 caratteri
        self.NI=NI#integer Number of points along a latitude circle
        self.NJ=NJ#integer Number of points along a longitude meridian
        self.DI=DI#float the longitudinal direction increment
        self.DJ=DJ#float the latitudinal direction increment
        #attributi della BitMap Data Section
        self.gridbitmap=[]
        #attributi della Binary Data Section
        self.grid=[]
        
    def decodeparameter(self):
        parameter_int=[2,11,31,32,33,34,52,61,71]
        parameter_str=["Pressure MSL","Temperature","Wind Direction","Wind speed","U component","V component",
                       "U.R.","Total Precipitation","Total Cloud Cover"]
        if self.parameter in parameter_int:
            stringa=parameter_str[parameter_int.index(self.parameter)]
        else:
            stringa="parameter nr."+str(self.parameter)
        return stringa
    def decodecenter(self):
        center_int=[0,7,8,9,34,35,59,74,75,80,81,85,98]
        center_str=["WMO","NCEP","NWSTG","US National Service","Tokyo","Tokyo","NOAA Forecast Systems Lab, Boulder",
                    "U.K. Met Office - Bracknell","U.K. Met Office - Bracknell","Rome","Rome",
                    "French Weather Service - Toulouse","European Centre for Medium Range Weather Forecasts"]
        if self.center in center_int:
            stringa=center_str[center_int.index(self.center)]
        else:
            stringa="center nr."+str(self.center)
        return stringa
    def decodedrtype(self):
        Drtype_int=[0,1,2,3,4,5,6]
        Drtype_str=["Lat/Lon grid","Mercator","Gnomonic","Lambert","Gaussian grid","Polar","UTM"]
        if self.DRType in Drtype_int:
            stringa=Drtype_str[Drtype_int.index(self.DRType)]
        else:
            stringa="Data Rappresentation Type nr."+str(self.DRType)
        return stringa
    def decodelevel(self):
        level_int=[1,2,3,4,20,100,103,105,200]
        level_str=["Ground or water surface","Cloud base level","Level of cloud tops",
                   "Level of 0°C isotherm","Isothermal level","Isobarci surface",
                   "Specified altitude above mean sea level","Specified height above ground","Entire atmosphere"]
        if self.level in level_int:
            stringa=level_str[level_int.index(self.level)]
        else:
            stringa="level/layer nr"+str(self.level)
        return stringa
    def decodetimeunits(self):
        units_int=[0,1,2,3,4,5,6,7,10,11,12,254]
        units_str=["minuti","ore","giorni","mesi","anni","decadi","(30anni)","secoli","3ore","6ore","12ore","secondi"]
        if self.timeunits in units_int:
            stringa=units_str[units_int.index(self.timeunits)]
        else:
            stringa="time units nr"+str(self.timeunits)
        return stringa

    def decodeflaguvcomp(self):
        if self.flaguvcomp[4]=="0":
            stringa="easterly/northerly"
        else:
            stringa="DI/DJ"
        return stringa

    def stampa(self):
        testo1="Record emesso il "+self.data+" da "+self.decodecenter()+" valid at +"+str(self.P2)+self.decodetimeunits()+"\n"
        testo2=self.decodeparameter()+" at "+self.decodelevel()+" "+str(self.height) +"\n"
        testo3=("Data Rappresentation Type:"+self.decodedrtype()+" u,v comp:"+self.decodeflaguvcomp()+"\n"+
                " LA1:"+str(self.LA1)+" LO1:"+str(self.LO1)+" LA2:"+str(self.LA2)+" LO2:"+str(self.LO2)+"\n"
                " NI (pti-meridiano):"+str(self.NI)+" NJ (pti-parallelo):"+str(self.NJ)+" DI:"+str(self.DI)+" DJ:"+str(self.DJ)+"\n")
        return testo1+testo2+testo3
        
    def inizializzaij(self):
        if self.flagscanmode[0]=="0":#Points scan in i direction
            i=0
        else:#Points scan in -i direction
            i=self.NI-1
        if self.flagscanmode[1]=="1":#Points scan in j direction
            j=0
        else:#Points scan in -j direction
            j=self.NJ-1
        return i,j

    def incrementaij(self,i,j):
        #incrementa i,j in modo congruente con flagscanmode
        #grid scritta dall'angolo SW all'angolo NE
        #i direction: west to east or left to right
        #j direction (south to north or bottom to top)
        if self.flagscanmode[2]=="0":#Adjacent points in i direction are consecutive
            if self.flagscanmode[0]=="0":#Points scan in +i direction
                i=i+1
                if i==self.NI:
                    i=0
                    if self.flagscanmode[1]=="1":#Points scan in +j direction
                        j=j+1
                    else:#Points scan in -j direction
                        j=j-1
            else:#Points scan in -i direction
                i=i-1
                if i==0:
                    i=self.NI-1
                    if self.flagscanmode[1]=="1":#Points scan in +j direction
                        j=j+1
                    else:#Points scan in -j direction
                        j=j-1
                

        if self.flagscanmode[2]=="1":#Adjacent points in j direction are consecutive
            if self.flagscanmode[1]=="1":#j direction
                j=j+1
                if j==self.NJ:
                    j=0
                    if self.flagscanmode[0]=="0":#Points scan in +i direction
                        i=i+1
                    else:#-i direction
                        i=i-1
            else:#-j direction
                j=j-1
                if j==0:
                    j=self.NJ-1
                    if self.flagscanmode[0]=="0":#Points scan in +i direction
                        i=i+1
                    else:#-i direction
                        i=i-1
        return i,j

class Grib:
    def __init__(self,nomefile=""):
        self.records=[]#lista di record
        self.index={}#dizionario chiavi[P2] valori[[record.parameter],[indicerecord]]
        self.nomefile=nomefile
        file=open(self.nomefile,"rb")
        Size=int(os.path.getsize(self.nomefile))
        n=0
        while n<Size:
            record=self.leggirecord(file)
            if record<>"":
                self.records.append(record)
                n=n+record.lenght
                print record.stampa()
                #carico l'indice
                i=len(self.records)-1
                if not self.index.has_key(record.P2):
                    self.index[record.P2]=[[record.parameter],[i]]
                else:
                    self.index[record.P2][0].append(record.parameter)
                    self.index[record.P2][1].append(i)
            else:
                print "Errore nella lettura del file"
                n=Size
        file.close()

    def leggirecord(self,file):
        record=gribrecord()
        controllo=True
        #sez0
        data=file.read(8)
        tupla=struct.unpack("4s1B1B1B1B",data)
        record.lenght=tupla[1]*256*256+tupla[2]*256+tupla[3]
        if tupla[0]<>"GRIB" or tupla[4]<>1:controllo=False    
        #sez1 PRODUCT DEFINITION
        data=file.read(3)#bit 1-3
        tupla=struct.unpack("1B1B1B",data)
        lenghtsez1=tupla[0]*256*256+tupla[1]*256+tupla[2]
        file.read(1)#bit 4
        data=file.read(1)#bit 5
        record.center=struct.unpack("1B",data)[0]
        file.read(1)#bit 6
        file.read(1)#bit 7
        data=file.read(1)#bit 8
        flagoptionalsez=str8bit(data)#flag GDS BMS yes/not
        data=file.read(1)#bit 9
        record.parameter=struct.unpack("1B",data)[0]
        data=file.read(1)#bit 10
        record.level=struct.unpack("1B",data)[0]
        data=file.read(2)#bit 11-12
        tupla=struct.unpack("1B1B",data)
        record.height=0
        if record.level in [20,100,103,105,107,109,111,113,115,117,119,125,160]:
            record.height=tupla[0]*256+tupla[1]
        if record.level in [101,104,106,108,110,112,114,116,120,121,128,141]:
            record.height=(tupla[0],tupla[1])
        data=file.read(1)#bit 13
        anno=struct.unpack("1B",data)[0]
        data=file.read(1)#bit 14
        mese=struct.unpack("1B",data)[0]
        data=file.read(1)#bit 15
        giorno=struct.unpack("1B",data)[0]
        data=file.read(1)#bit 16
        ora=struct.unpack("1B",data)[0]
        data=file.read(1)#bit 17
        minuto=struct.unpack("1B",data)[0]
        record.data=str(anno+2000)+"."+str(mese)+"."+str(giorno)+" ore "+str(ora)+":"+str(minuto)
        data=file.read(1)#bit 18
        record.timeunits=struct.unpack("1B",data)[0]
        data=file.read(1)#bit 19
        record.P1=struct.unpack("1B",data)[0]#atteso 0
        data=file.read(1)#bit 20
        record.P2=struct.unpack("1B",data)[0]#! tempo di riferimento
        file.read(1)#bit 21
        file.read(2)#bit 22-23
        file.read(1)#bit 24
        file.read(1)#bit 25
        file.read(1)#bit 26
        data=file.read(2)#bit 27-28
        tupla=struct.unpack("1B1B",data)
        if tupla[0]>=128:
            D=(tupla[0]-128)*256+tupla[1]
            D=-D
        else:
            D=tupla[0]*256+tupla[1]
        record.D=D
        file.read(lenghtsez1-28)
        #sez2 GRID DEFINITION optional
        lenghtsez2=0
        if flagoptionalsez[0]=="1":
            data=file.read(3)#bit 1-3
            tupla=struct.unpack("1B1B1B",data)
            lenghtsez2=tupla[0]*256*256+tupla[1]*256+tupla[2]
            file.read(1)#bit 4
            file.read(1)#bit 5
            data=file.read(1)#bit 6        
            record.DRType=struct.unpack("1B",data)[0]
            if record.DRType<>0:
                file.read(lenght-lenghtsez1-lenghtsez2-6)
            else:#griglia equidistante bit 7-32
                data=file.read(2)#bit 7-8
                tupla=struct.unpack("1B1B",data)
                record.NI=tupla[0]*256+tupla[1]#npti sul parallelo
                data=file.read(2)#bit 9-10
                tupla=struct.unpack("1B1B",data)
                record.NJ=tupla[0]*256+tupla[1]#npti sul meridiano
                data=file.read(3)#bit 11-13
                tupla=struct.unpack("1B1B1B",data)
                if tupla[0]>=128:#sud
                    LA1=(tupla[0]-128)*256*256+tupla[1]*256+tupla[2]
                    LA1=-LA1
                else:
                    LA1=tupla[0]*256*256+tupla[1]*256+tupla[2]
                record.LA1=LA1*10**-3#lat. primo punto in millesimi di grado

                data=file.read(3)#bit 14-16
                tupla=struct.unpack("1B1B1B",data)
                if tupla[0]>=128:#west
                    LO1=(tupla[0]-128)*256*256+tupla[1]*256+tupla[2]        
                    LO1=-LO1
                else:
                    LO1=tupla[0]*256*256+tupla[1]*256+tupla[2]
                LO1=LO1*10**-3#lon. primo punto in millesimi di grado
                if LO1>180:LO1=360-LO1
                if LO1<=-180:LO1=LO1+360
                record.LO1=LO1

                data=file.read(1)#bit 17
                record.flaguvcomp=str8bit(data)#stringa di 8bit

                data=file.read(3)#bit 18-20
                tupla=struct.unpack("1B1B1B",data)
                if tupla[0]>=128:#sud
                    LA2=(tupla[0]-128)*256*256+tupla[1]*256+tupla[2]
                    LA2=-LA2
                else:
                    LA2=tupla[0]*256*256+tupla[1]*256+tupla[2]
                record.LA2=LA2*10**-3#lat. ultimo punto in millesimi di grado

                data=file.read(3)#bit 21-23
                tupla=struct.unpack("1B1B1B",data)
                if tupla[0]>=128:#west
                    LO2=(tupla[0]-128)*256*256+tupla[1]*256+tupla[2]
                    LO2=-LO2
                else:
                    LO2=tupla[0]*256*256+tupla[1]*256+tupla[2]
                LO2=LO2*10**-3#lon. ultimo punto in millesimi di grado
                if LO2>180:LO2=360-LO2
                if LO2<=-180:LO2=LO2+360
                record.LO2=LO2

                data=file.read(2)#bit 24-25 DI
                '''
                tupla=struct.unpack("1B1B",data)
                if tupla[0]>=128:#controllo bit1
                    DI=(tupla[0]-128)*256+tupla[1]
                    DI=-DI
                else:
                    DI=tupla[0]*256+tupla[1]
                record.DI=DI*10**-3#DI in millesimi di grado
                '''
                #record.DI=(record.LA1-record.LA2)*1.0/(record.NI-1)
                record.DI=(record.LO1-record.LO2)*1.0/(record.NI-1)
                data=file.read(2)#bit 26-27 DJ
                '''
                tupla=struct.unpack("1B1B",data)
                if tupla[0]>=128:#controllo bit1
                    DJ=(tupla[0]-128)*256+tupla[1]
                    DJ=-DJ
                else:
                    DJ=tupla[0]*256+tupla[1]
                record.DJ=DJ*10**-3#DJ in millesimi di grado
                '''
                #record.DJ=(record.LO1-record.LO2)*1.0/(record.NJ-1)
                record.DJ=(record.LA1-record.LA2)*1.0/(record.NJ-1)

                data=file.read(1)#bit 28
                record.flagscanmode=str8bit(data)#stringa di 8bit
                
                file.read(4)#bit 29-32 fine sezione per griglia equidistante
        #sez3 BIT-MAP Section optional
        lenghtsez3=0
        if flagoptionalsez[1]=="1":
            data=file.read(3)#bit 1-3
            tupla=struct.unpack("1B1B1B",data)
            lenghtsez3=tupla[0]*256*256+tupla[1]*256+tupla[2]
            data=file.read(1)#bit 4
            unused=struct.unpack("1B",data)[0]
            data=file.read(2)#bit 5,6
            tupla=struct.unpack("1B1B",data)
            tablereferenze=tupla[0]*256+tupla[1]
            record.grid=record.NJ*[range(0,record.NI)]
            tuplaij=record.inizializzaij()
            i=tuplaij[0]
            j=tuplaij[1]
            for k in range(7,lenghtsez3+1):#bit 7-lenghtsez3
                data=file.read(1)
                record.grid[j][i]=struct.unpack("1B",data)[0]
                #incremento i,j in accordo a scanmode
                tuplaij=record.incrementaij(i,j)
                i=tuplaij[0]
                j=tuplaij[1]
            else:
                file.read(lenghtsez3-3)
        #sez4 BINARY DATA SECTION
        data=file.read(3)#bit 1-3
        tupla=struct.unpack("1B1B1B",data)
        lenghtsez4=tupla[0]*256*256+tupla[1]*256+tupla[2]
        data=file.read(1)#bit 4 Flag (see Code table 11) (first 4 bits). Number of unused bits at end of Section 4 (last 4 bits)
        flagdata=str8bit(data)
        unused=int(flagdata[4:],2)
        data=file.read(2)#bit 5-6 Scale factor (E)
        tupla=struct.unpack("1B1B",data)
        if tupla[0]>128:
            E=(tupla[0]-128)*256+tupla[1]
            E=-E
        else:
            E=tupla[0]*256+tupla[1]
        data=file.read(4)#bit 7-10 Reference value (minimum of packed values)
        R=floatpoint(data)
        data=file.read(1)#bit 11 Number of bits containing each packed value
        nbit=struct.unpack("1B",data)[0]
        if flagdata[0]=="0" and flagdata[1]=="0" and flagdata[2]=="0" and flagdata[3]=="0":
            record.grid=[]
            for i in range(0,record.NJ):
                record.grid.append(range(0,record.NI))
            bufferstr=""
            tuplaij=record.inizializzaij()
            i=tuplaij[0]
            j=tuplaij[1]
            octectreaded=11
            for N in range(0,record.NI*record.NJ):
                #leggiamo nbit
                n=(nbit-len(bufferstr))/8+1
                octectreaded=octectreaded+n
                for k in range(0,n):
                    data=file.read(1)
                    bufferstr=bufferstr+str8bit(data)
                Xstr=bufferstr[0:nbit]
                X=int(Xstr,2)
                bufferstr=bufferstr[nbit:]
                #
                record.grid[j][i]=(R+X*2**E)*10**-D
                #incremento i,j in accordo a scanmode
                tuplaij=record.incrementaij(i,j)
                i=tuplaij[0]
                j=tuplaij[1]
            file.read(lenghtsez4-octectreaded)
        else:
            file.read(lenghtsez4-11)
        #sez5
        data=file.read(4)
        tupla=struct.unpack("4s",data)
        if tupla[0]<>"7777":controllo==False
        if controllo:
            return record
        else:
            return ""    

    def find(self,p2,parameter):
        #rende il record che rispetta record.P2==t and record.parameter==parameter
        try:
            values=self.index[p2]#matrice [parametri][indici]
            indice=values[1][values[0].index(parameter)]
            record=self.records[indice]
        except:
            record=""
        return record 

    def calcola(self,parameter,t,lat,lon):
        #rende il valore di parameter per P2=t nel punto lat, lon, per t,lat,lon inclusi nel grib
        #altrimento rende la stringa vuota ""
        valore=""
        keys=self.index.keys()
        keys.sort()
        if t>=keys[0] and t<=keys[-1]:
            indice1=0#massimo p2 minore di t
            indice2=len(keys)-1#minimo p2 maggiore di t
            for n in range(0,len(keys)):
                if t>keys[n]:
                    indice1=n
            for n in range(len(keys)-1,-1,-1):
                if t<keys[n]:
                    indice2=n
            p21=keys[indice1]
            p22=keys[indice2]
            record1=self.find(p21,parameter)
            record2=self.find(p22,parameter)
            if record1<>"" and record2<>"":
                valore1=""
                valore2=""
                #record1
                minlat=min(record1.LA1,record1.LA2)
                minlon=min(record1.LO1,record1.LO2)
                maxlat=max(record1.LA1,record1.LA2)
                maxlon=max(record1.LO1,record1.LO2)
                if (lat>=minlat and lat<maxlat) and (lon>=minlon and lon<maxlon):
                    i=(lon-minlon)/(maxlon-minlon)*record1.NI
                    j=(lat-minlat)/(maxlat-minlat)*record1.NJ
                    di=i-int(i)#parte decimale
                    dj=j-int(j)#parte decimale
                    riga=int(j)
                    colonna=int(i)
                    #interpolazione primo ordine
                    valore11=record1.grid[riga][colonna]
                    valore12=record1.grid[riga][colonna+1]
                    valore13=record1.grid[riga+1][colonna]                    
                    valore1=valore11+(valore12-valore11)+dj*1.0/record1.DJ+(valore13-valore11)*di*1.0/record1.DI
                    #per u e v
                    if record1.flaguvcomp=="1":#componenti concordi con la griglia
                        if parameter==34:valore1=valore1*math.copysign(1,DJ)#rese northerly
                        if parameter==33:valore1=valore1*math.copysign(1,DI)#rese easterly
                #record2    
                minlat=min(record1.LA1,record1.LA2)
                minlon=min(record1.LO1,record1.LO2)
                maxlat=max(record1.LA1,record1.LA2)
                maxlon=max(record1.LO1,record1.LO2)
                if (lat>=minlat and lat<maxlat) and (lon>=minlon and lon<maxlon):
                    i=(lon-minlon)/(maxlon-minlon)*record2.NI
                    j=(lat-minlat)/(maxlat-minlat)*record2.NJ
                    di=i-int(i)#parte decimale
                    dj=j-int(j)#parte decimale
                    riga=int(j)
                    colonna=int(i)
                    #interpolazione primo ordine
                    valore21=record2.grid[riga][colonna]
                    valore22=record2.grid[riga][colonna+1]
                    valore23=record1.grid[riga+1][colonna]
                    valore2=valore21+(valore22-valore21)+dj*1.0/record2.DJ+(valore23-valore21)*di*1.0/record2.DI        
                    #per u e v
                    if record2.flaguvcomp=="1":#componenti concordi con la griglia
                        if parameter==34:valore2=valore2*math.copysign(1,DJ)#rese northerly
                        if parameter==33:valore2=valore2*math.copysign(1,DI)#rese easterly
                    
                if valore1<>"" and valore2<>"":
                    valore=valore1+(valore2-valore1)*(t-p21)*1.0/(p22-p21)
        return valore

    def vento(self,t,lat,lon):
        #ritorna (tws,twd) per t,lat e lon inclusi nel file grib
        #ritorna (0,0) per t,lat e lon non inclusi
        tws=0
        twd=0
        tws=self.calcola(32,t,lat,lon)
        twd=self.calcola(31,t,lat,lon)
        if tws=="" and twd=="":
            tws=0
            twd=0
            u=self.calcola(33,t,lat,lon)
            v=self.calcola(34,t,lat,lon)
            if u!="" and v!="":
                tws=(u**2+v**2)**0.5
                twd=math.atan2(u,v)+math.pi
                twd=riduci360(twd)
        return (tws,math.degrees(twd))

def riduci360(angolo):
    if angolo>2*math.pi:
        angolo=angolo-2*math.pi
    if angolo<0:
        angolo=angolo+2*math.pi
    return angolo

def str8bit(data):
    #data 1 octect
    flag=struct.unpack("1B",data)[0]#integer
    flag=bin(flag)[2:]#stringa di bit
    if len(flag)<8:
        flag=(8-len(flag))*"0"+flag
    return flag
def floatpoint(data):
    #data 4 octects
    tupla=struct.unpack("1B1B1B1B",data)
    if tupla[0]>128:
        A=(tupla[0]-128)
        s=-1
    else:
        A=tupla[0]
        s=1
    B=tupla[1]*256*256+tupla[2]*256+tupla[3]
    return s*(2**-24)*B*(16**(A-64))

def test():
    nomefile='GRIBB/20130311_120424_.grb'
    MioGrib=Grib(nomefile)
    tempi=MioGrib.index.keys()
    tempi.sort()
    record=MioGrib.find(36,2)
    print tempi
    print "indice dei [parametri],[record] per t=36", MioGrib.index[36]
    print "record t=36, parametro=2", record.stampa()
    for riga in range(0,record.NJ):
        for colonna in range(0,record.NI):
            print riga, colonna, record.grid[riga][colonna]
    print "u",MioGrib.calcola(33,36,39,4)
    print "v",MioGrib.calcola(34,36,39,4)
    print "u",MioGrib.calcola(33,36,42,4)
    print "v",MioGrib.calcola(34,36,42,4)
    print "tws,twd in 39N4E +0ore", MioGrib.vento(0,39,4)
    print "tws,twd in 42N4E +0ore", MioGrib.vento(0,42,4)
    print "tws,twd in 39N4E +12ore", MioGrib.vento(12,39,4)
    print "tws,twd in 42N4E +12ore", MioGrib.vento(12,42,4)
    print "tws,twd in 39N4E +80ore", MioGrib.vento(80,39,4)
    print "tws,twd in 39N4E +200ore", MioGrib.vento(200,39,4)
    print "tws,twd in 39N15E +24ore", MioGrib.vento(24,39,15)

#Main------------------------------------------------------------------
#test()

