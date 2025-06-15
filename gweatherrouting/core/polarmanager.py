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
        self.load_or_save_default()

class PolarManager(EventDispatcher):
    def __init__(self):
        EventDispatcher.__init__(self)
        self.storage = PolarManagerStorage()
        self.polars_files = []
        self.polars = []

        self.load_default_pol()

    def load_default_pol(self):
        if not os.listdir(POLAR_DIR):
            default_polar = os.listdir(resource_path("gweatherrouting", "data/polars/"))
            for p in default_polar:
                target_filepath = os.path.join(POLAR_DIR, p)
                polar_file_path = resource_path("gweatherrouting", f"data/polars/{p}")
                shutil.copyfile(polar_file_path, target_filepath)
        
        for p in os.listdir(POLAR_DIR):
            self.polars_files.append(p)
            self.enable(p)
        self.polars_files.sort()

    '''
    def refresh_polars(self):
        self.polars = []
        for x in self.polars_files:
            if self.is_enabled(x):
                self.polars.append(x)
        self.polars.sort()
    '''
    def store_enabled_polars(self):
        ss: List = []
        for x in self.polars:
            try:
                ss.index(x.name)
            except:
                ss.append(x.name)
        self.storage.enabled = ss
    
    def load(self, path):
        logger.info("Loading polar %s", path)
        polar_name = path.split("/")[-1]
        self.polars.append(polar_name)
    
    def enable(self, name):
        if name not in self.polars:
            self.polars.append(name)
        if name not in self.storage.enabled:
            self.storage.enabled.append(name)
            self.storage.save()
        self.polars.sort()
        self.dispatch("polars-list-updated", self.polars)

    def disable(self, name):
        if name in self.storage.enabled:
            self.polars.remove(name)
            # TODO: Remove from storage
            self.polars.sort()
            self.storage.save() 

        self.polars.sort()
        self.dispatch("polars-list-updated", self.polars)
    
    def is_enabled(self, name) -> bool:
        return name in self.polars
    
    def delete_polar(self, name):
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
        self.polars_files.append(polar_filename)
        self.polars_files.sort()
        self.enable(polar_filename)
        self.dispatch("polars-list-updated", self.polars)
    
    def get_path(self, name):
        if name not in self.polars:
            logger.error(f"Polar {name} not found in the list of polars.")
            return None 
        return os.path.join(POLAR_DIR, name)