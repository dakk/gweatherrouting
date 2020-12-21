import serial
import pynmea2
from . import DataSource

class SerialDataSource(DataSource):
    def __init__(self, port):
        self.uri = port
        self.s = serial.Serial(port)

    def read(self):
        msgs = []

        if (self.s.inWaiting() > 0):
            d = self.s.read(self.s.inWaiting()).decode('ascii')

            for x in d.split('\n'):
                try:
                    msg = pynmea2.parse(x)
                    msgs.append(msg)
                except:
                    pass
        
        return msgs
