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
        self.refresh_local_polars()

        if self.storage.enabled:
            logger.info("Loading enabled polars from storage: %s", self.storage.enabled)
            for p in self.storage.enabled:
                if p in self.polars_files:
                    self.enable(p)
        else:
            self.storage.enabled = []
            logger.info("No enabled polars found in storage, initializing with default polars.")
            self.enable(self.polars_files[0]) if self.polars_files else None



    def refresh_local_polars(self):
        if not os.listdir(POLAR_DIR):
            default_polar = os.listdir(resource_path("gweatherrouting", "data/polars/"))
            for p in default_polar:
                target_filepath = os.path.join(POLAR_DIR, p)
                polar_file_path = resource_path("gweatherrouting", f"data/polars/{p}")
                shutil.copyfile(polar_file_path, target_filepath)
        
        for p in os.listdir(POLAR_DIR):
            self.polars_files.append(p)
        self.polars_files.sort()

    def store_enabled_polars(self):
        ss: List = []
        for x in self.polars:
            try:
                ss.index(x)
            except:
                ss.append(x)
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
        self.store_enabled_polars()
        self.dispatch("polars-list-updated", self.polars)

    def disable(self, name):
        if name in self.storage.enabled:
            self.polars.remove(name)
            # TODO: Remove from storage
            self.polars.sort()
            self.storage.save() 

        self.polars.sort()
        self.store_enabled_polars()
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
        file_name = os.path.basename(polar_path)
        file_path = os.path.join(POLAR_DIR, file_name)
        shutil.copyfile(polar_path, file_path)
        logger.info(f"Copied {polar_path} to {file_path}")
        self.polars_files.append(file_name)
        self.polars_files.sort()
        self.enable(file_name)
        self.dispatch("polars-list-updated", self.polars)
    
    def get_path(self, name):
        if name not in self.polars:
            logger.error(f"Polar {name} not found in the list of polars.")
            return None 
        return os.path.join(POLAR_DIR, name)

    def download_orc_polar(self, orc_polar_name):
        file_name = orc_polar_name.replace("/", "_")
        file_name = f"{file_name}.pol"
        source_path = os.path.join(POLAR_DIR, 'test.pol')
        destination_path = os.path.join(POLAR_DIR, file_name)
        try:
            shutil.copy2(source_path, destination_path)
            logger.info(f"Copied {source_path} to {destination_path}")
            self.polars_files.append(file_name)
            self.polars_files.sort()
            self.enable(file_name)
            self.dispatch("polars-list-updated", self.polars)
        except Exception as e:
            logger.error(f"Failed to download orc polar {orc_polar_name}: {str(e)}")
            raise e