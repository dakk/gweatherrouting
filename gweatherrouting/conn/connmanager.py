import logging
import serial
import time
from threading import Thread
import serial.tools.list_ports
from . import SerialDataSource

logger = logging.getLogger ('gweatherrouting')

class ConnManager:
    def __init__(self):
        self.running = True
        self.sources = {}
        self.messageHandlers = []

    def __del__(self):
        self.running = False

    def plugAll(self):
        for x in serial.tools.list_ports.comports():
            try:
                self.sources[x.device] = SerialDataSource(x.device)
                logger.info ('Detected new data source: %s [%s]' % (x.device, x.description))
            except:
                pass 

    def poll(self):
        dd = []
        todel = []

        for x in self.sources:
            ds = self.sources[x]
            try:
                d = ds.read()
                if len(d): 
                    dd += d
            except:
                logger.info ('Data source %s disconnected' % ds.uri)
                todel.append(x)

        if len(dd) > 0:
            for x in self.messageHandlers:
                x(dd)

        if len(todel) > 0:
            for x in todel:
                del self.sources[x]
        if len(self.sources) == 0:
            self.plugAll()


    def pollLoop(self):
        while self.running:
            self.poll()
            time.sleep(0.5)

    def startPolling(self):
        logger.info ('Polling started')
        self.thread = Thread(target=self.pollLoop, args=())
        self.thread.start()
