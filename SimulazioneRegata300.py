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

Gegraphy Data by
Global Self-consistent Hierarchical High-resolution Geography
Version 2.2.2 January 1, 2013

GSHHG is developed and maintained by
Paul Wessel, SOEST, University of Hawai'i, Honolulu, HI.
Walter H. F. Smith, NOAA Geosciences Lab, National Ocean Service, Silver Spring, MD.

more information on http://www.soest.hawaii.edu/pwessel/gshhg/
'''

import math,time,random
from ModuloBarca01 import *
from ModuloGrib01 import *
from ModuloCartografia import *
from ModuloNav import *
from Tkinter import *

#COSTANTI
FILEPOLARE='POL/PolareMini.pol'
FILEGRIB='GRIBB/20130311_120424_.grb'
FILECHART='GSHH/gshhs_l.b'#'GSHH/gshhs_i.b'#'GSHH/gshhs_f.b'
BOXCHART=[(math.radians(45),math.radians(0)),(math.radians(20),math.radians(-70))]#[(latmax,latmin),(lonmax,lonmin)]
#valori per Display 1024x500
MIOFONT="verdana 7"
TrackHeight=5
TrackWidth=50
InfoHeight=3
InfoWidth=TrackWidth-4
GraficoSxSize=214#
GraficoDxHeight=490
GraficoDxWidth=650
BGCOLOR="lightyellow"
infocolor="#FFFF66"
'''
#valori per Dispaly 1280x800
MIOFONT="verdana 10"
TrackHeight=14
TrackWidth=60
InfoHeight=6
InfoWidth=TrackWidth-4
GraficoSxSize=270
GraficoDxHeight=700
GraficoDxWidth=850
BGCOLOR="lightyellow"
infocolor="#FFFF66"
'''
#waypoints
LanzaroteLat=math.radians(29)
LanzaroteLon=math.radians(14)
GuadalupeLat=math.radians(16)
GuadalupeLon=math.radians(61)
LigureWestLon=-math.radians(5)
LigureEstLon=-math.radians(10)
LipariWestLon=-math.radians(10)
LipariEstLon=-math.radians(15)
GenovaLat=math.radians(44+24.0/60)
GenovaLon=-math.radians(8+57.0/60)
GiragliaLat=math.radians(43+1.0/60)
GiragliaLon=-math.radians(9+25.0/60)
PianosaLat=math.radians(42+33.0/60)
PianosaLon=-math.radians(10+00.0/60)
BBonifacioLat=math.radians(41+19.0/60)
BBonifacioLon=-math.radians(9+10.0/60)
CCominoLat=math.radians(40+31.0/60)
CCominoLon=-math.radians(9+51.0/60)
PorquerollesLat=math.radians(43+0.0/60)
PorquerollesLon=-math.radians(6+12.0/60)
PalmaLat=math.radians(39+17.0/60)
PalmaLon=-math.radians(3+27.0/60)
TouloseLat=math.radians(43+36.0/60)
TouloseLon=-math.radians(1+27.0/60)
ArgentarioLat=math.radians(42+21.0/60)
ArgentarioLon=-math.radians(11+9.0/60)
PonzaLat=math.radians(40.0+52.0/60.0)
PonzaLon=-math.radians(13.0+0.0/60.0)
UsticaLat=math.radians(38.0+43.0/60.0)
UsticaLon=-math.radians(13.0+10.0/60.0)
CapriLat=math.radians(40.0+31.0/60.0)
CapriLon=-math.radians(14.0+10.0/60.0)
IschiaLat=math.radians(42.0+42.0/60.0)
IschiaLon=-math.radians(13.0+50.0/60.0)
CapoPalinuroLat=math.radians(40.0+0.0/60)
CapoPalinuroLon=-math.radians(15.0+15.0/60)
CapoFinisterreLat=math.radians(43.0+0.0/60)
CapoFinisterreLon=math.radians(9.0+0.0/60)
HortaLat=math.radians(33.0+0.0/60)
HortaLon=math.radians(16.0+0.0/60)
CamargueLat=math.radians(43.0+23.0/60)
CamargueLon=-math.radians(4.0+32.0/60)
AnnabaLat=math.radians(37.0+00.0/60)
AnnabaLon=-math.radians(7.0+46.0/60)

#OGGETTI
#MASCHERA TKinter-------------------------------
class FinestraMain:
    def __init__(self,master):
        #Proprietà
        self.Partenza=()#tupla in formato (lat,lon)
        self.Arrivo=()
        self.Course=()#tupla in formato (dist,rotta)
        self.T=0.0#ore decimali
        self.Dt=0#Dt veriabile in funzione della lunghezza del percorso
        self.OrigineIsocrone=()#tupla in formato (lat,lon)
        self.Esempio=1
        self.MaVie=Barca(filepolare=FILEPOLARE)
        self.Isocrone=[]#array di isocrone
        self.GribMeteo=""
        #self.GribMeteo=Grib(FILEGRIB)
        self.Cartografia=Carta(FILECHART,BOXCHART)
        self.mode="wind"#"compass","gps","vmg"
        self.run=False
        #self.maxcmgutility=False
        #self.brgutility=False
        self.isocronamodo=False
        self.Controllo=False#controlla il modo di reazione ai tasti orza, puggia, ruota
        self.rafficautility=False
        self.RitardiDiFase=[]#vettore degli sfasamenti delle 2 onde componenti la raffica di vento
        self.FattoreDiScala=1.0#calcolato in disegnafincature
        self.q=1#rapporto lat/lon della finestra grafica, definito in disegnafincature
        self.Bbox=()#tupla in formato ((latNW,lonNW),(latSE,lonSE)) cordinate dell'angolo NW e SE del bbox del percorso
        self.TWA_strvar=StringVar()
        self.TWD_strvar=StringVar()
        self.TWS_strvar=StringVar()
        self.VMGTWD_strvar=StringVar()
        self.HDG_strvar=StringVar()
        self.Speed_strvar=StringVar()
        self.Log_strvar=StringVar()
        self.BRG_strvar=StringVar()
        self.Dist_strvar=StringVar()
        self.VMGBRG_strvar=StringVar()
        self.XCourse_strvar=StringVar()
        self.YCourse_strvar=StringVar()
        self.VMGCourse_strvar=StringVar()
        self.Lat_strvar=StringVar()
        self.Lon_strvar=StringVar()
        self.T_strvar=StringVar()
        self.bottoneplay_strvar=StringVar()
        self.bottonemaxcmg_strvar=StringVar()
        self.raffica_strvar=StringVar()
        self.bottonebrg_strvar=StringVar()
        self.bottoneisocrona_strvar=StringVar()
        
        #FRAME
        FrameA=Frame(master,bg=BGCOLOR)
        FrameA.pack(side=LEFT,fill=Y)
        FrameB=Frame(master,bg=BGCOLOR)
        FrameB.pack(side=LEFT,fill=Y)
        FrameC=Frame(master,bg=BGCOLOR)
        FrameC.pack(side=LEFT,fill=BOTH,expand=1)
        FrameA0=Frame(FrameA,bg=BGCOLOR,bd=2,relief="groove")
        FrameA0.pack(side=TOP,fill=X)
        FrameA1A8=Frame(FrameA,bg=BGCOLOR,bd=2,relief="groove")
        FrameA1A8.pack(side=TOP,fill=X)
        FrameA1=Frame(FrameA1A8,bg=BGCOLOR,bd=2)
        FrameA1.pack(side=TOP,fill=X)
        FrameA2=Frame(FrameA1A8,bg=BGCOLOR)
        FrameA2.pack(side=TOP,fill=X)
        FrameA3=Frame(FrameA1A8,bg=BGCOLOR)
        FrameA3.pack(side=TOP,fill=X)
        FrameA4=Frame(FrameA1A8,bg=BGCOLOR)
        FrameA4.pack(side=TOP,fill=X)
        FrameA5=Frame(FrameA1A8,bg=BGCOLOR)
        FrameA5.pack(side=TOP,fill=X)
        FrameA6=Frame(FrameA1A8,bg=BGCOLOR)
        FrameA6.pack(side=TOP,fill=X)
        FrameA7=Frame(FrameA1A8,bg=BGCOLOR)
        FrameA7.pack(side=TOP,fill=X)
        FrameA8=Frame(FrameA1A8,bg=BGCOLOR)
        FrameA8.pack(side=TOP,fill=X)
        FrameA9=Frame(FrameA,bg=BGCOLOR,bd=2,relief="groove")
        FrameA9.pack(side=TOP,fill=X)
        FrameA10=Frame(FrameA,bg=BGCOLOR,bd=2,relief="groove")
        FrameA10.pack(side=TOP,fill=X)
        FrameA11=Frame(FrameA,bg=BGCOLOR)
        FrameA11.pack(side=BOTTOM,fill=X)
        FrameB1=Frame(FrameB,bg=BGCOLOR,width=GraficoDxWidth)
        FrameB1.pack(side=TOP,fill=X)
        FrameB2=Frame(FrameB,bg=BGCOLOR,width=GraficoDxWidth)
        FrameB2.pack(side=BOTTOM,fill=X)
        #FrameA
        self.Info=Text(FrameA0,height=InfoHeight,width=InfoWidth,font=MIOFONT,bg=BGCOLOR,relief="flat",
                       wrap=WORD)
        self.Info.pack(side=LEFT)
        self.Info.config(state=DISABLED)
        scrollbar=Scrollbar(FrameA0,orient=VERTICAL,relief="flat")
        self.Esempiolistbox=Listbox(FrameA0,width=3,height=InfoHeight,font=MIOFONT,bg=BGCOLOR,relief="flat",
                                    selectmode=SINGLE,yscrollcommand=scrollbar.set)
        self.Esempiolistbox.bind("<Double-Button-1>", self.CambiaEsempio)
        self.Esempiolistbox.pack(side=LEFT)
        for i in range (1,28):
            self.Esempiolistbox.insert(END,str(i))
        self.Esempiolistbox.selection_set(first=0)
        scrollbar.config(command=self.Esempiolistbox.yview)
        scrollbar.pack(side=LEFT,fill=Y)
        Label(FrameA1,text="TWD",width=8,anchor="e",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        Label(FrameA1,textvariable=self.TWD_strvar,bg=infocolor,width=8,anchor="w",font=MIOFONT).pack(side=LEFT)
        Label(FrameA1,text="TWS",width=8,anchor="e",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        Label(FrameA1,textvariable=self.TWS_strvar,bg=infocolor,width=8,anchor="w",font=MIOFONT).pack(side=LEFT)
        Label(FrameA1,text="Time",width=8,anchor="e",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        Label(FrameA1,textvariable=self.T_strvar,width=8,anchor="w",bg=infocolor,font=MIOFONT).pack(side=LEFT)
        Label(FrameA2,text="TWA",width=8,anchor="e",bg=BGCOLOR, font=MIOFONT).pack(side=LEFT)
        self.LabelTWA=Label(FrameA2,textvariable=self.TWA_strvar,bg=infocolor,width=8,anchor="w",font=MIOFONT)
        self.LabelTWA.pack(side=LEFT)
        orza=Button(FrameA2,text="UP",width=6,font=MIOFONT)
        orza.pack(side=LEFT)
        orza.bind("<Button-1>",self.orza)
        orza.bind("<Button-2>",self.orza)
        orza.bind("<Button-3>",self.orza)
        puggia=Button(FrameA2,text="DOWN",width=6,font=MIOFONT)
        puggia.pack(side=LEFT)
        puggia.bind("<Button-1>",self.puggia)
        puggia.bind("<Button-2>",self.puggia)
        puggia.bind("<Button-3>",self.puggia)
        virastramba=Button(FrameA2,text="TACK",width=6,font=MIOFONT)
        virastramba.pack(side=LEFT)
        virastramba.bind("<Button-1>",self.virastramba)
        Label(FrameA3,text="HDG",width=8,anchor="e",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        self.LabelHDG=Label(FrameA3,textvariable=self.HDG_strvar,bg=infocolor,width=8,anchor="w",font=MIOFONT)
        self.LabelHDG.pack(side=LEFT)
        ruotaantiorario=Button(FrameA3,text="-",width=6,font=MIOFONT)
        ruotaantiorario.pack(side=LEFT)
        ruotaantiorario.bind("<Button-1>",self.ruotaantiorario)
        ruotaantiorario.bind("<Button-2>",self.ruotaantiorario)
        ruotaantiorario.bind("<Button-3>",self.ruotaantiorario)
        ruotaorario=Button(FrameA3,text="+",width=6,font=MIOFONT)
        ruotaorario.pack(side=LEFT)
        ruotaorario.bind("<Button-1>",self.ruotaorario)
        ruotaorario.bind("<Button-2>",self.ruotaorario)
        ruotaorario.bind("<Button-3>",self.ruotaorario)
        Label(FrameA4,text="Speed",width=8,anchor="e",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        Label(FrameA4,textvariable=self.Speed_strvar,bg=infocolor,width=8,anchor="w",font=MIOFONT).pack(side=LEFT)
        Label(FrameA4,text="Log",width=8,anchor="e",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        Label(FrameA4,textvariable=self.Log_strvar,bg=infocolor,width=8,anchor="w",font=MIOFONT).pack(side=LEFT)
        Label(FrameA5,text="BRG",width=8,anchor="e",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        Label(FrameA5,textvariable=self.BRG_strvar,bg=infocolor,width=8,anchor="w",font=MIOFONT).pack(side=LEFT)
        Label(FrameA5,text="Dist",width=8,anchor="e",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        Label(FrameA5,textvariable=self.Dist_strvar,bg=infocolor,width=8,anchor="w",font=MIOFONT).pack(side=LEFT)
        Label(FrameA6,text="Lat",width=8,anchor="e",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        Label(FrameA6,textvariable=self.Lat_strvar,bg=infocolor,width=8,anchor="w",font=MIOFONT).pack(side=LEFT)
        Label(FrameA6,text="Lon",width=8,anchor="e",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        Label(FrameA6,textvariable=self.Lon_strvar,bg=infocolor,width=8,anchor="w",font=MIOFONT).pack(side=LEFT)
        Label(FrameA7,text="XCrs",width=8,anchor="e",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        Label(FrameA7,textvariable=self.XCourse_strvar,bg=infocolor,width=8,anchor="w",font=MIOFONT).pack(side=LEFT)
        Label(FrameA7,text="OffSet",width=8,anchor="e",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        Label(FrameA7,textvariable=self.YCourse_strvar,bg=infocolor,width=8,anchor="w",font=MIOFONT).pack(side=LEFT)
        Label(FrameA8,text="VMGtwd",width=8,anchor="e",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        Label(FrameA8,textvariable=self.VMGTWD_strvar,bg=infocolor,width=8,anchor="w",font=MIOFONT).pack(side=LEFT)
        Label(FrameA8,text="VMGwp",width=8,anchor="e",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        Label(FrameA8,textvariable=self.VMGBRG_strvar,bg=infocolor,width=8,anchor="w",font=MIOFONT).pack(side=LEFT)
        Label(FrameA8,text="CMG",width=8,anchor="e",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        Label(FrameA8,textvariable=self.VMGCourse_strvar,bg=infocolor,width=8,anchor="w",font=MIOFONT).pack(side=LEFT)
        FrameA9sx=Frame(FrameA9,bg=BGCOLOR)
        FrameA9sx.pack(side=LEFT,fill=X)
        FrameA9dx=Frame(FrameA9,bg=BGCOLOR)
        FrameA9dx.pack(side=LEFT,fill=BOTH)
        self.Graficosx=Canvas(FrameA9sx,width=GraficoSxSize,height=GraficoSxSize,bg="lightgray",bd=2,relief="sunken")
        self.Graficosx.pack(side=TOP)
        FrameA91dx=Frame(FrameA9dx,bg=BGCOLOR)
        FrameA91dx.pack(side=TOP,fill=X)        
        FrameA92dx=Frame(FrameA9dx,bg=BGCOLOR)
        FrameA92dx.pack(side=TOP,fill=X)
        FrameA93dx=Frame(FrameA9dx,bg=BGCOLOR)
        FrameA93dx.pack(side=TOP,fill=X)
        FrameA94dx=Frame(FrameA9dx,bg=BGCOLOR)
        FrameA94dx.pack(side=TOP,fill=X)
        FrameA95dx=Frame(FrameA9dx,bg=BGCOLOR)
        FrameA95dx.pack(side=TOP,fill=X)
        FrameA96dx=Frame(FrameA9dx,bg=BGCOLOR)
        FrameA96dx.pack(side=TOP,fill=X)
        FrameA97dx=Frame(FrameA9dx,bg=BGCOLOR)
        FrameA97dx.pack(side=TOP,fill=X)
        FrameA98dx=Frame(FrameA9dx,bg=BGCOLOR)
        FrameA98dx.pack(side=TOP,fill=X)
        FrameA99dx=Frame(FrameA9dx,bg=BGCOLOR)
        FrameA99dx.pack(side=TOP,fill=X)
        FrameA100dx=Frame(FrameA9dx,bg=BGCOLOR)
        FrameA100dx.pack(side=TOP,fill=X)
        FrameA101dx=Frame(FrameA9dx,bg=BGCOLOR)
        FrameA101dx.pack(side=TOP,fill=X)
        play=Button(FrameA91dx,textvariable=self.bottoneplay_strvar,font=MIOFONT,width=8)
        play.pack(side=LEFT)
        play.bind("<Button-1>",self.Play)
        replay=Button(FrameA92dx,text="RePlay",font=MIOFONT,width=8)
        replay.pack(side=LEFT)
        replay.bind("<Button-1>",self.RePlay)
        Label(FrameA93dx,text="Raffica",width=8,bg=BGCOLOR,anchor="w",font=MIOFONT).pack(side=LEFT)
        self.rafficamode_intvar=IntVar()
        rbrafficaoff=Radiobutton(FrameA94dx,text="OFF",variable=self.rafficamode_intvar,value=0,command=self.RafficaOnOff,
                        bg=BGCOLOR,font=MIOFONT, borderwidth=0)
        rbrafficaoff.pack(side=LEFT,anchor="e")
        rbrafficaon=Radiobutton(FrameA94dx,text="ON",variable=self.rafficamode_intvar,value=1,command=self.RafficaOnOff,
                        bg=BGCOLOR,font=MIOFONT)
        rbrafficaon.pack(side=LEFT,anchor="e")
        Label(FrameA95dx,text="Isocrone",width=8,bg=BGCOLOR,anchor="w",font=MIOFONT).pack(side=LEFT)
        self.isocronamode_intvar=IntVar()
        rbisocroff=Radiobutton(FrameA96dx,text="OFF",variable=self.isocronamode_intvar,value=0,command=self.IsocronaOnOff,
                        bg=BGCOLOR,font=MIOFONT)
        rbisocroff.pack(side=LEFT,anchor="e")
        rbisocron=Radiobutton(FrameA96dx,text="ON",variable=self.isocronamode_intvar,value=1,command=self.IsocronaOnOff,
                        bg=BGCOLOR,font=MIOFONT)
        rbisocron.pack(side=LEFT,anchor="e")
        self.steermode_intvar=IntVar()
        Label(FrameA97dx,text="Steering Mode",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)
        rb1=Radiobutton(FrameA98dx,text="Wind",variable=self.steermode_intvar,value=0,command=self.steermode,
                        bg=BGCOLOR,font=MIOFONT)
        rb1.pack(side=LEFT,anchor="e")
        rb2=Radiobutton(FrameA99dx, text="Compass",variable=self.steermode_intvar,value=1,command=self.steermode,
                        bg=BGCOLOR,font=MIOFONT)
        rb2.pack(side=LEFT,anchor="e")
        rb3=Radiobutton(FrameA100dx, text="GPS",variable=self.steermode_intvar,value=2,command=self.steermode,
                        bg=BGCOLOR,font=MIOFONT)
        rb3.pack(side=LEFT,anchor="e")
        rb4=Radiobutton(FrameA101dx, text="maxVMG", variable=self.steermode_intvar, value=3,command=self.steermode,
                        bg=BGCOLOR,font=MIOFONT)
        rb4.pack(side=LEFT,anchor="e")
        barratrackdx=Scrollbar(FrameA10,orient=VERTICAL)
        barratrackdown=Scrollbar(FrameA10,orient=HORIZONTAL)
        self.Track=Text(FrameA10,height=TrackHeight,width=TrackWidth,font=MIOFONT,bg=BGCOLOR,relief="flat",
                        yscrollcommand=barratrackdx.set,xscrollcommand=barratrackdown.set,wrap="none",tabs=('1.8c','3.6c'))
        barratrackdown.config(command=self.Track.xview)
        barratrackdown.pack(side=BOTTOM,fill=X)
        self.Track.pack(side=LEFT)
        barratrackdx.config(command=self.Track.yview)
        barratrackdx.pack(side=LEFT,fill=Y)
        self.Track.config(state=DISABLED)
        Label(FrameA11,text="©Riccardo Apolloni, free software under GNU License",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)       
        #FrameB
        barradx=Scrollbar(FrameB1,orient=VERTICAL)
        barradown=Scrollbar(FrameB1,orient=HORIZONTAL)
        self.Graficodx=Canvas(FrameB1,bg="lightgray",width=GraficoDxWidth,height=GraficoDxHeight,
                              xscrollcommand=barradown.set,yscrollcommand=barradx.set,bd=2,relief="sunken")
        barradx.config(command=self.Graficodx.yview)
        barradx.pack(side=RIGHT,fill=Y)
        barradown.config(command=self.Graficodx.xview)
        barradown.pack(side=BOTTOM,fill=X)
        self.Graficodx.pack(side=TOP)
        Label(FrameB2,text="Gegraphy Data by Global Self-consistent Hierarchical High-resolution Geography Version 2.2.2 January 1, 2013 ",bg=BGCOLOR,font=MIOFONT).pack(side=LEFT)       
        
    #EVENTI
    def orza(self,event):
        self.Controllo=not self.Controllo
        while self.Controllo:
            self.mode="wind"
            self.steermode_intvar.set(0)
            twa=self.MaVie.TWA
            self.MaVie.Orza()
            self.aggiornavalori()
            self.DisegnaVettoriBarca()
            self.SettaBottoni()
            if event.num<>2:self.Controllo=False
            if twa==self.MaVie.TWA:self.Controllo=False
    def puggia(self,event):
        self.Controllo=not self.Controllo
        while self.Controllo:
            self.mode="wind"
            self.steermode_intvar.set(0)
            twa=self.MaVie.TWA
            self.MaVie.Puggia()
            self.aggiornavalori()
            self.DisegnaVettoriBarca()
            self.SettaBottoni()
            if event.num<>2:self.Controllo=False
            if twa==self.MaVie.TWA:self.Controllo=False
    def virastramba(self,event):
        self.mode="wind"
        self.steermode_intvar.set(0)
        self.MaVie.CambiaMura()
        self.aggiornavalori()        
        self.DisegnaVettoriBarca()
        self.SettaBottoni()
    def ruotaorario(self,event):
        self.Controllo=not self.Controllo
        while self.Controllo:
            self.mode="compass"
            self.steermode_intvar.set(1)
            self.MaVie.TWA=self.MaVie.TWA-math.radians(1.0)
            self.MaVie.TWA=riduci180(self.MaVie.TWA)
            self.aggiornavalori()
            self.DisegnaVettoriBarca()
            self.SettaBottoni()
            if event.num<>2:self.Controllo=False
    def ruotaantiorario(self,event):
        self.Controllo=not self.Controllo
        while self.Controllo:
            self.mode="compass"
            self.steermode_intvar.set(1)
            self.MaVie.TWA=self.MaVie.TWA+math.radians(1.0)
            self.MaVie.TWA=riduci180(self.MaVie.TWA)
            self.aggiornavalori()
            self.DisegnaVettoriBarca()
            self.SettaBottoni()
            if event.num<>2:self.Controllo=False
    def RePlay(self,event):
        #self.MaVie.Log=0.0
        self.inizia(1)
    def Play(self,event):
        self.run=not self.run
        while self.run:
            if self.mode=="vmg":
                self.MaVie.TWA=self.MaVie.TWAmaxVMGWP(self.Arrivo)
            if self.mode=="gps":
                self.MaVie.TWA=riduci180(self.MaVie.TW[0]-self.MaVie.BRGGPS(self.Arrivo))
            if self.isocronamodo:
                self.CalcolaIsocrona()
                curvaisocrona=[]
                bestcourse=[]
                mindist=self.Course[0]
                for valore in self.Isocrone[-1]:
                    pto=valore[0]
                    curvaisocrona.append(pto)
                    losso=lossodromica(pto[0],pto[1],self.Arrivo[0],self.Arrivo[1])
                    dist=losso[0]
                    if dist<mindist:
                        mindist=dist
                        bestpto=pto
                        previusindice=valore[1]
                bestcourse.append(bestpto)
                for i in range(-2,-len(self.Isocrone),-1):
                    valore=self.Isocrone[i][previusindice]
                    pto=valore[0]
                    previusindice=valore[1]
                    bestcourse.append(pto)
                bestcourse.append(self.OrigineIsocrone)
                self.Graficodx.delete("bestcourse")
                self.disegna(bestcourse,"#8B4519","bestcourse")
                self.disegna(curvaisocrona,"dodgerblue","isocrona")
            pos1=self.MaVie.Pos
            twa_arrivo=riduci180(self.MaVie.TW[0]-self.MaVie.BRG(self.Arrivo))
            v_arrivo=self.MaVie.Plr.SpeedRoutage(self.MaVie.TW[1],math.copysign(twa_arrivo,1))
            Dt_arrivo=self.MaVie.Dist(self.Arrivo)/v_arrivo
            if self.Dt>Dt_arrivo:#ultimo passo
                self.run=False
                self.MaVie.TWA=twa_arrivo
                self.MaVie.MuoviRoutage(Dt_arrivo)
                self.T=self.T+Dt_arrivo
            else:#passo standard
                if self.mode=="gps":
                    self.MaVie.MuoviRoutage(self.Dt)
                else:
                    self.MaVie.Muovi(self.Dt)
                self.T=self.T+self.Dt  
            hdg=self.MaVie.HDG()#prima di aggiornare il vento memorizzo la hdg per il modo compass
            self.MaVie.TW=self.vento(self.MaVie.Pos[0],self.MaVie.Pos[1])
            if self.mode=="compass":
                self.MaVie.TWA=riduci180(self.MaVie.TW[0]-hdg)
            self.DisegnaCampoDiVento()
            self.disegna([pos1,self.MaVie.Pos],"darkblue","tracking")
            self.Graficodx.delete("brg")
            self.disegna([self.MaVie.Pos,self.Arrivo],"yellow","brg")
            self.Graficodx.update()
            self.Graficodx.config(scrollregion=self.Graficodx.bbox(ALL))
            self.DisegnaVettoriBarca()
            self.SettaStrVar()
            self.SettaBottoni()
            time.sleep(0.0001)
    def RafficaUtility(self,event):
        self.rafficautility=not self.rafficautility
        self.MaVie.TW=self.vento(self.MaVie.Pos[0],self.MaVie.Pos[1])
        self.Track.config(state=NORMAL)
        start="1.end"
        stop="2.end"
        self.Track.delete(start,stop)
        self.Track.config(state=DISABLED)
        self.SettaStrVar()
        self.DisegnaVettoriBarca()
        self.DisegnaCampoDiVento()   
        self.SettaBottoni()
    def CambiaEsempio(self,event):
        n=int(self.Esempiolistbox.curselection()[0])
        if self.Esempio<>n+1:
            self.Esempio=n+1
            self.inizia()
    def steermode(self):
        if self.steermode_intvar.get()==0:self.mode="wind"
        if self.steermode_intvar.get()==1:self.mode="compass"
        if self.steermode_intvar.get()==2:self.mode="gps"
        if self.steermode_intvar.get()==3:self.mode="vmg"
        if self.mode=="gps":
            self.MaVie.TWA=riduci180(self.MaVie.TW[0]-self.MaVie.BRG(self.Arrivo))
            self.aggiornavalori()        
            self.DisegnaVettoriBarca()
        if self.mode=="vmg":
            self.MaVie.TWA=self.MaVie.TWAmaxVMGWP(self.Arrivo)
            self.aggiornavalori()        
            self.DisegnaVettoriBarca()
        self.SettaBottoni()
    def IsocronaOnOff(self):
        if self.isocronamode_intvar.get()==0:
            self.isocronamodo=False
        if self.isocronamode_intvar.get()==1:
            self.isocronamodo=True
        if not self.isocronamodo:
            self.Isocrone=[]
    def RafficaOnOff(self):
        if self.rafficamode_intvar.get()==0:
            self.rafficautility=False
        if self.rafficamode_intvar.get()==1:
            self.rafficautility=True
        self.MaVie.TW=self.vento(self.MaVie.Pos[0],self.MaVie.Pos[1])
        self.Track.config(state=NORMAL)
        start="1.end"
        stop="2.end"
        self.Track.delete(start,stop)
        self.Track.config(state=DISABLED)
        self.SettaStrVar()
        self.DisegnaVettoriBarca()
        self.DisegnaCampoDiVento()   


    #METODI
    def InfoCorsa(self):
        #definisce partenza, arrivo e campo di vento,
        #calcola Dt, campo di regata (bbox), fattore di scala
        #info Corse, aggiornate al 11.03.2013
        if self.Esempio==1:
            self.Partenza=(UsticaLat,UsticaLon)
            self.Arrivo=(PonzaLat,PonzaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 1: Ustica Ponza"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zone Lipari e Circeo: N4"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==2:
            self.Partenza=(PonzaLat,PonzaLon)
            self.Arrivo=(UsticaLat,UsticaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 2: Ponza Ustica"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zone Lipari e Circeo: N4"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==3:
            self.Partenza=(UsticaLat,UsticaLon)
            self.Arrivo=(CapriLat,CapriLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 3: Ustica Capri"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zone Lipari e Circeo: N4"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==4:
            self.Partenza=(CapriLat,CapriLon)
            self.Arrivo=(UsticaLat,UsticaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 4: Capri Ustica"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zone Lipari e Circeo: N4"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==5:
            self.Partenza=(UsticaLat,UsticaLon)
            self.Arrivo=(PonzaLat,PonzaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 5: Ustica Ponza"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zone Lipari e Circeo: N4, in rotazione a NNW4"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==6:
            self.Partenza=(PonzaLat,PonzaLon)
            self.Arrivo=(UsticaLat,UsticaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 6: Ponza Ustica"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zone Lipari e Circeo: N4, in rotazione a NNW4"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==7:
            self.Partenza=(PonzaLat,PonzaLon)
            self.Arrivo=(UsticaLat,UsticaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 7: Ponza Ustica"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zone Lipari e Circeo: variabile settore S forza 4"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==8:
            self.Partenza=(UsticaLat,UsticaLon)
            self.Arrivo=(PonzaLat,PonzaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 8: Ustica Ponza"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zone Lipari e Circeo: variabile settore S forza 4"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==9:
            self.Partenza=(UsticaLat,UsticaLon)
            self.Arrivo=(PonzaLat,PonzaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 9: Ustica Ponza"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zone Lipari e Circeo: N3 settore est, N4 settore ovest"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==10:
            self.Partenza=(PonzaLat,PonzaLon)
            self.Arrivo=(UsticaLat,UsticaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 10: Ponza Ustica"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zone Lipari e Circeo: N3 settore est, N4 settore ovest"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==11:
            self.Partenza=(PonzaLat,PonzaLon)
            self.Arrivo=(UsticaLat,UsticaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 11: Ponza Ustica"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zona: Circeo S3 settore est, S4 settore ovest - Lipari: SSE3 settore est, SSE4 settore ovest"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==12:
            self.Partenza=(PonzaLat,PonzaLon)
            self.Arrivo=(UsticaLat,UsticaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 12: Ponza Ustica"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zona: Circeo N3 settore est, N4 settore ovest - Lipari: NNW3 settore est, NNW4 settore ovest"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==13:
            self.Partenza=(GenovaLat,GenovaLon)
            self.Arrivo=(GiragliaLat,GiragliaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 13: Genova Giraglia"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zona: Ligure N3 in rotazione a NNE3"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==14:
            self.Partenza=(GenovaLat,GenovaLon)
            self.Arrivo=(GiragliaLat,GiragliaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 14: Genova Giraglia"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zona: Ligure NNE3 in rotazione a E3"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==15:
            self.Partenza=(GenovaLat,GenovaLon)
            self.Arrivo=(GiragliaLat,GiragliaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 15: Genova Giraglia"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zona: Ligure N3 in rotazione a E3"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==16:
            self.Partenza=(GenovaLat,GenovaLon)
            self.Arrivo=(GiragliaLat,GiragliaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 16: Genova Giraglia"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zona: Ligure ESE3 in rotazione a NNE3"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==17:
            self.Partenza=(GiragliaLat,GiragliaLon)
            self.Arrivo=(GenovaLat,GenovaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 17:Giraglia Genova"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zona: Ligure SSE3 settore est, SSE4 settore ovest"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==18:
            self.Partenza=(GiragliaLat,GiragliaLon)
            self.Arrivo=(GenovaLat,GenovaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 18:Giraglia Genova"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zona: Ligure SSE3 settore est, S4 settore ovest"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==19:
            self.Partenza=(GiragliaLat,GiragliaLon)
            self.Arrivo=(GenovaLat,GenovaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 19:Giraglia Genova"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zona: Ligure SSE5 settore E, S6 settore ovest"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==20:
            self.Partenza=(ArgentarioLat,ArgentarioLon)
            self.Arrivo=(GenovaLat,GenovaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 20:Argentario Genova"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zone: Elba e Ligure SE5 in attenuazione a SE2"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==21:
            self.Partenza=(ArgentarioLat,ArgentarioLon)
            self.Arrivo=(GenovaLat,GenovaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 21:Argentario Genova"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zone: Elba e Ligure NE5 in attenuazione a NE2"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==22:
            self.Partenza=(PianosaLat,PianosaLon)
            self.Arrivo=(CCominoLat,CCominoLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 22:Pianosa Capo Comino"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zone: Maddalena Ovest3, localmente 4 su Bocche di Bonifacio"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==23:
            self.Partenza=(PorquerollesLat,PorquerollesLon)
            self.Arrivo=(PalmaLat,PalmaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 23:Porquerolles Palma"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+"Bollettino zone: Provenza e Minorca SW4, fronte ovest Baleari muove E"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==24:
            self.Partenza=(PorquerollesLat,PorquerollesLon)
            self.Arrivo=(PalmaLat,PalmaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 24:Porquerolles Palma"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+u"Bollettino zone: Provenza e Minorca var.depressionario, Bassa 1005mmbar in 41°N 4°40'E"
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==25:
            self.Partenza=(CapoFinisterreLat,CapoFinisterreLon)
            self.Arrivo=(HortaLat,HortaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 25: Capo Finistre Horta"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+(u"Bollettino zone: H1030mmbar in 38°N 25°W, B1005mmbar in 39°N 4°W  si colma, B1000mmbar in 15°N 0°W si scava")
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==26:
            self.Partenza=(LanzaroteLat,LanzaroteLon)
            self.Arrivo=(GuadalupeLat,GuadalupeLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            Info="Corsa 26: Lanzarote Guadalupe"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+("Bollettino Aliseo")
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)
        if self.Esempio==27:
            self.Partenza=(CamargueLat,CamargueLon)
            self.Arrivo=(AnnabaLat,AnnabaLon)
            losso=lossodromica(self.Partenza[0],self.Partenza[1],self.Arrivo[0],self.Arrivo[1])
            self.Course=losso
            self.GribMeteo=Grib(FILEGRIB)
            record=self.GribMeteo.records[0]#primo record
            tempi=self.GribMeteo.index.keys()
            tempi.sort()
            Info="Corsa 27: Camargue Annaba (Tunisia)"
            Info=Info+" --- %3.0f"%math.degrees(losso[1])+u"°"+" %3.0f"%losso[0]+"nm\n"
            Info=Info+("GRIB emesso da "+record.decodecenter()+" il "+
                       record.data+" valid up +"+str(tempi[-1])+record.decodetimeunits())
            self.Info.config(state=NORMAL)
            self.Info.delete(1.0,END)
            self.Info.insert(END,Info)
            self.Info.config(state=DISABLED)

        self.Dt=5.0/60.0*(1+int(self.Course[0]*1.0/50))
        #self.Dt=min(6.0,self.Dt)
        self.Bbox=self.calcolabbox()
        self.RitardiDiFase=random.sample(xrange(0,360),3)#vettore degli sfasamenti delle 2 onde componenti la raffica di vento
        for i in range(0,len(self.RitardiDiFase)):
            self.RitardiDiFase[i]=math.radians(self.RitardiDiFase[i])
        self.DisegnaFincature()
        self.Graficodx.config(scrollregion=self.Graficodx.bbox(ALL))#centra lo scrollregion sulla area di corsa
        self.DisegnaCartografia()
        self.Graficodx.config(scrollregion=self.Graficodx.bbox(ALL))#estende lo scrollregion alla cartografia

    def inizia(self,replay=0):
        if replay==0:#solo per cambi esercizi
            self.InfoCorsa()
        self.T=0
        self.MaVie.Log=0.0
        self.MaVie.Pos=self.Partenza
        self.MaVie.TW=self.vento(self.MaVie.Pos[0],self.MaVie.Pos[1])
        if self.mode=="wind" or self.mode=="gps" or self.mode=="compass":
            twa=riduci180(self.MaVie.TW[0]-self.MaVie.BRG(self.Arrivo))
            self.MaVie.TWA=twa
        if self.mode=="vmg":
            self.MaVie.TWA=self.MaVie.TWAmaxVMGWP(self.Arrivo)
        #intestazioni tracking
        trackinfo="Time"+"\t"
        trackinfo=trackinfo+"TWD\t"
        trackinfo=trackinfo+"TWS\t"
        trackinfo=trackinfo+"TWA\t"
        trackinfo=trackinfo+"HDG\t"
        trackinfo=trackinfo+"Speed\t"
        trackinfo=trackinfo+"Log\t"
        trackinfo=trackinfo+"BRG\t"
        trackinfo=trackinfo+"DIST\t"
        trackinfo=trackinfo+"Lat\t"
        trackinfo=trackinfo+"Lon\t"
        trackinfo=trackinfo+"XCourse\t"
        trackinfo=trackinfo+"Offset\t"
        trackinfo=trackinfo+"VMGtwd\t"
        trackinfo=trackinfo+"WMGwp\t"
        trackinfo=trackinfo+"CMG\n"
        self.Track.config(state=NORMAL)
        self.Track.delete(1.0,END)
        self.Track.insert(END,trackinfo)
        self.Track.config(state=DISABLED)
        self.SettaStrVar()
        self.DisegnaCampoDiVento()
        self.SettaBottoni()
        self.DisegnaVettoriBarca()
        self.run=False
        #self.rafficautility=False
        #self.isocronamodo=False
        self.Isocrone=[]
        self.Graficodx.delete("brg")
        self.Graficodx.delete("tracking")
        self.Graficodx.delete("raggi","isocrona","bestcourse")
        
        
    def CalcolaIsocrona(self):
        #Prima Isocrona: polare per il p.to di origine dell'isocrone
        isocronazero=[]
        if len(self.Isocrone)==0:
            self.OrigineIsocrone=(self.MaVie.Pos[0],self.MaVie.Pos[1])
            TW=self.vento(self.OrigineIsocrone[0],self.OrigineIsocrone[1])
            TWD=TW[0]
            TWS=TW[1]
            passo=5#per valori più bassi si rischia instabilità
            for TWA in range(-180,180,passo):
                TWA=math.radians(TWA)
                brg=riduci360(TWD+TWA)
                Speed=self.MaVie.Plr.SpeedRoutage(TWS,math.copysign(TWA,1))
                ptoiso=puntodistanterotta(self.OrigineIsocrone[0],self.OrigineIsocrone[1],Speed*self.Dt,brg)
                isocronazero.append((ptoiso,0))
            isocronazero.append(isocronazero[0])#chiude l'isocrona
            self.Isocrone.append(isocronazero)                                               
        else:#Isocrona i-esima: pti raggiunti navigando (alla migliore CMG) nella direzione normale all'isocrona i-esima-1            
            pto1=self.Isocrone[-1][0][0]
            isocrona=[]
            self.Graficodx.delete("raggi")
            self.Graficodx.delete("raggi")            
            for i in range(0,len(self.Isocrone[-1])-1):
                #pto1=self.Isocrone[-1][i][0]
                pto2=self.Isocrone[-1][i+1][0]
                #self.disegna((self.OrigineIsocrone,pto1),"orangered","raggi")
                distbrg=lossodromica(pto1[0],pto1[1],pto2[0],pto2[1])
                dist=distbrg[0]
                
                brg=distbrg[1]#rotta tra i punti 1 e 2
                brgorto=riduci360(brg-math.pi/2)#normale al tratto 1-2, per self.Isocrona percorsa in senso orario
                pto=puntodistanterotta(pto1[0],pto1[1],0.5*dist,brg)#pto medio del tratto i-esimo
                rlvpto=lossodromica(self.OrigineIsocrone[0],self.OrigineIsocrone[1],pto[0],pto[1])[1]
                if dist>0.05 and math.cos(scartorotta(rlvpto,brgorto))>0:
                    TW=self.vento(pto[0],pto[1])
                    TWD=TW[0]
                    TWS=TW[1]
                    TWA=riduci180(TWD-brgorto)
                    #qui arrotondimo per migliorare le ricerche nell'oggetto polare (dizionario vmg) 
                    TWS=int(TWS+0.5)
                    TWA=arrotonda(TWA,2)
                    tuplamaxCMGOrto=self.MaVie.Plr.maxVMGtwa(TWS,math.copysign(TWA,1))
                    TWAmaxCMGOrto=math.copysign(tuplamaxCMGOrto[1],TWA)
                    VMGmaxCMGOrto=tuplamaxCMGOrto[0]
                    IsoSpeed=VMGmaxCMGOrto/math.cos(TWAmaxCMGOrto-TWA)
                    IsoBrg=riduci360(TWD-TWAmaxCMGOrto)
                    ptoiso=puntodistanterotta(pto[0],pto[1],IsoSpeed*self.Dt,IsoBrg)
                    self.disegna((pto,ptoiso),"orangered","raggi")
                    previusindice=i        
                    if (lossodromica(ptoiso[0],ptoiso[1],pto1[0],pto1[1])[0]>
                        lossodromica(ptoiso[0],ptoiso[1],pto2[0],pto2[1])[0]):
                        previusindice=i+1
                    isocrona.append((ptoiso,previusindice))
                else:
                    print "punto scartatato"
                pto1=(pto2[0],pto2[1])
                self.Graficodx.update()
            #Ordino l'isocrona in senso orario
            rlvs=[]
            rlvsordinati=[]
            isocronaordinata=[]
            for tupla in isocrona:
                punto=tupla[0]
                rlv=lossodromica(self.OrigineIsocrone[0],self.OrigineIsocrone[1],punto[0],punto[1])[1]
                #rlv=math.atan2(self.OrigineIsocrone[0]-punto[0],self.OrigineIsocrone[1]-punto[1])
                rlvs.append(rlv)
                rlvsordinati.append(rlv)
            rlvsordinati.sort()
            if rlvs<>rlvsordinati:
                for rlv in rlvsordinati:
                    indice=rlvs.index(rlv)
                    isocronaordinata.append(isocrona[indice])
                    rlvs[indice]=-100#rislve gi exequo
            else:#copia di isocorna
                for tupla in isocrona:
                    isocronaordinata.append(tupla)
            isocronaordinata.append(isocronaordinata[0])#chiude l'isocrona

            #Rimuovo gli eventuali pti interni all'isocrona precedente
            isocronapre=[]
            lista=[]
            for valore in self.Isocrone[-1]:
                isocronapre.append(valore[0])
            for i in range(0,len(isocronaordinata)):
                punto=isocronaordinata[i][0]
                if interno(isocronapre,punto):
                    lista.append(i)
            lista.reverse()
            for indice in lista:
                isocronaordinata.pop(indice)
                print "punto scartato", indice

            #Inserico pti dove troppo radi 
            base=0.02*self.Course[0]#valori troppo bassi producono instabilità
            isocronacompletata=[]
            for i in range(0,len(isocronaordinata)-1):
                pto1=isocronaordinata[i][0]
                indice1=isocronaordinata[i][1]
                pto2=isocronaordinata[i+1][0]
                indice2=isocronaordinata[i+1][1]
                distbrg=lossodromica(pto1[0],pto1[1],pto2[0],pto2[1])
                dist=distbrg[0]
                brg=distbrg[1]
                isocronacompletata.append((pto1,indice1))
                if dist>base:#inserisce pti dove troppo radi
                    N=int(dist/base)+1
                    for j in range(1,N+1):
                        k=j*1.0/N-0.5/N
                        pto=puntodistanterotta(pto1[0],pto1[1],k*dist,brg)#pti medio del tratto i-esimo
                        if k<=0.5:
                            indice=indice1        
                        else:
                            indice=indice2
                        isocronacompletata.append((pto,indice))
            isocronacompletata.append((pto2,indice2))
            self.Isocrone.append(isocronacompletata)
            
    def DisegnaFincature(self):
        self.Graficodx.delete(ALL)
        #self.Graficosx.delete("icona")
        NW=self.Bbox[0]#angolo NW
        SE=self.Bbox[1]#angolo SE
        N=25
        height=float(self.Graficodx.cget("height"))
        width=float(self.Graficodx.cget("width"))
        Df=math.log(math.tan(SE[0]/2+math.pi/4)/math.tan(NW[0]/2+math.pi/4),math.e)
        self.q=math.copysign((NW[0]-SE[0])/Df,1)
        self.FattoreDiScala=0.85*min(height/math.copysign((NW[0]-SE[0]),1),width/(self.q*math.copysign((NW[1]-SE[1]),1)))
        lat=NW[0]
        passo=(NW[0]-SE[0])*1.0/N
        for i in range(0,N+1):
            self.disegna([(lat,NW[1]),(lat,SE[1])],"darkgray","fincature")#orizontali
            lat=lat-passo
        lon=NW[1]
        passo=(NW[1]-SE[1])*1.0/N
        for i in range(0,N+1):
            self.disegna([(NW[0],lon),(SE[0],lon)],"darkgray","fincature")#verticali
            lon=lon-passo
        testo=stampalat(NW[0])
        x=-NW[1]*self.FattoreDiScala*self.q
        y=-NW[0]*self.FattoreDiScala
        self.Graficodx.create_text(x-5,y-15,text=testo,fill="darkgray",tags="fincature",anchor="e", font=MIOFONT)
        testo=stampalon(NW[1])
        self.Graficodx.create_text(x-5,y,text=testo,fill="darkgray",tags="fincature",anchor="e", font=MIOFONT)
        testo=stampalat(SE[0])
        x=-SE[1]*self.FattoreDiScala*self.q
        y=-SE[0]*self.FattoreDiScala
        self.Graficodx.create_text(x+5,y,text=testo,fill="darkgray",tags="fincature",anchor="w", font=MIOFONT)
        testo=stampalon(SE[1])
        self.Graficodx.create_text(x+5,y+15,text=testo,fill="darkgray",tags="fincature",anchor="w", font=MIOFONT)
        x1=-self.Partenza[1]*self.FattoreDiScala*self.q
        y1=-self.Partenza[0]*self.FattoreDiScala
        self.Graficodx.create_rectangle(x1-3,y1-3,x1+3,y1+3,fill="red",tags="fincature")
        x2=-self.Arrivo[1]*self.FattoreDiScala*self.q
        y2=-self.Arrivo[0]*self.FattoreDiScala
        self.Graficodx.create_rectangle(x2-3,y2-3,x2+3,y2+3,fill="green",tags="fincature")
        self.Graficodx.create_line(x1,y1,x2,y2,fill=BGCOLOR,tags="fincature")
    def DisegnaCartografia(self):
        #convenzione cartografia lon>0 Est
        self.Graficodx.delete("shoreline")
        for vettore in self.Cartografia.poligoni:
            for i in range(0,len(vettore)-1):
                x1=vettore[i][1]*self.FattoreDiScala*self.q
                y1=-vettore[i][0]*self.FattoreDiScala
                x2=vettore[i+1][1]*self.FattoreDiScala*self.q
                y2=-vettore[i+1][0]*self.FattoreDiScala
                self.Graficodx.create_line(x1,y1,x2,y2,fill="#8B4513",tags="shoreline")
        self.Graficodx.update()
    def DisegnaCampoDiVento(self):
        self.Graficodx.delete("vento")
        NW=self.Bbox[0]#angolo NW
        SE=self.Bbox[1]#angolo SE
        N=25
        lat=NW[0]
        passolat=(NW[0]-SE[0])*1.0/N
        passolon=(NW[1]-SE[1])*1.0/N
        for i in range(0,N+1):
            lon=NW[1]
            for j in range(0,N+1):
                tw=self.vento(lat,lon)
                twd=tw[0]
                tws=tw[1]
                twy=tws*math.cos(twd)*self.Dt*1.0/RaggioTerrestre
                twx=-tws*math.sin(twd)*self.Dt*1.0/RaggioTerrestre
                self.disegna([(lat,lon),(lat+twy,lon+twx)],windcolor(tws),"vento")
                self.disegna([(lat+twy,lon+twx),(lat+twy-0.30*twx,lon+twx+0.30*twy)],windcolor(tws),"vento")
                lon=lon-passolon
            lat=lat-passolat
    def aggiornavalori(self):
        #metodo chiamato dagli eventi orza, puggia, vira/stramba (copia ridotta di settastrvar)
        if self.MaVie.TWA>=0:
            self.TWA_strvar.set("%3.0f"%math.degrees(self.MaVie.TWA)+u"°-")
        else:
            self.TWA_strvar.set("%3.0f"%math.degrees(self.MaVie.TWA)+u"°")
        self.HDG_strvar.set("%3.0f"%math.degrees(self.MaVie.HDG())+u"°")
        self.Speed_strvar.set("%3.2f"%self.MaVie.Speed()+"knts")
        self.VMGTWD_strvar.set("%3.2f"%self.MaVie.VMGTWD()+"knts")
        self.VMGBRG_strvar.set("%3.2f"%self.MaVie.VMGWP(self.Arrivo)+"knts")
        self.VMGCourse_strvar.set("%3.2f"%self.MaVie.CMG(self.Course[1])+"knts")
        self.SettaBottoni()
    def SettaStrVar(self):
        #metodo chiamato dall'evento Play e dai metodi inizia e RafficaUtility 
        if self.MaVie.TWA>=0:
            self.TWA_strvar.set("%3.0f"%math.degrees(self.MaVie.TWA)+u"°-")
        else:
            self.TWA_strvar.set("%3.0f"%math.degrees(self.MaVie.TWA)+u"°")
        self.TWD_strvar.set("%3.0f"%math.degrees(self.MaVie.TW[0])+u"°")
        self.TWS_strvar.set("%3.1f"%self.MaVie.TW[1]+"knt")
        self.VMGTWD_strvar.set("%3.2f"%self.MaVie.VMGTWD()+"knts")
        hdg=self.MaVie.HDG()
        speed=self.MaVie.Speed()
        brg=self.MaVie.BRG(self.Arrivo)
        dist=self.MaVie.Dist(self.Arrivo)
        #if brg<>"nd":#caso dell'arrivo
        if dist>0:
            scarto=scartorotta(brg,self.Course[1])
            x=dist*math.cos(scarto)
            y=dist*math.sin(scarto)
            self.BRG_strvar.set("%3.0f"%math.degrees(brg)+u"°")
            self.Dist_strvar.set("%3.1f"%dist+"nm")
            self.VMGBRG_strvar.set("%3.2f"%self.MaVie.VMGWP(self.Arrivo)+"knts")
            self.Dist_strvar.set("%3.1f"%dist+"nm")
            self.XCourse_strvar.set("%3.1f"%x+"nm")
            self.YCourse_strvar.set("%3.1f"%y+"nm")
        else:#arrivo
            self.BRG_strvar.set(u"nd°")
            self.VMGBRG_strvar.set("0.00knts")
            self.XCourse_strvar.set("0.00nm")
            self.YCourse_strvar.set("0.00nm")
        self.VMGCourse_strvar.set("%3.2f"%self.MaVie.CMG(self.Course[1])+"knts")
        self.HDG_strvar.set("%3.0f"%math.degrees(hdg)+u"°")
        self.Speed_strvar.set("%3.2f"%speed+"knts")
        self.Log_strvar.set("%3.2f"%self.MaVie.Log+"nm")
        self.Dist_strvar.set("%3.1f"%dist+"nm")
        self.Lat_strvar.set(self.MaVie.StampaLat())
        self.Lon_strvar.set(self.MaVie.StampaLon())
        self.T_strvar.set(stampatempo(self.T))
        #aggiorna tracking        
        trackinfo=self.T_strvar.get()+"\t"
        trackinfo=trackinfo+self.TWD_strvar.get()+"\t"
        trackinfo=trackinfo+self.TWS_strvar.get()+"\t"
        trackinfo=trackinfo+self.TWA_strvar.get()+"\t"
        trackinfo=trackinfo+self.HDG_strvar.get()+"\t"
        trackinfo=trackinfo+self.Speed_strvar.get()+"\t"
        trackinfo=trackinfo+self.Log_strvar.get()+"\t"
        trackinfo=trackinfo+self.BRG_strvar.get()+"\t"
        trackinfo=trackinfo+self.Dist_strvar.get()+"\t"
        trackinfo=trackinfo+self.Lat_strvar.get()+"\t"
        trackinfo=trackinfo+self.Lon_strvar.get()+"\t"
        trackinfo=trackinfo+self.XCourse_strvar.get()+"\t"
        trackinfo=trackinfo+self.YCourse_strvar.get()+"\t"
        trackinfo=trackinfo+self.VMGTWD_strvar.get()+"\t"
        trackinfo=trackinfo+self.VMGBRG_strvar.get()+"\t"
        trackinfo=trackinfo+self.VMGCourse_strvar.get()+"\n"
        self.Track.config(state=NORMAL)
        self.Track.insert(2.0,trackinfo)
        self.Track.config(state=DISABLED)
        
        self.SettaBottoni()
        
    def SettaBottoni(self):
        if self.run:
            self.bottoneplay_strvar.set("Stop")#il bottone è Stop quando l'animazione è in corso
        else:
            self.bottoneplay_strvar.set("Play")
        if self.mode=="wind":
            self.LabelTWA.config(bg="red")
            self.LabelHDG.config(bg=infocolor)
        if self.mode=="compass":
            self.LabelTWA.config(bg=infocolor)
            self.LabelHDG.config(bg="red")
        if self.mode=="gps" or self.mode=="vmg":
            self.LabelTWA.config(bg=infocolor)
            self.LabelHDG.config(bg=infocolor)
            
    def DisegnaVettoriBarca(self):                                 
        iconafioccoranda=self.MaVie.Ruota()
        icona=iconafioccoranda[0]
        self.disegna2(icona,"orangered","icona")
        fiocco=iconafioccoranda[1]
        self.disegna2(fiocco,"orangered","fiocco")
        randa=iconafioccoranda[2]
        self.disegna2(randa,"orangered","randa")
        fsvettori=int(self.Graficosx.cget("height"))/30.0
        if self.mode=="gps":
            speed=self.MaVie.SpeedRoutage()
        else:
            speed=self.MaVie.Speed()
        hdg=self.MaVie.HDG()
        if speed>0:
            v=[(0,0),(fsvettori*speed*math.sin(hdg),fsvettori*speed*math.cos(hdg))]
            self.disegna2(v,"darkblue","v")
            iconafreccia=[(-0.75*fsvettori,0),(0,0),(0,0.75*fsvettori)]
            iconafrecciaruotata=[]
            for i in [0,1,2]:
                p=ruota(iconafreccia[i],hdg-math.radians(135))
                p=(p[0]+fsvettori*speed*math.sin(hdg),p[1]+fsvettori*speed*math.cos(hdg))
                iconafrecciaruotata.append(p)
            self.disegna2(iconafrecciaruotata,"darkblue","frecciavelocita")                                     
            hdgopposta=riduci360(self.MaVie.HDG()+2*self.MaVie.TWA)
            valtremura=[(0,0),(fsvettori*speed*math.sin(hdgopposta),fsvettori*speed*math.cos(hdgopposta))]
            self.disegna2(valtremura,"darkblue","vopp")
        else:
            self.Graficosx.delete("v")
            self.Graficosx.delete("frecciavelocita")
            self.Graficosx.delete("vopp")
        twx=fsvettori*self.MaVie.TW[1]*math.sin(self.MaVie.TW[0])
        twy=fsvettori*self.MaVie.TW[1]*math.cos(self.MaVie.TW[0])
        TW=[(0,0),(twx,twy),(twx+0.15*twy,twy-0.15*twx)]
        color=windcolor(self.MaVie.TW[1])
        self.disegna2(TW,color,"TW")
        brg=self.MaVie.BRG(self.Arrivo)
        dist=self.MaVie.Dist(self.Arrivo)
        if dist>0:#caso dell'arrivo
        #if brg<>"nd":#caso dell'arrivo
            rlvwp=[(0,0),(200*math.sin(brg),200*math.cos(brg))]
            self.disegna2(rlvwp,"yellow","rlvwm")
            twa=-self.MaVie.TWAmaxCMG(brg)#la polare è disegnata per barca mure a sinistra
            v=self.MaVie.Plr.Speed(self.MaVie.TW[1],math.copysign(twa,1))
            box=[(v*math.sin(twa)-0.15,v*math.cos(twa)-0.15),
                 (v*math.sin(twa)+0.15,v*math.cos(twa)-0.15),
                 (v*math.sin(twa)+0.15,v*math.cos(twa)+0.15),
                 (v*math.sin(twa)-0.15,v*math.cos(twa)+0.15),
                 (v*math.sin(twa)-0.15,v*math.cos(twa)-0.15)]
            boxruotato=[]
            for punto in box:
                boxscalato=(fsvettori*punto[0],fsvettori*punto[1])
                boxruotato.append(ruota(boxscalato,self.MaVie.TW[0]))
            self.disegna2(boxruotato,"navy","cmgmax")
        polare=self.MaVie.StampaPolare()
        polaresimmetrica=[]
        for punto in polare:
            polaresimmetrica.append([-punto[0],punto[1]])
        polaresimmetrica.reverse()
        polare=polare+polaresimmetrica[1:]
        polareruotata=[]
        for punto in polare:
            puntoscalato=(fsvettori*punto[0],fsvettori*punto[1])
            polareruotata.append(ruota(puntoscalato,self.MaVie.TW[0]))
        self.disegna2(polareruotata,"darkgray","polare")
        self.Graficosx.update()

    def disegna(self,vettore,color,tag):
        for i in range(0,len(vettore)-1):
            x1=-vettore[i][1]*self.FattoreDiScala*self.q
            y1=-vettore[i][0]*self.FattoreDiScala
            x2=-vettore[i+1][1]*self.FattoreDiScala*self.q
            y2=-vettore[i+1][0]*self.FattoreDiScala
            self.Graficodx.create_line(x1,y1,x2,y2,fill=color,tags=tag)
        #self.Graficodx.config(scrollregion=self.Graficodx.bbox(ALL))

    def disegna2(self,vettore,color,tag):
        self.Graficosx.delete(tag)
        height=float(self.Graficosx.cget("height"))
        width=float(self.Graficosx.cget("width"))
        fattorescala=min(height,width)/350.0
        for i in range(0,len(vettore)-1):
            x1=vettore[i][0]*fattorescala+width*0.5
            y1=-vettore[i][1]*fattorescala+height*0.5
            x2=vettore[i+1][0]*fattorescala+width*0.5
            y2=-vettore[i+1][1]*fattorescala+height*0.5
            self.Graficosx.create_line(x1,y1,x2,y2,fill=color,tags=tag)
        #self.Graficosx.config(scrollregion=self.Graficosx.bbox(ALL))
    def calcolabbox(self):
        #alfa=55-2.5*(1+int(self.Course[0]/100))
        #alfa=max(35,alfa)
        #alfa=math.radians(alfa)
        alfa=math.radians(45)
        rotta1=riduci360(self.Course[1]+alfa)
        rotta2=riduci360(self.Course[1]-alfa)
        distanza=self.Course[0]*0.5/math.cos(alfa)
        a=puntodistanterotta(self.Partenza[0],self.Partenza[1],distanza,rotta1)
        b=puntodistanterotta(self.Partenza[0],self.Partenza[1],distanza,rotta2)
        latmin=min(a[0],b[0],self.Partenza[0],self.Arrivo[0])
        latmax=max(a[0],b[0],self.Partenza[0],self.Arrivo[0])
        lonmin=min(a[1],b[1],self.Partenza[1],self.Arrivo[1])
        lonmax=max(a[1],b[1],self.Partenza[1],self.Arrivo[1])
        return [(latmax,lonmax),(latmin,lonmin)]
    def vento(self,lat,lon):
        if self.Esempio==1 or self.Esempio==2 or self.Esempio==3 or self.Esempio==4:#N4
            tws=16.0
            twd=math.radians(15.0)
        if self.Esempio==5 or self.Esempio==6:#N4 tendenza NNW
            tws=16.0
            twd=riduci360(math.radians(0.0)+math.radians(-22.5/12.0)*self.T)
        if self.Esempio==7 or self.Esempio==8:#S4 + oscillazione 30gradi/12ore
            tws=16.0
            omega=2*math.pi/12.0
            lamba=(2*math.pi)/(5.0*self.Course[0])
            losso=lossodromica(self.Partenza[0],self.Partenza[1],lat,lon)
            dist=losso[0]
            rlv=losso[1]
            propagazione=math.radians(30)#direzione di propagazione dell'oscillazione
            scarto=scartorotta(rlv,propagazione)
            distanza=dist*math.cos(scarto)
            twd=math.radians(180.0)+math.radians(30)*math.sin(omega*self.T+lamba*distanza)
        if self.Esempio==9 or self.Esempio==10:#zona Lipari e Circeo N, 3 settore est 4 settore ovest
            twd=math.radians(0.0)
            tws=10+(21-10)*(lon-LipariEstLon)/(LipariWestLon-LipariEstLon)
        if self.Esempio==11:#zona Circeo S3 settore est, 4 settore ovest, Lipari SSE3 settore est, 4 settore ovest
            twd=riduci360(math.radians(180.0)+math.radians(-22.5)*(PonzaLat-lat)/(PonzaLat-UsticaLat))        
            tws=10+(21-10)*(lon-LipariEstLon)/(LipariWestLon-LipariEstLon)
        if self.Esempio==12:#zona Circeo N3 settore est, 4 settore ovest, Lipari NNW3 settore est, 4 settore ovest
            twd=riduci360(math.radians(0.0)+math.radians(-22.5)*(PonzaLat-lat)/(PonzaLat-UsticaLat))        
            tws=10+(21-10)*(lon-CapoPalinuroLon)/(ArgentarioLon-CapoPalinuroLon)
        if self.Esempio==13:#N3 tendenza NNE3
            tws=16.0
            twd=riduci360(math.radians(0.0)+math.radians(22.5/12)*self.T)
        if self.Esempio==14:#NNE3 tendenza E3
            tws=16.0
            twd=riduci360(math.radians(22.5)+math.radians(67.5/12)*self.T)
        if self.Esempio==15:#N3 tendenza E3
            tws=16.0
            twd=riduci360(math.radians(0.0)+math.radians(90.0/12)*self.T)
        if self.Esempio==16:#ESE3 tendenza NNE3
            tws=16.0
            twd=riduci360(math.radians(112.5)+math.radians(-90.0/12)*self.T)
        if self.Esempio==17:#zona Ligure SSE3 settore est, 4 settore ovest 
            tws=10+(21-10)*(lon-LigureEstLon)/(LigureWestLon-LigureEstLon)
            twd=math.radians(157.5)
        if self.Esempio==18:#zona Ligure SSE3, S4 settore ovest 
            tws=10+(21-10)*(lon-LigureEstLon)/(LigureWestLon-LigureEstLon)
            twd=riduci360(math.radians(157.5)+math.radians(22.5)*(lon-LigureEstLon)/(LigureWestLon-LigureEstLon))
        if self.Esempio==19:#zona Ligure SSE5, S6 settore ovest 
            tws=21+(33-21)*(lon-LigureEstLon)/(LigureWestLon-LigureEstLon)
            twd=riduci360(math.radians(157.5)+math.radians(22.5)*(lon-LigureEstLon)/(LigureWestLon-LigureEstLon))
        if self.Esempio==20:#SE5 in attenuazione a SE2
            tws=21.0-(21-6.0)*(1-math.exp(-3.0/12.0*self.T))
            twd=riduci360(math.radians(135.0))
        if self.Esempio==21:#NE5 in attenuazione a NE2
            tws=21.0-(21-6.0)*(1-math.exp(-3.0/12.0*self.T))
            twd=riduci360(math.radians(45.0))
        if self.Esempio==22:#sett.Ovest3 su Bonifacio
            losso=lossodromica(BBonifacioLat,BBonifacioLon,lat,lon)
            D=losso[0]
            BRG=losso[1]
            twd=losso[1]
            if twd < math.pi:
                twd=twd-math.pi#ad est delle Bocche il vento soffia verso le Bocche
            tws=24-10*(1-math.e**-(0.05*D))#24 nodi a Bonifacio 14 nodi a 50nm
            if (BRG>math.radians(350) or BRG<math.radians(10)):
                tws=0.0
            if (BRG>math.radians(170) and BRG<math.radians(190)):
                tws=0.0
        if self.Esempio==23:#SW 20knts fronte freddo ovest baleari, muove ENE 24knots
            dirfronte=math.radians(240.0-1.5*self.T)#nel verso nord sud
            FrontePos=puntodistanterotta(TouloseLat,TouloseLon,24.0*self.T,math.radians(67.5))
            losso=lossodromica(FrontePos[0],FrontePos[1],lat,lon)
            dirfronteinversa=dirfronte+math.pi
            scarto=scartorotta(dirfronte,losso[1])
            distanzadalfronte=losso[0]*math.sin(scarto)
            sigma=math.tanh(distanzadalfronte*0.05)
            if losso[1]>dirfronte and losso[1]<dirfronteinversa:
                #NW 30knts ad Ovest del fronte
                twd=math.radians(270)+sigma*math.radians(45)
                tws=30.0
            else:                
                twd=math.radians(270)-sigma*math.radians(45)
                tws=20.0
        if self.Esempio==24:#var. depressionario, Low 1005mmbar in 41°00'N,4°00'E (1009mbar Partenza)
            LatCentroAzione=math.radians(41+0.0/60.0)
            LonCentroAzione=-math.radians(4+00.0/60.0)
            PCentroAzione=1005.0
            lamba=4*self.Course[0]
            vento=calcolaventogeostroficoCentroAzione(PCentroAzione,LatCentroAzione,LonCentroAzione,lamba,lat,lon)
            tws=vento[0]
            twd=vento[1]
        if self.Esempio==25:#H(1030)Azzorre + B(1010)Spagna +B(1005)Marcocco
            venti=[]
            HLat=math.radians(38)
            HLon=math.radians(28)
            HP=1030.0
            Hlamba=6*self.Course[0]
            vento=calcolaventogeostroficoCentroAzione(HP,HLat,HLon,Hlamba,lat,lon)
            venti.append(vento)
            Low1Lat=math.radians(39)
            Low1Lon=math.radians(4)
            Low1P=1010.0+self.T*3.0/24#si riempe di 3mmbar in 24ore
            Low1lamba=3*self.Course[0]
            vento=calcolaventogeostroficoCentroAzione(Low1P,Low1Lat,Low1Lon,Low1lamba,lat,lon)
            venti.append(vento)
            Low2Lat=math.radians(15)
            Low2Lon=math.radians(2)
            Low2P=1005.0-self.T*3.0/24#si scava di 3mmbar in 24ore
            Low2lamba=4*self.Course[0]
            vento=calcolaventogeostroficoCentroAzione(Low2P,Low2Lat,Low2Lon,Low2lamba,lat,lon)
            venti.append(vento)
            twx=0
            twy=0
            for vento in venti:
                twx=vento[0]*math.cos(vento[1])+twx
                twy=vento[0]*math.sin(vento[1])+twy
            tws=(twx**2+twy**2)**0.5
            twd=math.atan2(twy,twx)
            if twd<0:
                twd=twd+2*math.pi
        if self.Esempio==26:#Aliseo rotazione NNE a E
            rotazione=math.radians(65.0)
            losso=lossodromica(LanzaroteLat,LanzaroteLon,GuadalupeLat,GuadalupeLon)
            PtoLat=LanzaroteLat+0.75*(GuadalupeLat-LanzaroteLat)
            PtoLon=LanzaroteLon+0.75*(GuadalupeLon-LanzaroteLon)
            Distanza=0.75*0.5*losso[0]/math.cos(0.5*rotazione)
            CentroAzione=puntodistanterotta(PtoLat,PtoLon,Distanza,0.0)
            tws=24*(1-lat/(math.pi/2))
            twd=lossodromica(CentroAzione[0],CentroAzione[1],lat,lon)[1]
            twd=riduci360(twd-math.pi/2)
            latass=math.copysign(lat,1)
            correzione=(math.pi/2-twd)*(1-(math.tanh(latass))**0.1)
            twd=riduci360(twd+correzione)
        if self.Esempio==27:#grib
            tuplavento=self.GribMeteo.vento(self.T,math.degrees(lat),math.degrees(-lon))
            tws=tuplavento[0]*3600.0/1842.0
            twd=math.radians(tuplavento[1])
        if self.rafficautility:
            raffica=self.calcolaraffica(tws,lat,lon)
            tws=tws+raffica[0]
            twd=riduci360(twd+raffica[1])
        #tws=int(tws*10.0+0.5)*0.1#approssimazione alla prima cifra decimale
        return twd,tws
    def calcolaraffica(self,tws,lat,lon):
        #tre onde radianti da self.Partenza
        #prima onda: periodo 17*self.Dt ampiezza self.Course/5
        #seconda onda: periodo 57*self.Dt ore ampiezza self.Course/3        
        #terza ond: periodo 73*self.Dt ore ampiezza self.Course
        rafficaspeed=0
        rafficadirection=0
        r1=0.10*tws#oscillazioni del 10%
        d1=math.radians(10.0)*6.0/(tws+1)#oscillazioni 10° per TWS=5knots, minori per TWS>5knts 
        omega1=2*math.pi/(17.0*self.Dt)
        lamba1=2*math.pi/(self.Course[0]/5)
        alfa1=self.RitardiDiFase[0]
        r2=0.10*tws#oscillazioni del 10%
        d2=math.radians(20.0)*6.0/(tws+1)#oscillazioni 20° per TWS=5knots, minori per TWS>5knts
        omega2=2*math.pi/(57.0*self.Dt)
        lamba2=2*math.pi/(self.Course[0]/3)
        alfa2=self.RitardiDiFase[1]
        r3=0.10*tws#oscillazioni del 10%
        d3=math.radians(30.0)*6.0/(tws+1)#oscillazioni 30° per TWS=5knots, minori per TWS>5knts
        omega3=2*math.pi/(73.0*self.Dt)
        lamba3=2*math.pi/(self.Course[0])
        alfa3=self.RitardiDiFase[2]
        dist=lossodromica(self.Partenza[0],self.Partenza[1],lat,lon)[0]
        rafficaspeed=(r1*math.cos(omega1*self.T+lamba1*dist+alfa1)+
                      r2*math.cos(omega2*self.T+lamba2*dist+alfa2)+
                      r3*math.cos(omega3*self.T+lamba3*dist+alfa3))
        rafficadirection=(d1*math.cos(omega1*self.T+lamba1*dist+alfa1)+
                          d2*math.cos(omega2*self.T+lamba2*dist+alfa2)+
                          d3*math.cos(omega3*self.T+lamba3*dist+alfa3))
        return rafficaspeed,rafficadirection

#FUNZIONI
def stampatempo(t):
    #rende un tempo decimale (3.50) in formato xxhyym ("3h30m")
    ore=int(t)
    minuti=int((t-ore)*60)
    resto=t-ore-minuti*1.0/60
    if resto*3600>30:
        minuti=minuti+1
        if minuti>60:
            minuti=0
            ore=ore+1
    stringaore=str(ore)+"h"
    stringaminuti="%2d"%minuti+"m"
    stringaminuti.replace(" ","0")
    return stringaore+stringaminuti
def calcolaventogeostrofico(lat,GradientePressione,R):
    omega=2*math.pi/(24*3600)#rotazione terrestre
    f=2*omega*math.sin(lat)#parametro di coriolis
    densitaaria=1.2#kgm/mc vale per T=20gradi
    R=R*1853.0#curvatura isobare espressa in m
    GradientePressione=GradientePressione*100.0/1853.0#Gradiente espresso in Pa/m
    segno=GradientePressione/math.copysign(GradientePressione,1)
    a=segno/R
    b=-f
    c=math.copysign(GradientePressione,1)/densitaaria
    discriminante=(b**2-4*a*c)
    if discriminante >0:
        tws=(-b-discriminante**0.5)/(2*a)
        tws=tws*3600.0/1853.0#converte tws in knts
    else:
        tws=0.0#caso del centro di alta pressione
    return tws
def calcolaventogeostroficoCentroAzione(PCentroAzione,LatCentroAzione,LonCentroAzione,lamba,lat,lon):
    #campo di alta pressione: P=(H-1013)*cos(2pi/lamba*r)+1013, per r<=lamba/2, P=1013 per r >lamba/2
    #campo di bassa pressione: P=(1013-L)*cos(2pi/lamba*r+pi/2)+L, per r<=lamba/2, P=1013 per r>lamba/2
    #r distanza dal centro d'azione e raggio curvatura isobara
    losso=lossodromica(LatCentroAzione,LonCentroAzione,lat,lon)
    r=losso[0]
    brg=losso[1]
    tws=0
    twd=0
    segno=0
    if r<0.5*lamba:
        if PCentroAzione>1013:
            GradientePressione=-(PCentroAzione-1013)*2*math.pi/lamba*math.sin(2*math.pi/lamba*r)
            segno=1
        else:
            GradientePressione=-(1013-PCentroAzione)*2*math.pi/lamba*math.sin(2*math.pi/lamba*r)
            segno=-1
        tws=calcolaventogeostrofico(LatCentroAzione,GradientePressione,r)
        
        if LatCentroAzione>0:
            twd=riduci360(brg-segno*math.pi/2)#emisfero Nord
        else:
            twd=riduci360(brg+segno*math.pi/2)#emisfero Sud
    return tws,twd
def windcolor(tws):
    color=""
    if tws>=0 and tws<3:color="#0000CC"
    if tws>=3 and tws<6:color="#0066FF"
    if tws>=6 and tws<9:color="#00FFFF"    
    if tws>=9 and tws<12:color="#00FF66"
    if tws>=12 and tws<15:color="#00CC00"
    if tws>=15 and tws<18:color="#66FF33"
    if tws>=18 and tws<21:color="#CCFF33"
    if tws>=21 and tws<24:color="#FFFF66"
    if tws>=24 and tws<27:color="#FFCC00"
    if tws>=27 and tws<30:color="#FF9900"
    if tws>=30 and tws<33:color="#FF6600"
    if tws>=33 and tws<36:color="#FF3300"
    if tws>=36 and tws<39:color="#FF0000"
    if tws>=39 and tws<42:color="#CC6600"
    if tws>=42:color="#CC0000"
    return color

def interno(poligono,pto):
    #poligono orientato in senso orario
    somma=0
    for i in range(0,len(poligono)-1):
        v1=poligono[i]
        v2=poligono[i+1]
        rlv1=math.atan2((v1[1]-pto[1]),(v1[0]-pto[0]))
        if rlv1<0:rlv1=2*math.pi+rlv1
        rlv2=math.atan2((v2[1]-pto[1]),(v2[0]-pto[0]))
        if rlv2<0:rlv2=2*math.pi+rlv2
        angolo=math.copysign(rlv2-rlv1,1)
        if angolo>math.pi:
            angolo=2*math.pi-angolo
        somma=somma+angolo
    if somma<2*math.pi:
        Interno=False
    else:
        Interno=True
    return Interno

def arrotonda(alfa, precisione=1.0):
    #arrotonda un angolo (espresso in radianti) al grado
    if alfa>=0:
        alfarounded=int(alfa*1.0/math.radians(precisione)+0.5)*math.radians(precisione)
    else:
        alfarounded=int(alfa*1.0/math.radians(precisione)-0.5)*math.radians(precisione)
    return alfarounded
	


#MAIN------------------------------------------------------------
root=Tk()
MiaApplicazione=FinestraMain(root)
root.title("Simulatore Regata 3.0, 17.04.2013")
MiaApplicazione.inizia()
root.mainloop()
