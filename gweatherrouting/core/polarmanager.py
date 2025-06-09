import logging
import os
import shutil
from shutil import copyfile
from typing import Dict, List


from gweatherrouting.core.storage import POLAR_DIR, Storage

logger = logging.getLogger("gweatherrouting")

class PolarManagerStorage(Storage):
    def __init__(self):
        Storage.__init__(self, "polar-manager")
        self.opened = []
        self.load_or_save_default()

class PolarManager():
    def __init__(self):
        self.storage = PolarManagerStorage()
        self.polars_files = None

        self.polars = []
        self.refresh_local_polars()

        for x in self.storage.opened:
            self.enable(x)
    
    def refresh_local_polars(self):
        self.local_polars = []
        for x in os.listdir(POLAR_DIR):
            if x[-4:] == ".pol":
                self.local_polars.append(x)
    
    def store_opened_polars(self):
        ss: List = []
        for x in self.polars:
            try:
                ss.index(x.name)
            except:
                ss.append(x.name)
        self.storage.opened = ss