import requests
import logging
import tempfile
import random
import struct

from .. import config

logger = logging.getLogger ('regattasim')


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

def str8bit(data):
	#data 1 octect
	flag=struct.unpack("1B",data)[0]#integer
	flag=bin(flag)[2:]#stringa di bit
	if len(flag)<8:
		flag=(8-len(flag))*"0"+flag
	return flag

class GribRecordParseException (Exception):
	pass

class GribRecordNotEquidistantException (Exception):
	pass

class GribRecord:
	def __init__ (self, f):
		## Section 0
		data = f.read (8)
		sez0 = struct.unpack ("4s1B1B1B1B", data)

		if sez0[0] != b"GRIB" or sez0[4] != 1:
			raise GribRecordParseException ()

		length = sez0[1] * 256 * 256 + sez0[2] * 256 + sez0[3]

		## Section 1 - Product definition
		data = f.read (3)
		t = struct.unpack ("1B1B1B", data)
		sez1len = t[0] * 256 * 256 + t[1] * 256 + t[2]

		f.read (1)
		data = f.read(1)#bit 5
		#record.center=struct.unpack("1B",data)[0] # centro emissione bollettino
		f.read(1)
		f.read(1)

		data=f.read(1)#bit 8
		flagoptionalsez=str8bit(data)#flag GDS BMS yes/not

		data=f.read(1)#bit 9
		self.parameter=struct.unpack("1B",data)[0]
		data=f.read(1)#bit 10
		#record.level=struct.unpack("1B",data)[0]
		data=f.read(2)#bit 11-12
		#tupla=struct.unpack("1B1B",data)
		#record.height=0
		#if record.level in [20,100,103,105,107,109,111,113,115,117,119,125,160]:
		#	record.height=tupla[0]*256+tupla[1]
		#if record.level in [101,104,106,108,110,112,114,116,120,121,128,141]:
		#	record.height=(tupla[0],tupla[1])
		data=f.read(1)#bit 13
		year = struct.unpack("1B",data)[0]
		data=f.read(1)#bit 14
		month = struct.unpack("1B",data)[0]
		data=f.read(1)#bit 15
		day = struct.unpack("1B",data)[0]
		data=f.read(1)#bit 16
		hour = struct.unpack("1B",data)[0]
		data=f.read(1)#bit 17
		minute = struct.unpack("1B",data)[0]
		
		self.date = (year + 2000, month, day, hour, minute)
		
		data=f.read(1)#bit 18
		self.timeunits=struct.unpack("1B",data)[0]

		data=f.read(1)#bit 19
		#self.p1=struct.unpack("1B",data)[0]#atteso 0
		data=f.read(1)#bit 20
		self.time=struct.unpack("1B",data)[0]#! tempo di riferimento
		f.read (6)

		data=f.read(2)#bit 27-28
		tupla=struct.unpack("1B1B",data)
		if tupla[0]>=128:
			D=(tupla[0]-128)*256+tupla[1]
			D=-D
		else:
			D=tupla[0]*256+tupla[1]
		#record.D=D
		f.read(sez1len-28)

		## Section 2 - Grid definition (optional)
		lenghtsez2 = 0
		if flagoptionalsez[0]=="1":
			data=f.read(3)#bit 1-3
			tupla=struct.unpack("1B1B1B",data)
			sez2len=tupla[0]*256*256+tupla[1]*256+tupla[2]
			f.read(1)#bit 4
			f.read(1)#bit 5
			data=f.read(1)#bit 6        
			DRType=struct.unpack("1B",data)[0]
			
			if DRType != 0:
				f.read (length - sez1len - sez2len - 6)
				raise GribRecordNotEquidistantException ()
			else:#griglia equidistante bit 7-32
				data=f.read(2)#bit 7-8
				tupla=struct.unpack("1B1B",data)
				NI=tupla[0]*256+tupla[1]#npti sul parallelo
				data=f.read(2)#bit 9-10
				tupla=struct.unpack("1B1B",data)
				NJ=tupla[0]*256+tupla[1]#npti sul meridiano

				self.size = (NI, NJ)

				data=f.read(3)#bit 11-13
				tupla=struct.unpack("1B1B1B",data)
				if tupla[0]>=128:#sud
					LA1=(tupla[0]-128)*256*256+tupla[1]*256+tupla[2]
					LA1=-LA1
				else:
					LA1=tupla[0]*256*256+tupla[1]*256+tupla[2]
				LA1=LA1*10**-3#lat. primo punto in millesimi di grado

				data=f.read(3)#bit 14-16
				tupla=struct.unpack("1B1B1B",data)
				if tupla[0]>=128:#west
					LO1=(tupla[0]-128)*256*256+tupla[1]*256+tupla[2]        
					LO1=-LO1
				else:
					LO1=tupla[0]*256*256+tupla[1]*256+tupla[2]
				LO1=LO1*10**-3#lon. primo punto in millesimi di grado
				if LO1>180:LO1=360-LO1
				if LO1<=-180:LO1=LO1+360
				LO1=LO1

				data=f.read(1)#bit 17
				flaguvcomp=str8bit(data)#stringa di 8bit

				data=f.read(3)#bit 18-20
				tupla=struct.unpack("1B1B1B",data)
				if tupla[0]>=128:#sud
					LA2=(tupla[0]-128)*256*256+tupla[1]*256+tupla[2]
					LA2=-LA2
				else:
					LA2=tupla[0]*256*256+tupla[1]*256+tupla[2]
				LA2=LA2*10**-3#lat. ultimo punto in millesimi di grado

				data=f.read(3)#bit 21-23
				tupla=struct.unpack("1B1B1B",data)
				if tupla[0]>=128:#west
					LO2=(tupla[0]-128)*256*256+tupla[1]*256+tupla[2]
					LO2=-LO2
				else:
					LO2=tupla[0]*256*256+tupla[1]*256+tupla[2]
				LO2=LO2*10**-3#lon. ultimo punto in millesimi di grado
				if LO2>180:LO2=360-LO2
				if LO2<=-180:LO2=LO2+360
				LO2=LO2

				self.bounds = [(LA1, LO1), (LA2, LO2)]

				data=f.read(2)#bit 24-25 DI
				DI=(LO1 - LO2)*1.0 / (NI-1)
				data=f.read(2)#bit 26-27 DJ
				DJ=(LA1-LA2)*1.0/(NJ-1)

				self.dirincrement = (DI, DJ)

				data=f.read(1)
				#record.flagscanmode=str8bit(data)#stringa di 8bit
				
				f.read (4)
		
		# Section 3 - Bit map (optional)
		lenghtsez3=0
		if flagoptionalsez[1]=="1":
			data=f.read(3)#bit 1-3
			tupla=struct.unpack("1B1B1B",data)
			lenghtsez3=tupla[0]*256*256+tupla[1]*256+tupla[2]
			data=f.read(1)#bit 4
			unused=struct.unpack("1B",data)[0]
			data=f.read(2)#bit 5,6
			tupla=struct.unpack("1B1B",data)
			tablereferenze=tupla[0]*256+tupla[1]
			#record.grid=record.NJ*[range(0,record.NI)]
			#tuplaij=record.inizializzaij()
			i=tuplaij[0]
			j=tuplaij[1]
			for k in range(7,lenghtsez3+1):#bit 7-lenghtsez3
				data=f.read(1)
				print (struct.unpack("1B",data)[0])
				#record.grid[j][i]=struct.unpack("1B",data)[0]
				#incremento i,j in accordo a scanmode
				#tuplaij=record.incrementaij(i,j)
				#i=tuplaij[0]
				#j=tuplaij[1]
			else:
				f.read(lenghtsez3-3)

		
		## Section 4 - Binary data
		data=f.read(3)#bit 1-3
		tupla=struct.unpack("1B1B1B",data)
		lenghtsez4=tupla[0]*256*256+tupla[1]*256+tupla[2]
		data=f.read(1)#bit 4 Flag (see Code table 11) (first 4 bits). Number of unused bits at end of Section 4 (last 4 bits)
		flagdata=str8bit(data)
		unused=int(flagdata[4:],2)
		data=f.read(2)#bit 5-6 Scale factor (E)
		tupla=struct.unpack("1B1B",data)
		if tupla[0]>128:
			E=(tupla[0]-128)*256+tupla[1]
			E=-E
		else:
			E=tupla[0]*256+tupla[1]
		data=f.read(4)#bit 7-10 Reference value (minimum of packed values)
		R=floatpoint(data)
		data=f.read(1)#bit 11 Number of bits containing each packed value
		nbit=struct.unpack("1B",data)[0]
		if flagdata[0]=="0" and flagdata[1]=="0" and flagdata[2]=="0" and flagdata[3]=="0":
			#record.grid=[]
			#for i in range(0,record.NJ):
			#    record.grid.append(range(0,record.NI))
			bufferstr=""
			#tuplaij=record.inizializzaij()
			#i=tuplaij[0]
			#j=tuplaij[1]
			octectreaded=11
			for N in range(0,NI*NJ):
				#leggiamo nbit
				n=int ((nbit-len(bufferstr))/8+1)
				octectreaded=octectreaded+n
				for k in range(0,n):
					data=f.read(1)
					bufferstr=bufferstr+str8bit(data)
				Xstr=bufferstr[0:nbit]
				X=int(Xstr,2)
				bufferstr=bufferstr[nbit:]

				#print ((R+X*2**E)*10**-D)
				#
				#record.grid[j][i]=(R+X*2**E)*10**-D
				#incremento i,j in accordo a scanmode
				#tuplaij=record.incrementaij(i,j)
				#i=tuplaij[0]
				#j=tuplaij[1]
			f.read(lenghtsez4-octectreaded)
		else:
			f.read(lenghtsez4-11)


		data=f.read (4)
		tupla=struct.unpack ("4s",data)
		if tupla[0] != b"7777":
			raise GribRecordParseException ()

		print (self.date, self.bounds, self.timeunits, self.time, self.parameter)

	def getValue (self, lat, lon):
		return 0.0

		
