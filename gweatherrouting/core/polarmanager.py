import logging
import os
import shutil
from shutil import copyfile
from typing import Dict, List

from gweatherrouting.common import resource_path
from gweatherrouting.core.storage import POLAR_DIR, Storage
from gweatherrouting.core.utils import EventDispatcher

logger = logging.getLogger("gweatherrouting")

class PolarManagerStorage(Storage):
    def __init__(self):
        Storage.__init__(self, "polar-manager")
        self.opened = []
        self.load_or_save_default()

class PolarManager(EventDispatcher):
    def __init__(self):
        EventDispatcher.__init__(self)
        self.storage = PolarManagerStorage()
        self.load_default_pol()
        self.polars_files = None

        self.polars = []
        self.refresh_polars()

        for x in self.storage.opened:
            self.enable(x)

    def load_default_pol(self):
        if not os.listdir(POLAR_DIR):
            default_polar = os.listdir(resource_path("gweatherrouting", "data/polars/"))
            for p in default_polar:
                target_filepath = os.path.join(POLAR_DIR, p)
                polar_file_path = resource_path("gweatherrouting", f"data/polars/{p}")
                shutil.copyfile(polar_file_path, target_filepath)

    def refresh_polars(self):
        self.polars = []
        for x in os.listdir(POLAR_DIR):
            if x[-4:] == ".pol":
                self.polars.append(x)
    
    def store_active_polars(self):
        ss: List = []
        for x in self.polars:
            try:
                ss.index(x.name)
            except:
                ss.append(x.name)
        self.storage.opened = ss
    
    def load(self, path):
        logger.info("Loading polar %s", path)
        polar_name = path.split("/")[-1]
        self.polars.append(polar_name)
    
    def enable(self, name):
        if name in self.polars:
            self.storage.opened.append(name)
            self.storage.save() 
            logger.info(f"Enabled polar: {name}")
            self.dispatch("polars-enabled", name, True)
    
    def disable(self, name):
        if name in self.storage.opened:
            self.storage.opened.remove(name)
            self.storage.save() 
            logger.info(f"Disabled polar: {name}")
            self.dispatch("polars-enabled", name, False)
    
    def is_enabled(self, name) -> bool:
        return name in self.storage.opened
    
    def remove(self, name):
        file_path = os.path.join(POLAR_DIR, name)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Removed polar file: {file_path}")
            self.refresh_polars() 
            self.dispatch("polars-list-updated")

    def add_polar_file(self, polar_path):
        polar_filename = os.path.basename(polar_path)
        target_filepath = os.path.join(POLAR_DIR, polar_filename)
        shutil.copyfile(polar_path, target_filepath)
        logger.info(f"Copied {polar_path} to {target_filepath}")
        self.refresh_polars()
        self.dispatch("polars-list-updated", self.polars)