class Grib:
	def __init__ (self):
		#self.parse (open ('/home/dakk/testgrib.grb', 'rb'))
		self.records = []
		self.rindex = {}

	# Return [dir (degree), speed]
	def getWind (self, t, lat, lon):
		#return [random.random () * 6, random.random () * 10]
		print (self.rindex)
		wdir = self.rindex[33][t].getValue (lat, lon)
		wspeed = self.rindex[34][t].getValue (lat, lon)

		return [wdir, wspeed]

	def parse (self, f):
		self.records = []
		self.rindex = {}
		i = 0
		while True:
			i += 1
			try:
				rec = GribRecord (f)
			except:
				return True
			
			self.records.append (rec)

			if not (rec.parameter in self.rindex):
				self.rindex [rec.parameter] = {}

			self.rindex [rec.parameter][rec.time] = rec

			if i == 4:
				return True

	def download (self, uri, percentageCallback, callback):
		logger.info ('starting download of %s' % uri)

		response = requests.get(uri, stream=True)
		total_length = response.headers.get('content-length')
		last_signal_percent = -1
		f = open ('/home/dakk/testgrib.grb', 'wb')

		if total_length is None:
			pass
		else:
			dl = 0
			total_length = int(total_length)
			for data in response.iter_content (chunk_size=4096):
				dl += len (data)
				f.write (data)
				done = int (100 * dl / total_length)
				
				if last_signal_percent != done:
					percentageCallback (done)  
					last_signal_percent = done
		
		f.close ()
		logger.info ('download completed %s' % uri)

		self.parse (open ('/home/dakk/testgrib.grb', 'rb'))
		callback (True)